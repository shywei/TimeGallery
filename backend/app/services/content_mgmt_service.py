import os
import re
import shutil
import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.core.paths import resolve_safe_path
from backend.app.core.time_utils import get_beijing_now_iso
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.collection import CollectionPhoto
from backend.app.models.moment import Moment, MomentMedia
from backend.app.services.image_service import (
    THUMBNAIL_DIR,
    PREVIEW_DIR,
    get_or_create_thumbnail,
    get_or_create_preview
)
from backend.app.services.moment_service import (
    MOMENT_PHOTO_EXTS,
    MOMENT_VIDEO_EXTS,
    MOMENT_THUMBNAIL_DIR,
    MOMENT_PREVIEW_DIR,
    get_moment_media_thumbnail
)
from backend.app.services.photo_scanner import calculate_sha256, get_image_info
from backend.app.services.storage_service import (
    get_configured_photo_roots,
    get_primary_photo_root
)

DATE_ISO_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def format_bytes(size: int) -> str:
    """Format bytes to human readable string."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"


def validate_date_str(date_str: str) -> date:
    """Validate YYYY-MM-DD date string format and value."""
    if not DATE_ISO_REGEX.match(date_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"日期格式无效: '{date_str}', 必须为 YYYY-MM-DD 格式 (例如 2024-11-03)"
        )
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的自然日历日期: '{date_str}'"
        )


def iso_to_yymmdd(d: date) -> str:
    """Format date to 6-digit YYMMDD string."""
    return f"{d.year % 100:02d}{d.month:02d}{d.day:02d}"


def move_to_trash(photo_root: Path, src_path: Path, category: str, date_prefix: str) -> Path:
    """
    Safely move file or directory to photo_root/.trash/{category}/ with a timestamp suffix.
    Guarantees no name collision on multiple deletions of the same day's media.
    """
    if category == "moment_media":
        trash_dir = photo_root / ".trash" / category / date_prefix
    else:
        trash_dir = photo_root / ".trash" / category
    trash_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = src_path.stem
    ext = src_path.suffix

    if src_path.is_file():
        target_name = f"{stem}_{timestamp_str}{ext}"
        target_path = trash_dir / target_name
        counter = 1
        while target_path.exists():
            target_path = trash_dir / f"{stem}_{timestamp_str}_{counter}{ext}"
            counter += 1
        shutil.move(str(src_path), str(target_path))
        return target_path
    elif src_path.is_dir():
        target_name = f"{src_path.name}_{timestamp_str}"
        target_path = trash_dir / target_name
        counter = 1
        while target_path.exists():
            target_path = trash_dir / f"{src_path.name}_{timestamp_str}_{counter}"
            counter += 1
        shutil.move(str(src_path), str(target_path))
        return target_path
    return src_path


class ContentManagementService:
    def __init__(self, db: Session):
        self.db = db

    def get_photo_roots(self) -> List[Path]:
        """Resolve all configured photo roots."""
        roots = get_configured_photo_roots(self.db)
        valid = [r for r in roots if r.exists() and r.is_dir()]
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未配置任何有效的本地相册目录。"
            )
        return valid

    def get_primary_photo_root(self) -> Path:
        """Resolve the primary photo root."""
        return get_primary_photo_root(self.db)

    def get_photo_root(self) -> Path:
        """Backward-compatible helper returning primary root."""
        return self.get_primary_photo_root()

    def get_trash_stats(self) -> Dict[str, Any]:
        """Get total files and size currently stored across all .trash directories."""
        roots = self.get_photo_roots()
        file_count = 0
        total_size = 0

        for r in roots:
            trash_dir = r / ".trash"
            if trash_dir.exists():
                for root, _, files in os.walk(trash_dir):
                    for f in files:
                        fp = Path(root) / f
                        try:
                            total_size += fp.stat().st_size
                            file_count += 1
                        except Exception:
                            pass

        return {
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_display": format_bytes(total_size)
        }

    def empty_trash(self) -> Dict[str, Any]:
        """Empty all .trash directories permanently across all roots."""
        stats = self.get_trash_stats()
        roots = self.get_photo_roots()

        for r in roots:
            trash_dir = r / ".trash"
            if trash_dir.exists():
                for item in trash_dir.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except Exception:
                        pass

        return {
            "freed_bytes": stats["total_size_bytes"],
            "deleted_count": stats["file_count"],
            "freed_display": stats["total_size_display"]
        }

    def get_day_status(self, date_str: str) -> Dict[str, Any]:
        """
        Get complete status of a specific day across all configured roots:
        - Daily main photo (Photo table & disk files)
        - Special moment (Moment table, disk directory, and media list)
        """
        date_obj = validate_date_str(date_str)
        yymmdd = iso_to_yymmdd(date_obj)
        roots = self.get_photo_roots()
        primary_root = self.get_primary_photo_root()

        # 1. Daily main photo
        photo_record = self.db.query(Photo).filter(
            Photo.photo_date == date_str,
            Photo.status == "ACTIVE"
        ).first()

        # Search for disk files across all roots
        all_disk_main_files: List[Tuple[Path, Path]] = []  # (file_path, root)
        for r in roots:
            for f in r.glob(f"{yymmdd}.*"):
                if f.is_file() and not f.name.startswith("."):
                    all_disk_main_files.append((f, r))

        daily_photo_info = None
        if photo_record:
            p_root = Path(photo_record.root_path) if photo_record.root_path else primary_root
            daily_photo_info = {
                "id": photo_record.id,
                "photo_date": photo_record.photo_date,
                "filename": photo_record.filename,
                "relative_path": photo_record.relative_path,
                "root_path": str(p_root),
                "file_size": photo_record.file_size,
                "file_size_display": format_bytes(photo_record.file_size),
                "width": photo_record.width,
                "height": photo_record.height,
                "mime_type": photo_record.mime_type,
                "thumbnail_url": photo_record.thumbnail_url,
                "preview_url": photo_record.preview_url,
                "description": photo_record.description,
                "is_highlight": photo_record.is_highlight,
                "tags": [t.name for t in photo_record.tags]
            }
        elif all_disk_main_files:
            f, r = all_disk_main_files[0]
            daily_photo_info = {
                "id": None,
                "photo_date": date_str,
                "filename": f.name,
                "relative_path": f.name,
                "root_path": str(r),
                "file_size": f.stat().st_size,
                "file_size_display": format_bytes(f.stat().st_size),
                "width": None,
                "height": None,
                "mime_type": "image/jpeg",
                "thumbnail_url": None,
                "preview_url": None,
                "description": None,
                "is_highlight": 0,
                "tags": [],
                "unindexed": True
            }

        # 2. Special Moment
        moment_record = self.db.query(Moment).filter(
            Moment.moment_date == date_str
        ).first()

        # Check existing moment folder across roots
        existing_moment_dirs: List[Tuple[Path, Path]] = []
        for r in roots:
            md = r / yymmdd
            if md.exists() and md.is_dir():
                existing_moment_dirs.append((md, r))

        moment_info = None
        if moment_record:
            m_root = Path(moment_record.root_path) if moment_record.root_path else primary_root
            media_items = []
            for m in moment_record.media_items:
                media_items.append({
                    "id": m.id,
                    "media_type": m.media_type,
                    "filename": m.filename,
                    "relative_path": m.relative_path,
                    "root_path": str(Path(m.root_path) if m.root_path else m_root),
                    "file_size": m.file_size,
                    "file_size_display": format_bytes(m.file_size),
                    "thumbnail_url": f"/api/moments/media/{m.id}/thumbnail",
                    "preview_url": f"/api/moments/media/{m.id}/preview" if m.media_type == "PHOTO" else f"/api/moments/media/{m.id}/raw",
                    "raw_url": f"/api/moments/media/{m.id}/raw",
                    "is_cover": m.id == moment_record.cover_media_id
                })

            cover_thumb = f"/api/moments/media/{moment_record.cover_media_id}/thumbnail" if moment_record.cover_media_id else (
                media_items[0]["thumbnail_url"] if media_items else None
            )

            moment_info = {
                "id": moment_record.id,
                "moment_date": moment_record.moment_date,
                "folder_name": moment_record.folder_name,
                "root_path": str(m_root),
                "title": moment_record.title,
                "description": moment_record.description,
                "cover_media_id": moment_record.cover_media_id,
                "cover_thumbnail_url": cover_thumb,
                "photo_count": len([m for m in media_items if m["media_type"] == "PHOTO"]),
                "video_count": len([m for m in media_items if m["media_type"] == "VIDEO"]),
                "media_items": media_items
            }
        elif existing_moment_dirs:
            md, r = existing_moment_dirs[0]
            moment_info = {
                "id": None,
                "moment_date": date_str,
                "folder_name": yymmdd,
                "root_path": str(r),
                "title": None,
                "description": None,
                "cover_media_id": None,
                "cover_thumbnail_url": None,
                "photo_count": 0,
                "video_count": 0,
                "media_items": [],
                "unindexed": True
            }

        return {
            "date": date_str,
            "yymmdd": yymmdd,
            "has_daily_photo": daily_photo_info is not None,
            "daily_photo": daily_photo_info,
            "has_moment": moment_info is not None,
            "moment": moment_info,
            "available_roots": [str(r) for r in roots],
            "primary_root": str(primary_root)
        }

    def save_daily_photo(
        self,
        date_str: str,
        file_bytes: bytes,
        original_filename: str,
        target_root_str: Optional[str] = None
    ) -> Photo:
        """
        Upload or replace the daily main photo for a specific date:
        1. Moves any existing file on disk for that day into .trash/daily/ with timestamp.
        2. Saves new file directly as target_root/{yymmdd}.ext.
        3. Updates/creates Photo DB record, preserving description, tags, highlights.
        4. Regenerates thumbnail and preview cache immediately.
        """
        date_obj = validate_date_str(date_str)
        yymmdd = iso_to_yymmdd(date_obj)
        roots = self.get_photo_roots()
        primary_root = self.get_primary_photo_root()

        # Determine target root
        target_root = primary_root
        if target_root_str and target_root_str.strip():
            candidate = Path(target_root_str.strip()).resolve()
            if candidate in roots:
                target_root = candidate

        # If existing record has a specific root, default to that root unless explicitly specified
        existing_photo = self.db.query(Photo).filter(Photo.photo_date == date_str).first()
        if existing_photo and not target_root_str and existing_photo.root_path:
            p_cand = Path(existing_photo.root_path).resolve()
            if p_cand in roots:
                target_root = p_cand

        ext = Path(original_filename).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"

        target_filename = f"{yymmdd}{ext}"
        target_path = target_root / target_filename
        target_root_str_saved = str(target_root.resolve())

        # 1. If any file for this day already exists on disk across all roots, move to respective trash
        for r in roots:
            for ef in r.glob(f"{yymmdd}.*"):
                if ef.is_file() and not ef.name.startswith("."):
                    move_to_trash(r, ef, "daily", yymmdd)

        # 2. Write new file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(file_bytes)

        # 3. Read image info & calculate SHA256
        sha256 = calculate_sha256(target_path)
        img_info = get_image_info(target_path)
        now_iso = get_beijing_now_iso()

        # 4. Update or create Photo record in DB
        photo = existing_photo
        if photo:
            # Invalidate old cache files
            for old_t in THUMBNAIL_DIR.glob(f"{photo.id}_*.webp"):
                old_t.unlink(missing_ok=True)
            for old_p in PREVIEW_DIR.glob(f"{photo.id}_*.webp"):
                old_p.unlink(missing_ok=True)

            photo.filename = target_filename
            photo.relative_path = target_filename
            photo.root_path = target_root_str_saved
            photo.extension = ext
            photo.file_size = len(file_bytes)
            photo.sha256 = sha256
            photo.width = img_info["width"]
            photo.height = img_info["height"]
            photo.mime_type = img_info["mime_type"]
            photo.status = "ACTIVE"
            photo.last_scanned_at = now_iso
        else:
            photo = Photo(
                photo_date=date_str,
                filename=target_filename,
                relative_path=target_filename,
                root_path=target_root_str_saved,
                extension=ext,
                file_size=len(file_bytes),
                sha256=sha256,
                width=img_info["width"],
                height=img_info["height"],
                mime_type=img_info["mime_type"],
                status="ACTIVE",
                imported_at=now_iso,
                last_scanned_at=now_iso
            )
            self.db.add(photo)

        self.db.commit()
        self.db.refresh(photo)

        # 5. Pre-warm thumbnail and preview
        try:
            get_or_create_thumbnail(photo, target_root)
            get_or_create_preview(photo, target_root)
        except Exception:
            pass

        return photo

    def delete_daily_photo(self, date_str: str) -> Dict[str, Any]:
        """
        Delete the daily main photo for a specific date:
        1. Moves original file(s) across all roots to .trash/daily/ with timestamp.
        2. Clears thumbnail and preview caches.
        3. Cleans up collection associations and deletes Photo record.
        """
        date_obj = validate_date_str(date_str)
        yymmdd = iso_to_yymmdd(date_obj)
        roots = self.get_photo_roots()

        # 1. Move disk files to trash across roots
        for r in roots:
            for ef in r.glob(f"{yymmdd}.*"):
                if ef.is_file() and not ef.name.startswith("."):
                    move_to_trash(r, ef, "daily", yymmdd)

        # 2. Database cleanup
        photo = self.db.query(Photo).filter(Photo.photo_date == date_str).first()
        if photo:
            for old_t in THUMBNAIL_DIR.glob(f"{photo.id}_*.webp"):
                old_t.unlink(missing_ok=True)
            for old_p in PREVIEW_DIR.glob(f"{photo.id}_*.webp"):
                old_p.unlink(missing_ok=True)

            self.db.query(CollectionPhoto).filter(CollectionPhoto.photo_id == photo.id).delete()
            self.db.delete(photo)
            self.db.commit()

        return {
            "success": True,
            "message": f"每日主图已安全移至回收站（日期：{date_str}）",
            "date": date_str
        }

    def upload_moment_media(
        self,
        date_str: str,
        files: List[Tuple[str, bytes]],
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_root_str: Optional[str] = None
    ) -> Moment:
        """
        Create a special moment folder or append photos/videos to an existing moment folder.
        Saves files into target_root/{yymmdd}/, indexes MomentMedia, generates thumbnails.
        """
        date_obj = validate_date_str(date_str)
        yymmdd = iso_to_yymmdd(date_obj)
        roots = self.get_photo_roots()
        primary_root = self.get_primary_photo_root()

        moment = self.db.query(Moment).filter(Moment.moment_date == date_str).first()

        # Determine target root:
        # If moment exists and already has a root, use it; else if target_root_str provided, use it; else primary
        target_root = primary_root
        if moment and moment.root_path:
            p_cand = Path(moment.root_path).resolve()
            if p_cand in roots:
                target_root = p_cand
        elif target_root_str and target_root_str.strip():
            candidate = Path(target_root_str.strip()).resolve()
            if candidate in roots:
                target_root = candidate

        target_root_str_saved = str(target_root.resolve())
        moment_dir = target_root / yymmdd
        moment_dir.mkdir(parents=True, exist_ok=True)

        now_dt = datetime.now()

        if not moment:
            moment = Moment(
                moment_date=date_str,
                folder_name=yymmdd,
                folder_rel_path=yymmdd,
                root_path=target_root_str_saved,
                title=title.strip() if title and title.strip() else None,
                description=description.strip() if description and description.strip() else None,
                photo_count=0,
                video_count=0,
                created_at=now_dt,
                updated_at=now_dt
            )
            self.db.add(moment)
            self.db.commit()
            self.db.refresh(moment)
        else:
            if title is not None:
                moment.title = title.strip() or None
            if description is not None:
                moment.description = description.strip() or None
            moment.root_path = target_root_str_saved
            moment.updated_at = now_dt
            self.db.commit()

        for original_name, content_bytes in files:
            ext = Path(original_name).suffix.lower()
            media_type = "VIDEO" if ext in MOMENT_VIDEO_EXTS else "PHOTO"

            stem = Path(original_name).stem
            safe_stem = re.sub(r"[^\w\-_.]", "_", stem) or "media"
            safe_filename = f"{safe_stem}{ext}"
            dest_file = moment_dir / safe_filename

            counter = 1
            while dest_file.exists():
                safe_filename = f"{safe_stem}_{counter}{ext}"
                dest_file = moment_dir / safe_filename
                counter += 1

            with open(dest_file, "wb") as f:
                f.write(content_bytes)

            sha256 = calculate_sha256(dest_file)
            media = MomentMedia(
                moment_id=moment.id,
                media_type=media_type,
                filename=safe_filename,
                relative_path=f"{yymmdd}/{safe_filename}",
                root_path=target_root_str_saved,
                file_size=len(content_bytes),
                file_mtime=int(dest_file.stat().st_mtime),
                file_hash=sha256,
                created_at=now_dt
            )
            self.db.add(media)
            self.db.commit()
            self.db.refresh(media)

            # Generate thumbnail
            try:
                get_moment_media_thumbnail(media, target_root)
            except Exception:
                pass

        # Update photo & video counts and set cover
        all_media = self.db.query(MomentMedia).filter(MomentMedia.moment_id == moment.id).all()
        moment.photo_count = len([m for m in all_media if m.media_type == "PHOTO"])
        moment.video_count = len([m for m in all_media if m.media_type == "VIDEO"])

        if not moment.cover_media_id and all_media:
            photos = [m for m in all_media if m.media_type == "PHOTO"]
            moment.cover_media_id = photos[0].id if photos else all_media[0].id

        self.db.commit()
        self.db.refresh(moment)
        return moment

    def delete_moment_media(self, media_id: int) -> Dict[str, Any]:
        """Delete a single media item from a special moment, safely moving it to trash."""
        media = self.db.query(MomentMedia).filter(MomentMedia.id == media_id).first()
        if not media:
            raise HTTPException(status_code=404, detail="Media item not found.")

        moment = self.db.query(Moment).filter(Moment.id == media.moment_id).first()
        roots = self.get_photo_roots()
        media_root = self.get_primary_photo_root()
        if media.root_path:
            p = Path(media.root_path).resolve()
            if p in roots:
                media_root = p
        elif moment and moment.root_path:
            p = Path(moment.root_path).resolve()
            if p in roots:
                media_root = p

        file_path = resolve_safe_path(media_root, media.relative_path)
        if file_path.exists():
            move_to_trash(media_root, file_path, "moment_media", moment.folder_name if moment else "media")

        # Delete thumbnail cache
        for f in MOMENT_THUMBNAIL_DIR.glob(f"{media.id}_*.webp"):
            f.unlink(missing_ok=True)

        if moment and moment.cover_media_id == media.id:
            next_m = self.db.query(MomentMedia).filter(
                MomentMedia.moment_id == moment.id,
                MomentMedia.id != media.id
            ).first()
            moment.cover_media_id = next_m.id if next_m else None

        self.db.delete(media)
        if moment:
            self.db.commit()
            moment.photo_count = self.db.query(MomentMedia).filter(
                MomentMedia.moment_id == moment.id,
                MomentMedia.media_type == "PHOTO"
            ).count()
            moment.video_count = self.db.query(MomentMedia).filter(
                MomentMedia.moment_id == moment.id,
                MomentMedia.media_type == "VIDEO"
            ).count()
            self.db.commit()

        return {
            "success": True,
            "message": "媒体文件已移至回收站并删除",
            "media_id": media_id
        }

    def delete_moment(self, date_str: str) -> Dict[str, Any]:
        """
        Delete an entire special moment for a specific date:
        1. Moves entire photo_root/{yymmdd}/ directory to .trash/moments/{yymmdd}_{ts}/ across all roots.
        2. Unlinks cached thumbnails for all moment media.
        3. Deletes Moment and all MomentMedia records from DB.
        """
        date_obj = validate_date_str(date_str)
        yymmdd = iso_to_yymmdd(date_obj)
        roots = self.get_photo_roots()

        # Check and move from any root that contains this folder
        for r in roots:
            moment_dir = r / yymmdd
            if moment_dir.exists() and moment_dir.is_dir():
                move_to_trash(r, moment_dir, "moments", yymmdd)

        moment = self.db.query(Moment).filter(Moment.moment_date == date_str).first()
        if moment:
            for m in moment.media_items:
                for f in MOMENT_THUMBNAIL_DIR.glob(f"{m.id}_*.webp"):
                    f.unlink(missing_ok=True)
            self.db.delete(moment)
            self.db.commit()

        return {
            "success": True,
            "message": f"特别时刻已安全移至回收站（日期：{date_str}）",
            "date": date_str
        }
