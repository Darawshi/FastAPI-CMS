from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import EmailStr
from sqlalchemy.orm import validates
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from app.models.user_role import UserRole
from sqlalchemy import Column, DateTime, String


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: EmailStr = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False)
    )
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.editor, index=True)
    is_active: bool = Field(default=True, index=True)
    last_login: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

    user_pic: Optional[str] = Field(
        default=None,
        sa_column=Column(String,unique=True, nullable=True)
    )

    # Add this field to link an editor to their category editor
    supervisor_id: Optional[UUID] = Field(default=None, foreign_key="user.id")

    # Relationship to supervisor
    supervisor: Optional["User"] = Relationship(back_populates="subordinates",
                                                sa_relationship_kwargs={"remote_side": "User.id"})


    # Users this user has created
    users_created: List["User"] = Relationship(back_populates="created_by")


    @validates("email")
    def normalize_email(self, _, address):
        return str(address).lower()