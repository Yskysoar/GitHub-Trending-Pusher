import shutil
from pathlib import Path

from loguru import logger

from database.connection import DatabaseConnection
from models.errors import DatabaseError, ErrorCode


class MigrationManager:
    """数据库迁移管理器。

    负责数据库版本检测、迁移执行和备份回滚。
    使用SQLite内置的user_version pragma进行版本管理。
    """

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def get_current_version(self) -> int:
        """获取当前数据库版本。"""
        return self.db.get_user_version()

    def _backup_database(self) -> Path:
        """备份数据库文件。"""
        db_path = self.db.db_path
        backup_path = Path(str(db_path) + ".bak")
        shutil.copy2(db_path, backup_path)
        logger.info(f"数据库已备份至: {backup_path}")
        return backup_path

    def _restore_backup(self, backup_path: Path) -> None:
        """从备份恢复数据库。"""
        db_path = self.db.db_path
        self.db.close()
        shutil.copy2(backup_path, db_path)
        logger.info(f"数据库已从备份恢复: {backup_path}")

    def run_migrations(self) -> None:
        """执行所有待执行的迁移。

        迁移执行前自动备份数据库，迁移失败时回滚至备份版本。
        """
        current_version = self.get_current_version()
        logger.info(f"当前数据库版本: {current_version}")

        from migrations.v1_init import V1_INIT_VERSION, migrate as v1_migrate

        migrations = [
            (V1_INIT_VERSION, v1_migrate),
        ]

        backup_path = None
        try:
            if current_version < migrations[-1][0]:
                backup_path = self._backup_database()

            for target_version, migrate_func in migrations:
                if current_version < target_version:
                    logger.info(f"执行迁移: v{current_version} -> v{target_version}")
                    migrate_func(self.db)
                    self.db.set_user_version(target_version)
                    current_version = target_version
                    logger.info(f"迁移完成: v{target_version}")

        except Exception as e:
            logger.error(f"迁移失败: {e}")
            if backup_path and backup_path.exists():
                self._restore_backup(backup_path)
                logger.error("已回滚至备份版本，应用启动被阻止")
            raise DatabaseError(ErrorCode.DB_ERROR, f"数据库迁移失败: {e}，已回滚至备份版本")
