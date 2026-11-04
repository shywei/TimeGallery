from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from backend.app.core.time_utils import get_beijing_now_iso

class ScanIssue(Base):
    __tablename__ = "scan_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False)
    # Types: INVALID_FILENAME, INVALID_DATE, DATE_OUT_OF_RANGE, DATE_CONFLICT,
    #        UNSUPPORTED_FORMAT, FILE_MISSING, FILE_UNREADABLE, DUPLICATE_CONTENT
    issue_type = Column(String(64), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    relative_path = Column(String(1024), nullable=False)
    parsed_date = Column(String(10), nullable=True)
    existing_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)
    details = Column(String(2000), nullable=True)
    # Status: OPEN / RESOLVED / IGNORED
    status = Column(String(32), default="OPEN", nullable=False, index=True)
    created_at = Column(
        String(32),
        default=get_beijing_now_iso,
        nullable=False
    )
    resolved_at = Column(String(32), nullable=True)

    scan_job = relationship("ScanJob", back_populates="issues")
    existing_photo = relationship("Photo", foreign_keys=[existing_photo_id])
