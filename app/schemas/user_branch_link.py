# app/schemas/user_branch_link.py

from uuid import UUID
from pydantic import BaseModel

class UserBranchLinkBase(BaseModel):
    user_id: UUID
    branch_id: UUID

class UserBranchLinkCreate(UserBranchLinkBase):
    pass

class UserBranchLinkRead(UserBranchLinkBase):
    pass