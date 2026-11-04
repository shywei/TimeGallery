from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.services.memory_service import MemoryService

router = APIRouter(prefix="/home", tags=["Home"])

@router.get("/overview")
def get_home_overview(db: Session = Depends(get_db)):
    service = MemoryService(db)
    return service.get_home_overview()
