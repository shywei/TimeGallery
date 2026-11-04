from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.photo import Photo
from backend.app.models.collection import Collection, CollectionPhoto
from backend.app.schemas.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
    CollectionListItem,
    CollectionDetailResponse,
    AddPhotosToCollectionRequest,
    ReorderPhotosRequest
)

router = APIRouter(prefix="/collections", tags=["Collections"])

@router.get("", response_model=List[CollectionListItem])
def list_collections(db: Session = Depends(get_db)):
    collections = db.query(Collection).order_by(Collection.sort_order.asc(), Collection.id.desc()).all()

    result = []
    for c in collections:
        count = db.query(CollectionPhoto).filter(CollectionPhoto.collection_id == c.id).count()
        cover_p = db.query(Photo).filter(Photo.id == c.cover_photo_id).first() if c.cover_photo_id else None
        cover_thumb = cover_p.thumbnail_url if cover_p else None

        result.append(CollectionListItem(
            id=c.id,
            name=c.name,
            description=c.description,
            cover_photo_id=c.cover_photo_id,
            cover_thumbnail_url=cover_thumb,
            photo_count=count,
            sort_order=c.sort_order,
            created_at=c.created_at
        ))
    return result

@router.post("", response_model=CollectionListItem)
def create_collection(payload: CollectionCreateRequest, db: Session = Depends(get_db)):
    col = Collection(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        cover_photo_id=payload.cover_photo_id,
        sort_order=payload.sort_order
    )
    db.add(col)
    db.commit()
    db.refresh(col)

    cover_p = db.query(Photo).filter(Photo.id == col.cover_photo_id).first() if col.cover_photo_id else None
    cover_thumb = cover_p.thumbnail_url if cover_p else None
    return CollectionListItem(
        id=col.id,
        name=col.name,
        description=col.description,
        cover_photo_id=col.cover_photo_id,
        cover_thumbnail_url=cover_thumb,
        photo_count=0,
        sort_order=col.sort_order,
        created_at=col.created_at
    )

@router.get("/{collection_id}", response_model=CollectionDetailResponse)
def get_collection(collection_id: int, db: Session = Depends(get_db)):
    col = db.query(Collection).filter(Collection.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")

    links = db.query(CollectionPhoto).filter(
        CollectionPhoto.collection_id == col.id
    ).order_by(CollectionPhoto.sort_order.asc(), CollectionPhoto.created_at.asc()).all()

    photos = []
    for link in links:
        p = db.query(Photo).filter(Photo.id == link.photo_id, Photo.status == "ACTIVE").first()
        if p:
            photos.append({
                "id": p.id,
                "photo_date": p.photo_date,
                "filename": p.filename,
                "width": p.width,
                "height": p.height,
                "is_highlight": p.is_highlight,
                "description": p.description,
                "thumbnail_url": p.thumbnail_url,
                "preview_url": p.preview_url,
                "sort_order": link.sort_order
            })

    cover_p = db.query(Photo).filter(Photo.id == col.cover_photo_id).first() if col.cover_photo_id else None
    cover_thumb = cover_p.thumbnail_url if cover_p else None

    return CollectionDetailResponse(
        id=col.id,
        name=col.name,
        description=col.description,
        cover_photo_id=col.cover_photo_id,
        cover_thumbnail_url=cover_thumb,
        sort_order=col.sort_order,
        created_at=col.created_at,
        photos=photos
    )

@router.put("/{collection_id}", response_model=CollectionDetailResponse)
def update_collection(
    collection_id: int,
    payload: CollectionUpdateRequest,
    db: Session = Depends(get_db)
):
    col = db.query(Collection).filter(Collection.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")

    if payload.name is not None:
        col.name = payload.name.strip()
    if payload.description is not None:
        col.description = payload.description.strip() or None
    if payload.cover_photo_id is not None:
        col.cover_photo_id = payload.cover_photo_id
    if payload.sort_order is not None:
        col.sort_order = payload.sort_order

    db.commit()
    return get_collection(collection_id, db)

@router.delete("/{collection_id}")
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    col = db.query(Collection).filter(Collection.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")

    db.delete(col)
    db.commit()
    return {"message": "Collection deleted successfully."}

@router.post("/{collection_id}/photos")
def add_photos_to_collection(
    collection_id: int,
    payload: AddPhotosToCollectionRequest,
    db: Session = Depends(get_db)
):
    col = db.query(Collection).filter(Collection.id == collection_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")

    for photo_id in payload.photo_ids:
        exists = db.query(CollectionPhoto).filter(
            CollectionPhoto.collection_id == col.id,
            CollectionPhoto.photo_id == photo_id
        ).first()
        if not exists:
            max_order = db.query(CollectionPhoto).filter(
                CollectionPhoto.collection_id == col.id
            ).count()
            link = CollectionPhoto(
                collection_id=col.id,
                photo_id=photo_id,
                sort_order=max_order + 1
            )
            db.add(link)

    # Set cover photo if not yet chosen
    if not col.cover_photo_id and payload.photo_ids:
        col.cover_photo_id = payload.photo_ids[0]

    db.commit()
    return get_collection(collection_id, db)

@router.delete("/{collection_id}/photos/{photo_id}")
def remove_photo_from_collection(
    collection_id: int,
    photo_id: int,
    db: Session = Depends(get_db)
):
    link = db.query(CollectionPhoto).filter(
        CollectionPhoto.collection_id == collection_id,
        CollectionPhoto.photo_id == photo_id
    ).first()
    if link:
        db.delete(link)
        db.commit()

    return {"message": "Photo removed from collection."}

@router.put("/{collection_id}/photos/order")
def reorder_photos(
    collection_id: int,
    payload: ReorderPhotosRequest,
    db: Session = Depends(get_db)
):
    for idx, photo_id in enumerate(payload.photo_ids):
        link = db.query(CollectionPhoto).filter(
            CollectionPhoto.collection_id == collection_id,
            CollectionPhoto.photo_id == photo_id
        ).first()
        if link:
            link.sort_order = idx

    db.commit()
    return get_collection(collection_id, db)
