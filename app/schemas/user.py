from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import EmailStr, constr, field_validator

from app.models.user import User
from app.models.user_role import UserRole
from sqlmodel import SQLModel


# Shared base for all user-related schemas
class UserBase(SQLModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.senior_editor
    is_active: bool = True


# Used when creating a user (e.g. during registration or admin creation)
class UserCreate(UserBase):
    password: constr(min_length=8)
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

    class Config:
        orm_mode = True


class UserUpdateBase(SQLModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[constr(min_length=8)] = None

    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip() if v else v

class UserUpdateOwn(UserUpdateBase):
    pass

class UserUpdate(UserUpdateBase):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

# Used internally for authentication (login input)
class UserLogin(SQLModel):
    email: EmailStr
    password: str
