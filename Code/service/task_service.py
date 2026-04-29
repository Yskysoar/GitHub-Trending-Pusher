from datetime import datetime

from config.settings import Settings
from core.scheduler import Scheduler, TaskCallback
from database.connection import DatabaseConnection
from database.crud import CrudOperations
from models.errors import AppError


class TaskService:
    """任务执行服务。

    提供立即执行、状态查询、取消任务和自启动管理功能。
    """

    def __init__(self, db: DatabaseConnection, settings: Settings | None = None):
        self.db = db
        self._settings = settings or Settings.get_instance()
        self._scheduler = Scheduler(db, settings)
        self._crud = CrudOperations(db)

    def run_task_now(self) -> None:
        """立即执行推送任务（异步执行，在后台线程中运行）。"""
        self._scheduler.run_task()

    def get_task_status(self) -> dict:
        """获取任务执行状态。"""
        last_summary = self._crud.get_latest_summary()
        last_run_time = last_summary.get("generated_at", "") if last_summary else ""
        next_run_time = self._scheduler.get_next_run_time() or ""

        return {
            "is_running": self._scheduler.is_running,
            "current_step": "",
            "progress": 0.0,
            "last_run_time": last_run_time,
            "next_run_time": next_run_time,
        }

    def cancel_task(self) -> None:
        """取消正在执行的任务。"""
        self._scheduler.cancel_task()

    def toggle_autostart(self, enabled: bool) -> None:
        """切换开机自启动（委托SettingsService.set_autostart实现）。"""
        from service.settings_service import SettingsService
        ss = SettingsService(self.db, self._settings)
        ss.set_autostart(enabled)

    def set_callback(self, callback: TaskCallback) -> None:
        """设置任务回调。"""
        self._scheduler.set_callback(callback)

    def start_scheduler(self) -> None:
        """启动定时调度。"""
        self._scheduler.start_scheduler()

    def stop_scheduler(self) -> None:
        """停止定时调度。"""
        self._scheduler.stop_scheduler()
