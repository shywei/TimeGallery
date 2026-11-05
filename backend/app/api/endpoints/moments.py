from datetime import date, datetime
from pathlib import Path
from typing import Optional, List
import mimetypes
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.core.config import settings
from backend.app.core.paths import resolve_safe_path
from backend.app.models.system_config import SystemSetting
from backend.app.models.moment import Moment, MomentMedia
from backend.app.models.photo import Photo
from backend.app.services.age_service import calculate_timeline_milestone, calculate_age
from backend.app.services.moment_service import (
    get_moment_media_thumbnail,
    get_moment_media_preview
)

from backend.app.services.storage_service import (
    resolve_media_root,
    get_primary_photo_root
)

router = APIRouter(prefix="/moments", tags=["Moments"])

def get_photo_root(db: Session) -> Path:
    return get_primary_photo_root(db)

def get_baseline_info(db: Session) -> tuple[Optional[date], str, str]:
    s = db.query(SystemSetting).filter(SystemSetting.key == "baseline_date").first()
    if not s or not s.value:
        s = db.query(SystemSetting).filter(SystemSetting.key == "birth_date").first()
    
    b_date = None
    if s and s.value:
        try:
            b_date = date.fromisoformat(s.value)
        except Exception:
            pass

    type_s = db.query(SystemSetting).filter(SystemSetting.key == "baseline_type").first()
    b_type = type_s.value if type_s and type_s.value else "BIRTHDAY"

    label_s = db.query(SystemSetting).filter(SystemSetting.key == "baseline_label").first()
    b_label = label_s.value if label_s and label_s.value else ""

    return b_date, b_type, b_label

def get_birth_date(db: Session) -> Optional[date]:
    d, _, _ = get_baseline_info(db)
    return d

@router.get("")
def list_moments(db: Session = Depends(get_db)):
    """
    Returns all special moments in descending chronological order.
    """
    moments = db.query(Moment).order_by(Moment.moment_date.desc()).all()
    baseline_date, b_type, b_label = get_baseline_info(db)

    results = []
    for m in moments:
        # Milestone at moment
        age_info = None
        if baseline_date and b_type != "NONE":
            try:
                m_date = date.fromisoformat(m.moment_date)
                age_info = calculate_timeline_milestone(baseline_date, m_date, baseline_type=b_type, custom_label=b_label)
            except Exception:
                pass

        # Cover image URL: either cover_media_id, first photo, or first media
        cover_url = None
        cover_media = None
        if m.cover_media_id:
            cover_media = db.query(MomentMedia).filter(MomentMedia.id == m.cover_media_id).first()
        if not cover_media:
            cover_media = next((item for item in m.media_items if item.media_type == "PHOTO"), None)
            if not cover_media:
                cover_media = next(iter(m.media_items), None)

        if cover_media:
            cover_url = f"/api/moments/media/{cover_media.id}/thumbnail"
        else:
            # Fallback to day's photo
            day_photo = db.query(Photo).filter(Photo.photo_date == m.moment_date, Photo.status == "ACTIVE").first()
            if day_photo:
                cover_url = day_photo.thumbnail_url

        results.append({
            "id": m.id,
            "moment_date": m.moment_date,
            "folder_name": m.folder_name,
            "title": m.title or f"{m.moment_date} 特别时刻",
            "description": m.description,
            "photo_count": m.photo_count,
            "video_count": m.video_count,
            "total_media": m.photo_count + m.video_count,
            "cover_url": cover_url,
            "age_display": age_info.get("display") if age_info else None
        })

    return results

@router.get("/{moment_date_or_id}")
def get_moment_detail(moment_date_or_id: str, db: Session = Depends(get_db)):
    """
    Returns a moment's details and full media item list by moment_date ('YYYY-MM-DD') or moment ID.
    """
    if moment_date_or_id.isdigit() and len(moment_date_or_id) < 6:
        moment = db.query(Moment).filter(Moment.id == int(moment_date_or_id)).first()
    else:
        moment = db.query(Moment).filter(Moment.moment_date == moment_date_or_id).first()

    if not moment:
        raise HTTPException(status_code=404, detail="Special moment not found.")

    baseline_date, b_type, b_label = get_baseline_info(db)
    age_info = None
    if baseline_date and b_type != "NONE":
        try:
            m_date = date.fromisoformat(moment.moment_date)
            age_info = calculate_timeline_milestone(baseline_date, m_date, baseline_type=b_type, custom_label=b_label)
        except Exception:
            pass

    # Query main archive photo of this day if available
    day_photo = db.query(Photo).filter(Photo.photo_date == moment.moment_date, Photo.status == "ACTIVE").first()
    day_photo_info = None
    if day_photo:
        day_photo_info = {
            "id": day_photo.id,
            "thumbnail_url": day_photo.thumbnail_url,
            "preview_url": day_photo.preview_url,
            "description": day_photo.description
        }

    media_list = []
    for item in moment.media_items:
        media_list.append({
            "id": item.id,
            "media_type": item.media_type,
            "filename": item.filename,
            "file_size": item.file_size,
            "thumbnail_url": f"/api/moments/media/{item.id}/thumbnail",
            "preview_url": f"/api/moments/media/{item.id}/preview" if item.media_type == "PHOTO" else None,
            "stream_url": f"/api/moments/media/{item.id}/stream" if item.media_type == "VIDEO" else None,
            "original_url": f"/api/moments/media/{item.id}/original",
            "sort_order": item.sort_order
        })

    return {
        "id": moment.id,
        "moment_date": moment.moment_date,
        "folder_name": moment.folder_name,
        "title": moment.title or f"{moment.moment_date} 特别时刻",
        "description": moment.description,
        "cover_media_id": moment.cover_media_id,
        "photo_count": moment.photo_count,
        "video_count": moment.video_count,
        "total_media": moment.photo_count + moment.video_count,
        "age_at_moment": age_info,
        "day_photo": day_photo_info,
        "media_items": media_list
    }

class UpdateMomentRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_media_id: Optional[int] = None

@router.put("/{moment_date_or_id}")
def update_moment(moment_date_or_id: str, payload: UpdateMomentRequest, db: Session = Depends(get_db)):
    """
    Updates the title, description/story, or cover media of a moment.
    """
    if moment_date_or_id.isdigit() and len(moment_date_or_id) < 6:
        moment = db.query(Moment).filter(Moment.id == int(moment_date_or_id)).first()
    else:
        moment = db.query(Moment).filter(Moment.moment_date == moment_date_or_id).first()

    if not moment:
        raise HTTPException(status_code=404, detail="Special moment not found.")

    if payload.title is not None:
        moment.title = payload.title.strip() or f"{moment.moment_date} 特别时刻"
    if payload.description is not None:
        moment.description = payload.description.strip() or None
    if payload.cover_media_id is not None:
        media = db.query(MomentMedia).filter(
            MomentMedia.id == payload.cover_media_id,
            MomentMedia.moment_id == moment.id
        ).first()
        if media:
            moment.cover_media_id = media.id

    moment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(moment)

    return {
        "id": moment.id,
        "moment_date": moment.moment_date,
        "title": moment.title,
        "description": moment.description,
        "cover_media_id": moment.cover_media_id,
        "message": "时刻信息更新成功"
    }

@router.get("/media/{media_id}/thumbnail")
def get_media_thumbnail(media_id: int, db: Session = Depends(get_db)):
    media = db.query(MomentMedia).filter(MomentMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media item not found.")

    photo_root = resolve_media_root(media, db)
    thumb_path = get_moment_media_thumbnail(media, photo_root)
    return FileResponse(thumb_path, media_type="image/webp")

@router.get("/media/{media_id}/preview")
def get_media_preview(media_id: int, db: Session = Depends(get_db)):
    media = db.query(MomentMedia).filter(MomentMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media item not found.")
    if media.media_type != "PHOTO":
        raise HTTPException(status_code=400, detail="Preview only available for photos.")

    photo_root = resolve_media_root(media, db)
    prev_path = get_moment_media_preview(media, photo_root)
    return FileResponse(prev_path, media_type="image/webp")

@router.get("/media/{media_id}/original")
def get_media_original(media_id: int, db: Session = Depends(get_db)):
    media = db.query(MomentMedia).filter(MomentMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media item not found.")

    photo_root = resolve_media_root(media, db)
    orig_path = resolve_safe_path(photo_root, media.relative_path)
    if not orig_path.exists():
        raise HTTPException(status_code=404, detail="Original file not found on disk.")

    mime_type, _ = mimetypes.guess_type(orig_path.name)
    return FileResponse(orig_path, media_type=mime_type or "application/octet-stream")

@router.get("/media/{media_id}/stream")
def stream_video(media_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Video streaming endpoint supporting HTTP 206 Partial Content (Range requests)
    for seamless seeking in browsers and mobile devices.
    """
    media = db.query(MomentMedia).filter(MomentMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media item not found.")
    if media.media_type != "VIDEO":
        raise HTTPException(status_code=400, detail="Streaming is only supported for video files.")

    photo_root = resolve_media_root(media, db)
    video_path = resolve_safe_path(photo_root, media.relative_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk.")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    mime_type, _ = mimetypes.guess_type(video_path.name)
    content_type = mime_type or "video/mp4"

    if not range_header:
        # Full content response
        return FileResponse(video_path, media_type=content_type)

    # Parse range header: e.g. "bytes=0-1048575" or "bytes=5000-"
    try:
        byte_range = range_header.strip().replace("bytes=", "")
        parts = byte_range.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        chunk_size = (end - start) + 1
    except Exception:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    def iterfile():
        with open(video_path, "rb") as f:
            f.seek(start)
            bytes_left = chunk_size
            while bytes_left > 0:
                read_len = min(65536, bytes_left)
                data = f.read(read_len)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": content_type
    }

    return StreamingResponse(iterfile(), status_code=206, headers=headers)
