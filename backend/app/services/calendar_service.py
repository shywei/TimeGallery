import calendar
import re
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.services.age_service import calculate_age
from backend.app.services.filename_parser import parse_filename_date
from backend.app.core.exceptions import InvalidDateError
from backend.app.core.time_utils import get_beijing_today

def parse_flexible_date(date_str: str) -> date:
    """
    Parses a date string in either 'YYYY-MM-DD' or 'yymmdd' format.
    Validates calendar authenticity.
    """
    date_str = date_str.strip()

    # Case 1: YYYY-MM-DD
    if re.fullmatch(r"^\d{4}-\d{2}-\d{2}$", date_str):
        try:
            return date.fromisoformat(date_str)
        except ValueError as e:
            raise InvalidDateError(date_str, reason=str(e))

    # Case 2: 6-digit yymmdd
    if re.fullmatch(r"^\d{6}$", date_str):
        return parse_filename_date(f"{date_str}.jpg")

    raise InvalidDateError(date_str, reason="Expected format 'YYYY-MM-DD' or 6-digit 'YYMMDD'")

class CalendarService:
    def __init__(self, db: Session):
        self.db = db
        birth_setting = db.query(SystemSetting).filter(SystemSetting.key == "birth_date").first()
        self.birth_date = None
        if birth_setting and birth_setting.value:
            try:
                self.birth_date = date.fromisoformat(birth_setting.value)
            except Exception:
                pass

    def get_day_view(self, target_date: date) -> Dict[str, Any]:
        date_iso = target_date.isoformat()
        photo = self.db.query(Photo).filter(
            Photo.photo_date == date_iso,
            Photo.status == "ACTIVE"
        ).first()

        prev_date = (target_date - timedelta(days=1)).isoformat()
        next_date = (target_date + timedelta(days=1)).isoformat()

        age_info = None
        if self.birth_date:
            age_info = calculate_age(self.birth_date, target_date)

        photo_data = None
        if photo:
            photo_data = {
                "id": photo.id,
                "photo_date": photo.photo_date,
                "filename": photo.filename,
                "width": photo.width,
                "height": photo.height,
                "is_highlight": photo.is_highlight,
                "description": photo.description,
                "thumbnail_url": photo.thumbnail_url,
                "preview_url": photo.preview_url,
                "original_url": photo.original_url,
                "tags": [t.name for t in photo.tags]
            }

        return {
            "date": date_iso,
            "has_photo": photo is not None,
            "photo": photo_data,
            "age": age_info,
            "prev_date": prev_date,
            "next_date": next_date
        }

    def get_week_view(self, target_date: date) -> Dict[str, Any]:
        # Monday is 0, Sunday is 6
        weekday = target_date.weekday()
        monday = target_date - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)

        week_dates = [monday + timedelta(days=i) for i in range(7)]
        date_strings = [d.isoformat() for d in week_dates]

        photos = self.db.query(Photo).filter(
            Photo.photo_date.in_(date_strings),
            Photo.status == "ACTIVE"
        ).all()
        photos_by_date = {p.photo_date: p for p in photos}

        days = []
        recorded_count = 0

        for d in week_dates:
            d_iso = d.isoformat()
            p = photos_by_date.get(d_iso)
            if p:
                recorded_count += 1
                photo_item = {
                    "id": p.id,
                    "photo_date": p.photo_date,
                    "thumbnail_url": p.thumbnail_url,
                    "preview_url": p.preview_url,
                    "width": p.width,
                    "height": p.height,
                    "is_highlight": p.is_highlight
                }
            else:
                photo_item = None

            days.append({
                "date": d_iso,
                "day_number": d.day,
                "day_of_week": d.weekday() + 1, # 1=Mon, 7=Sun
                "is_today": d == get_beijing_today(),
                "has_photo": photo_item is not None,
                "photo": photo_item
            })

        return {
            "start_date": monday.isoformat(),
            "end_date": sunday.isoformat(),
            "recorded_days": recorded_count,
            "total_days": 7,
            "days": days,
            "prev_week_date": (monday - timedelta(days=7)).isoformat(),
            "next_week_date": (monday + timedelta(days=7)).isoformat(),
            "current_week_date": get_beijing_today().isoformat()
        }

    def get_month_calendar_view(self, year: int, month: int) -> Dict[str, Any]:
        _, days_in_month = calendar.monthrange(year, month)
        first_day_date = date(year, month, 1)
        # weekday(): Monday is 0, Sunday is 6
        first_weekday = first_day_date.weekday()

        start_date_str = f"{year}-{month:02d}-01"
        end_date_str = f"{year}-{month:02d}-{days_in_month:02d}"

        photos = self.db.query(Photo).filter(
            Photo.photo_date >= start_date_str,
            Photo.photo_date <= end_date_str,
            Photo.status == "ACTIVE"
        ).all()
        photos_by_date = {p.photo_date: p for p in photos}

        # Calculate grid with leading days from previous month
        days = []

        # Previous month padding
        if first_weekday > 0:
            prev_year = year if month > 1 else year - 1
            prev_month = month - 1 if month > 1 else 12
            _, prev_days_count = calendar.monthrange(prev_year, prev_month)
            for i in range(first_weekday):
                p_day = prev_days_count - first_weekday + 1 + i
                p_date = date(prev_year, prev_month, p_day)
                days.append({
                    "date": p_date.isoformat(),
                    "day_number": p_day,
                    "is_current_month": False,
                    "is_today": p_date == date.today(),
                    "has_photo": False,
                    "photo": None
                })

        # Current month days
        recorded_count = 0
        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            d_iso = d.isoformat()
            p = photos_by_date.get(d_iso)
            if p:
                recorded_count += 1
                photo_item = {
                    "id": p.id,
                    "photo_date": p.photo_date,
                    "thumbnail_url": p.thumbnail_url,
                    "preview_url": p.preview_url,
                    "is_highlight": p.is_highlight
                }
            else:
                photo_item = None

            days.append({
                "date": d_iso,
                "day_number": day,
                "is_current_month": True,
                "is_today": d == get_beijing_today(),
                "has_photo": photo_item is not None,
                "photo": photo_item
            })

        # Trailing padding to fill full 7-day row
        remainder = len(days) % 7
        if remainder != 0:
            next_year = year if month < 12 else year + 1
            next_month = month + 1 if month < 12 else 1
            padding_needed = 7 - remainder
            for day in range(1, padding_needed + 1):
                d = date(next_year, next_month, day)
                days.append({
                    "date": d.isoformat(),
                    "day_number": day,
                    "is_current_month": False,
                    "is_today": d == get_beijing_today(),
                    "has_photo": False,
                    "photo": None
                })

        prev_y = year if month > 1 else year - 1
        prev_m = month - 1 if month > 1 else 12
        next_y = year if month < 12 else year + 1
        next_m = month + 1 if month < 12 else 1

        return {
            "year": year,
            "month": month,
            "days_in_month": days_in_month,
            "recorded_days": recorded_count,
            "total_days": days_in_month,
            "days": days,
            "prev_month": {"year": prev_y, "month": prev_m},
            "next_month": {"year": next_y, "month": next_m}
        }

    def get_month_photo_wall(self, year: int, month: int) -> Dict[str, Any]:
        prefix = f"{year}-{month:02d}-"
        photos = self.db.query(Photo).filter(
            Photo.photo_date.startswith(prefix),
            Photo.status == "ACTIVE"
        ).order_by(Photo.photo_date.asc()).all()

        items = [
            {
                "id": p.id,
                "photo_date": p.photo_date,
                "width": p.width,
                "height": p.height,
                "is_highlight": p.is_highlight,
                "description": p.description,
                "thumbnail_url": p.thumbnail_url,
                "preview_url": p.preview_url,
                "aspect_ratio": round(p.width / p.height, 3) if p.height > 0 else 1.0
            }
            for p in photos
        ]

        prev_y = year if month > 1 else year - 1
        prev_m = month - 1 if month > 1 else 12
        next_y = year if month < 12 else year + 1
        next_m = month + 1 if month < 12 else 1

        return {
            "year": year,
            "month": month,
            "total_photos": len(items),
            "items": items,
            "prev_month": {"year": prev_y, "month": prev_m},
            "next_month": {"year": next_y, "month": next_m}
        }
