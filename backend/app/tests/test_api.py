import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_system_status(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "拾光记"
    assert data["status"] == "healthy"
    assert "first_setup_completed" in data
    assert "photo_count" in data

def test_system_config(client):
    response = client.get("/api/system/config")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "拾光记"
    assert "data_root" in data
    assert "thumbnail_size" in data
    assert "baseline_type" in data

def test_spa_delivery_and_fallback(client):
    # Test root returns SPA index.html
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert "text/html" in root_resp.headers.get("content-type", "")
    assert "拾光记" in root_resp.text

    # Test client route fallback to SPA index.html
    fallback_resp = client.get("/calendar?view=month&date=2024-11-03")
    assert fallback_resp.status_code == 200
    assert "text/html" in fallback_resp.headers.get("content-type", "")

def test_tags_endpoint(client):
    resp = client.get("/api/tags")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

