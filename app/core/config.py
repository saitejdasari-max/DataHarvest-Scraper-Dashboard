from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Scraper Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "sqlite:///./scraper_dashboard.db"
    # Scraping
    SCRAPE_TIMEOUT: int = 30
    SCRAPE_RETRY_ATTEMPTS: int = 3
    SCRAPE_RETRY_DELAY: int = 5
    MAX_CONCURRENT_SCRAPERS: int = 5

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    DEFAULT_SCRAPE_INTERVAL_HOURS: int = 6

    # Selenium
    SELENIUM_HEADLESS: bool = True
    SELENIUM_DRIVER: str = "chrome"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
