from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from backend.app.core.time_utils import get_beijing_now_iso

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # The authoritative natural date of the photo, format: YYYY-MM-DD
    photo_date = Column(String(10), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    relative_path = Column(String(1024), unique=True, nullable=False)
    extension = Column(String(16), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    mime_type = Column(String(64), nullable=False)
    
    # Status: ACTIVE / MISSING / ERROR
    status = Column(String(16), default="ACTIVE", nullable=False)
    imported_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )
    last_scanned_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )
    description = Column(String(2000), nullable=True)
    is_highlight = Column(Integer, default=0, nullable=False, index=True)
    created_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )
    updated_at = Column(
        String(32),
        default=get_beijing_now_iso,
        onupdate=get_beijing_now_iso,
        nullable=False
    )

    # Relationships
    tags = relationship("Tag", secondary="photo_tags", back_populates="photos")
    collections = relationship("Collection", secondary="collection_photos", back_populates="photos")

    @property
    def thumbnail_url(self) -> str:
        v = f"?v={self.sha256[:8]}" if self.sha256 else ""
        return f"/api/photos/{self.id}/thumbnail{v}"

    @property
    def preview_url(self) -> str:
        v = f"?v={self.sha256[:8]}" if self.sha256 else ""
        return f"/api/photos/{self.id}/preview{v}"

    @property
    def original_url(self) -> str:
        return f"/api/photos/{self.id}/original"
