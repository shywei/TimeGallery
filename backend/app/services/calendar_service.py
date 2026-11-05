import calendar
import re
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.moment import Moment
from backend.app.services.age_service import calculate_timeline_milestone, calculate_age
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
        base_setting = db.query(SystemSetting).filter(SystemSetting.key == "baseline_date").first()
        if not base_setting or not base_setting.value:
            base_setting = db.query(SystemSetting).filter(SystemSetting.key == "birth_date").first()
        
        self.baseline_date = None
        if base_setting and base_setting.value:
            try:
                self.baseline_date = date.fromisoformat(base_setting.value)
            except Exception:
                pass
        self.birth_date = self.baseline_date

        type_setting = db.query(SystemSetting).filter(SystemSetting.key == "baseline_type").first()
        self.baseline_type = type_setting.value if type_setting and type_setting.value else "BIRTHDAY"

        label_setting = db.query(SystemSetting).filter(SystemSetting.key == "baseline_label").first()
        self.baseline_label = label_setting.value if label_setting and label_setting.value else ""

    def get_day_view(self, target_date: date) -> Dict[str, Any]:
        date_iso = target_date.isoformat()
        photo = self.db.query(Photo).filter(
            Photo.photo_date == date_iso,
            Photo.status == "ACTIVE"
        ).first()

        prev_date = (target_date - timedelta(days=1)).isoformat()
        next_date = (target_date + timedelta(days=1)).isoformat()

        moment = self.db.query(Moment).filter(Moment.moment_date == date_iso).first()
        moment_info = None
        if moment:
            cover_url = None
            if moment.cover_media_id:
                cover_url = f"/api/moments/media/{moment.cover_media_id}/thumbnail"
            elif moment.media_items:
                target_m = next((item for item in moment.media_items if item.media_type == "PHOTO"), moment.media_items[0])
                cover_url = f"/api/moments/media/{target_m.id}/thumbnail"
            moment_info = {
                "id": moment.id,
                "title": moment.title,
                "photo_count": moment.photo_count,
                "video_count": moment.video_count,
                "cover_url": cover_url
            }

        age_info = None
        if self.baseline_date and self.baseline_type != "NONE":
            age_info = calculate_timeline_milestone(
                self.baseline_date,
                target_date,
                baseline_type=self.baseline_type,
                custom_label=self.baseline_label
            )

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
            "has_moment": moment_info is not None,
            "moment": moment_info,
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

        moments = self.db.query(Moment).filter(Moment.moment_date.in_(date_strings)).all()
        moments_by_date = {m.moment_date: m for m in moments}

        days = []
        recorded_count = 0

        for d in week_dates:
            d_iso = d.isoformat()
            p = photos_by_date.get(d_iso)
            m = moments_by_date.get(d_iso)
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
                "photo": photo_item,
                "has_moment": m is not None,
                "moment": {
                    "id": m.id,
                    "title": m.title,
                    "photo_count": m.photo_count,
                    "video_count": m.video_count,
                    "cover_url": f"/api/moments/media/{m.cover_media_id}/thumbnail" if m.cover_media_id else (f"/api/moments/media/{m.media_items[0].id}/thumbnail" if m.media_items else None)
                } if m else None
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

        moments = self.db.query(Moment).filter(
            Moment.moment_date >= start_date_str,
            Moment.moment_date <= end_date_str
        ).all()
        moments_by_date = {m.moment_date: m for m in moments}

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
                    "photo": None,
                    "has_moment": False,
                    "moment": None
                })

        # Current month days
        recorded_count = 0
        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            d_iso = d.isoformat()
            p = photos_by_date.get(d_iso)
            m = moments_by_date.get(d_iso)
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
                "photo": photo_item,
                "has_moment": m is not None,
                "moment": {
                    "id": m.id,
                    "title": m.title,
                    "photo_count": m.photo_count,
                    "video_count": m.video_count,
                    "cover_url": f"/api/moments/media/{m.cover_media_id}/thumbnail" if m.cover_media_id else (f"/api/moments/media/{m.media_items[0].id}/thumbnail" if m.media_items else None)
                } if m else None
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
                    "photo": None,
                    "has_moment": False,
                    "moment": None
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

        moments = self.db.query(Moment).filter(Moment.moment_date.startswith(prefix)).all()
        moments_by_date = {m.moment_date: m for m in moments}

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
                "aspect_ratio": round(p.width / p.height, 3) if p.height > 0 else 1.0,
                "has_moment": p.photo_date in moments_by_date,
                "moment": {
                    "id": moments_by_date[p.photo_date].id,
                    "title": moments_by_date[p.photo_date].title,
                    "photo_count": moments_by_date[p.photo_date].photo_count,
                    "video_count": moments_by_date[p.photo_date].video_count,
                    "cover_url": f"/api/moments/media/{moments_by_date[p.photo_date].cover_media_id}/thumbnail" if moments_by_date[p.photo_date].cover_media_id else None
                } if p.photo_date in moments_by_date else None
            }
            for p in photos
        ]

        # Also include any moments in this month that don't have a daily archive photo
        photo_dates = {p.photo_date for p in photos}
        for m in moments:
            if m.moment_date not in photo_dates and m.cover_media_id:
                items.append({
                    "id": -(m.id),
                    "photo_date": m.moment_date,
                    "width": 1000,
                    "height": 1000,
                    "is_highlight": 0,
                    "description": m.title or f"{m.moment_date} 特别时刻",
                    "thumbnail_url": f"/api/moments/media/{m.cover_media_id}/thumbnail",
                    "preview_url": f"/api/moments/media/{m.cover_media_id}/thumbnail",
                    "aspect_ratio": 1.0,
                    "has_moment": True,
                    "moment": {
                        "id": m.id,
                        "title": m.title,
                        "photo_count": m.photo_count,
                        "video_count": m.video_count,
                        "cover_url": f"/api/moments/media/{m.cover_media_id}/thumbnail"
                    }
                })
        items.sort(key=lambda x: x["photo_date"])

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
