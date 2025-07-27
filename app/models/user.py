from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from app.models.user_role import UserRole
from sqlalchemy import Column, DateTime

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.editor)
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc))
    )