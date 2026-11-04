from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.services.backup_service import (
    create_sqlite_backup,
    list_backups,
    restore_sqlite_backup,
    export_metadata_json
)

router = APIRouter(prefix="/backup", tags=["Backup"])

class RestoreRequest(BaseModel):
    filename: str

@router.post("/create")
def trigger_backup():
    try:
        res = create_sqlite_backup()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def get_backup_list():
    return list_backups()

@router.post("/restore")
def restore_backup(payload: RestoreRequest):
    try:
        res = restore_sqlite_backup(payload.filename)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export-json")
def export_json(db: Session = Depends(get_db)):
    return export_metadata_json(db)
