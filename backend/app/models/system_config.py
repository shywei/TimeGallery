from sqlalchemy import Column, String
from backend.app.db.base import Base
from backend.app.core.time_utils import get_beijing_now_iso

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(64), primary_key=True)
    value = Column(String(512), nullable=False)
    updated_at = Column(
        String(32),
        default=get_beijing_now_iso,
        onupdate=get_beijing_now_iso,
        nullable=False
    )
