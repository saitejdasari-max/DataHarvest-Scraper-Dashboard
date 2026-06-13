from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class ScrapedItem(Base):
    __tablename__ = "scraped_items"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id", ondelete="CASCADE"), nullable=False)

    # Common fields across all item types
    title = Column(String(500), nullable=False, index=True)
    url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)

    # Job-specific fields
    company = Column(String(255), nullable=True, index=True)      # jobs
    location = Column(String(255), nullable=True, index=True)     # jobs
    salary = Column(String(255), nullable=True)                   # jobs
    job_type = Column(String(100), nullable=True)                 # jobs (full-time, etc.)

    # Product-specific
    price = Column(Float, nullable=True, index=True)
    currency = Column(String(10), nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    image_url = Column(Text, nullable=True)

    # News-specific
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    tags = Column(JSON, nullable=True)

    # Dedup hash (SHA256 of title + url)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Metadata
    extra_data = Column(JSON, nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    job = relationship("ScrapeJob", back_populates="items")

    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_scraped_item_hash"),
    )
