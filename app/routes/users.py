# app/routes/users.py
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form
from typing import List, Optional

from pydantic import EmailStr, constr
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.crud.user import create_user, delete_user_by_id, get_users, update_user_by_id, \
    deactivate_user_by_id, reactivate_user_by_id, get_user_by_id, update_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate, UserCreate, UserUpdateOwn
from app.core.dependencies import get_current_user, get_session
from app.models.user_role import UserRole
from app.services.image_service import  process_user_profile_image_upload
from app.services.permissions import validate_user_creation_permissions, \
    validate_user_update_permissions, validate_user_deactivate_reactivate, \
    require_admin_or_senior_editor_or_editor, \
    require_admin_or_senior_editor_or_editor_or_category_editor, prevent_self_action_on_user

router = APIRouter()


@router.post("/first_admin", response_model=UserRead, name="Create First Admin")
async def create_first_admin(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_session),
):
    return await create_user(session, user_create)

@router.post("/create", response_model=UserRead,name="Create User")
async def add_user(
        user_create: UserCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(require_admin_or_senior_editor_or_editor),
):
    validate_user_creation_permissions(current_user, user_create)
    return await create_user(session, user_create , created_by_id=current_user.id)

@router.get("/me", response_model=UserRead ,name="Profile")
async def read_own_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.patch("/me/update", response_model=UserRead, name="Update My Profile")
async def update_own_profile(
    email: Optional[EmailStr] = Form(None),
    full_name: Optional[str] = Form(None),
    password: Optional[constr(min_length=8)] = Form(None),
    file: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Create schema instance for validation
    user_update = UserUpdateOwn(email=email, full_name=full_name, password=password)
    return await update_user(session, current_user, user_update, file)

@router.post("/me/upload-pic", response_model=UserRead, name="upload profile picture")
async def upload_user_pic(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await process_user_profile_image_upload(file, current_user, session)
    return current_user

@router.get("/all", response_model=List[UserRead], name="Users List")
async def list_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor_or_editor_or_category_editor),
):
    users= await get_users(  # Directly return filtered/paginated results
        session=session,
        current_user=current_user,
        offset=offset,
        limit=limit,
        role=role,
        is_active=is_active
    )
    return  users

@router.get("/{user_id}", response_model=UserRead, name="Users by ID")
async def fetch_user_by_id(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor_or_editor_or_category_editor),
):
    user = await get_user_by_id(session,current_user, user_id)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,name="Admin Delete User")
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor_or_editor),
):
    prevent_self_action_on_user(current_user, user_id)
    await delete_user_by_id(session,current_user, user_id)

@router.patch("/{user_id}", response_model=UserRead , name="Update User by ID")
async def update_user_admin(
    user_id: UUID,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor_or_editor),
):
    target_user = await get_user_by_id(session,current_user, user_id)
    validate_user_update_permissions(current_user, target_user)
    return await update_user_by_id(session, user_id, user_update)

@router.post("/deactivate/{user_id}", response_model=UserRead,name="Deactivate User")
async def deactivate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor_or_editor),
):
    # Prevent self-deactivation
    prevent_self_action_on_user(current_user, user_id)
    # Fetch user to deactivate
    target_user = await get_user_by_id(session, current_user,user_id)
    validate_user_deactivate_reactivate(current_user, target_user)
    # Deactivate
    return await deactivate_user_by_id(session, user_id)

@router.post("/reactivate/{user_id}", response_model=UserRead,name="Reactivate User")
async def reactivate_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor_or_editor),
):
    # Prevent self-reactivate
    prevent_self_action_on_user(current_user, user_id)
    # Fetch user to reactivate
    target_user = await get_user_by_id(session,current_user, user_id)
    validate_user_deactivate_reactivate(current_user, target_user)
    return await reactivate_user_by_id(session, user_id)