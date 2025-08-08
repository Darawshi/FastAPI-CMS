# app/routes/auth.py
# This module defines the authentication routes for user login and password reset functionality.

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator
from app.core.dependencies import get_current_user
from app.crud.auth import send_reset_password_token, authenticate_user, reset_user_password, \
    perform_admin_password_reset, change_password_after_reset
from app.models.user import User
from app.schemas.user import UserLogin
from app.schemas.password import PasswordResetRequest, PasswordResetConfirm
from app.core.database import async_session
from app.services.permissions import require_admin_or_senior_editor

router = APIRouter()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

@router.post("/login" ,name="Login")
async def login(user_login: UserLogin, session: AsyncSession = Depends(get_session)):
    return await authenticate_user(user_login.email, user_login.password, session)

@router.post("/request-password-reset",name="Request Reset Password")
async def forgot_password(data: PasswordResetRequest, session: AsyncSession = Depends(get_session)):
    return await send_reset_password_token(data.email, session)

@router.post("/reset-password",name="Reset Password")
async def confirm_reset(data: PasswordResetConfirm, session: AsyncSession = Depends(get_session)):
    return await reset_user_password(data.token, data.new_password, session)

@router.post("/admin-reset-user-password/{user_id}", name="Admin Reset User Password")
async def reset_user_password_by_admin(user_id: UUID, session: AsyncSession = Depends(get_session) ,
    current_user: User = Depends(require_admin_or_senior_editor)):
    return await perform_admin_password_reset(user_id,current_user, session)

@router.post("/change-password", name="Change Password After Admin Reset")
async def change_password(data: PasswordResetConfirm, session: AsyncSession = Depends(get_session),current_user: User = Depends(get_current_user)):
    return await change_password_after_reset( data.new_password,current_user, session)
