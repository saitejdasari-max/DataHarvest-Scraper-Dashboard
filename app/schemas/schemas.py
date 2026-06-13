from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, HttpUrl, field_validator
from app.models.scrape_job import JobStatus, JobType


# ─── ScrapeJob Schemas ────────────────────────────────────────────────────────

class ScrapeJobBase(BaseModel):
    name: str
    url: str
    job_type: JobType = JobType.JOBS
    is_scheduled: bool = False
    schedule_interval_hours: Optional[int] = None
    use_selenium: bool = False


class ScrapeJobCreate(ScrapeJobBase):
    pass


class ScrapeJobUpdate(BaseModel):
    name: Optional[str] = None
    is_scheduled: Optional[bool] = None
    schedule_interval_hours: Optional[int] = None
    use_selenium: Optional[bool] = None


class ScrapeJobResponse(ScrapeJobBase):
    id: int
    status: JobStatus
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    total_runs: int
    successful_runs: int
    failed_runs: int
    items_scraped: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── ScrapedItem Schemas ──────────────────────────────────────────────────────

class ScrapedItemBase(BaseModel):
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    category: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    job_type: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class ScrapedItemCreate(ScrapedItemBase):
    job_id: int
    content_hash: str


class ScrapedItemResponse(ScrapedItemBase):
    id: int
    job_id: int
    content_hash: str
    scraped_at: datetime

    class Config:
        from_attributes = True


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Filters ──────────────────────────────────────────────────────────────────

class ItemFilterParams(BaseModel):
    q: Optional[str] = None
    job_id: Optional[int] = None
    source: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    page: int = 1
    page_size: int = 20

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v):
        if v > 100:
            raise ValueError("page_size cannot exceed 100")
        return v


# ─── Statistics ───────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_items: int
    total_jobs: int
    active_jobs: int
    failed_jobs: int
    items_today: int
    items_this_week: int
    top_sources: List[Dict[str, Any]]
    scrape_activity: List[Dict[str, Any]]


# ─── Export ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    format: str = "csv"  # csv | excel
    job_id: Optional[int] = None
    source: Optional[str] = None
    category: Optional[str] = None
