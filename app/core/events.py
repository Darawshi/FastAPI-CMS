# app/core/events.py

from sqlalchemy import event
from datetime import datetime, timezone
from app.models.user import User

@event.listens_for(User, "before_update", propagate=True)
def auto_update_timestamp(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
