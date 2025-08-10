# App/crud/user.py
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.crud.user_branch_link import add_user_to_branch, remove_all_branches_for_user, get_branches_for_user, \
    remove_user_from_branch
from app.models.user import User
from app.models.user_branch_link import UserBranchLink
from app.models.user_role import UserRole
from app.schemas.user import UserCreate, UserUpdate, UserUpdateBase
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.services.image_service import process_user_profile_image_upload
from fastapi import status
from app.services.permissions import get_user_visibility_condition, get_role_order, user_has_permission




async def get_users(session: AsyncSession,current_user: User,offset: int = 0,limit: int = 20,role: Optional[UserRole] = None,is_active: Optional[bool] = None,) -> List[User]:
    try:
        stmt = select(User).where(
            get_user_visibility_condition(current_user)
        ).options(selectinload(User.user_branch_links).selectinload(UserBranchLink.branch))
        # Apply optional filters
        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

            # Order and paginate
        stmt = stmt.order_by(get_role_order()).offset(offset).limit(limit)

        result = await session.execute(stmt)
        users = result.scalars().all()
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        return list(users)

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user retrieval"
        ) from e

async def get_user_by_id(session: AsyncSession,current_user: User, user_id: UUID) -> Optional[User]:
     try:
        # Fetch the requested user
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.user_branch_links).selectinload(UserBranchLink.branch))
        )
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
                status_code=403,
                detail="Unauthorized access"
            )
        return user
     except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during user retrieval"
        ) from e

async def create_user(session: AsyncSession, user_create: UserCreate ,created_by_id: Optional[UUID] = None ) -> User:
    try:
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
        await session.commit()
        await session.refresh(db_user, ["user_branch_links"])
        # Handle branch links if provided
        if user_create.branch_ids:
            for branch_id in user_create.branch_ids:
                await add_user_to_branch(session, db_user.id, branch_id)
        return db_user
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Create failed due to a constraint violation.") from e
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error during user creation") from e


# noinspection PyUnreachableCode
async def update_user(session: AsyncSession,db_user: User,user_update: UserUpdateBase,file: Optional[UploadFile] = None) -> User:
    try:
        update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)

        # Check for email conflict
        new_email = update_data.get("email")
        if new_email and new_email != db_user.email:
            # Normalize the email (just in case)
            normalized_email = str(new_email).lower()
            existing_user = (await session.execute(select(User).where(User.email == normalized_email))).scalar_one_or_none()

            if existing_user and existing_user.id != db_user.id:
                raise HTTPException(status_code=400, detail="Email is already in use by another user")

            # Set the normalized email
            update_data["email"] = normalized_email

        # Extract branch_ids from update_data (if present)
        branch_ids = update_data.pop("branch_ids", None)

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
        # Sync branch links if branch_ids provided
        if branch_ids is not None:
            current_branches = await get_branches_for_user(session, db_user.id)
            current_branch_ids = {branch.id for branch in current_branches}
            new_branch_ids = set(branch_ids)

            for branch_id in new_branch_ids - current_branch_ids:
                await add_user_to_branch(session, db_user.id, branch_id)
            for branch_id in current_branch_ids - new_branch_ids:
                await remove_user_from_branch(session, db_user.id, branch_id)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user, ["user_branch_links"])


        return db_user
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to a constraint violation.") from e
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error during user update") from e

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    try:
        normalized_email = email.lower().strip()
        result = await session.execute(select(User).where(User.email == normalized_email))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error during email lookup") from e

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

        # After fetching user and before deleting user:
        await remove_all_branches_for_user(session, user_id)  # delete all links
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
    try:
        user: User = await session.get(User, user_id)  # type: ignore
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_active = is_active
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Operation failed due to a constraint violation.") from e
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error during user update") from e

async def deactivate_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    return await set_user_active_status(session, user_id, False)

async def reactivate_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    return await set_user_active_status(session, user_id, True)

async def update_user_by_id(session: AsyncSession,user_id: UUID,user_update: UserUpdate,) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await update_user(session, user, user_update) # type: ignore