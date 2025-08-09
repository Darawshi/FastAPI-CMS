#app/models/branch.py
from sqlalchemy import Column, DateTime, ForeignKey
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.models.user_branch_link import UserBranchLink

if TYPE_CHECKING:
    from app.models.user import User


class Branch(SQLModel, table=True):
    __tablename__ = "branch"
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True))
    )

    # NEW: User who created the branch
    created_by_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    )
    created_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    users: list["User"] = Relationship(
        back_populates="branches", link_model=UserBranchLink
    )
    user_branch_links: list["UserBranchLink"] = Relationship(back_populates="branch")