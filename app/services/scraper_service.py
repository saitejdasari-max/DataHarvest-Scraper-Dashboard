from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.database.repository import ScrapeJobRepository, ScrapedItemRepository
from app.scrapers import get_scraper
from app.scrapers.base import ScraperError
from app.models.scrape_job import JobStatus, ScrapeJob
from app.schemas.schemas import ScrapeJobCreate, ScrapeJobUpdate, ItemFilterParams
from app.core.logging import app_logger


class ScraperService:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = ScrapeJobRepository(db)
        self.item_repo = ScrapedItemRepository(db)

    # ─── Job CRUD ─────────────────────────────────────────────────────────────

    def create_job(self, data: ScrapeJobCreate) -> ScrapeJob:
        return self.job_repo.create(data)

    def list_jobs(self) -> List[ScrapeJob]:
        return self.job_repo.get_all()

    def get_job(self, job_id: int) -> Optional[ScrapeJob]:
        return self.job_repo.get_by_id(job_id)

    def update_job(self, job_id: int, data: ScrapeJobUpdate) -> Optional[ScrapeJob]:
        return self.job_repo.update(job_id, data)

    def delete_job(self, job_id: int) -> bool:
        return self.job_repo.delete(job_id)

    # ─── Run a scrape ─────────────────────────────────────────────────────────

    def run_job(self, job_id: int) -> Tuple[int, int]:
        """
        Execute a scrape job synchronously.
        Returns (inserted, skipped) counts.
        """
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status == JobStatus.RUNNING:
            raise ValueError(f"Job {job_id} is already running")

        self.job_repo.update_status(job_id, JobStatus.RUNNING)
        app_logger.info(f"Running job id={job_id} type={job.job_type} url={job.url}")

        try:
            scraper = get_scraper(
                job_type=job.job_type,
                job_id=job_id,
                url=job.url,
                use_selenium=job.use_selenium,
            )
            raw_items = scraper.run()

            inserted, skipped = self.item_repo.bulk_create(raw_items)
            self.job_repo.increment_items(job_id, inserted)
            self.job_repo.update_status(job_id, JobStatus.COMPLETED)

            app_logger.info(
                f"Job {job_id} completed: {inserted} inserted, {skipped} skipped"
            )
            return inserted, skipped

        except (ScraperError, Exception) as e:
            error_msg = str(e)
            app_logger.error(f"Job {job_id} failed: {error_msg}")
            self.job_repo.update_status(job_id, JobStatus.FAILED, error=error_msg)
            raise

    # ─── Items ────────────────────────────────────────────────────────────────

    def list_items(self, filters: ItemFilterParams):
        return self.item_repo.get_filtered(filters)

    def get_stats(self) -> dict:
        jobs = self.job_repo.get_all()
        item_stats = self.item_repo.get_stats()
        return {
            **item_stats,
            "total_jobs": len(jobs),
            "active_jobs": sum(1 for j in jobs if j.status == JobStatus.RUNNING),
            "failed_jobs": sum(1 for j in jobs if j.status == JobStatus.FAILED),
        }

    def get_items_for_export(self, job_id: Optional[int], source: Optional[str]):
        return self.item_repo.get_all_for_export(job_id=job_id, source=source)
