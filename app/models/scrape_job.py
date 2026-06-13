from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.session import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class JobType(str, enum.Enum):
    JOBS = "jobs"
    PRODUCTS = "products"
    NEWS = "news"


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    job_type = Column(SAEnum(JobType), nullable=False, default=JobType.JOBS)
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    is_scheduled = Column(Boolean, default=False)
    schedule_interval_hours = Column(Integer, nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    items_scraped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    use_selenium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("ScrapedItem", back_populates="job", cascade="all, delete-orphan")
