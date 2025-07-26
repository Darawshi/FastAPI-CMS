from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import EmailStr
from app.models.user_role import UserRole
from sqlmodel import SQLModel


# Shared base for all user-related schemas
class UserBase(SQLModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.editor
    is_active: bool = True


# Used when creating a user (e.g. during registration or admin creation)
class UserCreate(UserBase):
    password: str


# Used when reading a user object (e.g. for GET responses)
class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Used when updating an existing user
class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# Used internally for authentication (login input)
class UserLogin(SQLModel):
    email: EmailStr
    password: str
