import json
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.time_utils import get_beijing_now, get_beijing_now_iso, BEIJING_TZ
from datetime import datetime
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.tag import Tag
from backend.app.models.collection import Collection, CollectionPhoto

BACKUP_DIR = settings.data_dir / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def create_sqlite_backup() -> Dict[str, Any]:
    """
    Creates an atomic, consistent SQLite snapshot using SQLite's online backup API.
    Uses Beijing Time for timestamps.
    """
    db_file = settings.data_dir / "growing_up.db"
    if not db_file.exists():
        raise FileNotFoundError("Database file does not exist.")

    now_bj = get_beijing_now()
    timestamp = now_bj.strftime("%Y%m%d_%H%M%S")
    backup_filename = f"growing_up_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_filename

    # Perform online snapshot
    src_conn = sqlite3.connect(str(db_file))
    dest_conn = sqlite3.connect(str(backup_path))
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()

    file_size = backup_path.stat().st_size
    return {
        "filename": backup_filename,
        "path": str(backup_path),
        "size_bytes": file_size,
        "created_at": get_beijing_now_iso()
    }

def list_backups() -> List[Dict[str, Any]]:
    """Lists all available database backup files formatted with Beijing Time."""
    backups = []
    for f in sorted(BACKUP_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True):
        bj_time = datetime.fromtimestamp(f.stat().st_mtime, BEIJING_TZ)
        backups.append({
            "filename": f.name,
            "size_bytes": f.stat().st_size,
            "created_at": bj_time.isoformat()
        })
    return backups

def export_metadata_json(db: Session) -> Dict[str, Any]:
    """
    Exports clean JSON package containing all metadata:
    system settings, photos, tags, highlights, and collections.
    """
    settings_records = db.query(SystemSetting).all()
    settings_dict = {s.key: s.value for s in settings_records}

    photos = db.query(Photo).all()
    photos_data = []
    for p in photos:
        photos_data.append({
            "photo_date": p.photo_date,
            "filename": p.filename,
            "relative_path": p.relative_path,
            "sha256": p.sha256,
            "status": p.status,
            "is_highlight": p.is_highlight,
            "description": p.description,
            "tags": [t.name for t in p.tags]
        })

    collections = db.query(Collection).all()
    collections_data = []
    for c in collections:
        items = db.query(CollectionPhoto).filter(CollectionPhoto.collection_id == c.id).all()
        collections_data.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "sort_order": c.sort_order,
            "photo_ids": [item.photo_id for item in items]
        })

    return {
        "export_version": "2.0",
        "exported_at": get_beijing_now_iso(),
        "timezone": "Asia/Shanghai (UTC+8)",
        "settings": settings_dict,
        "photos": photos_data,
        "collections": collections_data
    }

def restore_sqlite_backup(backup_filename: str) -> Dict[str, Any]:
    """
    Restores SQLite database from a specified backup file.
    """
    backup_path = (BACKUP_DIR / backup_filename).resolve()
    if not backup_path.exists() or not backup_path.is_file():
        raise FileNotFoundError(f"Backup file '{backup_filename}' not found.")

    conn = sqlite3.connect(str(backup_path))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        if not res or res[0] != "ok":
            raise ValueError(f"Integrity check failed: {res}")
    finally:
        conn.close()

    db_file = settings.data_dir / "growing_up.db"

    # Create safety snapshot before overwriting
    create_sqlite_backup()

    # Restore by copying
    shutil.copy2(backup_path, db_file)

    return {
        "message": f"Successfully restored database from {backup_filename}",
        "restored_at": get_beijing_now_iso()
    }
