from datetime import datetime, timezone as tz
from zoneinfo import ZoneInfo
from typing import Optional


def get_timezone(timezone_name: str) -> ZoneInfo:
    """Get ZoneInfo object for timezone name."""
    return ZoneInfo(timezone_name)


def now_in_timezone(timezone_name: str) -> datetime:
    """Get current datetime in specified timezone."""
    return datetime.now(get_timezone(timezone_name))


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(tz.utc)


def convert_timezone(
    dt: datetime,
    from_tz: str,
    to_tz: str
) -> datetime:
    """Convert datetime from one timezone to another."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=get_timezone(from_tz))
    return dt.astimezone(get_timezone(to_tz))


def format_datetime_ru(dt: datetime, include_time: bool = True) -> str:
    """Format datetime in Russian style."""
    months_ru = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]

    day = dt.day
    month = months_ru[dt.month - 1]
    year = dt.year

    if include_time:
        return f"{day} {month} {year}, {dt.strftime('%H:%M')}"
    return f"{day} {month} {year}"


def get_time_period(hour: int) -> str:
    """Determine time period based on hour."""
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"


def get_time_period_ru(period: str) -> str:
    """Get Russian name for time period."""
    periods = {
        "morning": "Утренний дайджест",
        "afternoon": "Дневной дайджест",
        "evening": "Вечерний дайджест"
    }
    return periods.get(period, "Дайджест")
