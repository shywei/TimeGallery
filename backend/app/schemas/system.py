from typing import Optional
from pydantic import BaseModel, Field

class SystemStatusResponse(BaseModel):
    app_name: str
    app_version: str
    status: str = "healthy"
    first_setup_completed: bool
    photo_count: int = 0
    days_recorded: int = 0
    photo_root_configured: bool = False

class SystemConfigResponse(BaseModel):
    app_name: str
    birth_date: Optional[str] = None
    photo_root: Optional[str] = None
    data_root: str
    thumbnail_size: int
    preview_size: int
    first_setup_completed: bool

class SetupRequest(BaseModel):
    birth_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    photo_root: str = Field(..., min_length=1)

class SystemConfigUpdateRequest(BaseModel):
    birth_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    photo_root: Optional[str] = None
    thumbnail_size: Optional[int] = Field(None, ge=120, le=1080)
    preview_size: Optional[int] = Field(None, ge=800, le=4096)
