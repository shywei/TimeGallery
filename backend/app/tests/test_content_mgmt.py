import io
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal, init_db
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.moment import Moment, MomentMedia
from backend.app.models.tag import Tag


def create_test_image_bytes(color=(120, 80, 220), size=(200, 150)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def mgmt_client(tmp_path):
    init_db()
    db = SessionLocal()

    # Clear DB
    db.query(Photo).delete()
    db.query(MomentMedia).delete()
    db.query(Moment).delete()
    db.query(Tag).delete()
    db.query(SystemSetting).delete()
    db.commit()

    photo_dir = tmp_path / "photos"
    photo_dir.mkdir(parents=True, exist_ok=True)

    db.add(SystemSetting(key="photo_root", value=str(photo_dir.resolve())))
    db.add(SystemSetting(key="first_setup_completed", value="true"))
    db.commit()
    db.close()

    client = TestClient(app)
    return client, photo_dir


def test_daily_photo_upload_replace_delete_trash(mgmt_client):
    client, photo_dir = mgmt_client
    date_str = "2024-11-11"

    # 1. Day status initially empty
    res = client.get(f"/api/mgmt/content/day/{date_str}")
    assert res.status_code == 200
    data = res.json()
    assert data["date"] == date_str
    assert data["yymmdd"] == "241111"
    assert data["has_daily_photo"] is False
    assert data["has_moment"] is False

    # 2. Upload daily photo
    img_bytes1 = create_test_image_bytes(color=(255, 0, 0))
    res_upload = client.post(
        "/api/mgmt/content/daily-photo",
        data={"date_str": date_str},
        files={"file": ("my_pic.jpg", img_bytes1, "image/jpeg")}
    )
    assert res_upload.status_code == 200
    up_data = res_upload.json()
    assert up_data["success"] is True
    assert (photo_dir / "241111.jpg").exists()

    # Verify day status now has daily photo
    res_status = client.get(f"/api/mgmt/content/day/{date_str}")
    assert res_status.json()["has_daily_photo"] is True
    assert res_status.json()["daily_photo"]["filename"] == "241111.jpg"

    # 3. Replace daily photo with a new image (blue)
    img_bytes2 = create_test_image_bytes(color=(0, 0, 255))
    res_replace = client.post(
        "/api/mgmt/content/daily-photo",
        data={"date_str": date_str},
        files={"file": ("new_pic.jpg", img_bytes2, "image/jpeg")}
    )
    assert res_replace.status_code == 200
    assert (photo_dir / "241111.jpg").exists()

    # Verify old file was moved to trash!
    trash_daily = photo_dir / ".trash" / "daily"
    assert trash_daily.exists()
    trashed_files = list(trash_daily.glob("241111_*.jpg"))
    assert len(trashed_files) == 1

    # 4. Delete daily photo
    res_del1 = client.delete(f"/api/mgmt/content/daily-photo/{date_str}")
    assert res_del1.status_code == 200
    assert not (photo_dir / "241111.jpg").exists()

    # Now trash should have 2 versioned files for 241111!
    trashed_files = list(trash_daily.glob("241111_*.jpg"))
    assert len(trashed_files) == 2

    # 5. Upload and delete AGAIN to verify multiple deletions never collide
    img_bytes3 = create_test_image_bytes(color=(0, 255, 0))
    client.post(
        "/api/mgmt/content/daily-photo",
        data={"date_str": date_str},
        files={"file": ("third.jpg", img_bytes3, "image/jpeg")}
    )
    res_del2 = client.delete(f"/api/mgmt/content/daily-photo/{date_str}")
    assert res_del2.status_code == 200

    trashed_files = list(trash_daily.glob("241111_*.jpg"))
    assert len(trashed_files) == 3


def test_special_moment_upload_and_delete(mgmt_client):
    client, photo_dir = mgmt_client
    date_str = "2024-11-20"

    # 1. Upload multiple media to special moment
    img1 = create_test_image_bytes(color=(100, 100, 100))
    img2 = create_test_image_bytes(color=(200, 200, 200))

    res_upload = client.post(
        "/api/mgmt/content/moment-media",
        data={
            "date_str": date_str,
            "title": "游乐园一日游",
            "description": "第一次去游乐园做旋转木马"
        },
        files=[
            ("files", ("photo1.jpg", img1, "image/jpeg")),
            ("files", ("photo2.jpg", img2, "image/jpeg"))
        ]
    )
    assert res_upload.status_code == 200
    moment_info = res_upload.json()
    assert moment_info["success"] is True
    assert moment_info["photo_count"] == 2

    moment_dir = photo_dir / "241120"
    assert moment_dir.exists()
    assert (moment_dir / "photo1.jpg").exists()
    assert (moment_dir / "photo2.jpg").exists()

    # Check day status
    res_day = client.get(f"/api/mgmt/content/day/{date_str}")
    day_data = res_day.json()
    assert day_data["has_moment"] is True
    assert day_data["moment"]["title"] == "游乐园一日游"
    assert len(day_data["moment"]["media_items"]) == 2

    # 2. Delete single media item
    first_media_id = day_data["moment"]["media_items"][0]["id"]
    res_del_media = client.delete(f"/api/mgmt/content/moment-media/{first_media_id}")
    assert res_del_media.status_code == 200

    trash_media = photo_dir / ".trash" / "moment_media" / "241120"
    assert trash_media.exists()
    assert len(list(trash_media.glob("photo1_*.jpg"))) == 1

    # 3. Delete entire special moment
    res_del_moment = client.delete(f"/api/mgmt/content/moment/{date_str}")
    assert res_del_moment.status_code == 200
    assert not moment_dir.exists()

    trash_moments = photo_dir / ".trash" / "moments"
    assert trash_moments.exists()
    assert len(list(trash_moments.glob("241120_*"))) == 1

    # 4. Check trash stats and empty trash
    res_stats = client.get("/api/mgmt/content/trash/stats")
    assert res_stats.status_code == 200
    assert res_stats.json()["file_count"] >= 2

    res_empty = client.post("/api/mgmt/content/trash/empty")
    assert res_empty.status_code == 200
    assert res_empty.json()["deleted_count"] >= 2

    # Verify trash is now empty
    res_stats_after = client.get("/api/mgmt/content/trash/stats")
    assert res_stats_after.json()["file_count"] == 0
