from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc_aware(value: datetime) -> datetime:
    """MongoDB returns naive UTC datetimes; normalize before comparing."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
