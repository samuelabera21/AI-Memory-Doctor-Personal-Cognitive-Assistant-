from datetime import datetime, timedelta
from dateutil import parser
from zoneinfo import ZoneInfo
from app.config import settings
import re

_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _day_bounds(d: datetime):
    return d.strftime("%Y-%m-%d"), d.strftime("%Y-%m-%d")


def get_time_range_from_label(query: str):
    q = query.lower()
    if "morning" in q:
        return "05:00", "11:59"
    if "afternoon" in q:
        return "12:00", "16:59"
    if "evening" in q:
        return "17:00", "21:59"
    if "night" in q:
        return "22:00", "23:59"
    return None, None


def parse_query_time_filters(query: str, now: datetime | None = None):
    now = now or datetime.now(ZoneInfo(settings.timezone))
    q = query.lower()

    start_date = None
    end_date = None

    if "today" in q:
        start_date, end_date = _day_bounds(now)
    elif "yesterday" in q:
        y = now - timedelta(days=1)
        start_date, end_date = _day_bounds(y)
    elif "last week" in q:
        end = now
        start = now - timedelta(days=7)
        start_date, end_date = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    elif "this week" in q:
        start = now - timedelta(days=now.weekday())
        start_date, end_date = start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
    elif "last month" in q:
        end = now
        start = now - timedelta(days=30)
        start_date, end_date = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    elif "this month" in q:
        start = now.replace(day=1)
        start_date, end_date = start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
    else:
        month_match = None
        for m in _MONTHS:
            if re.search(rf"\b{re.escape(m)}\b", q):
                month_match = m
                break
        if month_match:
            month_num = _MONTHS[month_match]
            year = now.year
            start = datetime(year, month_num, 1, tzinfo=now.tzinfo)
            if month_num == 12:
                next_month = datetime(year + 1, 1, 1, tzinfo=now.tzinfo)
            else:
                next_month = datetime(year, month_num + 1, 1, tzinfo=now.tzinfo)
            end = next_month - timedelta(days=1)
            start_date, end_date = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        else:
            try:
                parsed = parser.parse(query, fuzzy=True, default=now)
                if parsed.date() != now.date() or any(tok in q for tok in ["on", "at", "feb", "jan", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                    start_date, end_date = _day_bounds(parsed)
            except (ValueError, TypeError, OverflowError):
                pass

    start_time, end_time = get_time_range_from_label(query)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "start_time": start_time,
        "end_time": end_time,
    }


def in_time_window(time_str: str, start_time: str | None, end_time: str | None) -> bool:
    if not start_time or not end_time:
        return True
    if not time_str:
        return False
    return start_time <= time_str <= end_time
