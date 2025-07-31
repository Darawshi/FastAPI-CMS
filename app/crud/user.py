from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select, desc
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserUpdateOwn
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password



async def get_users(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 10,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
) -> List[User]:
    statement = select(User)
    if role is not None:
        statement = statement.where(User.role == role)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    statement = statement.order_by(desc(User.created_at)).offset(offset).limit(limit)
    result = await session.execute(statement)
    users: List[User] = list(result.scalars().all())
    return users

async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    normalized_email = str(user_create.email).lower().strip()  # normalize email
    existing = await get_user_by_email(session, normalized_email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        email=normalized_email,
        full_name=user_create.full_name,
        role=user_create.role,
        is_active=user_create.is_active,
        hashed_password=hash_password(user_create.password),
    )
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

async def update_user(session: AsyncSession, db_user: User, user_update: UserUpdate) -> User:
    update_data = user_update.model_dump(exclude_unset=True)

    # Check for email conflict
    new_email = update_data.get("email")
    if new_email and new_email != db_user.email:
        # Normalize the email (just in case)
        normalized_email = str(new_email).lower()
        result = await session.execute(select(User).where(User.email == normalized_email))
        existing_user = result.scalar_one_or_none()

        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(status_code=400, detail="Email is already in use by another user")

        # Set the normalized email
        update_data["email"] = normalized_email

    # Apply updates
    for key, value in update_data.items():
        if key == "password" and value is not None:
            db_user.hashed_password = hash_password(value)
        elif key != "password":
            setattr(db_user, key, value)

    db_user.updated_at = datetime.now(timezone.utc)

    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to a constraint violation.")


async def update_own_user(
        session: AsyncSession,
        db_user: User,
        user_update: UserUpdateOwn  # Use restricted schema
) -> User:
    update_data = user_update.model_dump(exclude_unset=True)

    # Existing security checks
    new_email = update_data.get("email")
    if new_email and new_email != db_user.email:
        normalized_email = str(new_email).lower()
        result = await session.execute(select(User).where(User.email == normalized_email))
        existing_user = result.scalar_one_or_none()
        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(status_code=400, detail="Email is already in use")
        update_data["email"] = normalized_email

    # Apply updates
    for key, value in update_data.items():
        if key == "password" and value is not None:
            db_user.hashed_password = hash_password(value)
        elif key != "password":
            setattr(db_user, key, value)

    db_user.updated_at = datetime.now(timezone.utc)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    normalized_email = email.lower().strip()
    result = await session.execute(select(User).where(User.email == normalized_email))
    return result.scalars().first()

async def update_user_by_id(
    session: AsyncSession,
    user_id: UUID,
    user_update: UserUpdate,
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await update_user(session, user, user_update)

async def delete_user_by_id(session: AsyncSession, user_id: UUID) -> None:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()

async def set_user_active_status(
    session: AsyncSession,
    user_id: UUID,
    is_active: bool
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def deactivate_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    return await set_user_active_status(session, user_id, False)

async def reactivate_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    return await set_user_active_status(session, user_id, True)