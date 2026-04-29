import threading
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from config.settings import Settings
from core.github_fetcher import GitHubFetcher
from core.rule_matcher import RuleMatcher
from core.repo_evaluator import RepoEvaluator
from core.llm_summarizer import LLMSummarizer
from database.connection import DatabaseConnection
from database.crud import CrudOperations
from models.errors import AppError, ErrorCode


class TaskCallback:
    """任务执行回调接口。"""

    def on_start(self) -> None:
        """任务开始回调。"""

    def on_progress(self, step: str, current: int, total: int) -> None:
        """任务进度回调。"""

    def on_complete(self, result: dict) -> None:
        """任务完成回调。"""

    def on_error(self, error: AppError) -> None:
        """任务错误回调。"""


class Scheduler:
    """定时任务调度器。

    负责编排完整的推送任务流程，协调各核心模块的调用顺序。
    """

    TOTAL_STEPS = 9

    def __init__(self, db: DatabaseConnection, settings: Settings | None = None):
        self.db = db
        self.crud = CrudOperations(db)
        self._settings = settings or Settings.get_instance()
        self._scheduler: BackgroundScheduler | None = None
        self._is_running = False
        self._cancel_flag = False
        self._callback: TaskCallback | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_callback(self, callback: TaskCallback) -> None:
        """设置任务回调。"""
        self._callback = callback

    def run_task(self, callback: TaskCallback | None = None) -> None:
        """执行完整的推送任务（在后台线程中运行）。"""
        if callback:
            self._callback = callback

        with self._lock:
            if self._is_running:
                logger.warning("任务正在执行中，忽略重复请求")
                return
            self._is_running = True
            self._cancel_flag = False

        thread = threading.Thread(target=self._run_task_internal, daemon=True)
        thread.start()

    def cancel_task(self) -> None:
        """取消正在执行的任务。"""
        self._cancel_flag = True
        logger.info("已发送取消任务信号")

    def _check_cancel(self) -> bool:
        """检查是否收到取消信号。"""
        return self._cancel_flag

    def _notify_start(self) -> None:
        if self._callback:
            self._callback.on_start()

    def _notify_progress(self, step: str, current: int) -> None:
        if self._callback:
            self._callback.on_progress(step, current, self.TOTAL_STEPS)

    def _notify_complete(self, result: dict) -> None:
        if self._callback:
            self._callback.on_complete(result)

    def _notify_error(self, error: AppError) -> None:
        if self._callback:
            self._callback.on_error(error)

    def _run_task_internal(self) -> None:
        """内部任务执行逻辑。"""
        try:
            self._notify_start()
            result = self._execute_pipeline()
            self._notify_complete(result)
        except AppError as e:
            logger.error(f"任务执行失败: {e.message}")
            self._notify_error(e)
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            self._notify_error(AppError(ErrorCode.EVAL_ERROR, str(e)))
        finally:
            with self._lock:
                self._is_running = False
                self._cancel_flag = False

    def _execute_pipeline(self) -> dict:
        """执行完整的推送任务流水线。"""
        settings = self._settings
        fetcher = GitHubFetcher(settings)
        matcher = RuleMatcher(self.db)
        evaluator = RepoEvaluator(self.db, settings)
        summarizer = LLMSummarizer(self.db, settings)

        try:
            # 步骤1：获取Trending项目
            self._notify_progress("获取GitHub Trending项目", 1)
            if self._check_cancel():
                return {"status": "cancelled"}
            trending_repos = fetcher.fetch_trending_repos(
                since=settings.get("github.growth_period", "daily")
            )
            for repo in trending_repos:
                repo["_from_trending"] = True

            # 步骤1：按规则Search API搜索
            self._notify_progress("按规则搜索GitHub项目", 1)
            if self._check_cancel():
                return {"status": "cancelled"}
            rules = self.crud.get_rules(enabled_only=True)
            search_repos = []
            for rule in rules:
                import json
                keywords = json.loads(rule.get("keywords", "[]")) if isinstance(rule.get("keywords"), str) else rule.get("keywords", [])
                topics = json.loads(rule.get("topics", "[]")) if isinstance(rule.get("topics"), str) else rule.get("topics", [])
                language = rule.get("language", "")
                min_stars = settings.get("github.min_stars", 100)

                if keywords:
                    try:
                        repos = fetcher.search_repos_by_query(keywords, topics, language, min_stars)
                        search_repos.extend(repos)
                    except Exception as e:
                        logger.warning(f"规则 '{rule.get('name')}' 搜索失败: {e}")

            # 合并去重
            all_repos = trending_repos + search_repos
            seen = set()
            unique_repos = []
            for repo in all_repos:
                fn = repo.get("full_name", "")
                if fn not in seen:
                    seen.add(fn)
                    unique_repos.append(repo)

            # max_repos_per_fetch截断
            max_repos = settings.get("github.max_repos_per_fetch", 50)
            if len(unique_repos) > max_repos:
                unique_repos.sort(key=lambda r: r.get("stars", 0), reverse=True)
                unique_repos = unique_repos[:max_repos]

            candidate_count = len(unique_repos)
            logger.info(f"步骤1完成: 候选仓库 {candidate_count} 个")

            # 存储候选仓库
            self.crud.upsert_repositories(unique_repos)

            # 重新从数据库读取（获取id）
            stored_repos = []
            for repo in unique_repos:
                db_repo = self.crud.get_repository_by_name(repo["full_name"])
                if db_repo:
                    for json_field in ("topics", "eval_details"):
                        val = db_repo.get(json_field)
                        if isinstance(val, str):
                            try:
                                db_repo[json_field] = json.loads(val)
                            except (json.JSONDecodeError, TypeError):
                                db_repo[json_field] = [] if json_field == "topics" else {}
                    merged = {**repo, **db_repo}
                    if "stars_growth" not in merged or merged["stars_growth"] == 0:
                        merged["stars_growth"] = repo.get("stars_growth", 0)
                    if "_from_trending" in repo:
                        merged["_from_trending"] = True
                    stored_repos.append(merged)

            # 步骤2：规则匹配
            self._notify_progress("执行规则匹配", 2)
            if self._check_cancel():
                self._rollback_eval(stored_repos)
                return {"status": "cancelled"}

            self.crud.clear_match_records()
            matched_repos = matcher.match_rules(stored_repos, rules)
            matched_count = len(matched_repos)

            # 步骤3-6：综合评估
            self._notify_progress("综合评估仓库", 3)
            if self._check_cancel():
                self._rollback_eval(matched_repos)
                return {"status": "cancelled"}

            top_n = settings.eval_top_n
            top_repos = evaluator.evaluate_repos(matched_repos, top_n, summarizer)

            # 步骤7-8：获取README + LLM评估已在evaluate_repos中完成
            self._notify_progress("获取项目README", 5)
            if self._check_cancel():
                self._rollback_eval(top_repos)
                return {"status": "cancelled"}

            for repo in top_repos:
                try:
                    readme = fetcher.get_readme_content(repo.get("full_name", ""))
                    repo["_readme_content"] = readme
                except Exception as e:
                    logger.warning(f"获取README失败 ({repo.get('full_name')}): {e}")
                    repo["_readme_content"] = ""

            # 步骤9：生成总结报告
            self._notify_progress("生成总结报告", 7)
            if self._check_cancel():
                self._rollback_eval(top_repos)
                return {"status": "cancelled"}

            summary_content = summarizer.generate_summary(top_repos)

            self._notify_progress("保存总结日志", 8)
            summary_id = summarizer.save_summary(
                summary_content, top_repos,
                candidate_count=candidate_count,
                matched_count=matched_count,
            )

            self._notify_progress("任务完成", 9)
            logger.info(f"推送任务完成: {len(top_repos)} 个推荐项目, 日志ID: {summary_id}")

            return {
                "status": "completed",
                "repo_count": len(top_repos),
                "candidate_count": candidate_count,
                "matched_count": matched_count,
                "summary_id": summary_id,
            }

        finally:
            fetcher.close()
            summarizer.close()

    def _rollback_eval(self, repos: list[dict]) -> None:
        """回滚中间数据（取消任务时调用）。"""
        logger.info("回滚中间数据...")
        self.crud.clear_match_records()
        for repo in repos:
            repo_id = repo.get("id")
            if repo_id:
                self.crud.reset_repo_eval(repo_id)

    def start_scheduler(self) -> None:
        """启动定时调度。"""
        if self._scheduler and self._scheduler.running:
            return

        enabled = self._settings.get("scheduler.enabled", True)
        if not enabled:
            logger.info("定时任务未启用")
            return

        run_time = self._settings.get("scheduler.run_time", "09:00")
        timezone = self._settings.get("scheduler.timezone", "Asia/Shanghai")
        interval_hours = self._settings.get("github.fetch_interval_hours", 24)

        self._scheduler = BackgroundScheduler(timezone=timezone)

        hour, minute = map(int, run_time.split(":"))
        if interval_hours >= 24:
            self._scheduler.add_job(
                self.run_task, "cron", hour=hour, minute=minute,
                id="push_task", replace_existing=True,
            )
        else:
            self._scheduler.add_job(
                self.run_task, "interval", hours=interval_hours,
                start_date=f"2026-01-01 {run_time}",
                id="push_task", replace_existing=True,
            )

        self._scheduler.start()
        logger.info(f"定时调度已启动: 间隔{interval_hours}小时, 执行时间{run_time}")

    def stop_scheduler(self) -> None:
        """停止定时调度。"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("定时调度已停止")

    def get_next_run_time(self) -> str | None:
        """获取下次执行时间。"""
        if self._scheduler and self._scheduler.running:
            job = self._scheduler.get_job("push_task")
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
        return None
