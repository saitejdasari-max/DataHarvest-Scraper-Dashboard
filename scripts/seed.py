#!/usr/bin/env python3
"""
Seed the database with demo jobs.
Run: python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database.session import SessionLocal, init_db
from app.database.repository import ScrapeJobRepository
from app.schemas.schemas import ScrapeJobCreate
from app.models.scrape_job import JobType

DEMO_JOBS = [
    ScrapeJobCreate(
        name="HackerNews Jobs",
        url="https://news.ycombinator.com/item?id=40224213",
        job_type=JobType.JOBS,
        is_scheduled=True,
        schedule_interval_hours=12,
        use_selenium=False,
    ),
    ScrapeJobCreate(
        name="Books Catalogue",
        url="https://books.toscrape.com",
        job_type=JobType.PRODUCTS,
        is_scheduled=True,
        schedule_interval_hours=24,
        use_selenium=False,
    ),
    ScrapeJobCreate(
        name="HackerNews Top Stories",
        url="https://hacker-news.firebaseio.com/v0/topstories.json",
        job_type=JobType.NEWS,
        is_scheduled=True,
        schedule_interval_hours=6,
        use_selenium=False,
    ),
]

def seed():
    print("Initialising database…")
    init_db()
    db = SessionLocal()
    repo = ScrapeJobRepository(db)
    for job_data in DEMO_JOBS:
        job = repo.create(job_data)
        print(f"  Created job: {job.name} (id={job.id})")
    db.close()
    print("Seed complete!")

if __name__ == "__main__":
    seed()
