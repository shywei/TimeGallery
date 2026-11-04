from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.tag import Tag
from backend.app.models.photo import Photo

router = APIRouter(prefix="/tags", tags=["Tags"])

@router.get("", response_model=List[Dict[str, Any]])
def list_tags(db: Session = Depends(get_db)):
    """
    Returns all existing tags with the count of active photos associated with each tag.
    """
    tags = db.query(Tag).order_by(Tag.name.asc()).all()
    results = []
    for t in tags:
        count = db.query(Photo).filter(
            Photo.status == "ACTIVE",
            Photo.tags.any(Tag.id == t.id)
        ).count()
        if count > 0:
            results.append({
                "id": t.id,
                "name": t.name,
                "count": count
            })
    return results
