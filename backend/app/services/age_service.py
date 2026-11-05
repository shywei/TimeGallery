import calendar
from datetime import date
from typing import Dict, Any, Optional

def calculate_timeline_milestone(
    baseline_date: date,
    target_date: date,
    baseline_type: str = "BIRTHDAY",
    custom_label: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculates age / milestone / anniversary / days elapsed
    between baseline_date and target_date based on baseline_type.
    """
    if baseline_type == "NONE":
        return {
            "years": 0,
            "months": 0,
            "days": 0,
            "total_days": 0,
            "display": "",
            "is_valid": False,
            "baseline_type": "NONE"
        }

    total_days = (target_date - baseline_date).days

    if target_date < baseline_date:
        before_label = "开始前"
        if baseline_type == "BIRTHDAY":
            before_label = "出生前"
        elif baseline_type == "ANNIVERSARY":
            before_label = "纪念日前"
        return {
            "years": 0,
            "months": 0,
            "days": 0,
            "total_days": total_days,
            "display": f"{before_label} {abs(total_days)} 天",
            "is_valid": False,
            "baseline_type": baseline_type
        }

    years = target_date.year - baseline_date.year
    months = target_date.month - baseline_date.month
    days = target_date.day - baseline_date.day

    if days < 0:
        prev_month = target_date.month - 1 if target_date.month > 1 else 12
        prev_year = target_date.year if target_date.month > 1 else target_date.year - 1
        _, days_in_prev_month = calendar.monthrange(prev_year, prev_month)
        days += days_in_prev_month
        months -= 1

    if months < 0:
        years -= 1
        months += 12

    display = ""

    if baseline_type == "BIRTHDAY":
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

    elif baseline_type == "ANNIVERSARY":
        label = custom_label.strip() if custom_label and custom_label.strip() else "相伴"
        day_count = total_days + 1
        if years > 0 and months == 0 and days == 0:
            display = f"{label} {years} 周年 (第 {day_count} 天)"
        else:
            display = f"{label}第 {day_count} 天"

    elif baseline_type == "START_DATE":
        label = custom_label.strip() if custom_label and custom_label.strip() else "记录"
        day_count = total_days + 1
        display = f"{label}第 {day_count} 天"

    elif baseline_type == "CUSTOM":
        label = custom_label.strip() if custom_label and custom_label.strip() else "第"
        day_count = total_days + 1
        display = f"{label} {day_count} 天" if not label.endswith("第") else f"{label}{day_count}天"

    else:
        # Default fallback to birthday format
        parts = []
        if years > 0:
            parts.append(f"{years} 岁")
        if months > 0:
            parts.append(f"{months} 个月")
        if days > 0 or not parts:
            parts.append(f"{days} 天")
        display = " ".join(parts)

    return {
        "years": years,
        "months": months,
        "days": days,
        "total_days": total_days,
        "display": display,
        "is_valid": True,
        "baseline_type": baseline_type
    }

def calculate_age(birth_date: date, target_date: date) -> Dict[str, Any]:
    """
    Backwards-compatible wrapper around calculate_timeline_milestone for BIRTHDAY.
    """
    return calculate_timeline_milestone(birth_date, target_date, baseline_type="BIRTHDAY")
