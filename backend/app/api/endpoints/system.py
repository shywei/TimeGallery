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
    photo_root = get_setting(db, "photo_root", settings.photo_root)
    photo_count = db.query(Photo).filter(Photo.status == "ACTIVE").count()

    return SystemStatusResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        status="healthy",
        first_setup_completed=first_setup,
        photo_count=photo_count,
        days_recorded=photo_count,
        photo_root_configured=bool(photo_root and Path(photo_root).exists())
    )

@router.get("/config", response_model=SystemConfigResponse)
def get_system_config(db: Session = Depends(get_db)):
    first_setup = get_setting(db, "first_setup_completed", "false").lower() == "true"
    birth_date = get_setting(db, "birth_date", settings.birth_date)
    photo_root = get_setting(db, "photo_root", settings.photo_root)
    thumb_size = int(get_setting(db, "thumbnail_size", str(settings.thumbnail_size)))
    prev_size = int(get_setting(db, "preview_size", str(settings.preview_size)))

    return SystemConfigResponse(
        app_name=settings.app_name,
        birth_date=birth_date or None,
        photo_root=photo_root or None,
        data_root=str(settings.data_dir),
        thumbnail_size=thumb_size,
        preview_size=prev_size,
        first_setup_completed=first_setup
    )

@router.post("/setup")
def setup_wizard(payload: SetupRequest, db: Session = Depends(get_db)):
    photo_path = Path(payload.photo_root)
    if not photo_path.exists() or not photo_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo directory '{payload.photo_root}' does not exist or is not a directory."
        )

    set_setting(db, "birth_date", payload.birth_date)
    set_setting(db, "photo_root", str(photo_path.resolve()))
    set_setting(db, "first_setup_completed", "true")

    return {"message": "Setup completed successfully."}

@router.put("/config")
def update_system_config(payload: SystemConfigUpdateRequest, db: Session = Depends(get_db)):
    if payload.photo_root is not None:
        p = Path(payload.photo_root)
        if not p.exists() or not p.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Photo directory '{payload.photo_root}' is invalid."
            )
        set_setting(db, "photo_root", str(p.resolve()))

    if payload.birth_date is not None:
        set_setting(db, "birth_date", payload.birth_date)

    if payload.thumbnail_size is not None:
        set_setting(db, "thumbnail_size", str(payload.thumbnail_size))

    if payload.preview_size is not None:
        set_setting(db, "preview_size", str(payload.preview_size))

    return {"message": "Configuration updated successfully."}
