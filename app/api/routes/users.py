# app/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from uuid import UUID
from app.crud.user import create_user, delete_user_by_id, update_user, get_users, update_user_by_id, \
    deactivate_user_by_id, reactivate_user_by_id
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate, UserCreate
from app.core.dependencies import get_current_user, get_session, require_admin
from app.models.user_role import UserRole


router = APIRouter()


@router.get("/me", response_model=UserRead ,name="Profile")
async def read_own_profile(
    current_user: User = Depends(get_current_user),
):
    # No need to query the database, current_user is already populated
    return current_user


@router.patch("/me/update", response_model=UserRead,name="Update My Profile")
async def update_own_profile(
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await update_user(session, current_user, user_update)

@router.post("/create", response_model=UserRead,name="Admin Create User")
async def create_user_admin(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(require_admin),
):
    return await create_user(session, user_create)

@router.get("/all", response_model=List[UserRead],name="Admin List Users")
async def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    return await get_users(session, offset, limit, role, is_active)


@router.patch("/{user_id}", response_model=UserRead , name="Admin Update User")
async def update_user_admin(
    user_id: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    return await update_user_by_id(session, user_id, user_update)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,name="Admin Delete User")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    await delete_user_by_id(session, user_id)


@router.post("/deactivate/{user_id}", response_model=UserRead,name="Admin Deactivate User")
async def deactivate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    return await deactivate_user_by_id(session, user_id)


@router.post("/reactivate/{user_id}", response_model=UserRead,name="Admin Reactivate User")
async def reactivate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    return await reactivate_user_by_id(session, user_id)



@router.post("/first_admin", response_model=UserRead, name="Create First Admin")
async def create_first_admin(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_session),
):
    # Check if email exists
    normalized_email = str(user_create.email).lower()  # normalize
    result = await session.execute(select(User).where(User.email == normalized_email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await create_user(session, user_create)