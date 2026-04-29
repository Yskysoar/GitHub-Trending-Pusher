import json
import statistics
from datetime import datetime

from loguru import logger

from config.settings import Settings
from database.connection import DatabaseConnection
from database.crud import CrudOperations
from models.evaluation import EvalDetails
from models.errors import ErrorCode, EvalError


class RepoEvaluator:
    """仓库综合评估器。

    负责两阶段评分：初始评分（三维度）→ LLM评估后最终评分（四维度）。
    评估维度：规则匹配度(30%)、Star阈值达标度(20%)、增长速度(20%)、学习价值(30%)。
    """

    def __init__(self, db: DatabaseConnection, settings: Settings | None = None):
        self.db = db
        self.crud = CrudOperations(db)
        self._settings = settings or Settings.get_instance()

    def evaluate_repos(self, matched_repos: list[dict], top_n: int = 10,
                       llm_summarizer=None) -> list[dict]:
        """综合评估仓库，返回TOP N项目。

        Args:
            matched_repos: 规则匹配后的仓库列表。
            top_n: 选取的项目数量。
            llm_summarizer: LLM总结生成器实例（用于学习价值评估）。

        Returns:
            最终排名的TOP N项目列表。
        """
        if not matched_repos:
            logger.info("候选仓库为空，跳过评估")
            return []

        weights = self._settings.eval_weights
        if not weights.validate_sum():
            raise EvalError(ErrorCode.EVAL_WEIGHT_INVALID,
                            f"评估权重之和不为1.0: {weights.model_dump()}")

        global_min_stars = self._settings.get("github.min_stars", 100)

        filtered_repos = self._star_threshold_filter(matched_repos, global_min_stars)
        if not filtered_repos:
            logger.info("Star阈值过滤后无仓库")
            return []

        for repo in filtered_repos:
            if not isinstance(repo.get("eval_details"), dict):
                repo["eval_details"] = {}

        self._calculate_growth_scores(filtered_repos)

        self._calculate_initial_scores(filtered_repos, weights)

        filtered_repos.sort(key=lambda r: r.get("initial_score", 0), reverse=True)
        top_repos = filtered_repos[:top_n]

        if llm_summarizer and top_repos:
            try:
                llm_results = llm_summarizer.evaluate_learning_value(top_repos)
                self._apply_llm_results(top_repos, llm_results)
            except Exception as e:
                logger.error(f"LLM学习价值评估失败: {e}")
                for repo in top_repos:
                    repo["learning_value_score"] = 50.0
                    repo.setdefault("eval_details", {})["learning_value_detail"] = None
                    repo.setdefault("eval_details", {})["parse_error"] = str(e)

        self._calculate_final_scores(top_repos, weights)

        top_repos.sort(key=lambda r: r.get("final_score", 0), reverse=True)

        self._save_eval_results(top_repos)

        logger.info(f"综合评估完成: TOP {len(top_repos)} 项目")
        return top_repos

    def _star_threshold_filter(self, repos: list[dict], global_min_stars: int) -> list[dict]:
        """Star阈值过滤。有效阈值=max(全局min_stars, 规则级min_stars)。"""
        filtered = []
        for repo in repos:
            matched_rules = repo.get("matched_rules", [])
            if matched_rules:
                rule_min_stars_list = [r.get("min_stars", 0) for r in matched_rules if r.get("min_stars", 0) > 0]
                effective_min_stars = max(global_min_stars, max(rule_min_stars_list)) if rule_min_stars_list else global_min_stars
            else:
                effective_min_stars = global_min_stars

            repo["effective_min_stars"] = effective_min_stars

            if effective_min_stars > 0 and repo.get("stars", 0) < effective_min_stars:
                logger.debug(f"仓库 {repo.get('full_name')} 低于Star阈值 ({repo.get('stars', 0)} < {effective_min_stars})，已过滤")
                continue
            filtered.append(repo)

        logger.info(f"Star阈值过滤: {len(repos)} -> {len(filtered)}")
        return filtered

    def _calculate_growth_scores(self, repos: list[dict]) -> None:
        """计算增长速度得分。"""
        trending_repos = [r for r in repos if r.get("stars_growth", 0) > 0 or r.get("_from_trending", False)]

        if not trending_repos:
            for repo in repos:
                repo["growth_speed_score"] = 50.0
                repo.setdefault("eval_details", {})["growth_source"] = "fallback"
            return

        growth_values = [r.get("stars_growth", 0) for r in trending_repos]

        if all(v == 0 for v in growth_values):
            for repo in repos:
                repo["growth_speed_score"] = 50.0
                repo.setdefault("eval_details", {})["growth_source"] = "trending"
            return

        median_growth = statistics.median(growth_values)
        if median_growth == 0:
            growth_threshold = statistics.mean(growth_values) + 1
        else:
            growth_threshold = median_growth

        for repo in repos:
            if repo.get("stars_growth", 0) > 0 and repo in trending_repos:
                ratio = min(repo["stars_growth"] / growth_threshold, 2.0) / 2.0
                repo["growth_speed_score"] = ratio * 100
                repo.setdefault("eval_details", {})["growth_source"] = "trending"
            else:
                repo["growth_speed_score"] = 50.0
                repo.setdefault("eval_details", {})["growth_source"] = "fallback"

    def _calculate_initial_scores(self, repos: list[dict], weights) -> None:
        """阶段一：初始评分（三维度，权重归一化）。"""
        w1 = weights.rule_match / (weights.rule_match + weights.star_threshold + weights.growth_speed)
        w2 = weights.star_threshold / (weights.rule_match + weights.star_threshold + weights.growth_speed)
        w3 = weights.growth_speed / (weights.rule_match + weights.star_threshold + weights.growth_speed)

        for repo in repos:
            rule_match_score = repo.get("rule_match_score", 50.0)
            star_threshold_score = self._calc_star_threshold_score(repo)
            growth_speed_score = repo.get("growth_speed_score", 50.0)

            initial_score = rule_match_score * w1 + star_threshold_score * w2 + growth_speed_score * w3

            repo["star_threshold_score"] = star_threshold_score
            repo["initial_score"] = round(initial_score, 2)

    @staticmethod
    def _calc_star_threshold_score(repo: dict) -> float:
        """计算Star阈值达标度得分（0-100）。"""
        min_stars = repo.get("effective_min_stars", 0)
        if min_stars <= 0:
            return 100.0
        stars = repo.get("stars", 0)
        ratio = min(stars / min_stars, 2.0) / 2.0
        return ratio * 100

    def _apply_llm_results(self, repos: list[dict], llm_results: list[dict]) -> None:
        """应用LLM学习价值评估结果。"""
        result_map = {r.get("repo", ""): r for r in llm_results}

        for repo in repos:
            full_name = repo.get("full_name", "")
            result = result_map.get(full_name)

            if result:
                scores = result.get("scores", {})
                innovation = max(0, min(10, scores.get("innovation", 5.0)))
                code_quality = max(0, min(10, scores.get("code_quality", 5.0)))
                practicality = max(0, min(10, scores.get("practicality", 5.0)))
                community = max(0, min(10, scores.get("community", 5.0)))

                avg = (innovation + code_quality + practicality + community) / 4
                learning_value_score = avg * 10

                repo["learning_value_score"] = round(learning_value_score, 1)
                repo["readme_summary"] = result.get("summary", repo.get("description", ""))
                repo.setdefault("eval_details", {})["learning_value_detail"] = {
                    "innovation": innovation,
                    "code_quality": code_quality,
                    "practicality": practicality,
                    "community": community,
                    "brief_reason": result.get("brief_reason", ""),
                }
                repo.setdefault("eval_details", {})["parse_error"] = None
            else:
                repo["learning_value_score"] = 50.0
                repo.setdefault("eval_details", {})["parse_error"] = "LLM未返回该仓库评估"

    def _calculate_final_scores(self, repos: list[dict], weights) -> None:
        """阶段二：最终评分（四维度加权）。"""
        for repo in repos:
            rule_match_score = repo.get("rule_match_score", 50.0)
            star_threshold_score = repo.get("star_threshold_score", 50.0)
            growth_speed_score = repo.get("growth_speed_score", 50.0)
            learning_value_score = repo.get("learning_value_score", 50.0)

            final_score = (
                rule_match_score * weights.rule_match
                + star_threshold_score * weights.star_threshold
                + growth_speed_score * weights.growth_speed
                + learning_value_score * weights.learning_value
            )

            repo["final_score"] = round(final_score, 2)
            repo["eval_score"] = repo["final_score"]

            matched_rules = repo.get("matched_rules", [])
            eval_details = EvalDetails(
                rule_match_score=round(rule_match_score, 1),
                star_threshold_score=round(star_threshold_score, 1),
                growth_speed_score=round(growth_speed_score, 1),
                learning_value_score=round(learning_value_score, 1),
                initial_score=round(repo.get("initial_score", 0), 1),
                final_score=repo["final_score"],
                matched_rules=matched_rules,
                effective_min_stars=repo.get("effective_min_stars", 0),
                learning_value_detail=repo.get("eval_details", {}).get("learning_value_detail"),
                growth_source=repo.get("eval_details", {}).get("growth_source", "trending"),
                parse_error=repo.get("eval_details", {}).get("parse_error"),
            )
            repo["eval_details_json"] = eval_details.model_dump_json()

    def _save_eval_results(self, repos: list[dict]) -> None:
        """保存评估结果到数据库。"""
        for repo in repos:
            repo_id = repo.get("id")
            if repo_id:
                self.crud.update_repo_eval(
                    repo_id=repo_id,
                    eval_score=repo.get("eval_score", 0.0),
                    eval_details=repo.get("eval_details_json", "{}"),
                    readme_summary=repo.get("readme_summary", ""),
                )
