from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class TagResponse(BaseModel):
    id: int
    name: str

class OnThisDayPhotoItem(BaseModel):
    id: int
    photo_date: str
    year: int
    diff_years: int
    title: str
    thumbnail_url: str
    preview_url: str
    age_display: Optional[str] = None

class PhotoListItem(BaseModel):
    id: int
    photo_date: str
    filename: str
    relative_path: str
    width: int
    height: int
    status: str
    is_highlight: int
    description: Optional[str] = None
    thumbnail_url: str
    preview_url: str

class PhotoDetailResponse(BaseModel):
    id: int
    photo_date: str
    filename: str
    relative_path: str
    width: int
    height: int
    file_size: int
    mime_type: str
    status: str
    is_highlight: int
    description: Optional[str] = None
    imported_at: str
    last_scanned_at: str
    thumbnail_url: str
    preview_url: str
    original_url: str
    age_at_photo: Optional[Dict[str, Any]] = None
    tags: List[TagResponse] = []
    collections: List[Dict[str, Any]] = []
    on_this_day_photos: List[OnThisDayPhotoItem] = []
    prev_photo_id: Optional[int] = None
    next_photo_id: Optional[int] = None
    prev_date: Optional[str] = None
    next_date: Optional[str] = None

class PhotoMetadataUpdateRequest(BaseModel):
    description: Optional[str] = None
    is_highlight: Optional[bool] = None
    tags: Optional[List[str]] = None

class PhotoListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PhotoListItem]
