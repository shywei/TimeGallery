import json
import threading
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.time_utils import get_beijing_now_iso
from backend.app.db.database import get_db, SessionLocal
from backend.app.models.scan_job import ScanJob
from backend.app.models.scan_issue import ScanIssue
from backend.app.schemas.scanner import (
    ScanJobResponse,
    ScanIssueResponse,
    StartScanResponse,
    MissingDatesSummary
)
from backend.app.services.photo_scanner import PhotoScanner, calculate_missing_archive_dates

router = APIRouter(prefix="/scanner", tags=["Scanner"])

def run_async_scan(job_id: int, scan_type: str):
    db = SessionLocal()
    try:
        scanner = PhotoScanner(db)
        scanner.run_scan(scan_type=scan_type, job_id=job_id)
    except Exception as e:
        try:
            db.rollback()
            job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
            if job and job.status == "RUNNING":
                job.status = "FAILED"
                job.message = f"Scan failed: {str(e)}"
                job.finished_at = get_beijing_now_iso()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()

@router.post("/full-scan", response_model=StartScanResponse)
def trigger_full_scan(db: Session = Depends(get_db)):
    # Check if a scan is already running
    running = db.query(ScanJob).filter(ScanJob.status == "RUNNING").first()
    if running:
        return StartScanResponse(
            job_id=running.id,
            status="RUNNING",
            message="A scan job is already currently running."
        )

    job = ScanJob(scan_type="FULL_SCAN", status="PENDING")
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch in background thread
    t = threading.Thread(target=run_async_scan, args=(job.id, "FULL_SCAN"), daemon=True)
    t.start()

    return StartScanResponse(
        job_id=job.id,
        status="PENDING",
        message="Full scan task initiated."
    )

@router.post("/incremental-scan", response_model=StartScanResponse)
def trigger_incremental_scan(db: Session = Depends(get_db)):
    running = db.query(ScanJob).filter(ScanJob.status == "RUNNING").first()
    if running:
        return StartScanResponse(
            job_id=running.id,
            status="RUNNING",
            message="A scan job is already currently running."
        )

    job = ScanJob(scan_type="INCREMENTAL_SCAN", status="PENDING")
    db.add(job)
    db.commit()
    db.refresh(job)

    t = threading.Thread(target=run_async_scan, args=(job.id, "INCREMENTAL_SCAN"), daemon=True)
    t.start()

    return StartScanResponse(
        job_id=job.id,
        status="PENDING",
        message="Incremental scan task initiated."
    )

def _format_job_response(job: ScanJob) -> ScanJobResponse:
    missing_info = None
    if job.missing_dates_json:
        try:
            missing_info = json.loads(job.missing_dates_json)
        except Exception:
            missing_info = None

    return ScanJobResponse(
        id=job.id,
        status=job.status,
        scan_type=job.scan_type,
        started_at=job.started_at,
        finished_at=job.finished_at,
        total_files=job.total_files,
        processed_files=job.processed_files,
        success_count=job.success_count,
        error_count=job.error_count,
        conflict_count=job.conflict_count,
        message=job.message,
        missing_info=missing_info
    )

@router.get("/missing-dates", response_model=MissingDatesSummary)
def get_missing_dates_summary(db: Session = Depends(get_db)):
    """Calculate and return missing dates between earliest and latest photos in the archive."""
    return calculate_missing_archive_dates(db)

@router.get("/jobs", response_model=List[ScanJobResponse])
def list_scan_jobs(limit: int = 20, db: Session = Depends(get_db)):
    jobs = db.query(ScanJob).order_by(ScanJob.id.desc()).limit(limit).all()
    return [_format_job_response(j) for j in jobs]

@router.get("/jobs/{job_id}", response_model=ScanJobResponse)
def get_scan_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found.")
    return _format_job_response(job)

@router.get("/issues", response_model=List[ScanIssueResponse])
def list_scan_issues(
    status_filter: Optional[str] = Query(None, alias="status"),
    job_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(ScanIssue)
    if status_filter:
        query = query.filter(ScanIssue.status == status_filter)
    if job_id:
        query = query.filter(ScanIssue.scan_job_id == job_id)
    return query.order_by(ScanIssue.id.desc()).limit(limit).all()

@router.get("/issues/{issue_id}", response_model=ScanIssueResponse)
def get_scan_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(ScanIssue).filter(ScanIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Scan issue not found.")
    return issue

@router.post("/issues/{issue_id}/resolve", response_model=ScanIssueResponse)
def resolve_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(ScanIssue).filter(ScanIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Scan issue not found.")
    issue.status = "RESOLVED"
    issue.resolved_at = get_beijing_now_iso()
    db.commit()
    db.refresh(issue)
    return issue

@router.post("/issues/{issue_id}/ignore", response_model=ScanIssueResponse)
def ignore_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(ScanIssue).filter(ScanIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Scan issue not found.")
    issue.status = "IGNORED"
    issue.resolved_at = get_beijing_now_iso()
    db.commit()
    db.refresh(issue)
    return issue
