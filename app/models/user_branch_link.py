# app/models/user_branch_link.py
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, Relationship
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.branch import Branch
    from app.models.user import User


class UserBranchLink(Base):
    __tablename__ = "user_branch_link"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    )
    branch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branch.id"), primary_key=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = Relationship(
        "User",
        back_populates="user_branch_links",
        lazy="selectin",
        overlaps="branches,user,branch"
    )

    branch: Mapped[Optional["Branch"]] = Relationship(
        "Branch",
        back_populates="user_branch_links",
        lazy="selectin",
        overlaps="users,branch,user"
    )