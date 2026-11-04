from datetime import date
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal, init_db
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.memory import MemoryDailySet
from backend.app.services.memory_service import MemoryService
from backend.app.services.photo_scanner import PhotoScanner

def create_dummy_image(path: Path, color=(120, 180, 240), size=(100, 100)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(path, format="JPEG")

@pytest.fixture
def memory_client(tmp_path):
    init_db()
    db = SessionLocal()

    db.query(MemoryDailySet).delete()
    db.query(Photo).delete()
    db.query(SystemSetting).delete()
    db.commit()

    photo_dir = tmp_path / "photos"
    photo_dir.mkdir(parents=True, exist_ok=True)

    db.add(SystemSetting(key="photo_root", value=str(photo_dir.resolve())))
    db.add(SystemSetting(key="birth_date", value="2023-01-01"))
    db.add(SystemSetting(key="first_setup_completed", value="true"))
    db.commit()

    # Create historical photos
    # Assume reference date is 2026-11-03:
    # On this day: 241103 (2 years ago), 251103 (1 year ago)
    # One year ago +- 7 days: 251105 (Nov 5, 2025)
    # Random candidate: 240615 (June 15, 2024)
    create_dummy_image(photo_dir / "241103.jpg")
    create_dummy_image(photo_dir / "251103.jpg")
    create_dummy_image(photo_dir / "240615.jpg")

    scanner = PhotoScanner(db)
    scanner.run_scan("FULL_SCAN")

    db.close()
    return TestClient(app)

def test_daily_memories_generation_and_stability(memory_client):
    db = SessionLocal()
    service = MemoryService(db)

    ref_today = date(2026, 11, 3)

    # 1. First invocation generates memories
    memories_1 = service.get_or_create_daily_memories(ref_today)
    assert len(memories_1) >= 2

    types = [m["memory_type"] for m in memories_1]
    assert "ON_THIS_DAY" in types

    # Check persistence in memory_daily_sets
    saved = db.query(MemoryDailySet).filter(MemoryDailySet.memory_date == "2026-11-03").all()
    assert len(saved) == len(memories_1)

    # 2. Second invocation on the SAME date returns exact same stable set
    memories_2 = service.get_or_create_daily_memories(ref_today)
    photo_ids_1 = [m["photo"]["id"] for m in memories_1]
    photo_ids_2 = [m["photo"]["id"] for m in memories_2]
    assert photo_ids_1 == photo_ids_2

    db.close()

def test_home_overview_api(memory_client):
    res = memory_client.get("/api/home/overview")
    assert res.status_code == 200
    data = res.json()

    assert "total_photos" in data
    assert data["total_photos"] == 3
    assert data["days_recorded"] == 3
    assert "current_age" in data
    assert data["current_age"] is not None
    assert "memories" in data
    assert "recent_moments" in data
    assert len(data["recent_moments"]) == 3

def test_option_b_exact_on_this_day(memory_client):
    db = SessionLocal()
    service = MemoryService(db)

    # Reference today is 2026-11-03
    # Existing photos: 2024-11-03, 2025-11-03, 2024-06-15
    ref_today = date(2026, 11, 3)
    memories = service.get_or_create_daily_memories(ref_today)

    otd = [m for m in memories if m["memory_type"] == "ON_THIS_DAY"]
    # Both 2025-11-03 and 2024-11-03 must be matched exactly
    assert len(otd) == 2
    dates = [m["photo"]["photo_date"] for m in otd]
    assert "2025-11-03" in dates
    assert "2024-11-03" in dates

    titles = {m["photo"]["photo_date"]: m["title"] for m in otd}
    assert titles["2025-11-03"] == "1 年前的今天"
    assert titles["2024-11-03"] == "2 年前的今天"

    # Now test a date with no exact matches, e.g. 2026-11-04
    ref_day_empty = date(2026, 11, 4)
    memories_empty = service.get_or_create_daily_memories(ref_day_empty)
    otd_empty = [m for m in memories_empty if m["memory_type"] == "ON_THIS_DAY"]
    # Option B strictly does NOT match adjacent dates like 2024-11-03 or 2025-11-03
    assert len(otd_empty) == 0

    db.close()
