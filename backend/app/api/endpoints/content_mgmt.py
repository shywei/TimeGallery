from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.services.content_mgmt_service import ContentManagementService

router = APIRouter(prefix="/mgmt/content", tags=["Content Management"])


@router.get("/day/{date_str}")
def get_day_status(date_str: str, db: Session = Depends(get_db)):
    """Get the current daily photo and moment status for a specific date."""
    service = ContentManagementService(db)
    return service.get_day_status(date_str)


@router.post("/daily-photo")
async def upload_daily_photo(
    date_str: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload or replace the daily main photo for a specific date."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    service = ContentManagementService(db)
    photo = service.save_daily_photo(date_str, content, file.filename)
    return {
        "success": True,
        "message": f"{date_str} 每日主图已成功归档并生成缩略图",
        "photo": {
            "id": photo.id,
            "photo_date": photo.photo_date,
            "filename": photo.filename,
            "file_size": photo.file_size,
            "width": photo.width,
            "height": photo.height,
            "thumbnail_url": photo.thumbnail_url,
            "preview_url": photo.preview_url
        }
    }


@router.delete("/daily-photo/{date_str}")
def delete_daily_photo(date_str: str, db: Session = Depends(get_db)):
    """Delete the daily main photo for a specific date, safely moving it to trash."""
    service = ContentManagementService(db)
    return service.delete_daily_photo(date_str)


@router.post("/moment-media")
async def upload_moment_media(
    date_str: str = Form(...),
    files: List[UploadFile] = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload photos and/or videos to a special moment for a specific date."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    file_tuples = []
    for f in files:
        if f.filename:
            content = await f.read()
            if len(content) > 0:
                file_tuples.append((f.filename, content))

    if not file_tuples:
        raise HTTPException(status_code=400, detail="All uploaded files are empty.")

    service = ContentManagementService(db)
    moment = service.upload_moment_media(date_str, file_tuples, title, description)
    return {
        "success": True,
        "message": f"成功向 {date_str} 特别时刻添加了 {len(file_tuples)} 个媒体文件",
        "moment_id": moment.id,
        "photo_count": moment.photo_count,
        "video_count": moment.video_count
    }


@router.delete("/moment-media/{media_id}")
def delete_moment_media(media_id: int, db: Session = Depends(get_db)):
    """Delete a single media file from a special moment, safely moving it to trash."""
    service = ContentManagementService(db)
    return service.delete_moment_media(media_id)


@router.delete("/moment/{date_str}")
def delete_moment(date_str: str, db: Session = Depends(get_db)):
    """Delete an entire special moment for a date, safely moving folder to trash."""
    service = ContentManagementService(db)
    return service.delete_moment(date_str)


@router.get("/trash/stats")
def get_trash_stats(db: Session = Depends(get_db)):
    """Get total files and size currently stored in the .trash directory."""
    service = ContentManagementService(db)
    return service.get_trash_stats()


@router.post("/trash/empty")
def empty_trash(db: Session = Depends(get_db)):
    """Empty the .trash directory contents permanently."""
    service = ContentManagementService(db)
    return service.empty_trash()
