import os
from pathlib import Path
from PIL import Image, ImageOps
from backend.app.core.config import settings
from backend.app.core.paths import resolve_safe_path
from backend.app.models.photo import Photo

THUMBNAIL_DIR = settings.data_dir / "thumbnails"
PREVIEW_DIR = settings.data_dir / "previews"

THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

def process_and_save_image(src_path: Path, dest_path: Path, max_dimension: int, quality: int):
    """
    Opens src image, applies EXIF orientation transpose, scales maintaining aspect ratio,
    and saves as WebP format at dest_path.
    """
    with Image.open(src_path) as img:
        # Correct EXIF rotation if present
        img = ImageOps.exif_transpose(img) or img

        # Handle RGBA/transparency
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            # Convert palette transparency to RGBA first
            img = img.convert("RGBA")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Calculate thumbnail aspect-ratio preserving size
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest_path, "WEBP", quality=quality, method=4)

def purge_image_caches() -> int:
    """
    Purges all cached thumbnail and preview WebP images.
    Returns the total number of deleted cache files.
    """
    deleted_count = 0
    for directory in [THUMBNAIL_DIR, PREVIEW_DIR]:
        if directory.exists():
            for cached_file in directory.glob("*.webp"):
                try:
                    cached_file.unlink()
                    deleted_count += 1
                except Exception:
                    pass
    return deleted_count

def get_or_create_thumbnail(photo: Photo, photo_root: Path) -> Path:
    """
    Returns the path to the cached 480px WebP thumbnail, creating it on demand if absent.
    """
    dest_path = THUMBNAIL_DIR / f"{photo.id}_{photo.sha256[:8]}.webp"
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return dest_path

    # Clean any outdated thumbnails for this photo ID
    for old_thumb in THUMBNAIL_DIR.glob(f"{photo.id}_*.webp"):
        if old_thumb.name != dest_path.name:
            try:
                old_thumb.unlink()
            except Exception:
                pass

    original_path = resolve_safe_path(photo_root, photo.relative_path)
    process_and_save_image(original_path, dest_path, settings.thumbnail_size, quality=82)
    return dest_path

def get_or_create_preview(photo: Photo, photo_root: Path) -> Path:
    """
    Returns the path to the cached 1600px WebP preview, creating it on demand if absent.
    """
    dest_path = PREVIEW_DIR / f"{photo.id}_{photo.sha256[:8]}.webp"
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return dest_path

    # Clean any outdated previews for this photo ID
    for old_prev in PREVIEW_DIR.glob(f"{photo.id}_*.webp"):
        if old_prev.name != dest_path.name:
            try:
                old_prev.unlink()
            except Exception:
                pass

    original_path = resolve_safe_path(photo_root, photo.relative_path)
    process_and_save_image(original_path, dest_path, settings.preview_size, quality=85)
    return dest_path
