"""
Jobs scraper – targets HackerNews "Who is Hiring?" posts.
Uses BeautifulSoup; no auth or dynamic rendering required.
"""
import re
from typing import List, Optional

from app.scrapers.base import BaseScraper
from app.core.logging import app_logger

# Fall-back demo URL (latest HN hiring thread)
DEFAULT_URL = "https://news.ycombinator.com/item?id=40224213"


class HackerNewsJobsScraper(BaseScraper):
    SOURCE_NAME = "hackernews"
    DEFAULT_CATEGORY = "jobs"

    def _parse_comment(self, comment) -> Optional[dict]:
        text_el = comment.select_one(".commtext")
        if not text_el:
            return None

        raw_text = text_el.get_text(" ", strip=True)

        # Must look like a job post (company | location pattern)
        if "|" not in raw_text[:300]:
            return None

        parts = [p.strip() for p in raw_text.split("|")]
        company = parts[0] if parts else "Unknown"
        location = parts[1] if len(parts) > 1 else None
        job_type = None
        salary = None

        # Detect remote / hybrid / on-site
        for p in parts:
            if re.search(r"\bremote\b", p, re.I):
                job_type = "Remote"
                break
            if re.search(r"\bhybrid\b", p, re.I):
                job_type = "Hybrid"
                break
            if re.search(r"\bon.?site\b", p, re.I):
                job_type = "On-site"
                break

        # Salary extraction  e.g. "$120k-$180k"
        salary_match = re.search(r"\$[\d,]+[kK]?\s*[-–]\s*\$[\d,]+[kK]?", raw_text)
        if salary_match:
            salary = salary_match.group(0)

        # Title = first real role description line
        title_match = re.search(
            r"(senior|junior|staff|lead|principal|software|backend|frontend|fullstack|data|ml|devops|sre|product|design)",
            raw_text[:500],
            re.I,
        )
        title = parts[0] if not title_match else raw_text[:120].split("|")[0].strip()

        # Link
        link_el = text_el.find("a")
        job_url = link_el["href"] if link_el and link_el.get("href") else None

        return self.build_item(
            title=title[:255],
            url=job_url,
            description=raw_text[:1000],
            company=company[:255],
            location=location[:255] if location else None,
            salary=salary,
            job_type=job_type,
        )

    def scrape(self) -> List[dict]:
        items = []
        soup = self.fetch_page(self.url)
        comments = soup.select(".athing.comtr")
        app_logger.info(f"[{self.SOURCE_NAME}] Found {len(comments)} raw comments")

        for comment in comments[:200]:  # cap at 200
            try:
                item = self._parse_comment(comment)
                if item:
                    items.append(item)
            except Exception as e:
                app_logger.warning(f"[{self.SOURCE_NAME}] Comment parse error: {e}")
                continue

        return items
