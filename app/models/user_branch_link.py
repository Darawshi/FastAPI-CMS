# app/models/user_branch_link.py
from sqlmodel import SQLModel, Field
from uuid import UUID


class UserBranchLink(SQLModel, table=True):
    __tablename__ = "user_branch_link"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    branch_id: UUID = Field(foreign_key="branch.id", primary_key=True)