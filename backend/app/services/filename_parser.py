import re
from datetime import date
from pathlib import Path
from typing import Tuple
from backend.app.core.exceptions import (
    InvalidFilenameError,
    InvalidDateError,
    DateOutOfRangeError
)

from backend.app.core.time_utils import get_beijing_today

# Supported image file extensions (lowercase)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def is_supported_image(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS

def parse_filename_date(filename: str) -> date:
    """
    Parses a photo date strictly from the 6-digit 'yymmdd' filename stem.
    Year is strictly 2000 + YY (2000 - 2099).
    Validates calendar authenticity.
    """
    path = Path(filename)
    stem = path.stem

    # Rule: Stem must be strictly 6 digits, without prefix, suffix or separators
    if not re.fullmatch(r"\d{6}", stem):
        raise InvalidFilenameError(filename)

    yy = int(stem[0:2])
    mm = int(stem[2:4])
    dd = int(stem[4:6])

    yyyy = 2000 + yy

    try:
        parsed_date = date(yyyy, mm, dd)
    except ValueError as e:
        raise InvalidDateError(f"{stem} (derived: {yyyy}-{mm:02d}-{dd:02d})", reason=str(e))

    return parsed_date

def validate_date_range(photo_date: date, birth_date: date, current_date: date | None = None) -> None:
    """
    Validates whether the photo date is within [birth_date, today] in Beijing Time.
    """
    today = current_date or get_beijing_today()

    if photo_date < birth_date:
        raise DateOutOfRangeError(
            photo_date.isoformat(),
            reason=f"Date is earlier than child's birth date ({birth_date.isoformat()})"
        )
    if photo_date > today:
        raise DateOutOfRangeError(
            photo_date.isoformat(),
            reason=f"Date is in the future relative to today ({today.isoformat()})"
        )
