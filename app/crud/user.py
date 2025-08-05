from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserUpdateBase
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.services.image_service import process_user_profile_image_upload
from fastapi import status




from app.services.permissions import get_user_visibility_condition, get_role_order, user_has_permission

async def get_users(session: AsyncSession,current_user: User,offset: int = 0,limit: int = 20,role: Optional[UserRole] = None,is_active: Optional[bool] = None,) -> List[User]:
    stmt = select(User).where(
        get_user_visibility_condition(current_user)
    )
    # Apply optional filters
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

        # Order and paginate
    stmt = stmt.order_by(get_role_order()).offset(offset).limit(limit)

    result = await session.execute(stmt)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return list(result.scalars().all())

async def get_user_by_id(session: AsyncSession,current_user: User, user_id: UUID) -> Optional[User]:
    # Fetch the requested user
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Apply visibility rules
    if not user_has_permission(current_user, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

async def create_user(session: AsyncSession, user_create: UserCreate ,created_by_id: Optional[UUID] = None ) -> User:
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
        created_by_id=created_by_id,  # 🟢 new line
    )
    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Create failed due to a constraint violation.")

async def update_user(session: AsyncSession,db_user: User,user_update: UserUpdateBase,file: Optional[UploadFile] = None) -> User:

    update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)

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

    # Process image if uploaded
    if file:
        filename = await process_user_profile_image_upload(file, db_user, session)
        db_user.user_pic = filename
    db_user.updated_at = datetime.now(timezone.utc)

    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
        return db_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to a constraint violation.")

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    normalized_email = email.lower().strip()
    result = await session.execute(select(User).where(User.email == normalized_email))
    return result.scalars().first()

async def update_user_by_id(session: AsyncSession,user_id: UUID,user_update: UserUpdate,) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await update_user(session, user, user_update) # type: ignore

async def delete_user_by_id(session: AsyncSession, current_user: User, user_id: UUID) -> None:
    try:
        # Get visibility condition (same as in GET "all" route)
        visibility_condition = get_user_visibility_condition(current_user)

        # Create select query with visibility filter
        stmt = (
            select(User)
            .where(User.id == user_id)
            .where(visibility_condition)
        )

        # Execute query
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Maintain 404 for consistency - don't reveal existence of hidden users
            raise HTTPException(status_code=404, detail="User not found")

        await session.delete(user)
        await session.commit()

    except IntegrityError as e:
        # Handle constraint violations specifically
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cannot delete user due to related resources"
        ) from e

    except SQLAlchemyError as e:
        # General database failures
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error while deleting user"
        ) from e

async def set_user_active_status(session: AsyncSession,user_id: UUID,is_active: bool) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user   # type: ignore

async def deactivate_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    return await set_user_active_status(session, user_id, False)

async def reactivate_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    return await set_user_active_status(session, user_id, True)


"""
async def update_own_user(
        session: AsyncSession,
        db_user: User,
        user_update: UserUpdateOwn , # Use restricted schema
        file: Optional[UploadFile] = None) -> User:
    update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)

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


    # Process image if uploaded
    if file:
        filename = await process_user_profile_image_upload(file, db_user, session)
        db_user.user_pic = filename
    db_user.updated_at = datetime.now(timezone.utc)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user
"""