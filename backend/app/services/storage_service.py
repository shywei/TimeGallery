import json
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.moment import MomentMedia, Moment

logger = logging.getLogger("gallery.storage")


def get_configured_photo_roots(db: Session) -> List[Path]:
    """
    Returns the list of configured photo roots as resolved Path objects.
    Ensures backward compatibility with single 'photo_root'.
    """
    roots: List[Path] = []

    # 1. Check "photo_roots" (JSON list)
    setting_roots = db.query(SystemSetting).filter(SystemSetting.key == "photo_roots").first()
    if setting_roots and setting_roots.value:
        try:
            paths = json.loads(setting_roots.value)
            if isinstance(paths, list):
                for p_str in paths:
                    if p_str and str(p_str).strip():
                        p = Path(str(p_str).strip()).resolve()
                        if p not in roots:
                            roots.append(p)
        except Exception as e:
            logger.warning(f"Failed to parse 'photo_roots' JSON from database: {e}")

    # 2. Check "photo_root" fallback if photo_roots was empty
    if not roots:
        setting_single = db.query(SystemSetting).filter(SystemSetting.key == "photo_root").first()
        single_str = setting_single.value if setting_single and setting_single.value else settings.photo_root
        if single_str and single_str.strip():
            p = Path(single_str.strip()).resolve()
            if p not in roots:
                roots.append(p)

    return roots


def get_primary_photo_root(db: Session) -> Path:
    """
    Returns the primary photo root used for new uploads.
    Defaults to the first configured root or settings.photo_root.
    """
    primary_setting = db.query(SystemSetting).filter(SystemSetting.key == "primary_photo_root").first()
    if primary_setting and primary_setting.value and primary_setting.value.strip():
        p = Path(primary_setting.value.strip()).resolve()
        if p.exists() and p.is_dir():
            return p

    roots = get_configured_photo_roots(db)
    for r in roots:
        if r.exists() and r.is_dir():
            return r

    if roots:
        return roots[0]

    return Path(settings.photo_root or "pics").resolve()


def set_configured_photo_roots(
    db: Session,
    roots: List[str],
    primary: Optional[str] = None
) -> List[str]:
    """
    Validates and stores the list of photo roots and primary root in SystemSetting.
    Raises HTTPException if any path is invalid or not a directory.
    """
    resolved_paths: List[str] = []
    seen = set()

    for r in roots:
        r_str = str(r).strip()
        if not r_str:
            continue
        p = Path(r_str)
        if not p.exists() or not p.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"相册目录 '{r_str}' 不存在或不是有效的本地文件夹"
            )
        resolved_str = str(p.resolve())
        if resolved_str not in seen:
            seen.add(resolved_str)
            resolved_paths.append(resolved_str)

    if not resolved_paths:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须至少配置一个有效的本地相册目录"
        )

    # Determine primary root
    chosen_primary = resolved_paths[0]
    if primary and str(primary).strip():
        primary_resolved = str(Path(str(primary).strip()).resolve())
        if primary_resolved in resolved_paths:
            chosen_primary = primary_resolved

    # Save to database
    def _upsert(k: str, v: str):
        row = db.query(SystemSetting).filter(SystemSetting.key == k).first()
        if row:
            row.value = v
        else:
            db.add(SystemSetting(key=k, value=v))

    _upsert("photo_roots", json.dumps(resolved_paths, ensure_ascii=False))
    _upsert("primary_photo_root", chosen_primary)
    _upsert("photo_root", chosen_primary)  # keep backward compatibility
    db.commit()

    return resolved_paths


def resolve_photo_root(photo: Photo, db: Session) -> Path:
    """
    Locates the physical root directory for a specific Photo record.
    """
    if photo.root_path:
        p = Path(photo.root_path).resolve()
        if p.exists() and (p / photo.relative_path).exists():
            return p

    # Fallback: scan through all configured roots
    roots = get_configured_photo_roots(db)
    for r in roots:
        if (r / photo.relative_path).exists():
            # Auto-repair root_path for fast lookup next time
            try:
                photo.root_path = str(r.resolve())
                db.commit()
            except Exception:
                pass
            return r

    if photo.root_path:
        return Path(photo.root_path).resolve()

    return get_primary_photo_root(db)


def resolve_media_root(media: MomentMedia, db: Session) -> Path:
    """
    Locates the physical root directory for a specific MomentMedia item.
    """
    if media.root_path:
        p = Path(media.root_path).resolve()
        if p.exists() and (p / media.relative_path).exists():
            return p

    roots = get_configured_photo_roots(db)
    for r in roots:
        if (r / media.relative_path).exists():
            try:
                media.root_path = str(r.resolve())
                db.commit()
            except Exception:
                pass
            return r

    if media.root_path:
        return Path(media.root_path).resolve()

    return get_primary_photo_root(db)


def resolve_moment_root(moment: Moment, db: Session) -> Path:
    """
    Locates the physical root directory for a specific Moment item.
    """
    if moment.root_path:
        p = Path(moment.root_path).resolve()
        if p.exists() and (p / moment.folder_rel_path).exists():
            return p

    roots = get_configured_photo_roots(db)
    for r in roots:
        if (r / moment.folder_rel_path).exists():
            try:
                moment.root_path = str(r.resolve())
                db.commit()
            except Exception:
                pass
            return r

    if moment.root_path:
        return Path(moment.root_path).resolve()

    return get_primary_photo_root(db)
