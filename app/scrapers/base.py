import hashlib
import time
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fake_useragent import UserAgent

from app.core.config import settings
from app.core.logging import app_logger


class ScraperError(Exception):
    pass


class BaseScraper(ABC):
    """Base class for all scrapers with retry, logging, and dedup support."""

    SOURCE_NAME: str = "base"
    DEFAULT_CATEGORY: str = "general"

    def __init__(self, job_id: int, url: str):
        self.job_id = job_id
        self.url = url
        self.session = self._build_session()
        self.ua = UserAgent()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        return session

    def _get_headers(self) -> dict:
        return {"User-Agent": self.ua.random}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ScraperError)),
    )
    def fetch_page(self, url: str, params: dict = None) -> BeautifulSoup:
        """Fetch a page with retry logic."""
        app_logger.debug(f"[{self.SOURCE_NAME}] Fetching: {url}")
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=settings.SCRAPE_TIMEOUT,
            )
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.HTTPError as e:
            app_logger.warning(f"[{self.SOURCE_NAME}] HTTP error {e.response.status_code}: {url}")
            raise
        except requests.RequestException as e:
            app_logger.error(f"[{self.SOURCE_NAME}] Request failed: {e}")
            raise

    @staticmethod
    def make_hash(title: str, url: str = "") -> str:
        """SHA-256 of title + url for deduplication."""
        raw = f"{title.strip().lower()}|{url.strip().lower()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def build_item(self, **kwargs) -> dict:
        """Build a standardised item dict ready for DB insertion."""
        title = kwargs.get("title", "")
        url = kwargs.get("url", "")
        return {
            "job_id": self.job_id,
            "source": kwargs.get("source", self.SOURCE_NAME),
            "category": kwargs.get("category", self.DEFAULT_CATEGORY),
            "title": title,
            "url": url,
            "description": kwargs.get("description"),
            "company": kwargs.get("company"),
            "location": kwargs.get("location"),
            "salary": kwargs.get("salary"),
            "job_type": kwargs.get("job_type"),
            "price": kwargs.get("price"),
            "currency": kwargs.get("currency", "USD"),
            "rating": kwargs.get("rating"),
            "review_count": kwargs.get("review_count"),
            "image_url": kwargs.get("image_url"),
            "author": kwargs.get("author"),
            "published_at": kwargs.get("published_at"),
            "tags": kwargs.get("tags"),
            "extra_data": kwargs.get("extra_data"),
            "content_hash": self.make_hash(title, url),
        }

    @abstractmethod
    def scrape(self) -> List[dict]:
        """Main scraping logic – must return list of item dicts."""
        ...

    def run(self) -> List[dict]:
        app_logger.info(f"[{self.SOURCE_NAME}] Starting scrape for job_id={self.job_id}")
        start = time.time()
        try:
            items = self.scrape()
            elapsed = round(time.time() - start, 2)
            app_logger.info(
                f"[{self.SOURCE_NAME}] Finished in {elapsed}s – {len(items)} items collected"
            )
            return items
        except Exception as e:
            app_logger.error(f"[{self.SOURCE_NAME}] Scrape failed: {e}")
            raise ScraperError(str(e)) from e
