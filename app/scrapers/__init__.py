from typing import Type
from app.scrapers.base import BaseScraper
from app.scrapers.jobs_scraper import HackerNewsJobsScraper
from app.scrapers.products_scraper import BooksScraper
from app.scrapers.news_scraper import HackerNewsNewsScraper
from app.models.scrape_job import JobType

# Registry maps (job_type, use_selenium) → scraper class
SCRAPER_REGISTRY: dict = {
    JobType.JOBS: HackerNewsJobsScraper,
    JobType.PRODUCTS: BooksScraper,
    JobType.NEWS: HackerNewsNewsScraper,
}

# Default URLs for each job type (used when no custom URL is given)
DEFAULT_URLS: dict = {
    JobType.JOBS: "https://news.ycombinator.com/item?id=40224213",
    JobType.PRODUCTS: "https://books.toscrape.com",
    JobType.NEWS: "https://hacker-news.firebaseio.com/v0/topstories.json",
}


def get_scraper(job_type: JobType, job_id: int, url: str, use_selenium: bool = False) -> BaseScraper:
    """Factory – returns the correct scraper instance for the given job type."""
    if use_selenium:
        from app.scrapers.selenium_scraper import IndeedJobsScraper
        scraper_cls = IndeedJobsScraper
    else:
        scraper_cls = SCRAPER_REGISTRY.get(job_type)

    if not scraper_cls:
        raise ValueError(f"No scraper registered for job_type={job_type}")

    effective_url = url or DEFAULT_URLS.get(job_type, "")
    return scraper_cls(job_id=job_id, url=effective_url)
