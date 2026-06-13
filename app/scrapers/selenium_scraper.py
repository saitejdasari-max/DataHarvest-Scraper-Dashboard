"""
Selenium-based scraper for dynamic / JS-rendered pages.
Used when BeautifulSoup + requests cannot access the content.
"""
from typing import List, Optional
import time

from app.scrapers.base import BaseScraper
from app.core.config import settings
from app.core.logging import app_logger

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    app_logger.warning("Selenium not available – dynamic scraping disabled")


class SeleniumBaseScraper(BaseScraper):
    """Extend this class for any scraper that needs JS rendering."""

    SOURCE_NAME = "selenium_base"
    WAIT_TIMEOUT = 15

    def _build_driver(self) -> Optional[object]:
        if not SELENIUM_AVAILABLE:
            app_logger.error("Selenium is not installed")
            return None

        options = Options()
        if settings.SELENIUM_HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"user-agent={self._get_headers()['User-Agent']}")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def fetch_dynamic_page(self, url: str, wait_selector: str = None) -> Optional[str]:
        """Fetch a page with Selenium; returns page source HTML."""
        driver = None
        try:
            driver = self._build_driver()
            if not driver:
                return None
            driver.get(url)
            if wait_selector:
                WebDriverWait(driver, self.WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
            else:
                time.sleep(2)
            return driver.page_source
        except Exception as e:
            app_logger.error(f"[{self.SOURCE_NAME}] Selenium error: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def scrape(self) -> List[dict]:
        # Override in subclass
        raise NotImplementedError("Implement scrape() in subclass")


class IndeedJobsScraper(SeleniumBaseScraper):
    """
    Example Selenium scraper for Indeed job listings.
    NOTE: Only use this on sites where scraping is permitted.
    This demonstrates the pattern; actual selectors depend on current Indeed HTML.
    """
    SOURCE_NAME = "indeed"
    DEFAULT_CATEGORY = "jobs"

    def scrape(self) -> List[dict]:
        html = self.fetch_dynamic_page(self.url, wait_selector=".jobsearch-ResultsList")
        if not html:
            return []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        items = []

        for card in soup.select(".job_seen_beacon"):
            try:
                title_el = card.select_one("h2.jobTitle span[title]")
                company_el = card.select_one("[data-testid='company-name']")
                location_el = card.select_one("[data-testid='text-location']")
                salary_el = card.select_one(".salary-snippet-container")
                link_el = card.select_one("a[data-jk]")

                title = title_el["title"] if title_el else "Unknown"
                company = company_el.text.strip() if company_el else None
                location = location_el.text.strip() if location_el else None
                salary = salary_el.text.strip() if salary_el else None
                job_url = f"https://www.indeed.com{link_el['href']}" if link_el else None

                items.append(self.build_item(
                    title=title,
                    url=job_url,
                    company=company,
                    location=location,
                    salary=salary,
                ))
            except Exception as e:
                app_logger.warning(f"[{self.SOURCE_NAME}] Card parse error: {e}")

        return items
