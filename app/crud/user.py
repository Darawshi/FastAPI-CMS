from typing import Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await session.exec(select(User).where(User.id == user_id))
    return result.first()


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.exec(select(User).where(User.email == email))
    return result.first()


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    db_user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        role=user_create.role,
        is_active=user_create.is_active,
        hashed_password=get_password_hash(user_create.password),
    )
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise


async def update_user(session: AsyncSession, db_user: User, user_update: UserUpdate) -> User:
    for key, value in user_update.dict(exclude_unset=True).items():
        if key == "password":
            db_user.hashed_password = get_password_hash(value)
        else:
            setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def delete_user(session: AsyncSession, db_user: User) -> None:
    await session.delete(db_user)
    await session.commit()
