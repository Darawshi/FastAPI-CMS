# app/models/password_reset_token.py

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime
from uuid import uuid4, UUID
from sqlmodel import SQLModel, Field, Relationship
if TYPE_CHECKING:
    from app.models.user import User  # ✅ Import only for type checking



class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_token"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    token: str = Field(index=True, unique=True)
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), index=True)  # Add index
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

    user: Optional["User"] = Relationship(back_populates="reset_tokens")  #