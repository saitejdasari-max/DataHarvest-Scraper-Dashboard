import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    logger.remove()  # Remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )

    # File handler – general logs
    logger.add(
        LOG_DIR / "app.log",
        format=log_format,
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    # File handler – errors only
    logger.add(
        LOG_DIR / "errors.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
    )

    # File handler – scraper activity
    logger.add(
        LOG_DIR / "scraper.log",
        format=log_format,
        level="DEBUG",
        rotation="50 MB",
        retention="14 days",
        filter=lambda r: "scraper" in r["name"].lower(),
    )

    return logger


app_logger = setup_logging()
