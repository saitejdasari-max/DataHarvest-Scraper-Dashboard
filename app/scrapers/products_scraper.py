"""
Products scraper – targets books.toscrape.com (free scraping sandbox).
Demonstrates multi-page pagination handling.
"""
from typing import List
from urllib.parse import urljoin

from app.scrapers.base import BaseScraper
from app.core.logging import app_logger

BASE_URL = "https://books.toscrape.com"
RATING_MAP = {"One": 1.0, "Two": 2.0, "Three": 3.0, "Four": 4.0, "Five": 5.0}


class BooksScraper(BaseScraper):
    SOURCE_NAME = "books_to_scrape"
    DEFAULT_CATEGORY = "books"
    MAX_PAGES = 5

    def _parse_price(self, text: str) -> float:
        try:
            return float(text.replace("£", "").replace("Â", "").strip())
        except Exception:
            return 0.0

    def _scrape_page(self, url: str) -> List[dict]:
        items = []
        soup = self.fetch_page(url)

        for article in soup.select("article.product_pod"):
            try:
                title_el = article.select_one("h3 a")
                title = title_el["title"] if title_el else "Unknown"
                relative_url = title_el["href"] if title_el else ""
                product_url = urljoin(url, relative_url)

                price_el = article.select_one(".price_color")
                price = self._parse_price(price_el.text) if price_el else 0.0

                rating_el = article.select_one("p.star-rating")
                rating_class = rating_el["class"][1] if rating_el else "One"
                rating = RATING_MAP.get(rating_class, 0.0)

                availability_el = article.select_one(".availability")
                availability = availability_el.text.strip() if availability_el else None

                img_el = article.select_one("img")
                img_url = urljoin(BASE_URL, img_el["src"]) if img_el else None

                items.append(
                    self.build_item(
                        title=title,
                        url=product_url,
                        description=availability,
                        price=price,
                        currency="GBP",
                        rating=rating,
                        image_url=img_url,
                    )
                )
            except Exception as e:
                app_logger.warning(f"[{self.SOURCE_NAME}] Item parse error: {e}")
                continue

        return items

    def scrape(self) -> List[dict]:
        all_items: List[dict] = []
        url = self.url or BASE_URL
        page = 1

        while url and page <= self.MAX_PAGES:
            app_logger.info(f"[{self.SOURCE_NAME}] Scraping page {page}: {url}")
            items = self._scrape_page(url)
            all_items.extend(items)

            # Find next page
            soup = self.fetch_page(url)
            next_el = soup.select_one("li.next a")
            if next_el:
                url = urljoin(url, next_el["href"])
                page += 1
            else:
                break

        return all_items
