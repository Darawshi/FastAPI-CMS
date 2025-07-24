from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from app.models.user_role import UserRole


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.editor_user)
    is_active: bool = Field(default=True)
