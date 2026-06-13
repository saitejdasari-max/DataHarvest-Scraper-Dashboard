"""
Scraper unit tests – validates hashing, item building, and dedup logic.
No network calls are made; scrapers are tested with mock data.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.scrapers.base import BaseScraper


class DummyScraper(BaseScraper):
    SOURCE_NAME = "test_source"
    DEFAULT_CATEGORY = "test"

    def scrape(self):
        return [self.build_item(title="Test Job", url="https://example.com/job/1")]


# ── Hash / dedup ──────────────────────────────────────────────────────────
def test_make_hash_deterministic():
    h1 = BaseScraper.make_hash("Python Developer", "https://example.com/1")
    h2 = BaseScraper.make_hash("Python Developer", "https://example.com/1")
    assert h1 == h2


def test_make_hash_case_insensitive():
    h1 = BaseScraper.make_hash("Python Developer", "HTTPS://EXAMPLE.COM/1")
    h2 = BaseScraper.make_hash("python developer", "https://example.com/1")
    assert h1 == h2


def test_make_hash_different_inputs():
    h1 = BaseScraper.make_hash("Job A", "https://a.com")
    h2 = BaseScraper.make_hash("Job B", "https://b.com")
    assert h1 != h2


def test_make_hash_length():
    h = BaseScraper.make_hash("Test", "https://test.com")
    assert len(h) == 64  # SHA-256 hex


# ── Build item ────────────────────────────────────────────────────────────
def test_build_item_required_fields():
    scraper = DummyScraper(job_id=1, url="https://test.com")
    item = scraper.build_item(title="Test", url="https://test.com/item")
    assert item["title"] == "Test"
    assert item["job_id"] == 1
    assert item["source"] == "test_source"
    assert item["content_hash"] is not None
    assert len(item["content_hash"]) == 64


def test_build_item_optional_fields_none():
    scraper = DummyScraper(job_id=1, url="https://test.com")
    item = scraper.build_item(title="Test", url="")
    assert item["company"] is None
    assert item["price"] is None
    assert item["author"] is None


def test_scraper_run_returns_list():
    scraper = DummyScraper(job_id=42, url="https://test.com")
    result = scraper.run()
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["title"] == "Test Job"


# ── Hash collision prevention ─────────────────────────────────────────────
def test_no_hash_collision_same_title_different_url():
    h1 = BaseScraper.make_hash("Senior Engineer", "https://company-a.com/job/1")
    h2 = BaseScraper.make_hash("Senior Engineer", "https://company-b.com/job/1")
    assert h1 != h2


def test_hash_empty_url_still_unique_by_title():
    h1 = BaseScraper.make_hash("Job A", "")
    h2 = BaseScraper.make_hash("Job B", "")
    assert h1 != h2
