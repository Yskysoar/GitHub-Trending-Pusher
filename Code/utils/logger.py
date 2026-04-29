import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path(__file__).parent.parent / "logs"


def setup_logger(level: str = "INFO") -> None:
    """配置loguru日志。

    Args:
        level: 日志级别，默认INFO。
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    )

    logger.add(
        str(LOG_DIR / "app_{time:YYYY-MM-DD}.log"),
        rotation="1 day",
        retention="30 days",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}",
        encoding="utf-8",
    )

    logger.info("日志系统已初始化")
