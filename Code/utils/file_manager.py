import os
import subprocess
from datetime import datetime
from pathlib import Path

from loguru import logger

from models.errors import ErrorCode, FileError


class FileManager:
    """文件管理工具。

    负责日志文件保存、目录操作和文件打开。
    """

    @staticmethod
    def save_summary(content: str, file_path: str) -> str:
        """保存总结日志到文件。

        Args:
            content: 日志内容（Markdown格式）。
            file_path: 保存路径。

        Returns:
            实际保存的文件完整路径。

        Raises:
            FileError: 文件保存失败时抛出。
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info(f"总结日志已保存: {path}")
            return str(path)
        except Exception as e:
            raise FileError(ErrorCode.FILE_SAVE_ERROR, f"文件保存失败: {e}")

    @staticmethod
    def ensure_dir(dir_path: str) -> None:
        """确保目录存在，不存在则创建。

        Args:
            dir_path: 目录路径。

        Raises:
            FileError: 目录创建失败时抛出。
        """
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileError(ErrorCode.DIR_NOT_FOUND, f"目录创建失败: {e}")

    @staticmethod
    def open_file(file_path: str) -> None:
        """用系统默认程序打开文件。"""
        try:
            os.startfile(file_path)
        except Exception as e:
            logger.error(f"打开文件失败: {e}")

    @staticmethod
    def open_directory(dir_path: str) -> None:
        """打开目录。"""
        try:
            os.startfile(dir_path)
        except Exception as e:
            logger.error(f"打开目录失败: {e}")

    @staticmethod
    def generate_filename(template: str, date: str | None = None) -> str:
        """根据模板生成文件名。

        Args:
            template: 文件名模板，支持{date}占位符。
            date: 日期字符串，默认为当前日期。
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return template.replace("{date}", date)

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """删除文件。"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"文件已删除: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
