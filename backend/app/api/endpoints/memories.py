from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.services.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["Memories"])

@router.get("/today")
def get_daily_memories(db: Session = Depends(get_db)):
    service = MemoryService(db)
    return service.get_or_create_daily_memories()

@router.get("/on-this-day")
def get_on_this_day(db: Session = Depends(get_db)):
    service = MemoryService(db)
    all_memories = service.get_or_create_daily_memories()
    return [m for m in all_memories if m["memory_type"] == "ON_THIS_DAY"]

@router.get("/one-year-ago")
def get_one_year_ago(db: Session = Depends(get_db)):
    service = MemoryService(db)
    all_memories = service.get_or_create_daily_memories()
    return [m for m in all_memories if m["memory_type"] == "ON_THIS_DAY" and "1 年前的今天" in m.get("title", "")]

@router.get("/random")
def get_random_memory(db: Session = Depends(get_db)):
    service = MemoryService(db)
    all_memories = service.get_or_create_daily_memories()
    return [m for m in all_memories if m["memory_type"] == "RANDOM_MEMORY"]
