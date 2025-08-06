from datetime import datetime, timedelta, timezone

# Simple in-memory store: {email: datetime_of_next_allowed_request}
_reset_request_cache = {}

RESET_REQUEST_INTERVAL = timedelta(minutes=5)  # 1 request per 5 minutes

async def can_request_reset(email: str) -> bool:
    now = datetime.now(timezone.utc)
    allowed_time = _reset_request_cache.get(email)
    if allowed_time and allowed_time > now:
        return False
    return True

async def mark_reset_requested(email: str):
    _reset_request_cache[email] = datetime.now(timezone.utc) + RESET_REQUEST_INTERVAL