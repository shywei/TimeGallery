import hashlib
import json
import logging
import re
from datetime import date, timedelta
from backend.app.core.time_utils import get_beijing_today, get_beijing_now_iso
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image

from sqlalchemy.orm import Session
from backend.app.db.database import SessionLocal
from backend.app.core.config import settings
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.scan_job import ScanJob
from backend.app.models.scan_issue import ScanIssue
from backend.app.models.memory import MemoryDailySet
from backend.app.services.filename_parser import (
    parse_filename_date,
    is_supported_image,
    validate_date_range,
    SUPPORTED_EXTENSIONS
)
from backend.app.core.exceptions import (
    InvalidFilenameError,
    InvalidDateError,
    DateOutOfRangeError
)

logger = logging.getLogger("scanner")

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_image_info(filepath: Path) -> Dict[str, Any]:
    """Read image dimensions, format and mime type using Pillow safely."""
    with Image.open(filepath) as img:
        width, height = img.size
        img_format = img.format or "JPEG"
        mime_type = Image.MIME.get(img_format, "image/jpeg")
        return {
            "width": width,
            "height": height,
            "mime_type": mime_type,
            "format": img_format
        }

def calculate_missing_archive_dates(db: Session) -> Dict[str, Any]:
    """
    Find gaps in photo archive between earliest photo date and latest photo date.
    Per user requirement: only dates strictly before/between the latest photo date are checked.
    Dates after the latest photo (e.g. latest is 10/20, today is 11/4) are NOT included.
    """
    photos = db.query(Photo.photo_date).filter(
        Photo.status == "ACTIVE"
    ).order_by(Photo.photo_date.asc()).all()

    if not photos or len(photos) < 2:
        start_d = photos[0][0] if photos else None
        return {
            "range_start": start_d,
            "range_end": start_d,
            "total_days": len(photos),
            "recorded_days": len(photos),
            "missing_count": 0,
            "missing_dates": [],
            "missing_ranges": []
        }

    dates = [p[0] for p in photos]
    min_d = date.fromisoformat(dates[0])
    max_d = date.fromisoformat(dates[-1])
    date_set = set(dates)

    curr = min_d
    missing_dates = []
    while curr <= max_d:
        iso = curr.isoformat()
        if iso not in date_set:
            missing_dates.append(iso)
        curr += timedelta(days=1)

    # Group into consecutive ranges for clean display
    missing_ranges = []
    if missing_dates:
        start_range = date.fromisoformat(missing_dates[0])
        end_range = start_range
        for d_str in missing_dates[1:]:
            d = date.fromisoformat(d_str)
            if d == end_range + timedelta(days=1):
                end_range = d
            else:
                missing_ranges.append({
                    "start": start_range.isoformat(),
                    "end": end_range.isoformat(),
                    "count": (end_range - start_range).days + 1
                })
                start_range = d
                end_range = d
        missing_ranges.append({
            "start": start_range.isoformat(),
            "end": end_range.isoformat(),
            "count": (end_range - start_range).days + 1
        })

    total_days = (max_d - min_d).days + 1

    return {
        "range_start": min_d.isoformat(),
        "range_end": max_d.isoformat(),
        "total_days": total_days,
        "recorded_days": len(date_set),
        "missing_count": len(missing_dates),
        "missing_dates": missing_dates,
        "missing_ranges": missing_ranges
    }

class PhotoScanner:
    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str, default: str = "") -> str:
        s = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
        return s.value if s else default

    def run_scan(self, scan_type: str = "FULL_SCAN", job_id: Optional[int] = None) -> ScanJob:
        # Create or fetch scan job
        if job_id:
            job = self.db.query(ScanJob).filter(ScanJob.id == job_id).first()
        else:
            job = ScanJob(scan_type=scan_type, status="RUNNING")
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)

        job.status = "RUNNING"
        self.db.commit()

        photo_root_str = self.get_setting("photo_root", settings.photo_root)
        birth_date_str = self.get_setting("birth_date", settings.birth_date)

        if not photo_root_str:
            job.status = "FAILED"
            job.message = "Photo root directory is not configured."
            job.finished_at = get_beijing_now_iso()
            self.db.commit()
            return job

        photo_root = Path(photo_root_str).resolve()
        if not photo_root.exists() or not photo_root.is_dir():
            job.status = "FAILED"
            job.message = f"Photo root directory '{photo_root}' does not exist or is not a directory."
            job.finished_at = get_beijing_now_iso()
            self.db.commit()
            return job

        birth_date = None
        if birth_date_str:
            try:
                birth_date = date.fromisoformat(birth_date_str)
            except ValueError:
                logger.warning(f"Invalid configured birth_date: {birth_date_str}")

        today = get_beijing_today()

        try:
            # In FULL_SCAN: purge all cached image files, daily memory sets, and prior scan issues to rebuild completely
            if scan_type == "FULL_SCAN":
                from backend.app.services.image_service import purge_image_caches
                logger.info("FULL_SCAN: Purging thumbnail and preview image caches from disk...")
                purge_image_caches()
                self.db.query(ScanIssue).delete()
                self.db.query(MemoryDailySet).delete()
                self.db.commit()

            # 1. Discover all candidate files in photo_root (excluding files inside 'yymmdd' moment subdirectories)
            candidate_files = []
            for path in photo_root.rglob("*"):
                if path.is_file():
                    try:
                        rel = path.relative_to(photo_root)
                        if any(re.fullmatch(r"\d{6}", part) for part in rel.parts[:-1]):
                            continue
                    except ValueError:
                        pass
                    candidate_files.append(path)

            job.total_files = len(candidate_files)
            job.processed_files = 0
            job.success_count = 0
            job.error_count = 0
            job.conflict_count = 0
            self.db.commit()

            active_scanned_ids = set()

            for file_path in candidate_files:
                try:
                    rel_path = file_path.relative_to(photo_root).as_posix()
                except ValueError:
                    rel_path = file_path.name

                filename = file_path.name
                job.processed_files += 1

                # Check extension
                ext = file_path.suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    # If file stem is 6 digits but extension is unsupported
                    stem = file_path.stem
                    if stem.isdigit() and len(stem) == 6:
                        self._create_issue(
                            job.id, "UNSUPPORTED_FORMAT", filename, rel_path,
                            details=f"Unsupported image format: {ext}"
                        )
                        job.error_count += 1
                    continue

                # Filename validation & date parsing
                try:
                    parsed_photo_date = parse_filename_date(filename)
                except InvalidFilenameError:
                    self._create_issue(
                        job.id, "INVALID_FILENAME", filename, rel_path,
                        details="Filename stem must be strictly 6 digits 'yymmdd'."
                    )
                    job.error_count += 1
                    continue
                except InvalidDateError as e:
                    self._create_issue(
                        job.id, "INVALID_DATE", filename, rel_path,
                        details=str(e)
                    )
                    job.error_count += 1
                    continue

                date_iso = parsed_photo_date.isoformat()

                # Date range validation
                if birth_date:
                    try:
                        validate_date_range(parsed_photo_date, birth_date, today)
                    except DateOutOfRangeError as e:
                        self._create_issue(
                            job.id, "DATE_OUT_OF_RANGE", filename, rel_path,
                            parsed_date=date_iso,
                            details=str(e)
                        )
                        job.error_count += 1
                        continue

                # Read image dimensions and verify readability
                try:
                    img_info = get_image_info(file_path)
                    file_size = file_path.stat().st_size
                    sha256 = calculate_sha256(file_path)
                except Exception as e:
                    self._create_issue(
                        job.id, "FILE_UNREADABLE", filename, rel_path,
                        parsed_date=date_iso,
                        details=f"Failed to read image or calculate hash: {str(e)}"
                    )
                    job.error_count += 1
                    continue

                # Check SHA256 duplicate content for informational issue
                dup_photo = self.db.query(Photo).filter(
                    Photo.sha256 == sha256,
                    Photo.relative_path != rel_path
                ).first()
                if dup_photo:
                    self._create_issue(
                        job.id, "DUPLICATE_CONTENT", filename, rel_path,
                        parsed_date=date_iso,
                        existing_photo_id=dup_photo.id,
                        details=f"File content is identical to photo ID {dup_photo.id} ({dup_photo.relative_path})."
                    )

                # Check Date Uniqueness / Conflict
                existing_date_photo = self.db.query(Photo).filter(
                    Photo.photo_date == date_iso
                ).first()

                now_iso = get_beijing_now_iso()

                if existing_date_photo:
                    if existing_date_photo.relative_path == rel_path:
                        # Same file already indexed: update scan timestamp and status
                        existing_date_photo.status = "ACTIVE"
                        existing_date_photo.last_scanned_at = now_iso
                        existing_date_photo.file_size = file_size
                        existing_date_photo.sha256 = sha256
                        existing_date_photo.width = img_info["width"]
                        existing_date_photo.height = img_info["height"]
                        existing_date_photo.mime_type = img_info["mime_type"]
                        active_scanned_ids.add(existing_date_photo.id)
                        job.success_count += 1
                    elif not (photo_root / existing_date_photo.relative_path).exists():
                        # Old file no longer exists: User replaced or renamed the photo file for this date!
                        # Update record to new path and attributes while preserving user metadata (description, highlight, tags)
                        existing_date_photo.relative_path = rel_path
                        existing_date_photo.filename = filename
                        existing_date_photo.extension = ext
                        existing_date_photo.status = "ACTIVE"
                        existing_date_photo.last_scanned_at = now_iso
                        existing_date_photo.file_size = file_size
                        existing_date_photo.sha256 = sha256
                        existing_date_photo.width = img_info["width"]
                        existing_date_photo.height = img_info["height"]
                        existing_date_photo.mime_type = img_info["mime_type"]
                        active_scanned_ids.add(existing_date_photo.id)
                        job.success_count += 1
                    else:
                        # CONFLICT: A different file has the exact same date and both files exist on disk!
                        # Rule: NEVER overwrite existing photo. Record DATE_CONFLICT issue.
                        self._create_issue(
                            job.id, "DATE_CONFLICT", filename, rel_path,
                            parsed_date=date_iso,
                            existing_photo_id=existing_date_photo.id,
                            details=f"Conflict with existing photo ID {existing_date_photo.id} ({existing_date_photo.relative_path}) for date {date_iso}."
                        )
                        job.conflict_count += 1
                else:
                    # Check if relative_path already exists (e.g., date changed or previous issue)
                    existing_path_photo = self.db.query(Photo).filter(
                        Photo.relative_path == rel_path
                    ).first()

                    if existing_path_photo:
                        # Update date if moved/renamed within date
                        existing_path_photo.photo_date = date_iso
                        existing_path_photo.filename = filename
                        existing_path_photo.status = "ACTIVE"
                        existing_path_photo.last_scanned_at = now_iso
                        active_scanned_ids.add(existing_path_photo.id)
                        job.success_count += 1
                    else:
                        # Insert new active photo archive
                        new_photo = Photo(
                            photo_date=date_iso,
                            filename=filename,
                            relative_path=rel_path,
                            extension=ext,
                            file_size=file_size,
                            sha256=sha256,
                            width=img_info["width"],
                            height=img_info["height"],
                            mime_type=img_info["mime_type"],
                            status="ACTIVE",
                            imported_at=now_iso,
                            last_scanned_at=now_iso,
                            created_at=now_iso,
                            updated_at=now_iso
                        )
                        self.db.add(new_photo)
                        self.db.flush()
                        active_scanned_ids.add(new_photo.id)
                        job.success_count += 1

                # Commit every 50 files for responsiveness
                if job.processed_files % 50 == 0:
                    self.db.commit()

            # 2. Check Missing Files: active photos in DB whose original files disappeared
            all_active = self.db.query(Photo).filter(Photo.status == "ACTIVE").all()
            for photo in all_active:
                if photo.id not in active_scanned_ids:
                    target_file = photo_root / photo.relative_path
                    if not target_file.exists():
                        photo.status = "MISSING"
                        self._create_issue(
                            job.id, "FILE_MISSING", photo.filename, photo.relative_path,
                            parsed_date=photo.photo_date,
                            existing_photo_id=photo.id,
                            details="Original photo file is missing on disk."
                        )
                        job.error_count += 1

            self.db.commit()

            # 3. Archive Completeness Check (Missing Dates between earliest and latest photos)
            missing_info = calculate_missing_archive_dates(self.db)
            job.missing_dates_json = json.dumps(missing_info)

            job.status = "COMPLETED"
            job.finished_at = get_beijing_now_iso()

            if job.scan_type == "FULL_SCAN":
                if missing_info["missing_count"] > 0:
                    cnt = missing_info["missing_count"]
                    sample_dates = "、".join(missing_info["missing_dates"][:5])
                    if cnt > 5:
                        sample_dates += f" 等共 {cnt} 天"
                    job.message = (
                        f"全量扫描完成。处理 {job.processed_files} 个文件，成功归档 {job.success_count} 张。"
                        f"在归档区间（{missing_info['range_start']} 至 {missing_info['range_end']}）内检测到缺少 {cnt} 天的照片数据（{sample_dates}）。"
                    )
                else:
                    r_msg = f"（{missing_info['range_start']} 至 {missing_info['range_end']}）" if missing_info["range_start"] else ""
                    job.message = f"全量扫描完成。处理 {job.processed_files} 个文件，成功归档 {job.success_count} 张。归档区间{r_msg}内照片完整连续，无缺失日期。"
            else:
                job.message = f"增量扫描完成。处理 {job.processed_files} 个文件，成功归档 {job.success_count} 张。"

            # 4. Scan Special Moments ('yymmdd' folders)
            try:
                from backend.app.services.moment_service import MomentScanner
                m_scanner = MomentScanner(self.db)
                m_result = m_scanner.scan_moments(photo_root)
                logger.info(f"Moment scan completed: {m_result}")
            except Exception as e:
                logger.warning(f"Moment scan failed: {e}")
                try:
                    self.db.rollback()
                except Exception:
                    pass

            # Refresh today's memories so changes in archive are immediately visible on homepage
            today_iso = get_beijing_today().isoformat()
            self.db.query(MemoryDailySet).filter(MemoryDailySet.memory_date == today_iso).delete()

            self.db.commit()

        except Exception as e:
            logger.exception("Scan job encountered fatal error")
            try:
                self.db.rollback()
            except Exception:
                pass
            job.status = "FAILED"
            job.message = f"Scan failed: {str(e)}"
            job.finished_at = get_beijing_now_iso()
            try:
                self.db.commit()
            except Exception:
                pass

        return job

    def _create_issue(
        self,
        job_id: int,
        issue_type: str,
        filename: str,
        relative_path: str,
        parsed_date: Optional[str] = None,
        existing_photo_id: Optional[int] = None,
        details: Optional[str] = None
    ) -> ScanIssue:
        issue = ScanIssue(
            scan_job_id=job_id,
            issue_type=issue_type,
            filename=filename,
            relative_path=relative_path,
            parsed_date=parsed_date,
            existing_photo_id=existing_photo_id,
            details=details,
            status="OPEN"
        )
        self.db.add(issue)
        return issue
