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
        """获取最近一次推送任务的统计概览。

        数据来源于最近一条summary_logs记录，若尚无任务记录则返回全零值。

        Returns:
            包含 candidate_count、matched_count、recommended_count 的字典。
        """
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
