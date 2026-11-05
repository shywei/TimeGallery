from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.core.config import settings
from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.schemas.system import (
    SystemStatusResponse,
    SystemConfigResponse,
    SetupRequest,
    SystemConfigUpdateRequest
)
from backend.app.services.storage_service import (
    get_configured_photo_roots,
    get_primary_photo_root,
    set_configured_photo_roots
)
from pathlib import Path

router = APIRouter(prefix="/system", tags=["System"])

def get_setting(db: Session, key: str, default: str = "") -> str:
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    return setting.value if setting else default

def set_setting(db: Session, key: str, value: str):
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = SystemSetting(key=key, value=value)
        db.add(setting)
    db.commit()

@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    first_setup = get_setting(db, "first_setup_completed", "false").lower() == "true"
    photo_roots = get_configured_photo_roots(db)
    valid_roots = [p for p in photo_roots if p.exists() and p.is_dir()]
    photo_count = db.query(Photo).filter(Photo.status == "ACTIVE").count()

    return SystemStatusResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        status="healthy",
        first_setup_completed=first_setup,
        photo_count=photo_count,
        days_recorded=photo_count,
        photo_root_configured=len(valid_roots) > 0,
        photo_roots_count=len(valid_roots)
    )

@router.get("/config", response_model=SystemConfigResponse)
def get_system_config(db: Session = Depends(get_db)):
    first_setup = get_setting(db, "first_setup_completed", "false").lower() == "true"
    birth_date = get_setting(db, "birth_date", settings.birth_date)
    baseline_type = get_setting(db, "baseline_type", settings.baseline_type or "BIRTHDAY")
    baseline_date = get_setting(db, "baseline_date", settings.baseline_date or birth_date)
    baseline_label = get_setting(db, "baseline_label", settings.baseline_label)
    
    photo_roots = [str(p) for p in get_configured_photo_roots(db)]
    primary_root = str(get_primary_photo_root(db)) if photo_roots else None
    
    thumb_size = int(get_setting(db, "thumbnail_size", str(settings.thumbnail_size)))
    prev_size = int(get_setting(db, "preview_size", str(settings.preview_size)))

    return SystemConfigResponse(
        app_name=settings.app_name,
        birth_date=baseline_date or birth_date or None,
        baseline_type=baseline_type,
        baseline_date=baseline_date or birth_date or None,
        baseline_label=baseline_label or None,
        photo_root=primary_root,
        photo_roots=photo_roots,
        primary_photo_root=primary_root,
        data_root=str(settings.data_dir),
        thumbnail_size=thumb_size,
        preview_size=prev_size,
        first_setup_completed=first_setup
    )

@router.post("/setup")
def setup_wizard(payload: SetupRequest, db: Session = Depends(get_db)):
    roots = payload.photo_roots or ([payload.photo_root] if payload.photo_root else [])
    if not roots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供至少一个相册根目录。"
        )

    set_configured_photo_roots(db, roots, payload.primary_photo_root or payload.photo_root)

    b_date = payload.baseline_date or payload.birth_date or ""
    b_type = payload.baseline_type or "BIRTHDAY"
    b_label = payload.baseline_label or ""

    set_setting(db, "birth_date", b_date)
    set_setting(db, "baseline_date", b_date)
    set_setting(db, "baseline_type", b_type)
    set_setting(db, "baseline_label", b_label)
    set_setting(db, "first_setup_completed", "true")

    return {"message": "Setup completed successfully."}

@router.put("/config")
def update_system_config(payload: SystemConfigUpdateRequest, db: Session = Depends(get_db)):
    if payload.photo_roots is not None:
        set_configured_photo_roots(db, payload.photo_roots, payload.primary_photo_root)
    elif payload.photo_root is not None:
        set_configured_photo_roots(db, [payload.photo_root], payload.photo_root)
    elif payload.primary_photo_root is not None:
        current_roots = [str(p) for p in get_configured_photo_roots(db)]
        set_configured_photo_roots(db, current_roots, payload.primary_photo_root)

    if payload.baseline_date is not None:
        set_setting(db, "baseline_date", payload.baseline_date)
        set_setting(db, "birth_date", payload.baseline_date)
    elif payload.birth_date is not None:
        set_setting(db, "baseline_date", payload.birth_date)
        set_setting(db, "birth_date", payload.birth_date)

    if payload.baseline_type is not None:
        set_setting(db, "baseline_type", payload.baseline_type)

    if payload.baseline_label is not None:
        set_setting(db, "baseline_label", payload.baseline_label)

    if payload.thumbnail_size is not None:
        set_setting(db, "thumbnail_size", str(payload.thumbnail_size))

    if payload.preview_size is not None:
        set_setting(db, "preview_size", str(payload.preview_size))

    return {"message": "Configuration updated successfully."}
