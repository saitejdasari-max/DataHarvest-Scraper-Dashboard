"""
News scraper – HackerNews top stories via their public Firebase API.
No HTML parsing needed; demonstrates API-based scraping.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Optional

import requests

from app.scrapers.base import BaseScraper
from app.core.logging import app_logger

HN_API = "https://hacker-news.firebaseio.com/v0"


class HackerNewsNewsScraper(BaseScraper):
    SOURCE_NAME = "hackernews_news"
    DEFAULT_CATEGORY = "technology"
    MAX_STORIES = 50
    MAX_WORKERS = 10

    def _fetch_story(self, story_id: int) -> Optional[dict]:
        try:
            resp = self.session.get(
                f"{HN_API}/item/{story_id}.json",
                timeout=10,
                headers=self._get_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            if not data or data.get("type") != "story" or not data.get("url"):
                return None

            title = data.get("title", "")
            url = data.get("url", "")
            score = data.get("score", 0)
            by = data.get("by", "Anonymous")
            ts = data.get("time")
            pub_dt = datetime.utcfromtimestamp(ts) if ts else None

            # Derive tags from domain
            tags = []
            if url:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "")
                tags.append(domain)

            return self.build_item(
                title=title,
                url=url,
                description=f"Score: {score} | By: {by}",
                author=by,
                published_at=pub_dt,
                tags=tags,
                extra_data={"hn_id": story_id, "score": score, "comments": data.get("descendants", 0)},
            )
        except Exception as e:
            app_logger.debug(f"[{self.SOURCE_NAME}] Story {story_id} failed: {e}")
            return None

    def scrape(self) -> List[dict]:
        # Get top story IDs
        resp = self.session.get(f"{HN_API}/topstories.json", timeout=15)
        resp.raise_for_status()
        story_ids = resp.json()[: self.MAX_STORIES]
        app_logger.info(f"[{self.SOURCE_NAME}] Fetching {len(story_ids)} stories")

        items = []
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {executor.submit(self._fetch_story, sid): sid for sid in story_ids}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    items.append(result)

        items.sort(key=lambda x: x.get("extra_data", {}).get("score", 0), reverse=True)
        return items
