import sqlite3
from pathlib import Path

from loguru import logger

from models.errors import DatabaseError, ErrorCode

DEFAULT_DB_DIR = Path(__file__).parent.parent / "data"
DEFAULT_DB_NAME = "github_pusher.db"


class DatabaseConnection:
    """SQLite数据库连接管理器。

    提供单例模式的数据库连接管理，负责连接创建、初始化和上下文管理。

    Attributes:
        db_path: 数据库文件完整路径。
    """

    _instance: "DatabaseConnection | None" = None

    def __init__(self, db_dir: Path | None = None):
        db_dir = db_dir or DEFAULT_DB_DIR
        db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_dir / DEFAULT_DB_NAME
        self._connection: sqlite3.Connection | None = None

    @classmethod
    def get_instance(cls, db_dir: Path | None = None) -> "DatabaseConnection":
        """获取数据库连接单例。"""
        if cls._instance is None:
            cls._instance = cls(db_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（仅用于测试）。"""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接。

        Returns:
            sqlite3.Connection: 数据库连接对象。

        Raises:
            DatabaseError: 数据库连接失败时抛出。
        """
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(
                    str(self.db_path),
                    check_same_thread=False,
                )
                self._connection.row_factory = sqlite3.Row
                self._connection.execute("PRAGMA journal_mode=WAL")
                self._connection.execute("PRAGMA foreign_keys=ON")
                logger.info(f"数据库连接已建立: {self.db_path}")
            except sqlite3.Error as e:
                raise DatabaseError(ErrorCode.DB_ERROR, f"数据库连接失败: {e}")
        return self._connection

    def close(self) -> None:
        """关闭数据库连接。"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("数据库连接已关闭")

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句。

        Args:
            sql: SQL语句。
            params: SQL参数。

        Returns:
            sqlite3.Cursor: 执行结果游标。

        Raises:
            DatabaseError: SQL执行失败时抛出。
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(ErrorCode.DB_ERROR, f"SQL执行失败: {e}")

    def executemany(self, sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
        """批量执行SQL语句。

        Args:
            sql: SQL语句。
            params_list: SQL参数列表。

        Returns:
            sqlite3.Cursor: 执行结果游标。

        Raises:
            DatabaseError: SQL执行失败时抛出。
        """
        conn = self.get_connection()
        try:
            cursor = conn.executemany(sql, params_list)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(ErrorCode.DB_ERROR, f"批量SQL执行失败: {e}")

    def fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        """查询单条记录。

        Args:
            sql: SQL查询语句。
            params: SQL参数。

        Returns:
            查询结果字典，无结果时返回None。
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"查询失败: {e}")

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        """查询所有记录。

        Args:
            sql: SQL查询语句。
            params: SQL参数。

        Returns:
            查询结果字典列表。
        """
        conn = self.get_connection()
        try:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(ErrorCode.DB_ERROR, f"查询失败: {e}")

    def get_user_version(self) -> int:
        """获取数据库版本号。"""
        result = self.fetchone("PRAGMA user_version")
        return result["user_version"] if result else 0

    def set_user_version(self, version: int) -> None:
        """设置数据库版本号。"""
        self.execute(f"PRAGMA user_version = {version}")
