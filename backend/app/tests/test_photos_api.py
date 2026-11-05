from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal, init_db
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.tag import Tag
from backend.app.services.photo_scanner import PhotoScanner

def create_dummy_image(path: Path, color=(120, 80, 220), size=(200, 150)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(path, format="JPEG")

@pytest.fixture
def photo_client(tmp_path):
    init_db()
    db = SessionLocal()

    # Clear previous records
    db.query(Photo).delete()
    db.query(Tag).delete()
    db.query(SystemSetting).delete()
    db.commit()

    photo_dir = tmp_path / "photos"
    photo_dir.mkdir(parents=True, exist_ok=True)

    db.add(SystemSetting(key="photo_root", value=str(photo_dir.resolve())))
    db.add(SystemSetting(key="birth_date", value="2024-01-01"))
    db.add(SystemSetting(key="first_setup_completed", value="true"))
    db.commit()

    # Create dummy images
    create_dummy_image(photo_dir / "240501.jpg", color=(255, 0, 0), size=(800, 600))
    create_dummy_image(photo_dir / "240502.jpg", color=(0, 255, 0), size=(1200, 900))

    scanner = PhotoScanner(db)
    scanner.run_scan("FULL_SCAN")

    db.close()

    client = TestClient(app)
    return client

def test_list_and_filter_photos(photo_client):
    res = photo_client.get("/api/photos")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["photo_date"] == "240502" or "2024-05-02"

    # Year filter
    res_year = photo_client.get("/api/photos?year=2024&month=5")
    assert res_year.status_code == 200
    assert res_year.json()["total"] == 2

    # Backend search query
    res_search = photo_client.get("/api/photos?search=0501")
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["photo_date"] == "2024-05-01"

    # Years endpoint
    res_years = photo_client.get("/api/photos/years")
    assert res_years.status_code == 200
    assert "2024" in res_years.json()

    res_empty = photo_client.get("/api/photos?year=2025")
    assert res_empty.status_code == 200
    assert res_empty.json()["total"] == 0

def test_photo_detail_and_age(photo_client):
    list_res = photo_client.get("/api/photos")
    photo_id = list_res.json()["items"][0]["id"]

    res = photo_client.get(f"/api/photos/{photo_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == photo_id
    assert "age_at_photo" in detail
    assert detail["age_at_photo"] is not None
    assert detail["age_at_photo"]["display"] is not None
    assert detail["age_at_photo"]["months"] == 4  # Jan 1 to May 2

def test_thumbnails_and_preview_generation(photo_client):
    list_res = photo_client.get("/api/photos")
    photo_id = list_res.json()["items"][0]["id"]

    # Thumbnail
    thumb_res = photo_client.get(f"/api/photos/{photo_id}/thumbnail")
    assert thumb_res.status_code == 200
    assert thumb_res.headers["content-type"] == "image/webp"
    assert len(thumb_res.content) > 0

    # Preview
    prev_res = photo_client.get(f"/api/photos/{photo_id}/preview")
    assert prev_res.status_code == 200
    assert prev_res.headers["content-type"] == "image/webp"
    assert len(prev_res.content) > 0

    # Original
    orig_res = photo_client.get(f"/api/photos/{photo_id}/original")
    assert orig_res.status_code == 200
    assert "image" in orig_res.headers["content-type"]

def test_update_photo_metadata(photo_client):
    list_res = photo_client.get("/api/photos")
    photo_id = list_res.json()["items"][0]["id"]

    update_payload = {
        "description": "Lovely sunny morning stroll in the garden.",
        "is_highlight": True,
        "tags": ["Spring", "Garden", "Sunny"]
    }
    put_res = photo_client.put(f"/api/photos/{photo_id}/metadata", json=update_payload)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["description"] == "Lovely sunny morning stroll in the garden."
    assert updated["is_highlight"] == 1
    tag_names = {t["name"] for t in updated["tags"]}
    assert tag_names == {"Spring", "Garden", "Sunny"}

    # Query with highlight filter
    highlight_res = photo_client.get("/api/photos?is_highlight=true")
    assert highlight_res.status_code == 200
    assert highlight_res.json()["total"] == 1

def test_photo_detail_on_this_day_photos(photo_client, tmp_path):
    db = SessionLocal()
    photo_dir = tmp_path / "photos"
    # Add a photo in 2025 on May 1 (matching 240501.jpg)
    create_dummy_image(photo_dir / "250501.jpg", color=(10, 20, 30))
    scanner = PhotoScanner(db)
    scanner.run_scan("FULL_SCAN")

    p_2024 = db.query(Photo).filter(Photo.photo_date == "2024-05-01").first()
    p_2025 = db.query(Photo).filter(Photo.photo_date == "2025-05-01").first()
    p_2024_02 = db.query(Photo).filter(Photo.photo_date == "2024-05-02").first()
    db.close()

    assert p_2024 is not None
    assert p_2025 is not None

    # Query detail for 2025-05-01
    res = photo_client.get(f"/api/photos/{p_2025.id}")
    assert res.status_code == 200
    detail = res.json()
    assert "on_this_day_photos" in detail
    assert len(detail["on_this_day_photos"]) == 1
    otd = detail["on_this_day_photos"][0]
    assert otd["id"] == p_2024.id
    assert otd["photo_date"] == "2024-05-01"
    assert otd["title"] == "1 年前的今天"

    # Query detail for 2024-05-02 (no other year exists)
    res_single = photo_client.get(f"/api/photos/{p_2024_02.id}")
    assert res_single.status_code == 200
    detail_single = res_single.json()
    assert detail_single["on_this_day_photos"] == []

def test_adjacent_photos_navigation(photo_client):
    db = SessionLocal()
    # Photos in fixture: 2024-05-01, 2024-05-02, and test_on_this_day_photos added 2025-05-01
    p1 = db.query(Photo).filter(Photo.photo_date == "2024-05-01").first()
    p2 = db.query(Photo).filter(Photo.photo_date == "2024-05-02").first()
    p3 = db.query(Photo).filter(Photo.photo_date == "2025-05-01").first()
    db.close()

    if p1 and p2:
        res1 = photo_client.get(f"/api/photos/{p1.id}")
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["prev_photo_id"] is None
        assert d1["next_photo_id"] == p2.id
        assert d1["next_date"] == p2.photo_date

        res2 = photo_client.get(f"/api/photos/{p2.id}")
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["prev_photo_id"] == p1.id
        assert d2["prev_date"] == p1.photo_date
