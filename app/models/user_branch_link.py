# app/models/user_branch_link.py
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID
if TYPE_CHECKING:
    from app.models.branch import Branch
    from app.models.user import User


class UserBranchLink(SQLModel, table=True):
    __tablename__ = "user_branch_link"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    branch_id: UUID = Field(foreign_key="branch.id", primary_key=True)

    user: Optional["User"] = Relationship(back_populates="user_branch_links")
    branch: Optional["Branch"] = Relationship(back_populates="user_branch_links")