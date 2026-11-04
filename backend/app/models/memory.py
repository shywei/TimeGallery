from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from backend.app.core.time_utils import get_beijing_now_iso

class MemoryDailySet(Base):
    __tablename__ = "memory_daily_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_date = Column(String(10), nullable=False, index=True)
    # Type: ON_THIS_DAY / ONE_YEAR_AGO / RANDOM_MEMORY
    memory_type = Column(String(32), nullable=False, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )

    photo = relationship("Photo")

    __table_args__ = (
        UniqueConstraint("memory_date", "memory_type", "photo_id", name="uq_memory_daily_item"),
    )
