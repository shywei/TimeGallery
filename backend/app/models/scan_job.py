from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from backend.app.core.time_utils import get_beijing_now_iso

class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Status: PENDING / RUNNING / COMPLETED / FAILED / CANCELLED
    status = Column(String(32), default="PENDING", nullable=False)
    # Type: FULL_SCAN / INCREMENTAL_SCAN / STARTUP_SCAN
    scan_type = Column(String(32), nullable=False)
    started_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )
    finished_at = Column(String(32), nullable=True)
    total_files = Column(Integer, default=0, nullable=False)
    processed_files = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    conflict_count = Column(Integer, default=0, nullable=False)
    message = Column(String(1000), nullable=True)
    missing_dates_json = Column(String, nullable=True)

    issues = relationship("ScanIssue", back_populates="scan_job", cascade="all, delete-orphan")
