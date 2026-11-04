from datetime import date
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal, init_db
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.services.calendar_service import parse_flexible_date
from backend.app.services.photo_scanner import PhotoScanner
from backend.app.core.exceptions import InvalidDateError

def create_dummy_image(path: Path, color=(100, 150, 200), size=(100, 100)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(path, format="JPEG")

@pytest.fixture
def calendar_client(tmp_path):
    init_db()
    db = SessionLocal()

    db.query(Photo).delete()
    db.query(SystemSetting).delete()
    db.commit()

    photo_dir = tmp_path / "photos"
    photo_dir.mkdir(parents=True, exist_ok=True)

    db.add(SystemSetting(key="photo_root", value=str(photo_dir.resolve())))
    db.add(SystemSetting(key="birth_date", value="2024-01-01"))
    db.add(SystemSetting(key="first_setup_completed", value="true"))
    db.commit()

    # Create test photos in Nov 2024:
    # 2024-11-04 is a Monday!
    # 2024-11-06 is a Wednesday!
    create_dummy_image(photo_dir / "241104.jpg")
    create_dummy_image(photo_dir / "241106.jpg")
    create_dummy_image(photo_dir / "241120.jpg")

    scanner = PhotoScanner(db)
    scanner.run_scan("FULL_SCAN")

    db.close()
    return TestClient(app)

def test_flexible_date_parsing():
    # Both standard ISO and 6-digit yymmdd are supported
    assert parse_flexible_date("2024-11-03") == date(2024, 11, 3)
    assert parse_flexible_date("241103") == date(2024, 11, 3)
    assert parse_flexible_date("250228") == date(2025, 2, 28)
    assert parse_flexible_date("240229") == date(2024, 2, 29) # Leap year

    with pytest.raises(InvalidDateError):
        parse_flexible_date("2411030") # 7 digits
    with pytest.raises(InvalidDateError):
        parse_flexible_date("250230") # Invalid calendar date
    with pytest.raises(InvalidDateError):
        parse_flexible_date("invalid-date")

def test_day_view(calendar_client):
    # Day with photo
    res_photo = calendar_client.get("/api/calendar/day/2024-11-04")
    assert res_photo.status_code == 200
    data = res_photo.json()
    assert data["date"] == "2024-11-04"
    assert data["has_photo"] is True
    assert data["photo"]["filename"] == "241104.jpg"
    assert data["prev_date"] == "2024-11-03"
    assert data["next_date"] == "2024-11-05"
    assert data["age"]["months"] == 10

    # Day without photo
    res_empty = calendar_client.get("/api/calendar/day/241105")
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["date"] == "2024-11-05"
    assert data_empty["has_photo"] is False
    assert data_empty["photo"] is None

def test_week_view(calendar_client):
    # Query Wednesday 2024-11-06
    res = calendar_client.get("/api/calendar/week/2024-11-06")
    assert res.status_code == 200
    data = res.json()
    # Monday must be 2024-11-04, Sunday must be 2024-11-10
    assert data["start_date"] == "2024-11-04"
    assert data["end_date"] == "2024-11-10"
    assert data["total_days"] == 7
    assert data["recorded_days"] == 2 # 241104 and 241106

    days = data["days"]
    assert len(days) == 7
    # Day 0 (Monday): has photo
    assert days[0]["date"] == "2024-11-04"
    assert days[0]["has_photo"] is True
    # Day 1 (Tuesday): no photo
    assert days[1]["date"] == "2024-11-05"
    assert days[1]["has_photo"] is False

def test_month_calendar_and_photo_wall(calendar_client):
    # Standard Month Calendar
    res = calendar_client.get("/api/calendar/month/2024/11")
    assert res.status_code == 200
    data = res.json()
    assert data["year"] == 2024
    assert data["month"] == 11
    assert data["days_in_month"] == 30
    assert data["recorded_days"] == 3 # 3 photos in Nov 2024
    assert len(data["days"]) % 7 == 0 # Complete 7-column rows

    # Month Photo Wall (asc order)
    res_wall = calendar_client.get("/api/calendar/month/2024/11/photo-wall")
    assert res_wall.status_code == 200
    data_wall = res_wall.json()
    assert data_wall["total_photos"] == 3
    dates = [p["photo_date"] for p in data_wall["items"]]
    assert dates == ["2024-11-04", "2024-11-06", "2024-11-20"] # strictly ASC

def test_quick_date_lookup(calendar_client):
    # Lookup using 6-digit format
    res = calendar_client.get("/api/calendar/date/241104")
    assert res.status_code == 200
    data = res.json()
    assert data["date"] == "2024-11-04"
    assert data["has_photo"] is True
    assert data["photo_id"] is not None

    # Lookup using ISO format for empty date
    res2 = calendar_client.get("/api/calendar/date/2024-11-05")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["date"] == "2024-11-05"
    assert data2["has_photo"] is False

def test_timeline_stream(calendar_client):
    res = calendar_client.get("/api/timeline")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["groups"]) == 1
    assert data["groups"][0]["period"] == "2024-11"
    # Timeline is DESC order by default
    photos = data["groups"][0]["photos"]
    assert photos[0]["photo_date"] == "2024-11-20"
    assert photos[1]["photo_date"] == "2024-11-06"
    assert photos[2]["photo_date"] == "2024-11-04"
