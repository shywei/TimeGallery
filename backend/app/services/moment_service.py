import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.photo import Photo  # noqa
from backend.app.models.tag import Tag, photo_tags  # noqa
from backend.app.models.collection import Collection, CollectionPhoto  # noqa
from backend.app.models.moment import Moment, MomentMedia
from backend.app.models.system_config import SystemSetting
from backend.app.core.paths import resolve_safe_path
from backend.app.services.filename_parser import parse_filename_date
from backend.app.services.image_service import THUMBNAIL_DIR, PREVIEW_DIR, process_and_save_image
from backend.app.core.config import settings
from backend.app.core.time_utils import get_beijing_now_iso

MOMENT_PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
MOMENT_VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}

MOMENT_THUMBNAIL_DIR = settings.data_dir / "moment_thumbs"
MOMENT_PREVIEW_DIR = settings.data_dir / "moment_previews"
MOMENT_THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
MOMENT_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def parse_folder_date(folder_name: str) -> Optional[date]:
    """
    Parses a 6-digit 'yymmdd' folder name into a datetime.date.
    Returns None if folder_name is not 6 digits or not a valid date.
    """
    if not re.fullmatch(r"\d{6}", folder_name):
        return None
    try:
        return parse_filename_date(f"{folder_name}.jpg")
    except Exception:
        return None


def get_moment_media_thumbnail(media: MomentMedia, photo_root: Path) -> Path:
    """
    Returns the path to the cached thumbnail for a MomentMedia item.
    For photos: creates a 480px WebP thumbnail using Pillow.
    For videos: extracts a representative frame using OpenCV and creates a 480px WebP thumbnail.
    """
    dest_path = MOMENT_THUMBNAIL_DIR / f"{media.id}_{media.file_hash[:8] if media.file_hash else 'thumb'}.webp"
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return dest_path

    orig_path = resolve_safe_path(photo_root, media.relative_path)
    if not orig_path.exists():
        return dest_path

    if media.media_type == "PHOTO":
        try:
            process_and_save_image(orig_path, dest_path, settings.thumbnail_size, quality=82)
            return dest_path
        except Exception:
            pass
    elif media.media_type == "VIDEO":
        try:
            import cv2
            cap = cv2.VideoCapture(str(orig_path))
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 1
                target_frame = min(int(fps * 0.5), max(0, int(frame_count - 1)))
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                success, frame = cap.read()
                if not success:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    success, frame = cap.read()
                cap.release()

                if success and frame is not None:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    from PIL import Image
                    img = Image.fromarray(rgb_frame)
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    img.thumbnail((settings.thumbnail_size, settings.thumbnail_size), Image.Resampling.LANCZOS)
                    img.save(dest_path, "WEBP", quality=82)
                    return dest_path
        except Exception:
            pass

    # If video extraction failed or photo processing failed: generate a clean fallback card
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (480, 480), color=(40, 36, 32))
        draw = ImageDraw.Draw(img)
        # Draw a small film / play indicator
        draw.polygon([(210, 190), (210, 290), (300, 240)], fill=(220, 210, 195))
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest_path, "WEBP", quality=80)
        return dest_path
    except Exception:
        return dest_path


def get_moment_media_preview(media: MomentMedia, photo_root: Path) -> Path:
    """
    Returns the path to the cached 1600px preview for a MomentMedia item (photos only).
    """
    dest_path = MOMENT_PREVIEW_DIR / f"{media.id}_{media.file_hash[:8] if media.file_hash else 'prev'}.webp"
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return dest_path

    orig_path = resolve_safe_path(photo_root, media.relative_path)
    process_and_save_image(orig_path, dest_path, settings.preview_size, quality=85)
    return dest_path


class MomentScanner:
    """
    Scans the photo_root for 'yymmdd' subdirectories and indexes them into moments & moment_media.
    """
    def __init__(self, db: Session):
        self.db = db

    def scan_moments(self, photo_roots: Any) -> Dict[str, Any]:
        """
        Discovers all 'yymmdd' directories in one or more photo roots (root-level or subdirectories).
        Syncs moments and moment_media records in the database.
        """
        if isinstance(photo_roots, Path):
            roots = [photo_roots]
        elif isinstance(photo_roots, (list, tuple)):
            roots = [Path(r) for r in photo_roots]
        else:
            roots = [Path(photo_roots)]

        # Find all directories whose name is 6 digits 'yymmdd' across all roots
        candidate_dirs = []
        for root in roots:
            if not root.exists() or not root.is_dir():
                continue
            for path in root.rglob("*"):
                if path.is_dir() and re.fullmatch(r"\d{6}", path.name):
                    candidate_dirs.append((path, root))

        found_moments_count = 0
        total_photos = 0
        total_videos = 0

        active_moment_ids = set()

        for folder_path, root in candidate_dirs:
            parsed_date = parse_folder_date(folder_path.name)
            if not parsed_date:
                continue

            date_iso = parsed_date.isoformat()
            try:
                rel_folder_path = folder_path.relative_to(root).as_posix()
            except ValueError:
                rel_folder_path = folder_path.name

            root_str = str(root.resolve())

            # Find or create Moment record
            moment = self.db.query(Moment).filter(Moment.moment_date == date_iso).first()
            if not moment:
                moment = Moment(
                    moment_date=date_iso,
                    folder_name=folder_path.name,
                    folder_rel_path=rel_folder_path,
                    root_path=root_str,
                    title=f"{date_iso} 特别时刻"
                )
                self.db.add(moment)
                self.db.flush()
            else:
                moment.folder_name = folder_path.name
                moment.folder_rel_path = rel_folder_path
                moment.root_path = root_str
                moment.updated_at = datetime.utcnow()

            active_moment_ids.add(moment.id)

            # Discover media files in this moment folder (supporting arbitrary filenames and subdirectories)
            photo_count = 0
            video_count = 0
            order_idx = 0

            existing_media = {m.relative_path: m for m in moment.media_items}
            seen_rel_paths = set()

            # Find all files inside the moment folder
            raw_files = [p for p in folder_path.rglob("*") if p.is_file()]
            # Natural sort: photos first, then videos; alphabetical within each group
            sorted_files = sorted(
                raw_files,
                key=lambda p: (0 if p.suffix.lower() in MOMENT_PHOTO_EXTS else 1, p.name.lower())
            )

            for file_path in sorted_files:
                ext = file_path.suffix.lower()
                is_photo = ext in MOMENT_PHOTO_EXTS
                is_video = ext in MOMENT_VIDEO_EXTS

                if not is_photo and not is_video:
                    continue

                filename = file_path.name
                media_type = "PHOTO" if is_photo else "VIDEO"

                if is_photo:
                    photo_count += 1
                else:
                    video_count += 1

                try:
                    rel_media_path = file_path.relative_to(root).as_posix()
                except ValueError:
                    rel_media_path = f"{rel_folder_path}/{filename}"

                seen_rel_paths.add(rel_media_path)

                stat = file_path.stat()
                file_size = stat.st_size
                file_mtime = int(stat.st_mtime)

                media_obj = existing_media.get(rel_media_path)
                if not media_obj:
                    # New media item
                    media_obj = MomentMedia(
                        moment_id=moment.id,
                        media_type=media_type,
                        filename=filename,
                        relative_path=rel_media_path,
                        root_path=root_str,
                        file_size=file_size,
                        file_mtime=file_mtime,
                        file_hash=f"{file_size}_{file_mtime}",
                        sort_order=order_idx
                    )
                    self.db.add(media_obj)
                    self.db.flush()
                else:
                    # Update existing media
                    media_obj.filename = filename
                    media_obj.relative_path = rel_media_path
                    media_obj.root_path = root_str
                    media_obj.file_size = file_size
                    media_obj.file_mtime = file_mtime
                    media_obj.file_hash = f"{file_size}_{file_mtime}"
                    media_obj.sort_order = order_idx

                order_idx += 1

            # Delete media items that no longer exist on disk
            for rel_p, m_obj in existing_media.items():
                if rel_p not in seen_rel_paths:
                    self.db.delete(m_obj)

            self.db.flush()

            moment.photo_count = photo_count
            moment.video_count = video_count

            # Determine cover media and pre-extract thumbnail
            cover_candidate = self.db.query(MomentMedia).filter(
                MomentMedia.moment_id == moment.id,
                MomentMedia.media_type == "PHOTO"
            ).order_by(MomentMedia.sort_order.asc()).first()

            if not cover_candidate:
                cover_candidate = self.db.query(MomentMedia).filter(
                    MomentMedia.moment_id == moment.id
                ).order_by(MomentMedia.sort_order.asc()).first()

            if cover_candidate:
                moment.cover_media_id = cover_candidate.id
                try:
                    get_moment_media_thumbnail(cover_candidate, root)
                except Exception as e:
                    pass
            else:
                moment.cover_media_id = None

            total_photos += photo_count
            total_videos += video_count
            found_moments_count += 1

        # Delete moments whose folder was deleted from disk
        if active_moment_ids:
            stale_moments = self.db.query(Moment).filter(~Moment.id.in_(active_moment_ids)).all()
            for sm in stale_moments:
                self.db.delete(sm)
        else:
            self.db.query(Moment).delete()

        self.db.commit()

        return {
            "moments_count": found_moments_count,
            "total_photos": total_photos,
            "total_videos": total_videos
        }
