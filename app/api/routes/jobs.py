from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.scraper_service import ScraperService
from app.services.scheduler import register_job, unregister_job
from app.schemas.schemas import ScrapeJobCreate, ScrapeJobUpdate, ScrapeJobResponse
from app.core.logging import app_logger

router = APIRouter(prefix="/jobs", tags=["Scrape Jobs"])


def _get_service(db: Session = Depends(get_db)) -> ScraperService:
    return ScraperService(db)


@router.post("/", response_model=ScrapeJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(data: ScrapeJobCreate, service: ScraperService = Depends(_get_service)):
    """Create a new scrape job configuration."""
    job = service.create_job(data)
    if job.is_scheduled and job.schedule_interval_hours:
        register_job(job.id, job.schedule_interval_hours)
    return job


@router.get("/", response_model=List[ScrapeJobResponse])
def list_jobs(service: ScraperService = Depends(_get_service)):
    """List all scrape jobs."""
    return service.list_jobs()


@router.get("/{job_id}", response_model=ScrapeJobResponse)
def get_job(job_id: int, service: ScraperService = Depends(_get_service)):
    """Get a specific scrape job by ID."""
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.patch("/{job_id}", response_model=ScrapeJobResponse)
def update_job(
    job_id: int,
    data: ScrapeJobUpdate,
    service: ScraperService = Depends(_get_service),
):
    """Update job configuration."""
    job = service.update_job(job_id, data)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.is_scheduled and job.schedule_interval_hours:
        register_job(job.id, job.schedule_interval_hours)
    elif not job.is_scheduled:
        unregister_job(job.id)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, service: ScraperService = Depends(_get_service)):
    """Delete a scrape job and all its items."""
    unregister_job(job_id)
    if not service.delete_job(job_id):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.post("/{job_id}/run", status_code=status.HTTP_202_ACCEPTED)
def run_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    service: ScraperService = Depends(_get_service),
    db: Session = Depends(get_db),
):
    """Trigger a scrape job to run (async in background)."""
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    def _run():
        # Create a fresh DB session for the background task
        from app.database.session import SessionLocal
        bg_db = SessionLocal()
        try:
            bg_service = ScraperService(bg_db)
            bg_service.run_job(job_id)
        finally:
            bg_db.close()

    background_tasks.add_task(_run)
    return {"message": f"Job {job_id} queued for execution", "job_id": job_id}
