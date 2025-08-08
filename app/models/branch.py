#app/models/branch.py
from sqlalchemy import Column, DateTime
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


    users: list["User"] = Relationship(
        back_populates="branches", link_model=UserBranchLink
    )