from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from backend.app.core.time_utils import get_beijing_now_iso

photo_tags = Table(
    "photo_tags",
    Base.metadata,
    Column("photo_id", Integer, ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", String(32), default=get_beijing_now_iso, nullable=False)
)

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )

    photos = relationship("Photo", secondary=photo_tags, back_populates="tags")
