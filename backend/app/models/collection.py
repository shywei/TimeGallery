from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from backend.app.core.time_utils import get_beijing_now_iso

class CollectionPhoto(Base):
    __tablename__ = "collection_photos"

    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )

class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(String(1000), nullable=True)
    cover_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
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

    photos = relationship("Photo", secondary="collection_photos", back_populates="collections")
    cover_photo = relationship("Photo", foreign_keys=[cover_photo_id])
