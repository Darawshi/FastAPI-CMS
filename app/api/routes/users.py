# app/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from uuid import UUID
from datetime import datetime, timezone
from app.crud.user import create_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate, UserCreate
from app.core.dependencies import get_current_user, get_session
from app.models.user_role import UserRole
from app.core.security import hash_password


router = APIRouter()


def apply_user_update(user: User, user_update: UserUpdate) -> None:
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value is not None:
            setattr(user, "hashed_password", hash_password(value))
        elif field != "password":
            setattr(user, field, value)
    # Add this line to update the timestamp
    user.updated_at = datetime.now(timezone.utc)



@router.get("/me", response_model=UserRead)
async def read_own_profile(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = select(User).where(User.id == current_user.id)
    result = await session.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me/update", response_model=UserRead)
async def update_own_profile(
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    apply_user_update(current_user, user_update)
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.get("/", response_model=List[UserRead])
async def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    statement = select(User)
    if role is not None:
        statement = statement.where(User.role == role)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)

    statement = statement.offset(offset).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()


@router.patch("/{user_id}", response_model=UserRead)
async def update_user_admin(
    user_id: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    statement = select(User).where(User.id == user_id)
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    apply_user_update(user, user_update)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/", response_model=UserRead)
async def create_user_admin(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Check if email exists
    result = await session.execute(select(User).where(User.email == user_create.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(session, user_create)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()
    return


@router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/{user_id}/reactivate", response_model=UserRead)
async def reactivate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.post("/first_admin", response_model=UserRead)
async def create_first_admin(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_session),
):
    # Check if email exists
    result = await session.execute(select(User).where(User.email == user_create.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(session, user_create)