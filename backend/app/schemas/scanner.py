from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class MissingRange(BaseModel):
    start: str
    end: str
    count: int

class MissingDatesSummary(BaseModel):
    range_start: Optional[str] = None
    range_end: Optional[str] = None
    total_days: int = 0
    recorded_days: int = 0
    missing_count: int = 0
    missing_dates: List[str] = []
    missing_ranges: List[MissingRange] = []

class ScanIssueResponse(BaseModel):
    id: int
    scan_job_id: int
    issue_type: str
    filename: str
    relative_path: str
    parsed_date: Optional[str] = None
    existing_photo_id: Optional[int] = None
    details: Optional[str] = None
    status: str
    created_at: str
    resolved_at: Optional[str] = None

class ScanJobResponse(BaseModel):
    id: int
    status: str
    scan_type: str
    started_at: str
    finished_at: Optional[str] = None
    total_files: int
    processed_files: int
    success_count: int
    error_count: int
    conflict_count: int
    message: Optional[str] = None
    missing_info: Optional[MissingDatesSummary] = None

class StartScanResponse(BaseModel):
    job_id: int
    status: str
    message: str
