from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from datetime import datetime, timedelta

from app.models.scrape_job import ScrapeJob, JobStatus
from app.models.scraped_item import ScrapedItem
from app.schemas.schemas import ScrapeJobCreate, ScrapeJobUpdate, ItemFilterParams
from app.core.logging import app_logger


class ScrapeJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, job_data: ScrapeJobCreate) -> ScrapeJob:
        job = ScrapeJob(**job_data.model_dump())
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        app_logger.info(f"Created scrape job: {job.name} (id={job.id})")
        return job

    def get_by_id(self, job_id: int) -> Optional[ScrapeJob]:
        return self.db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ScrapeJob]:
        return self.db.query(ScrapeJob).order_by(desc(ScrapeJob.created_at)).offset(skip).limit(limit).all()

    def update(self, job_id: int, update_data: ScrapeJobUpdate) -> Optional[ScrapeJob]:
        job = self.get_by_id(job_id)
        if not job:
            return None
        for key, value in update_data.model_dump(exclude_none=True).items():
            setattr(job, key, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_status(self, job_id: int, status: JobStatus, error: str = None) -> Optional[ScrapeJob]:
        job = self.get_by_id(job_id)
        if not job:
            return None
        job.status = status
        job.updated_at = datetime.utcnow()
        if status == JobStatus.RUNNING:
            job.last_run_at = datetime.utcnow()
            job.total_runs += 1
        elif status == JobStatus.COMPLETED:
            job.successful_runs += 1
        elif status == JobStatus.FAILED:
            job.failed_runs += 1
            job.error_message = error
        self.db.commit()
        self.db.refresh(job)
        return job

    def increment_items(self, job_id: int, count: int):
        job = self.get_by_id(job_id)
        if job:
            job.items_scraped += count
            self.db.commit()

    def delete(self, job_id: int) -> bool:
        job = self.get_by_id(job_id)
        if not job:
            return False
        self.db.delete(job)
        self.db.commit()
        app_logger.info(f"Deleted scrape job id={job_id}")
        return True

    def get_scheduled_jobs(self) -> List[ScrapeJob]:
        return (
            self.db.query(ScrapeJob)
            .filter(ScrapeJob.is_scheduled == True, ScrapeJob.status != JobStatus.RUNNING)
            .all()
        )


class ScrapedItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, item_data: dict) -> Optional[ScrapedItem]:
        """Create item; returns None if duplicate (by content_hash)."""
        existing = self.db.query(ScrapedItem).filter(
            ScrapedItem.content_hash == item_data["content_hash"]
        ).first()
        if existing:
            app_logger.debug(f"Duplicate skipped: {item_data.get('title', '')[:60]}")
            return None
        item = ScrapedItem(**item_data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def bulk_create(self, items: List[dict]) -> Tuple[int, int]:
        """Bulk insert; returns (inserted, skipped)."""
        inserted, skipped = 0, 0
        hashes = {i["content_hash"] for i in items}
        existing_hashes = {
            row[0]
            for row in self.db.query(ScrapedItem.content_hash)
            .filter(ScrapedItem.content_hash.in_(hashes))
            .all()
        }
        new_items = []
        for item_data in items:
            if item_data["content_hash"] in existing_hashes:
                skipped += 1
            else:
                new_items.append(ScrapedItem(**item_data))
                inserted += 1
        if new_items:
            self.db.bulk_save_objects(new_items)
            self.db.commit()
        app_logger.info(f"Bulk insert: {inserted} new, {skipped} duplicates skipped")
        return inserted, skipped

    def get_filtered(self, filters: ItemFilterParams) -> Tuple[List[ScrapedItem], int]:
        query = self.db.query(ScrapedItem)

        if filters.job_id:
            query = query.filter(ScrapedItem.job_id == filters.job_id)
        if filters.source:
            query = query.filter(ScrapedItem.source.ilike(f"%{filters.source}%"))
        if filters.category:
            query = query.filter(ScrapedItem.category.ilike(f"%{filters.category}%"))
        if filters.location:
            query = query.filter(ScrapedItem.location.ilike(f"%{filters.location}%"))
        if filters.company:
            query = query.filter(ScrapedItem.company.ilike(f"%{filters.company}%"))
        if filters.min_price is not None:
            query = query.filter(ScrapedItem.price >= filters.min_price)
        if filters.max_price is not None:
            query = query.filter(ScrapedItem.price <= filters.max_price)
        if filters.q:
            search_term = f"%{filters.q}%"
            query = query.filter(
                or_(
                    ScrapedItem.title.ilike(search_term),
                    ScrapedItem.description.ilike(search_term),
                    ScrapedItem.company.ilike(search_term),
                    ScrapedItem.location.ilike(search_term),
                )
            )

        total = query.count()
        items = (
            query.order_by(desc(ScrapedItem.scraped_at))
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .all()
        )
        return items, total

    def get_all_for_export(self, job_id: Optional[int] = None, source: Optional[str] = None) -> List[ScrapedItem]:
        query = self.db.query(ScrapedItem)
        if job_id:
            query = query.filter(ScrapedItem.job_id == job_id)
        if source:
            query = query.filter(ScrapedItem.source.ilike(f"%{source}%"))
        return query.order_by(desc(ScrapedItem.scraped_at)).all()

    def get_stats(self) -> dict:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        total = self.db.query(func.count(ScrapedItem.id)).scalar()
        today = self.db.query(func.count(ScrapedItem.id)).filter(ScrapedItem.scraped_at >= today_start).scalar()
        this_week = self.db.query(func.count(ScrapedItem.id)).filter(ScrapedItem.scraped_at >= week_start).scalar()

        top_sources = (
            self.db.query(ScrapedItem.source, func.count(ScrapedItem.id).label("count"))
            .group_by(ScrapedItem.source)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        # Last 7 days activity
        activity = []
        for i in range(6, -1, -1):
            day = today_start - timedelta(days=i)
            next_day = day + timedelta(days=1)
            count = self.db.query(func.count(ScrapedItem.id)).filter(
                and_(ScrapedItem.scraped_at >= day, ScrapedItem.scraped_at < next_day)
            ).scalar()
            activity.append({"date": day.strftime("%b %d"), "count": count})

        return {
            "total_items": total,
            "items_today": today,
            "items_this_week": this_week,
            "top_sources": [{"source": s or "Unknown", "count": c} for s, c in top_sources],
            "scrape_activity": activity,
        }
