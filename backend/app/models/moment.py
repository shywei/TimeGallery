from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

class Moment(Base):
    """
    Represents a special moment / event on a specific date (e.g. 2024-11-03 from folder '241103').
    """
    __tablename__ = "moments"

    id = Column(Integer, primary_key=True, index=True)
    moment_date = Column(String(10), unique=True, index=True, nullable=False)  # 'YYYY-MM-DD'
    folder_name = Column(String(50), nullable=False)  # 'yymmdd' e.g. '241103'
    folder_rel_path = Column(String(500), nullable=False)  # relative to photo_root
    title = Column(String(200), nullable=True)  # optional custom title, defaults to date
    description = Column(Text, nullable=True)  # optional story for this moment
    cover_media_id = Column(Integer, nullable=True)  # ID of cover media
    photo_count = Column(Integer, default=0, nullable=False)
    video_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    media_items = relationship("MomentMedia", back_populates="moment", cascade="all, delete-orphan", order_by="MomentMedia.sort_order.asc(), MomentMedia.filename.asc()")


class MomentMedia(Base):
    """
    Represents a single media item (photo or video) inside a moment's folder.
    """
    __tablename__ = "moment_media"

    id = Column(Integer, primary_key=True, index=True)
    moment_id = Column(Integer, ForeignKey("moments.id", ondelete="CASCADE"), index=True, nullable=False)
    media_type = Column(String(10), nullable=False)  # 'PHOTO' or 'VIDEO'
    filename = Column(String(255), nullable=False)
    relative_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    file_mtime = Column(Integer, default=0, nullable=False)
    file_hash = Column(String(64), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds, if available
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    moment = relationship("Moment", back_populates="media_items")
