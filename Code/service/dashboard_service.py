from database.connection import DatabaseConnection
from database.crud import CrudOperations


class DashboardService:
    """仪表盘服务。

    提供推送统计概览、TOP项目列表、最新推送日志等数据。
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.crud = CrudOperations(db)

    def get_today_stats(self) -> dict:
        """获取最近一次推送任务的统计概览。"""
        latest = self.crud.get_latest_summary()
        if latest:
            return {
                "candidate_count": latest.get("candidate_count", 0),
                "matched_count": latest.get("matched_count", 0),
                "recommended_count": latest.get("repo_count", 0),
            }
        return {
            "candidate_count": 0,
            "matched_count": 0,
            "recommended_count": 0,
        }

    def get_top_repos(self, limit: int = 5) -> list[dict]:
        """获取综合评估TOP N项目。"""
        return self.crud.get_top_repos(limit)

    def get_latest_summary(self) -> dict | None:
        """获取最新推送日志信息。"""
        return self.crud.get_latest_summary()

    def get_dashboard_summary(self) -> dict:
        """获取仪表盘完整摘要数据。"""
        stats = self.get_today_stats()
        top_repos = self.get_top_repos(10)
        rules = self.crud.get_rules(enabled_only=True)
        return {
            "total_fetched": stats.get("candidate_count", 0),
            "hot_repos": stats.get("matched_count", 0),
            "pushed": stats.get("recommended_count", 0),
            "active_rules": len(rules),
            "top_repos": top_repos,
        }

    def run_pipeline(self) -> dict:
        """执行推送流水线。"""
        try:
            from core.scheduler import Scheduler

            scheduler = Scheduler(self.db)
            scheduler.run_task()
            return {"success": True, "message": "推送任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"推送任务执行失败: {e}"}
