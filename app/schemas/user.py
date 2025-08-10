# app/schemas/user.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID

from app.models.user_role import UserRole
from .common import PasswordType


# Shared base for all user-related schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.senior_editor
    is_active: bool = True
    branch_ids: Optional[List[UUID]] = None  # << Add this
    model_config = {
        "from_attributes": True
    }

# Used when creating a user (e.g. during registration or admin creation)
class UserCreate(UserBase):
    password:str = PasswordType
    # noinspection PyMethodFirstArgAssignment
    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()  # Normalize email to lowercase and strip whitespace


# Used when reading a user object (e.g. for GET responses)
class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    user_pic: Optional[str]
    branch_ids: Optional[List[UUID]] = None
    model_config = {
        "from_attributes": True
    }


class UserUpdateBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[PasswordType] = None  # ✅ This works
    branch_ids: Optional[List[UUID]] = None
    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip() if v else v

    model_config = {
        "from_attributes": True
    }

class UserUpdateOwn(UserUpdateBase):
    pass

class UserUpdate(UserUpdateBase):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

# Used internally for authentication (login input)
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    model_config = {
        "from_attributes": True
    }