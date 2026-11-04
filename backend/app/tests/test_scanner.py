import os
import shutil
from pathlib import Path
from datetime import date
from PIL import Image
import pytest
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal, init_db
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.scan_job import ScanJob
from backend.app.models.scan_issue import ScanIssue
from backend.app.services.photo_scanner import PhotoScanner

def create_dummy_image(path: Path, color=(200, 100, 50), size=(100, 100)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(path, format="JPEG")

@pytest.fixture
def test_env(tmp_path):
    init_db()
    db = SessionLocal()

    # Clear previous test data
    db.query(ScanIssue).delete()
    db.query(ScanJob).delete()
    db.query(Photo).delete()
    db.query(SystemSetting).delete()
    db.commit()

    # Configure dummy photo root and birth date
    photo_dir = tmp_path / "photos"
    photo_dir.mkdir(parents=True, exist_ok=True)

    db.add(SystemSetting(key="photo_root", value=str(photo_dir.resolve())))
    db.add(SystemSetting(key="birth_date", value="2024-01-01"))
    db.add(SystemSetting(key="first_setup_completed", value="true"))
    db.commit()

    yield db, photo_dir

    db.close()

def test_scanner_valid_and_conflict_handling(test_env):
    db, photo_dir = test_env

    # 1. Create valid photo: 2024-11-03
    p1 = photo_dir / "241103.jpg"
    create_dummy_image(p1, color=(100, 150, 200))

    scanner = PhotoScanner(db)
    job = scanner.run_scan("FULL_SCAN")

    assert job.status == "COMPLETED"
    assert job.success_count == 1
    assert job.error_count == 0
    assert job.conflict_count == 0

    photo = db.query(Photo).filter(Photo.photo_date == "2024-11-03").first()
    assert photo is not None
    assert photo.status == "ACTIVE"
    assert photo.width == 100
    assert photo.height == 100
    assert photo.filename == "241103.jpg"

    # 2. Add conflicting photo for SAME DATE in a subdirectory
    # PRD & TDD Rule: NEVER overwrite existing photo, create DATE_CONFLICT issue
    sub_dir = photo_dir / "backup_folder"
    p1_conflict = sub_dir / "241103.jpg"
    create_dummy_image(p1_conflict, color=(50, 50, 50))

    job2 = scanner.run_scan("FULL_SCAN")
    assert job2.status == "COMPLETED"
    assert job2.conflict_count == 1

    # Verify original photo still intact and unchanged
    photo_after = db.query(Photo).filter(Photo.photo_date == "2024-11-03").first()
    assert photo_after.id == photo.id
    assert photo_after.relative_path == "241103.jpg"

    # Verify conflict issue was recorded
    conflict_issue = db.query(ScanIssue).filter(ScanIssue.issue_type == "DATE_CONFLICT").first()
    assert conflict_issue is not None
    assert conflict_issue.existing_photo_id == photo.id
    assert conflict_issue.parsed_date == "2024-11-03"

    # Verify original file was not modified or deleted
    assert p1.exists()
    assert p1_conflict.exists()

def test_scanner_invalid_filenames_and_dates(test_env):
    db, photo_dir = test_env

    # Invalid filename: not 6 digits
    create_dummy_image(photo_dir / "IMG_241103.jpg")
    create_dummy_image(photo_dir / "241103_01.jpg")

    # Invalid date: Feb 30 does not exist
    create_dummy_image(photo_dir / "250230.jpg")

    # Date out of range: before birth date (birth is 2024-01-01)
    create_dummy_image(photo_dir / "231103.jpg")

    scanner = PhotoScanner(db)
    job = scanner.run_scan("FULL_SCAN")

    assert job.status == "COMPLETED"
    assert job.error_count == 4

    issues = db.query(ScanIssue).all()
    issue_types = {issue.issue_type for issue in issues}
    assert "INVALID_FILENAME" in issue_types
    assert "INVALID_DATE" in issue_types
    assert "DATE_OUT_OF_RANGE" in issue_types

def test_scanner_missing_file_detection(test_env):
    db, photo_dir = test_env

    # Create and scan photo
    p = photo_dir / "240615.jpg"
    create_dummy_image(p)

    scanner = PhotoScanner(db)
    scanner.run_scan("FULL_SCAN")

    photo = db.query(Photo).filter(Photo.photo_date == "2024-06-15").first()
    assert photo.status == "ACTIVE"

    # Simulate user removing the file from disk
    os.remove(p)

    # Re-scan
    scanner.run_scan("FULL_SCAN")

    # Check status changed to MISSING and issue recorded
    db.refresh(photo)
    assert photo.status == "MISSING"

    missing_issue = db.query(ScanIssue).filter(
        ScanIssue.issue_type == "FILE_MISSING",
        ScanIssue.existing_photo_id == photo.id
    ).first()
    assert missing_issue is not None

def test_scanner_missing_dates_detection(test_env):
    db, photo_dir = test_env

    # Earliest photo: 2024-10-10
    # Next photo: 2024-10-12 (missing 2024-10-11)
    # Latest photo: 2024-10-20 (missing 2024-10-13 to 2024-10-19)
    create_dummy_image(photo_dir / "241010.jpg")
    create_dummy_image(photo_dir / "241012.jpg")
    create_dummy_image(photo_dir / "241020.jpg")

    scanner = PhotoScanner(db)
    job = scanner.run_scan("FULL_SCAN")

    assert job.status == "COMPLETED"
    assert job.success_count == 3
    assert job.missing_dates_json is not None

    import json
    info = json.loads(job.missing_dates_json)
    assert info["range_start"] == "2024-10-10"
    assert info["range_end"] == "2024-10-20"
    assert info["total_days"] == 11
    assert info["recorded_days"] == 3
    assert info["missing_count"] == 8

    # Verify specific missing dates
    assert "2024-10-11" in info["missing_dates"]
    assert "2024-10-13" in info["missing_dates"]
    assert "2024-10-19" in info["missing_dates"]

    # Crucial user requirement:
    # Dates strictly after the latest photo (e.g. 2024-10-21 through today) must NOT be reported as missing
    assert "2024-10-21" not in info["missing_dates"]
    assert "2024-11-04" not in info["missing_dates"]

    # Verify ranges
    assert len(info["missing_ranges"]) == 2
    assert info["missing_ranges"][0]["start"] == "2024-10-11"
    assert info["missing_ranges"][0]["count"] == 1
    assert info["missing_ranges"][1]["start"] == "2024-10-13"
    assert info["missing_ranges"][1]["end"] == "2024-10-19"
    assert info["missing_ranges"][1]["count"] == 7

    assert "缺少 8 天" in job.message

def test_full_scan_preserves_user_metadata(test_env):
    db, photo_dir = test_env
    from backend.app.models.tag import Tag

    # 1. Create and scan initial photo
    p = photo_dir / "241201.jpg"
    create_dummy_image(p)

    scanner = PhotoScanner(db)
    scanner.run_scan("FULL_SCAN")

    photo = db.query(Photo).filter(Photo.photo_date == "2024-12-01").first()
    assert photo is not None

    # 2. User sets highlight, description, and tags
    photo.is_highlight = 1
    photo.description = "宝宝第一次翻身，非常开心！"
    tag = Tag(name="里程碑")
    db.add(tag)
    photo.tags.append(tag)
    db.commit()

    # 3. Perform FULL_SCAN again
    job = scanner.run_scan("FULL_SCAN")
    assert job.status == "COMPLETED"

    # 4. Verify that user metadata is completely intact!
    db.refresh(photo)
    assert photo.is_highlight == 1
    assert photo.description == "宝宝第一次翻身，非常开心！"
    assert len(photo.tags) == 1
    assert photo.tags[0].name == "里程碑"

    # 5. Test: User replaces the photo file with a NEW image (same filename, new content)
    old_hash = photo.sha256
    create_dummy_image(p, color=(50, 100, 200), size=(300, 200)) # different image
    scanner.run_scan("FULL_SCAN")

    db.refresh(photo)
    assert photo.sha256 != old_hash
    assert photo.width == 300
    assert photo.height == 200
    # Metadata STILL preserved!
    assert photo.is_highlight == 1
    assert photo.description == "宝宝第一次翻身，非常开心！"
    assert len(photo.tags) == 1

    # 6. Test: User replaces photo with different extension (removes .jpg, adds .png)
    os.remove(p)
    p_png = photo_dir / "241201.png"
    img_png = Image.new("RGB", (400, 300), color=(10, 20, 30))
    img_png.save(p_png, format="PNG")

    scanner.run_scan("FULL_SCAN")

    db.refresh(photo)
    assert photo.filename == "241201.png"
    assert photo.width == 400
    assert photo.is_highlight == 1
    assert photo.description == "宝宝第一次翻身，非常开心！"
    assert len(photo.tags) == 1
