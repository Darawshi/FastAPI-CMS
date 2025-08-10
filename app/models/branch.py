#app/models/branch.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, List
from uuid import UUID, uuid4

from sqlalchemy import  DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, Relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base  # your new Base class

if TYPE_CHECKING:
    from app.models.user import User


class Branch(Base):
    __tablename__ = "branch"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    created_by: Mapped[Optional["User"]] = Relationship(
        "User",
        lazy="selectin"
    )

    users: Mapped[List["User"]] = Relationship(
        "User",
        secondary="user_branch_link",
        back_populates="branches",
        lazy="selectin",
        overlaps="user_branch_links,user,branch"
    )

    user_branch_links: Mapped[List["UserBranchLink"]] = Relationship(
        "UserBranchLink",
        back_populates="branch",
        lazy="selectin",
        overlaps="users,branch,user"
    )

