import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from loguru import logger

from database.connection import DatabaseConnection
from database.migrations import MigrationManager
from config.settings import Settings


def init_app() -> None:
    """初始化应用：日志、配置、数据库。"""
    setup_logger()
    logger.info("========== GitHub热点推送 启动 ==========")

    Settings.get_instance()
    logger.info("配置管理初始化完成")

    db = DatabaseConnection.get_instance()
    migration_manager = MigrationManager(db)
    migration_manager.run_migrations()
    logger.info("数据库初始化完成")

    logger.info("========== 应用初始化完成 ==========")


def main() -> None:
    """程序入口。"""
    try:
        init_app()
    except Exception as e:
        logger.critical(f"应用初始化失败: {e}")
        sys.exit(1)

    import customtkinter as ctk
    from gui.app import App
    from service.task_service import TaskService

    app = App()

    task_svc = TaskService(DatabaseConnection.get_instance(), Settings.get_instance())
    task_svc.start_scheduler()
    logger.info("定时任务调度已启动")

    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

    task_svc.stop_scheduler()
    DatabaseConnection.get_instance().close()


if __name__ == "__main__":
    main()
