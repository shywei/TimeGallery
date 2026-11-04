import pytest
from datetime import date
from backend.app.services.filename_parser import (
    parse_filename_date,
    is_supported_image,
    validate_date_range
)
from backend.app.core.exceptions import (
    InvalidFilenameError,
    InvalidDateError,
    DateOutOfRangeError
)

def test_parse_valid_filenames():
    assert parse_filename_date("240101.jpg") == date(2024, 1, 1)
    assert parse_filename_date("241103.png") == date(2024, 11, 3)
    assert parse_filename_date("250228.jpeg") == date(2025, 2, 28)
    assert parse_filename_date("240229.webp") == date(2024, 2, 29) # Leap year
    assert parse_filename_date("991231.jpg") == date(2099, 12, 31) # 2099

def test_parse_invalid_filenames():
    invalid_stems = [
        "IMG_241103.jpg",
        "241103_01.jpg",
        "20241103.jpg",
        "2411.jpg",
        "2411030.jpg",
        "photo.jpg",
        "abcdef.jpg"
    ]
    for stem in invalid_stems:
        with pytest.raises(InvalidFilenameError):
            parse_filename_date(stem)

def test_parse_invalid_calendar_dates():
    invalid_dates = [
        "250230.jpg", # Feb 30 does not exist
        "241332.jpg", # Month 13, day 32
        "250229.jpg", # 2025 is not a leap year
        "240431.jpg", # April has 30 days
    ]
    for filename in invalid_dates:
        with pytest.raises(InvalidDateError):
            parse_filename_date(filename)

def test_supported_extensions():
    assert is_supported_image("241103.jpg") is True
    assert is_supported_image("241103.JPG") is True
    assert is_supported_image("241103.jpeg") is True
    assert is_supported_image("241103.png") is True
    assert is_supported_image("241103.webp") is True
    assert is_supported_image("241103.bmp") is False
    assert is_supported_image("241103.gif") is False
    assert is_supported_image("241103.mp4") is False

def test_date_range_validation():
    birth = date(2024, 1, 1)
    today = date(2026, 11, 3)

    # Valid
    validate_date_range(date(2024, 1, 1), birth, today)
    validate_date_range(date(2025, 6, 15), birth, today)
    validate_date_range(date(2026, 11, 3), birth, today)

    # Before birth
    with pytest.raises(DateOutOfRangeError):
        validate_date_range(date(2023, 12, 31), birth, today)

    # Future date
    with pytest.raises(DateOutOfRangeError):
        validate_date_range(date(2026, 11, 4), birth, today)
