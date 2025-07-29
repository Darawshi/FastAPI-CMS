from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator
from app.schemas.user import UserLogin
from app.schemas.password import ForgotPasswordRequest, ResetPasswordRequest
from app.core.database import async_session

from app.crud import auth as auth_crud
router = APIRouter()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

@router.post("/login")
async def login(user_login: UserLogin, session: AsyncSession = Depends(get_session)):
    return await auth_crud.authenticate_user(user_login.email, user_login.password, session)

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    return await auth_crud.send_reset_password_token(data.email, session)

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    return await auth_crud.reset_user_password(data.token, data.new_password, session)
