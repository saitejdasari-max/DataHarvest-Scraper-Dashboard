import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.scraper_service import ScraperService
from app.services.export_service import export_csv, export_excel
from app.schemas.schemas import ItemFilterParams, PaginatedResponse, ScrapedItemResponse, DashboardStats

router = APIRouter(prefix="/items", tags=["Scraped Items"])


def _get_service(db: Session = Depends(get_db)) -> ScraperService:
    return ScraperService(db)


@router.get("/", response_model=PaginatedResponse)
def list_items(
    q: Optional[str] = Query(None, description="Full-text search"),
    job_id: Optional[int] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    company: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ScraperService = Depends(_get_service),
):
    """List items with full filtering, search, and pagination."""
    filters = ItemFilterParams(
        q=q, job_id=job_id, source=source, category=category,
        location=location, company=company,
        min_price=min_price, max_price=max_price,
        page=page, page_size=page_size,
    )
    items, total = service.list_items(filters)
    total_pages = math.ceil(total / page_size)
    return PaginatedResponse(
        items=[ScrapedItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=DashboardStats)
def get_stats(service: ScraperService = Depends(_get_service)):
    """Dashboard statistics."""
    return service.get_stats()


@router.get("/export")
def export_items(
    format: str = Query("csv", regex="^(csv|excel)$"),
    job_id: Optional[int] = None,
    source: Optional[str] = None,
    service: ScraperService = Depends(_get_service),
):
    """Export filtered items as CSV or Excel."""
    items = service.get_items_for_export(job_id=job_id, source=source)

    if format == "csv":
        data = export_csv(items)
        return StreamingResponse(
            iter([data]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=scraped_data.csv"},
        )
    else:
        data = export_excel(items)
        return StreamingResponse(
            iter([data]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=scraped_data.xlsx"},
        )
