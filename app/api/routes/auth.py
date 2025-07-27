from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import timedelta, datetime, timezone
from typing import AsyncGenerator

from app.models.user_role import UserRole
from app.schemas.user import UserCreate, UserRead, UserLogin
from app.schemas.password import ForgotPasswordRequest, ResetPasswordRequest
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.database import async_session
from app.core.email_utils import send_email
from uuid import UUID

router = APIRouter()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


@router.post("/register", response_model=UserRead)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == user_create.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hash_password(user_create.password),
        role=user_create.role or UserRole.editor
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login")
async def login(user_login: UserLogin, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == user_login.email))
    user = result.scalars().first()

    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update times with timezone-aware datetime
    now = datetime.now(timezone.utc)
    user.last_login = now
    user.updated_at = now
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}



@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token(
        data={"sub": str(user.id), "purpose": "reset"},
        expires_delta=timedelta(minutes=15)
    )

    # Compose email
    subject = "Password Reset Request"
    body = (
        f"Hello {user.full_name},\n\n"
        f"To reset your password, use the following token (valid for 15 minutes):\n\n"
        f"{token}\n\n"
        "If you didn’t request this, you can ignore this email.\n\n"
        "Best regards,\nYour Support Team"
    )

    await send_email(subject=subject, to_email=user.email, body=body)

    return {"message": "Reset token sent to your email"}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    payload = decode_access_token(data.token)
    if not payload or payload.get("purpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Get the user ID from the token payload
    user_id_from_token = payload.get("sub")  # This was missing in your code
    if not user_id_from_token:
        raise HTTPException(status_code=400, detail="Invalid token")

    try:
        user_id = UUID(user_id_from_token)  # Convert string to UUID
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    # Now query using the UUID
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    session.add(user)
    await session.commit()

    return {"message": "Password reset successful"}
