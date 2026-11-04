from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class CollectionCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    cover_photo_id: Optional[int] = None
    sort_order: int = 0

class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_photo_id: Optional[int] = None
    sort_order: Optional[int] = None

class CollectionListItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cover_photo_id: Optional[int] = None
    cover_thumbnail_url: Optional[str] = None
    photo_count: int
    sort_order: int
    created_at: str

class CollectionDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cover_photo_id: Optional[int] = None
    cover_thumbnail_url: Optional[str] = None
    sort_order: int
    created_at: str
    photos: List[Dict[str, Any]]

class AddPhotosToCollectionRequest(BaseModel):
    photo_ids: List[int]

class ReorderPhotosRequest(BaseModel):
    photo_ids: List[int]
