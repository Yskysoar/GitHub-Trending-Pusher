import math

from database.connection import DatabaseConnection
from database.crud import CrudOperations
from utils.file_manager import FileManager


class HistoryService:
    """历史记录服务。

    提供历史日志查询、搜索、删除和文件操作功能。
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.crud = CrudOperations(db)

    def get_summaries(self, page: int = 1, size: int = 10) -> dict:
        """分页获取历史日志。"""
        rows, total = self.crud.get_summary_logs(page, size)
        return self._build_paginated_result(rows, total, page, size)

    def search_summaries(self, keyword: str, page: int = 1, size: int = 10) -> dict:
        """按关键词搜索历史日志。"""
        rows, total = self.crud.search_summary_logs(keyword, page, size)
        return self._build_paginated_result(rows, total, page, size)

    def get_summary_detail(self, log_id: int) -> dict | None:
        """获取日志详情。"""
        return self.crud.get_summary_detail(log_id)

    def delete_summary(self, log_id: int) -> None:
        """删除日志（同时删除数据库记录、关联的summary_repos记录、磁盘上的日志文件）。"""
        detail = self.crud.get_summary_detail(log_id)
        if detail:
            file_path = detail.get("file_path", "")
            if file_path:
                FileManager.delete_file(file_path)
            self.crud.delete_summary_log(log_id)

    def get_history(self) -> list[dict]:
        """获取历史记录列表（用于UI展示）。"""
        rows, _ = self.crud.get_summary_logs(page=1, size=50)
        result = []
        for row in rows:
            result.append({
                "date": row.get("generated_at", ""),
                "status": "success" if row.get("repo_count", 0) > 0 else "empty",
                "pushed_count": row.get("repo_count", 0),
                "repos": [],
            })
        return result

    @staticmethod
    def open_file(file_path: str) -> None:
        """用系统默认程序打开文件。"""
        FileManager.open_file(file_path)

    @staticmethod
    def open_directory(dir_path: str) -> None:
        """打开目录。"""
        FileManager.open_directory(dir_path)

    @staticmethod
    def _build_paginated_result(rows: list[dict], total: int,
                                 page: int, size: int) -> dict:
        """构建分页结果。"""
        total_pages = math.ceil(total / size) if size > 0 else 0
        return {
            "items": rows,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
        }
