from datetime import datetime, timezone, timedelta
from backend.app.core.time_utils import (
    BEIJING_TZ,
    get_beijing_now,
    get_beijing_today,
    get_beijing_now_iso
)

def test_beijing_timezone_offset():
    now_bj = get_beijing_now()
    offset = now_bj.utcoffset()
    assert offset == timedelta(hours=8)
    assert "+08:00" in now_bj.isoformat()

def test_beijing_now_iso_format():
    iso_str = get_beijing_now_iso()
    assert "+08:00" in iso_str

def test_beijing_today():
    today = get_beijing_today()
    expected = datetime.now(BEIJING_TZ).date()
    assert today == expected
