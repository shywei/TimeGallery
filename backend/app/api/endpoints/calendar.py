from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.services.calendar_service import CalendarService, parse_flexible_date
from backend.app.core.exceptions import InvalidDateError

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.get("/day/{date_str}")
def get_day_view(date_str: str, db: Session = Depends(get_db)):
    try:
        parsed_date = parse_flexible_date(date_str)
    except InvalidDateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.message))

    service = CalendarService(db)
    return service.get_day_view(parsed_date)

@router.get("/week/{date_str}")
def get_week_view(date_str: str, db: Session = Depends(get_db)):
    try:
        parsed_date = parse_flexible_date(date_str)
    except InvalidDateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.message))

    service = CalendarService(db)
    return service.get_week_view(parsed_date)

@router.get("/month/{year}/{month}")
def get_month_calendar_view(year: int, month: int, db: Session = Depends(get_db)):
    if year < 2000 or year > 2099:
        raise HTTPException(status_code=400, detail="Year must be between 2000 and 2099.")
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")

    service = CalendarService(db)
    return service.get_month_calendar_view(year, month)

@router.get("/month/{year}/{month}/photo-wall")
def get_month_photo_wall(year: int, month: int, db: Session = Depends(get_db)):
    if year < 2000 or year > 2099:
        raise HTTPException(status_code=400, detail="Year must be between 2000 and 2099.")
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")

    service = CalendarService(db)
    return service.get_month_photo_wall(year, month)

@router.get("/date/{date_str}")
def resolve_quick_date(date_str: str, db: Session = Depends(get_db)):
    """
    Rapid date query: accepts either YYYY-MM-DD or 6-digit YYMMDD,
    returns standard date, photo presence, and target URLs.
    """
    try:
        parsed_date = parse_flexible_date(date_str)
    except InvalidDateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.message))

    service = CalendarService(db)
    day_view = service.get_day_view(parsed_date)

    return {
        "input": date_str,
        "date": parsed_date.isoformat(),
        "has_photo": day_view["has_photo"],
        "photo_id": day_view["photo"]["id"] if day_view["photo"] else None,
        "day_view_url": f"/api/calendar/day/{parsed_date.isoformat()}"
    }
