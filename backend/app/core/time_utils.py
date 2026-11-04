from datetime import datetime, date, timezone, timedelta

# Beijing Time is UTC+8 (Asia/Shanghai), no DST
BEIJING_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")

def get_beijing_now() -> datetime:
    """Returns the current datetime in Beijing Time (UTC+8)."""
    return datetime.now(BEIJING_TZ)

def get_beijing_today() -> date:
    """Returns today's date according to Beijing Time (UTC+8)."""
    return get_beijing_now().date()

def get_beijing_now_iso() -> str:
    """Returns ISO 8601 formatted string of current Beijing Time."""
    return get_beijing_now().isoformat()
