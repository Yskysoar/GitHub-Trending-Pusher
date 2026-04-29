import json
from datetime import datetime

from loguru import logger

from database.connection import DatabaseConnection
from models.errors import DatabaseError, ErrorCode, RuleError
from models.evaluation import EvalDetails


class CrudOperations:
    """通用数据库CRUD操作。"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    # ==================== 规则操作 ====================

    def get_rules(self, enabled_only: bool = False) -> list[dict]:
        """获取规则列表。"""
        if enabled_only:
            return self.db.fetchall("SELECT * FROM rules WHERE enabled = 1 ORDER BY priority DESC")
        return self.db.fetchall("SELECT * FROM rules ORDER BY priority DESC")

    def get_rule_by_id(self, rule_id: int) -> dict | None:
        """根据ID获取规则。"""
        return self.db.fetchone("SELECT * FROM rules WHERE id = ?", (rule_id,))

    def get_rule_by_name(self, name: str) -> dict | None:
        """根据名称获取规则。"""
        return self.db.fetchone("SELECT * FROM rules WHERE name = ?", (name,))

    def add_rule(self, name: str, keywords: list[str], topics: list[str] | None = None,
                 language: str = "", min_stars: int = 0, priority: int = 5,
                 enabled: bool = True) -> int:
        """新增规则，返回规则ID。"""
        now = datetime.now().isoformat()
        topics = topics or []
        try:
            cursor = self.db.execute(
                """INSERT INTO rules (name, keywords, topics, language, min_stars, priority, enabled, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, json.dumps(keywords, ensure_ascii=False),
                 json.dumps(topics, ensure_ascii=False),
                 language, min_stars, priority, 1 if enabled else 0, now, now),
            )
            rule_id = cursor.lastrowid
            logger.info(f"新增规则: {name} (ID: {rule_id})")
            return rule_id
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise RuleError(ErrorCode.RULE_INVALID, f"规则名称已存在: {name}")
            raise DatabaseError(ErrorCode.DB_ERROR, f"新增规则失败: {e}")

    def update_rule(self, rule_id: int, **kwargs) -> bool:
        """更新规则。"""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise RuleError(ErrorCode.RULE_NOT_FOUND, f"规则不存在: ID {rule_id}")

        allowed_fields = {"name", "keywords", "topics", "language", "min_stars", "priority", "enabled"}
        updates = {}
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                if key in ("keywords", "topics"):
                    updates[key] = json.dumps(value, ensure_ascii=False)
                elif key == "enabled":
                    updates[key] = 1 if value else 0
                else:
                    updates[key] = value

        if not updates:
            return False

        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [rule_id]

        try:
            self.db.execute(f"UPDATE rules SET {set_clause} WHERE id = ?", values)
            logger.info(f"更新规则: ID {rule_id}")
            return True
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise RuleError(ErrorCode.RULE_INVALID, f"规则名称已存在: {kwargs.get('name')}")
            raise DatabaseError(ErrorCode.DB_ERROR, f"更新规则失败: {e}")

    def delete_rule(self, rule_id: int) -> bool:
        """删除规则（级联删除关联的match_records）。"""
        try:
            cursor = self.db.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            if cursor.rowcount > 0:
                logger.info(f"删除规则: ID {rule_id}")
                return True
            return False
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"删除规则失败: {e}")

    def toggle_rule(self, rule_id: int, enabled: bool) -> bool:
        """启用/禁用规则。"""
        return self.update_rule(rule_id, enabled=enabled)

    # ==================== 仓库操作 ====================

    def upsert_repositories(self, repos: list[dict]) -> int:
        """批量存储仓库数据（UPSERT，按full_name去重更新）。"""
        if not repos:
            return 0
        now = datetime.now().isoformat()
        params_list = []
        for repo in repos:
            params_list.append((
                repo.get("full_name", ""),
                repo.get("description", ""),
                repo.get("url", ""),
                repo.get("homepage", ""),
                repo.get("stars", 0),
                repo.get("stars_growth", 0),
                repo.get("forks", 0),
                repo.get("language", ""),
                json.dumps(repo.get("topics", []), ensure_ascii=False),
                repo.get("fetched_at", now),
            ))

        sql = """INSERT INTO repositories (full_name, description, url, homepage, stars, stars_growth, forks, language, topics, fetched_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT(full_name) DO UPDATE SET
                   description = excluded.description,
                   stars = excluded.stars,
                   stars_growth = excluded.stars_growth,
                   forks = excluded.forks,
                   language = excluded.language,
                   topics = excluded.topics,
                   fetched_at = excluded.fetched_at"""
        try:
            self.db.executemany(sql, params_list)
            logger.info(f"批量存储仓库: {len(params_list)} 条")
            return len(params_list)
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"批量存储仓库失败: {e}")

    def get_repository_by_name(self, full_name: str) -> dict | None:
        """根据full_name获取仓库。"""
        return self.db.fetchone("SELECT * FROM repositories WHERE full_name = ?", (full_name,))

    def get_repository_by_id(self, repo_id: int) -> dict | None:
        """根据ID获取仓库。"""
        return self.db.fetchone("SELECT * FROM repositories WHERE id = ?", (repo_id,))

    def update_repo_eval(self, repo_id: int, eval_score: float, eval_details: str,
                         readme_summary: str) -> bool:
        """更新仓库评估得分、评估详情和项目简介。"""
        try:
            self.db.execute(
                "UPDATE repositories SET eval_score = ?, eval_details = ?, readme_summary = ? WHERE id = ?",
                (eval_score, eval_details, readme_summary, repo_id),
            )
            return True
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"更新仓库评估失败: {e}")

    def reset_repo_eval(self, repo_id: int) -> bool:
        """重置仓库评估数据为默认值（用于任务取消回滚）。"""
        try:
            self.db.execute(
                "UPDATE repositories SET eval_score = 0.0, eval_details = '{}', readme_summary = '' WHERE id = ?",
                (repo_id,),
            )
            return True
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"重置仓库评估失败: {e}")

    # ==================== 匹配记录操作 ====================

    def clear_match_records(self) -> None:
        """清空历史匹配记录（每次评估任务前调用）。"""
        try:
            self.db.execute("DELETE FROM match_records")
            logger.info("已清空历史匹配记录")
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"清空匹配记录失败: {e}")

    def save_match_records(self, records: list[dict]) -> int:
        """批量存储匹配记录。"""
        if not records:
            return 0
        now = datetime.now().isoformat()
        params_list = [
            (r["rule_id"], r["repo_id"], r["match_score"], now)
            for r in records
        ]
        sql = """INSERT INTO match_records (rule_id, repo_id, match_score, matched_at)
                 VALUES (?, ?, ?, ?)"""
        try:
            self.db.executemany(sql, params_list)
            logger.info(f"存储匹配记录: {len(params_list)} 条")
            return len(params_list)
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"存储匹配记录失败: {e}")

    # ==================== 总结日志操作 ====================

    def save_summary_log(self, log_data: dict, repo_ids: list[int]) -> int:
        """存储总结日志记录及日志-仓库关联记录。"""
        try:
            cursor = self.db.execute(
                """INSERT INTO summary_logs (title, content, file_path, repo_count, candidate_count, matched_count, generated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (log_data["title"], log_data["content"], log_data["file_path"],
                 log_data.get("repo_count", 0), log_data.get("candidate_count", 0),
                 log_data.get("matched_count", 0), log_data.get("generated_at", datetime.now().isoformat())),
            )
            summary_id = cursor.lastrowid

            if repo_ids:
                rank = 1
                summary_repo_params = [(summary_id, repo_id, rank + i) for i, repo_id in enumerate(repo_ids)]
                self.db.executemany(
                    "INSERT INTO summary_repos (summary_id, repo_id, rank) VALUES (?, ?, ?)",
                    summary_repo_params,
                )

            logger.info(f"存储总结日志: {log_data['title']} (ID: {summary_id})")
            return summary_id
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"存储总结日志失败: {e}")

    def get_summary_logs(self, page: int = 1, size: int = 10) -> tuple[list[dict], int]:
        """分页获取总结日志。"""
        total = self.db.fetchone("SELECT COUNT(*) as cnt FROM summary_logs")
        total_count = total["cnt"] if total else 0
        offset = (page - 1) * size
        rows = self.db.fetchall(
            "SELECT * FROM summary_logs ORDER BY generated_at DESC LIMIT ? OFFSET ?",
            (size, offset),
        )
        return rows, total_count

    def search_summary_logs(self, keyword: str, page: int = 1, size: int = 10) -> tuple[list[dict], int]:
        """按关键词搜索总结日志。"""
        like_param = f"%{keyword}%"
        total = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM summary_logs WHERE title LIKE ? OR content LIKE ?",
            (like_param, like_param),
        )
        total_count = total["cnt"] if total else 0
        offset = (page - 1) * size
        rows = self.db.fetchall(
            "SELECT * FROM summary_logs WHERE title LIKE ? OR content LIKE ? ORDER BY generated_at DESC LIMIT ? OFFSET ?",
            (like_param, like_param, size, offset),
        )
        return rows, total_count

    def get_summary_detail(self, log_id: int) -> dict | None:
        """获取总结日志详情。"""
        return self.db.fetchone("SELECT * FROM summary_logs WHERE id = ?", (log_id,))

    def delete_summary_log(self, log_id: int) -> bool:
        """删除总结日志（级联删除summary_repos）。"""
        try:
            cursor = self.db.execute("DELETE FROM summary_logs WHERE id = ?", (log_id,))
            if cursor.rowcount > 0:
                logger.info(f"删除总结日志: ID {log_id}")
                return True
            return False
        except Exception as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"删除总结日志失败: {e}")

    def get_latest_summary(self) -> dict | None:
        """获取最新一条总结日志。"""
        return self.db.fetchone("SELECT * FROM summary_logs ORDER BY generated_at DESC LIMIT 1")

    def get_top_repos(self, limit: int = 5) -> list[dict]:
        """获取综合评估TOP N项目。"""
        return self.db.fetchall(
            "SELECT * FROM repositories WHERE eval_score > 0 ORDER BY eval_score DESC LIMIT ?",
            (limit,),
        )
