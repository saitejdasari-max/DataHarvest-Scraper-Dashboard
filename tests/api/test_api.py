"""
API tests – run with:  pytest tests/ -v
These test the job CRUD and items endpoints via TestClient.
DB uses SQLite in-memory to avoid requiring Postgres.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base, get_db
from app.main import app

# ── In-memory SQLite for tests ────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────
def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Jobs CRUD ─────────────────────────────────────────────────────────────
def test_list_jobs_empty(client):
    resp = client.get("/api/v1/jobs/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_job(client):
    payload = {
        "name": "Test Job",
        "url": "https://example.com",
        "job_type": "news",
        "is_scheduled": False,
        "use_selenium": False,
    }
    resp = client.post("/api/v1/jobs/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Job"
    assert data["job_type"] == "news"
    assert data["status"] == "pending"
    return data["id"]


def test_get_job(client):
    # Create first
    payload = {"name": "Get Test", "url": "https://example.com", "job_type": "products"}
    create_resp = client.post("/api/v1/jobs/", json=payload)
    job_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


def test_get_job_not_found(client):
    resp = client.get("/api/v1/jobs/999999")
    assert resp.status_code == 404


def test_update_job(client):
    payload = {"name": "Update Test", "url": "https://example.com", "job_type": "jobs"}
    create_resp = client.post("/api/v1/jobs/", json=payload)
    job_id = create_resp.json()["id"]

    resp = client.patch(f"/api/v1/jobs/{job_id}", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_delete_job(client):
    payload = {"name": "Delete Me", "url": "https://example.com", "job_type": "news"}
    job_id = client.post("/api/v1/jobs/", json=payload).json()["id"]

    resp = client.delete(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 204

    get_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 404


# ── Items ─────────────────────────────────────────────────────────────────
def test_list_items_paginated(client):
    resp = client.get("/api/v1/items/?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert data["page"] == 1


def test_list_items_with_filters(client):
    resp = client.get("/api/v1/items/?q=python&category=jobs&page=1&page_size=5")
    assert resp.status_code == 200


def test_stats_endpoint(client):
    resp = client.get("/api/v1/items/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_items" in data
    assert "total_jobs" in data
    assert "scrape_activity" in data


def test_export_csv(client):
    resp = client.get("/api/v1/items/export?format=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_export_excel(client):
    resp = client.get("/api/v1/items/export?format=excel")
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
