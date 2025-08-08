# app/schemas/branch.py
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BranchBase(BaseModel):
    name: str
    description: Optional[str] = None


class BranchCreate(BranchBase):
    pass


class BranchRead(BranchBase):
    id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class BranchUpdate(BranchBase):
    name: Optional[str] = None
    description: Optional[str] = None