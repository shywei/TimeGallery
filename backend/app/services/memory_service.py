import random
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.system_config import SystemSetting
from backend.app.models.photo import Photo
from backend.app.models.memory import MemoryDailySet
from backend.app.services.age_service import calculate_age
from backend.app.core.time_utils import get_beijing_today, get_beijing_now_iso

class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        birth_setting = db.query(SystemSetting).filter(SystemSetting.key == "birth_date").first()
        self.birth_date = None
        if birth_setting and birth_setting.value:
            try:
                self.birth_date = date.fromisoformat(birth_setting.value)
            except Exception:
                pass

    def _format_photo_memory(self, photo: Photo, memory_type: str, title: str, subtitle: str) -> Dict[str, Any]:
        p_date = date.fromisoformat(photo.photo_date)
        age_info = calculate_age(self.birth_date, p_date) if self.birth_date else None

        return {
            "memory_type": memory_type,
            "title": title,
            "subtitle": subtitle,
            "photo": {
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
                "age": age_info
            }
        }

    def get_or_create_daily_memories(self, today_date: Optional[date] = None) -> List[Dict[str, Any]]:
        today = today_date or get_beijing_today()
        today_iso = today.isoformat()

        # 1. Check persistent memory_daily_sets for today
        cached_sets = self.db.query(MemoryDailySet).filter(
            MemoryDailySet.memory_date == today_iso
        ).order_by(MemoryDailySet.sort_order.asc()).all()

        target_md = today.strftime("-%m-%d")

        if cached_sets:
            is_valid = True
            results = []
            for item in cached_sets:
                photo = self.db.query(Photo).filter(
                    Photo.id == item.photo_id,
                    Photo.status == "ACTIVE"
                ).first()
                if not photo:
                    is_valid = False
                    break
                # Strict check: ON_THIS_DAY must strictly match today's month and day
                if item.memory_type == "ON_THIS_DAY" and not photo.photo_date.endswith(target_md):
                    is_valid = False
                    break
                title, subtitle = self._get_titles(item.memory_type, photo.photo_date, today)
                results.append(self._format_photo_memory(photo, item.memory_type, title, subtitle))
            if is_valid and results:
                return results
            else:
                # Invalidate stale or corrupted cache
                self.db.query(MemoryDailySet).filter(MemoryDailySet.memory_date == today_iso).delete()
                self.db.commit()

        # 2. Compute fresh memory set for today
        memories = []
        selected_photo_ids = set()

        # A. ON_THIS_DAY (历史上的今天 - 严格匹配所有往年同月同日)
        otd_photos = self.db.query(Photo).filter(
            Photo.photo_date.endswith(target_md),
            Photo.photo_date < today_iso,
            Photo.status == "ACTIVE"
        ).order_by(Photo.photo_date.desc()).all()

        for p in otd_photos:
            p_year = int(p.photo_date[:4])
            diff_years = today.year - p_year
            title = f"{diff_years} 年前的今天" if diff_years > 0 else "历史上的今天"
            subtitle = f"记录于 {p.photo_date}"
            memories.append({
                "type": "ON_THIS_DAY",
                "photo": p,
                "title": title,
                "subtitle": subtitle
            })
            selected_photo_ids.add(p.id)

        # B. RANDOM_MEMORY (随机回忆)
        # Select from remaining active photos
        rng = random.Random(today.toordinal())
        candidate_photos = self.db.query(Photo).filter(
            Photo.status == "ACTIVE",
            ~Photo.id.in_(selected_photo_ids) if selected_photo_ids else True
        ).all()

        if candidate_photos:
            sample_size = min(2, len(candidate_photos))
            chosen = rng.sample(candidate_photos, sample_size)
            for p in chosen:
                memories.append({
                    "type": "RANDOM_MEMORY",
                    "photo": p,
                    "title": "随机回忆",
                    "subtitle": f"成长瞬间 · {p.photo_date}"
                })
                selected_photo_ids.add(p.id)

        # If still empty (e.g. very early archive), take any active photo
        if not memories:
            all_active = self.db.query(Photo).filter(Photo.status == "ACTIVE").limit(3).all()
            for p in all_active:
                memories.append({
                    "type": "RANDOM_MEMORY",
                    "photo": p,
                    "title": "成长瞬间",
                    "subtitle": f"记录于 {p.photo_date}"
                })

        # 3. Persist into memory_daily_sets
        # Clear any stale records for today
        self.db.query(MemoryDailySet).filter(MemoryDailySet.memory_date == today_iso).delete()

        for idx, m in enumerate(memories):
            rec = MemoryDailySet(
                memory_date=today_iso,
                memory_type=m["type"],
                photo_id=m["photo"].id,
                sort_order=idx
            )
            self.db.add(rec)
        self.db.commit()

        # Format return
        return [
            self._format_photo_memory(m["photo"], m["type"], m["title"], m["subtitle"])
            for m in memories
        ]

    def _get_titles(self, memory_type: str, photo_date_str: str, today: date):
        if memory_type == "ON_THIS_DAY":
            diff = today.year - int(photo_date_str[:4])
            return (f"{diff} 年前的今天" if diff > 0 else "历史上的今天", f"记录于 {photo_date_str}")
        else:
            return ("随机回忆", f"成长瞬间 · {photo_date_str}")

    def get_home_overview(self, today_date: Optional[date] = None) -> Dict[str, Any]:
        today = today_date or get_beijing_today()

        # 1. Total photos & recorded days
        total_photos = self.db.query(Photo).filter(Photo.status == "ACTIVE").count()

        # 2. Current Age
        current_age = None
        if self.birth_date:
            current_age = calculate_age(self.birth_date, today)

        # 3. Hero Memories
        memories = self.get_or_create_daily_memories(today)

        # 4. Recent Moments: recent 7 photos
        recent_photos = self.db.query(Photo).filter(
            Photo.status == "ACTIVE"
        ).order_by(Photo.photo_date.desc()).limit(7).all()

        recent_moments = []
        for p in recent_photos:
            p_d = date.fromisoformat(p.photo_date)
            age_info = calculate_age(self.birth_date, p_d) if self.birth_date else None
            recent_moments.append({
                "id": p.id,
                "photo_date": p.photo_date,
                "width": p.width,
                "height": p.height,
                "is_highlight": p.is_highlight,
                "description": p.description,
                "thumbnail_url": p.thumbnail_url,
                "preview_url": p.preview_url,
                "age": age_info
            })

        # 5. Selected Memories (Highlights)
        highlight_photos = self.db.query(Photo).filter(
            Photo.status == "ACTIVE",
            Photo.is_highlight == 1
        ).order_by(Photo.photo_date.desc()).limit(8).all()

        selected_memories = [
            {
                "id": p.id,
                "photo_date": p.photo_date,
                "width": p.width,
                "height": p.height,
                "is_highlight": p.is_highlight,
                "description": p.description,
                "thumbnail_url": p.thumbnail_url,
                "preview_url": p.preview_url,
                "tags": [t.name for t in p.tags]
            }
            for p in highlight_photos
        ]

        return {
            "current_date": today.isoformat(),
            "total_photos": total_photos,
            "days_recorded": total_photos,
            "current_age": current_age,
            "memories": memories,
            "recent_moments": recent_moments,
            "selected_memories": selected_memories
        }
