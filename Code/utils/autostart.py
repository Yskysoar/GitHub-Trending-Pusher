import sys

from loguru import logger

from models.errors import AutoStartError, ErrorCode

if sys.platform == "win32":
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None

AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "GitHubTrendingPusher"


class AutoStart:
    """开机自启动管理（Windows注册表实现）。"""

    @staticmethod
    def is_enabled() -> bool:
        """检查开机自启动是否已启用。"""
        if winreg is None:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, APP_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"检查自启动状态失败: {e}")
            return False

    @staticmethod
    def set_autostart(enabled: bool, exe_path: str | None = None) -> None:
        """设置开机自启动。

        Args:
            enabled: True启用，False禁用。
            exe_path: 可执行文件路径，默认使用当前Python解释器+main.py。

        Raises:
            AutoStartError: 设置失败时抛出。
        """
        if winreg is None:
            raise AutoStartError(ErrorCode.AUTOSTART_ERROR, "当前平台不支持开机自启动")

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_WRITE)
            try:
                if enabled:
                    if exe_path is None:
                        import os
                        exe_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
                    logger.info("开机自启动已启用")
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                        logger.info("开机自启动已禁用")
                    except FileNotFoundError:
                        pass
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            raise AutoStartError(ErrorCode.AUTOSTART_ERROR, f"设置开机自启动失败: {e}")
