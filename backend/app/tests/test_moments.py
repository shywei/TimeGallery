import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from backend.app.main import app
from backend.app.db.database import get_db, Base, engine, SessionLocal
from backend.app.models.system_config import SystemSetting
from backend.app.models.moment import Moment, MomentMedia
from backend.app.services.moment_service import MomentScanner

@pytest.fixture
def client(tmp_path):
    # Setup test DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Setup sample moment folder in tmp_path
    photo_root = tmp_path / "photos"
    photo_root.mkdir()
    
    moment_folder = photo_root / "241103"
    moment_folder.mkdir()
    
    # Create sample image
    sample_img = moment_folder / "img1.jpg"
    from PIL import Image
    im = Image.new("RGB", (100, 100), color="blue")
    im.save(sample_img)
    
    # Create sample video file
    sample_vid = moment_folder / "vid1.mp4"
    sample_vid.write_bytes(b"dummy video content 12345")
    
    # Configure photo_root
    db.query(SystemSetting).filter(SystemSetting.key == "photo_root").delete()
    setting = SystemSetting(key="photo_root", value=str(photo_root))
    db.add(setting)
    db.commit()
    
    # Run MomentScanner
    scanner = MomentScanner(db)
    scanner.scan_moments(photo_root)
    
    db.close()
    
    with TestClient(app) as test_client:
        yield test_client

def test_list_and_get_moments(client):
    # 1. List moments
    res = client.get("/api/moments")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["moment_date"] == "2024-11-03"
    assert data[0]["photo_count"] == 1
    assert data[0]["video_count"] == 1
    assert data[0]["total_media"] == 2

    # 2. Get moment detail
    res_detail = client.get("/api/moments/2024-11-03")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["moment_date"] == "2024-11-03"
    assert len(detail["media_items"]) == 2
    
    types = {m["media_type"] for m in detail["media_items"]}
    assert "PHOTO" in types
    assert "VIDEO" in types

    # 3. Test video streaming endpoint
    vid_item = next(m for m in detail["media_items"] if m["media_type"] == "VIDEO")
    stream_res = client.get(f"/api/moments/media/{vid_item['id']}/stream")
    assert stream_res.status_code in (200, 206)
    assert stream_res.content == b"dummy video content 12345"

    # 4. Test re-scan (update existing moment without crashing on updated_at)
    db = SessionLocal()
    setting = db.query(SystemSetting).filter(SystemSetting.key == "photo_root").first()
    scanner = MomentScanner(db)
    result = scanner.scan_moments(Path(setting.value))
    assert result["moments_count"] == 1
    assert result["total_photos"] == 1
    assert result["total_videos"] == 1
    db.close()

    # 5. Test updating title and description
    put_res = client.put("/api/moments/2024-11-03", json={
        "title": "宝宝抓周特别时刻",
        "description": "抓周选了画笔，大家都很开心！"
    })
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["title"] == "宝宝抓周特别时刻"
    assert updated_data["description"] == "抓周选了画笔，大家都很开心！"

    # Verify detail reflects updated metadata
    res_after = client.get("/api/moments/2024-11-03")
    assert res_after.status_code == 200
    assert res_after.json()["title"] == "宝宝抓周特别时刻"
    assert res_after.json()["description"] == "抓周选了画笔，大家都很开心！"
