from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.photo import Photo
from backend.app.models.tag import Tag
from backend.app.schemas.photo import PhotoListItem, PhotoDetailResponse, PhotoMetadataUpdateRequest
from backend.app.api.endpoints.photos import get_photo_detail

router = APIRouter(prefix="/highlights", tags=["Highlights"])

@router.get("", response_model=List[PhotoListItem])
def list_highlights(
    tag: Optional[str] = None,
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    query = db.query(Photo).filter(
        Photo.status == "ACTIVE",
        Photo.is_highlight == 1
    )

    if tag:
        query = query.filter(Photo.tags.any(Tag.name == tag.strip()))

    if sort == "asc":
        query = query.order_by(Photo.photo_date.asc())
    else:
        query = query.order_by(Photo.photo_date.desc())

    photos = query.all()

    return [
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

@router.post("/{photo_id}", response_model=PhotoDetailResponse)
def set_highlight(photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    photo.is_highlight = 1
    db.commit()
    return get_photo_detail(photo_id, db)

@router.delete("/{photo_id}", response_model=PhotoDetailResponse)
def remove_highlight(photo_id: int, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    photo.is_highlight = 0
    db.commit()
    return get_photo_detail(photo_id, db)

@router.put("/{photo_id}/metadata", response_model=PhotoDetailResponse)
def update_highlight_metadata(
    photo_id: int,
    payload: PhotoMetadataUpdateRequest,
    db: Session = Depends(get_db)
):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")

    if payload.description is not None:
        photo.description = payload.description.strip() or None

    if payload.tags is not None:
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
    return get_photo_detail(photo_id, db)
