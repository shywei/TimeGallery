import calendar
from datetime import date
from typing import Dict, Any

def calculate_age(birth_date: date, target_date: date) -> Dict[str, Any]:
    """
    Accurately calculates child's calendar age (years, months, days)
    between birth_date and target_date.
    """
    if target_date < birth_date:
        return {
            "years": 0,
            "months": 0,
            "days": 0,
            "display": "未出生",
            "is_valid": False
        }

    years = target_date.year - birth_date.year
    months = target_date.month - birth_date.month
    days = target_date.day - birth_date.day

    if days < 0:
        # Borrow from previous month of target_date
        prev_month = target_date.month - 1 if target_date.month > 1 else 12
        prev_year = target_date.year if target_date.month > 1 else target_date.year - 1
        _, days_in_prev_month = calendar.monthrange(prev_year, prev_month)
        days += days_in_prev_month
        months -= 1

    if months < 0:
        years -= 1
        months += 12

    # Human readable display string
    parts = []
    if years > 0:
        parts.append(f"{years} 岁")
    if months > 0:
        parts.append(f"{months} 个月")
    if days > 0 or not parts:
        if not parts and days == 0:
            parts.append("出生当天")
        else:
            parts.append(f"{days} 天")

    display = " ".join(parts)

    return {
        "years": years,
        "months": months,
        "days": days,
        "display": display,
        "is_valid": True
    }
