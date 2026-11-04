from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.tag import Tag
from backend.app.services.age_service import calculate_age

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("")
def get_timeline(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    birth_setting = db.query(SystemSetting).filter(SystemSetting.key == "birth_date").first()
    birth_date = None
    if birth_setting and birth_setting.value:
        try:
            birth_date = date.fromisoformat(birth_setting.value)
        except Exception:
            pass

    query = db.query(Photo).filter(Photo.status == "ACTIVE")
    if tag:
        query = query.filter(Photo.tags.any(Tag.name == tag.strip()))

    total = query.count()

    if sort == "asc":
        query = query.order_by(Photo.photo_date.asc())
    else:
        query = query.order_by(Photo.photo_date.desc())

    offset = (page - 1) * page_size
    photos = query.offset(offset).limit(page_size).all()

    # Group photos by Year-Month
    groups: Dict[str, List[Dict[str, Any]]] = {}

    for p in photos:
        ym = p.photo_date[:7]  # e.g. "2024-11"
        if ym not in groups:
            groups[ym] = []

        age_info = None
        if birth_date:
            try:
                p_date = date.fromisoformat(p.photo_date)
                age_info = calculate_age(birth_date, p_date)
            except Exception:
                pass

        groups[ym].append({
            "id": p.id,
            "photo_date": p.photo_date,
            "filename": p.filename,
            "width": p.width,
            "height": p.height,
            "is_highlight": p.is_highlight,
            "description": p.description,
            "thumbnail_url": p.thumbnail_url,
            "preview_url": p.preview_url,
            "age": age_info
        })

    group_list = [
        {"period": ym, "photos": items}
        for ym, items in groups.items()
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": (offset + len(photos)) < total,
        "groups": group_list
    }
