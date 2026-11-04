from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal, init_db
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.collection import Collection, CollectionPhoto
from backend.app.services.photo_scanner import PhotoScanner

def create_dummy_image(path: Path, color=(150, 150, 150), size=(100, 100)):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(path, format="JPEG")

@pytest.fixture
def app_client(tmp_path):
    init_db()
    db = SessionLocal()

    db.query(CollectionPhoto).delete()
    db.query(Collection).delete()
    db.query(Photo).delete()
    db.query(SystemSetting).delete()
    db.commit()

    photo_dir = tmp_path / "photos"
    photo_dir.mkdir(parents=True, exist_ok=True)

    db.add(SystemSetting(key="photo_root", value=str(photo_dir.resolve())))
    db.add(SystemSetting(key="birth_date", value="2024-01-01"))
    db.add(SystemSetting(key="first_setup_completed", value="true"))
    db.commit()

    create_dummy_image(photo_dir / "240801.jpg")
    create_dummy_image(photo_dir / "240802.jpg")

    scanner = PhotoScanner(db)
    scanner.run_scan("FULL_SCAN")

    db.close()
    return TestClient(app)

def test_collections_crud_and_photos(app_client):
    # 1. Create Collection
    create_payload = {
        "name": "Summer Beach Trip",
        "description": "Our wonderful time by the sea",
        "sort_order": 1
    }
    create_res = app_client.post("/api/collections", json=create_payload)
    assert create_res.status_code == 200
    col_id = create_res.json()["id"]

    # 2. Get Photos to add
    photos_res = app_client.get("/api/photos")
    photo_ids = [p["id"] for p in photos_res.json()["items"]]
    assert len(photo_ids) == 2

    # 3. Add Photos to Collection
    add_res = app_client.post(f"/api/collections/{col_id}/photos", json={"photo_ids": photo_ids})
    assert add_res.status_code == 200
    assert len(add_res.json()["photos"]) == 2

    # 4. List Collections
    list_res = app_client.get("/api/collections")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert list_res.json()[0]["photo_count"] == 2

    # 5. Remove one photo from collection
    del_photo_res = app_client.delete(f"/api/collections/{col_id}/photos/{photo_ids[0]}")
    assert del_photo_res.status_code == 200

    detail_res = app_client.get(f"/api/collections/{col_id}")
    assert len(detail_res.json()["photos"]) == 1

    # 6. Delete collection (must NOT delete photos)
    del_col_res = app_client.delete(f"/api/collections/{col_id}")
    assert del_col_res.status_code == 200

    photos_after = app_client.get("/api/photos")
    assert photos_after.json()["total"] == 2  # Photos are untouched!

def test_highlights_crud(app_client):
    photos_res = app_client.get("/api/photos")
    p_id = photos_res.json()["items"][0]["id"]

    # Mark as highlight
    post_res = app_client.post(f"/api/highlights/{p_id}")
    assert post_res.status_code == 200
    assert post_res.json()["is_highlight"] == 1

    # Update metadata
    put_res = app_client.put(f"/api/highlights/{p_id}/metadata", json={
        "description": "Golden sunset",
        "tags": ["Beach", "Sunset"]
    })
    assert put_res.status_code == 200
    assert put_res.json()["description"] == "Golden sunset"

    # List highlights
    list_h = app_client.get("/api/highlights")
    assert list_h.status_code == 200
    assert len(list_h.json()) == 1

    # Filter by tag
    tag_h = app_client.get("/api/highlights?tag=Beach")
    assert len(tag_h.json()) == 1
    empty_h = app_client.get("/api/highlights?tag=Winter")
    assert len(empty_h.json()) == 0

    # Remove from highlight
    del_res = app_client.delete(f"/api/highlights/{p_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_highlight"] == 0

def test_backup_and_json_export(app_client):
    # Create backup snapshot
    backup_res = app_client.post("/api/backup/create")
    assert backup_res.status_code == 200
    b_data = backup_res.json()
    assert "filename" in b_data
    filename = b_data["filename"]

    # List backups
    list_res = app_client.get("/api/backup/list")
    assert list_res.status_code == 200
    assert any(b["filename"] == filename for b in list_res.json())

    # Export JSON
    json_res = app_client.get("/api/backup/export-json")
    assert json_res.status_code == 200
    exported = json_res.json()
    assert exported["export_version"] == "2.0"
    assert "photos" in exported
    assert len(exported["photos"]) == 2
    assert "settings" in exported
