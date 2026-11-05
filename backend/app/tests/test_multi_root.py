import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import get_db, Base, engine, SessionLocal
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.moment import Moment
from backend.app.services.photo_scanner import PhotoScanner
from backend.app.services.storage_service import set_configured_photo_roots


@pytest.fixture
def client_with_two_roots(tmp_path):
    root1 = tmp_path / "photos_root1"
    root2 = tmp_path / "photos_root2"
    root1.mkdir(parents=True, exist_ok=True)
    root2.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        db.query(SystemSetting).delete()
        db.query(Photo).delete()
        db.query(Moment).delete()
        db.commit()

        set_configured_photo_roots(db, [str(root1), str(root2)], str(root1))
        db.add(SystemSetting(key="first_setup_completed", value="true"))
        db.commit()

    with TestClient(app) as client:
        yield client, root1, root2


def create_test_image(path: Path, color=(200, 100, 50)):
    img = Image.new("RGB", (600, 400), color=color)
    img.save(path, "JPEG")


def test_multi_root_scan_and_read(client_with_two_roots):
    client, root1, root2 = client_with_two_roots

    # Root 1 gets 240501.jpg
    create_test_image(root1 / "240501.jpg")
    # Root 2 gets 240502.jpg
    create_test_image(root2 / "240502.jpg")

    # Moment folder in Root 2
    m_dir = root2 / "240503"
    m_dir.mkdir()
    create_test_image(m_dir / "pic1.jpg")

    with SessionLocal() as db:
        scanner = PhotoScanner(db)
        job = scanner.run_scan("FULL_SCAN")
        assert job.status == "COMPLETED"
        assert job.success_count == 2

        # Check DB records have root_path recorded
        p1 = db.query(Photo).filter(Photo.photo_date == "2024-05-01").first()
        p2 = db.query(Photo).filter(Photo.photo_date == "2024-05-02").first()
        assert p1 is not None
        assert p2 is not None
        assert p1.root_path == str(root1.resolve())
        assert p2.root_path == str(root2.resolve())

        m = db.query(Moment).filter(Moment.moment_date == "2024-05-03").first()
        assert m is not None
        assert m.root_path == str(root2.resolve())

        p1_id = p1.id
        p2_id = p2.id

    # Verify thumbnails & original downloads work via API for both roots
    res1 = client.get(f"/api/photos/{p1_id}/thumbnail")
    assert res1.status_code == 200
    assert res1.headers["content-type"] == "image/webp"

    res2 = client.get(f"/api/photos/{p2_id}/thumbnail")
    assert res2.status_code == 200
    assert res2.headers["content-type"] == "image/webp"

    res_orig = client.get(f"/api/photos/{p2_id}/original")
    assert res_orig.status_code == 200


def test_multi_root_content_mgmt(client_with_two_roots):
    client, root1, root2 = client_with_two_roots

    # Check day status returns available roots
    res = client.get("/api/mgmt/content/day/2024-06-01")
    assert res.status_code == 200
    data = res.json()
    assert str(root1.resolve()) in data["available_roots"]
    assert str(root2.resolve()) in data["available_roots"]

    # Upload photo to Root 2 explicitly
    temp_file = root1.parent / "temp.jpg"
    with open(temp_file, "wb") as f:
        Image.new("RGB", (300, 300), (10, 20, 30)).save(f, "JPEG")

    with open(temp_file, "rb") as f:
        upload_res = client.post(
            "/api/mgmt/content/daily-photo",
            data={"date_str": "2024-06-01", "target_root": str(root2.resolve())},
            files={"file": ("test.jpg", f, "image/jpeg")}
        )
    assert upload_res.status_code == 200

    # Verify file was written to root2, not root1
    assert (root2 / "240601.jpg").exists()
    assert not (root1 / "240601.jpg").exists()

    # Delete photo -> should be moved to root2/.trash
    del_res = client.delete("/api/mgmt/content/daily-photo/2024-06-01")
    assert del_res.status_code == 200
    assert not (root2 / "240601.jpg").exists()
    assert (root2 / ".trash" / "daily").exists()

    # Trash stats should reflect the item
    stats_res = client.get("/api/mgmt/content/trash/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["file_count"] >= 1

    # Empty trash
    empty_res = client.post("/api/mgmt/content/trash/empty")
    assert empty_res.status_code == 200
    stats_res2 = client.get("/api/mgmt/content/trash/stats")
    assert stats_res2.json()["file_count"] == 0
