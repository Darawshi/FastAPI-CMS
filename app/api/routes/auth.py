from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator
from app.crud.auth import send_reset_password_token, authenticate_user, reset_user_password
from app.schemas.user import UserLogin
from app.schemas.password import PasswordResetRequest, PasswordResetConfirm
from app.core.database import async_session


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
