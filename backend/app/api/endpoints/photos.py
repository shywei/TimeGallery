from datetime import date
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.core.config import settings
from backend.app.core.paths import resolve_safe_path
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.tag import Tag
from backend.app.models.collection import Collection, CollectionPhoto
from backend.app.schemas.photo import (
    PhotoListResponse,
    PhotoListItem,
    PhotoDetailResponse,
    PhotoMetadataUpdateRequest,
    TagResponse,
    OnThisDayPhotoItem
)
from backend.app.services.image_service import (
    get_or_create_thumbnail,
    get_or_create_preview
)
from backend.app.services.age_service import calculate_age

router = APIRouter(prefix="/photos", tags=["Photos"])

def get_photo_root(db: Session) -> Path:
    s = db.query(SystemSetting).filter(SystemSetting.key == "photo_root").first()
    root_str = s.value if s else settings.photo_root
    if not root_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo root directory is not configured in settings."
        )
    p = Path(root_str).resolve()
    if not p.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo root directory '{root_str}' does not exist on disk."
        )
    return p

@router.get("", response_model=PhotoListResponse)
def list_photos(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    year: Optional[int] = Query(None, ge=2000, le=2099),
    month: Optional[int] = Query(None, ge=1, le=12),
    is_highlight: Optional[bool] = None,
    tag_id: Optional[int] = None,
    collection_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=200),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    query = db.query(Photo).filter(Photo.status == "ACTIVE")

    if start_date:
        query = query.filter(Photo.photo_date >= start_date)
    if end_date:
        query = query.filter(Photo.photo_date <= end_date)

    if year is not None:
        if month is not None:
            prefix = f"{year}-{month:02d}"
            query = query.filter(Photo.photo_date.startswith(prefix))
        else:
            prefix = f"{year}-"
            query = query.filter(Photo.photo_date.startswith(prefix))

    if is_highlight is not None:
        query = query.filter(Photo.is_highlight == (1 if is_highlight else 0))

    if tag_id is not None:
        query = query.filter(Photo.tags.any(Tag.id == tag_id))

    if collection_id is not None:
        query = query.join(CollectionPhoto).filter(CollectionPhoto.collection_id == collection_id)

    total = query.count()

    if sort == "asc":
        query = query.order_by(Photo.photo_date.asc())
    else:
        query = query.order_by(Photo.photo_date.desc())

    offset = (page - 1) * page_size
    photos = query.offset(offset).limit(page_size).all()

    items = [
        PhotoListItem(
            id=p.id,
            photo_date=p.photo_date,
            filename=p.filename,
            relative_path=p.relative_path,
            width=p.width,
            height=p.height,
            status=p.status,
            is_highlight=p.is_highlight,
            description=p.description,
            thumbnail_url=p.thumbnail_url,
            preview_url=p.preview_url
        )
        for p in photos
    ]

    return PhotoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )

@router.get("/{photo_id}", response_model=PhotoDetailResponse)
def get_photo_detail(photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    # Calculate child's age on photo date
    age_info = None
    b_date = None
    birth_setting = db.query(SystemSetting).filter(SystemSetting.key == "birth_date").first()
    if birth_setting and birth_setting.value:
        try:
            b_date = date.fromisoformat(birth_setting.value)
            p_date = date.fromisoformat(photo.photo_date)
            age_info = calculate_age(b_date, p_date)
        except Exception:
            pass

    # Find On This Day photos (same month-day in other historical years)
    target_md = photo.photo_date[4:]  # "-MM-DD"
    current_year = int(photo.photo_date[:4])
    other_year_photos = db.query(Photo).filter(
        Photo.photo_date.endswith(target_md),
        Photo.id != photo.id,
        Photo.status == "ACTIVE"
    ).order_by(Photo.photo_date.desc()).all()

    on_this_day_items = []
    for op in other_year_photos:
        op_year = int(op.photo_date[:4])
        diff = current_year - op_year
        if diff > 0:
            title = f"{diff} 年前的今天"
        elif diff < 0:
            title = f"{abs(diff)} 年后的今天"
        else:
            title = f"{op_year} 年的今天"

        op_age_display = None
        if b_date:
            try:
                op_d = date.fromisoformat(op.photo_date)
                op_age = calculate_age(b_date, op_d)
                op_age_display = op_age.get("display")
            except Exception:
                pass

        on_this_day_items.append(
            OnThisDayPhotoItem(
                id=op.id,
                photo_date=op.photo_date,
                year=op_year,
                diff_years=diff,
                title=title,
                thumbnail_url=op.thumbnail_url,
                preview_url=op.preview_url,
                age_display=op_age_display
            )
        )

    # Find adjacent photos by date (chronologically previous and next)
    prev_photo = db.query(Photo).filter(
        Photo.status == "ACTIVE",
        or_(
            Photo.photo_date < photo.photo_date,
            and_(Photo.photo_date == photo.photo_date, Photo.id < photo.id)
        )
    ).order_by(Photo.photo_date.desc(), Photo.id.desc()).first()

    next_photo = db.query(Photo).filter(
        Photo.status == "ACTIVE",
        or_(
            Photo.photo_date > photo.photo_date,
            and_(Photo.photo_date == photo.photo_date, Photo.id > photo.id)
        )
    ).order_by(Photo.photo_date.asc(), Photo.id.asc()).first()

    return PhotoDetailResponse(
        id=photo.id,
        photo_date=photo.photo_date,
        filename=photo.filename,
        relative_path=photo.relative_path,
        width=photo.width,
        height=photo.height,
        file_size=photo.file_size,
        mime_type=photo.mime_type,
        status=photo.status,
        is_highlight=photo.is_highlight,
        description=photo.description,
        imported_at=photo.imported_at,
        last_scanned_at=photo.last_scanned_at,
        thumbnail_url=photo.thumbnail_url,
        preview_url=photo.preview_url,
        original_url=photo.original_url,
        age_at_photo=age_info,
        tags=[TagResponse(id=t.id, name=t.name) for t in photo.tags],
        collections=[{"id": c.id, "name": c.name} for c in photo.collections],
        on_this_day_photos=on_this_day_items,
        prev_photo_id=prev_photo.id if prev_photo else None,
        next_photo_id=next_photo.id if next_photo else None,
        prev_date=prev_photo.photo_date if prev_photo else None,
        next_date=next_photo.photo_date if next_photo else None
    )

@router.get("/{photo_id}/thumbnail")
def get_photo_thumbnail(
    photo_id: int,
    v: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    etag = f'"{photo.sha256}"'
    if request and request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    photo_root = get_photo_root(db)
    try:
        thumb_path = get_or_create_thumbnail(photo, photo_root)
        cache_control = "public, max-age=31536000, immutable" if v else "no-cache, must-revalidate"
        return FileResponse(
            thumb_path,
            media_type="image/webp",
            headers={"Cache-Control": cache_control, "ETag": etag}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load thumbnail: {str(e)}")

@router.get("/{photo_id}/preview")
def get_photo_preview(
    photo_id: int,
    v: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    etag = f'"{photo.sha256}"'
    if request and request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    photo_root = get_photo_root(db)
    try:
        prev_path = get_or_create_preview(photo, photo_root)
        cache_control = "public, max-age=31536000, immutable" if v else "no-cache, must-revalidate"
        return FileResponse(
            prev_path,
            media_type="image/webp",
            headers={"Cache-Control": cache_control, "ETag": etag}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load preview: {str(e)}")

@router.get("/{photo_id}/original")
def get_photo_original(photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    photo_root = get_photo_root(db)
    try:
        orig_path = resolve_safe_path(photo_root, photo.relative_path)
        if not orig_path.exists():
            raise HTTPException(status_code=404, detail="Original photo file is missing on disk.")
        return FileResponse(orig_path, media_type=photo.mime_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot access original photo: {str(e)}")

@router.put("/{photo_id}/metadata", response_model=PhotoDetailResponse)
def update_photo_metadata(
    photo_id: int,
    payload: PhotoMetadataUpdateRequest,
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    if payload.description is not None:
        photo.description = payload.description.strip() or None

    if payload.is_highlight is not None:
        photo.is_highlight = 1 if payload.is_highlight else 0

    if payload.tags is not None:
        # Re-associate tags
        new_tags = []
        for tag_name in payload.tags:
            tag_name_clean = tag_name.strip()
            if not tag_name_clean:
                continue
            tag = db.query(Tag).filter(Tag.name == tag_name_clean).first()
            if not tag:
                tag = Tag(name=tag_name_clean)
                db.add(tag)
                db.flush()
            new_tags.append(tag)
        photo.tags = new_tags

    db.commit()
    db.refresh(photo)
    return get_photo_detail(photo_id=photo_id, db=db)
