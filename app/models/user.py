from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.orm import validates, Mapped, mapped_column, Relationship, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, DateTime, ForeignKey
from datetime import datetime, timezone

from app.models.password_reset_token import PasswordResetToken
from app.models.user_role import UserRole
from app.models.user_branch_link import UserBranchLink

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.branch import Branch



class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        unique=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    role: Mapped[UserRole] = mapped_column(
        nullable=False, default=UserRole.editor, index=True
    )

    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)
    must_change_password: Mapped[bool] = mapped_column(nullable=False, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    user_pic: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)

    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Relationships
    created_by: Mapped[Optional["User"]] = Relationship(
        "User",
        back_populates="users_created",
        remote_side=[id],
        lazy = "selectin"
    )
    users_created: Mapped[List["User"]] = Relationship(
        "User",
        back_populates="created_by",
        cascade="save-update, merge"
    )

    reset_tokens: Mapped[List[PasswordResetToken]] = Relationship(back_populates="user")

    branches: Mapped[List["Branch"]] = relationship(
        "Branch",
        secondary="user_branch_link",
        back_populates="users",
        overlaps="user_branch_links,user,branch",
        lazy="selectin",
    )
    user_branch_links: Mapped[List[UserBranchLink]] = relationship(
        "UserBranchLink",
        back_populates="user",
        lazy="selectin",
        overlaps="branches,user,branch"
    )

    @validates("email")
    def normalize_email(self, _, address: str) -> str:
        return str(address).lower()

    @property
    def branch_ids(self) -> List[UUID]:
        return [link.branch_id for link in self.user_branch_links]