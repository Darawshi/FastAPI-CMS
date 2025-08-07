# app/crud/auth.py
import secrets
from uuid import UUID

from pydantic import EmailStr
from sqlmodel import select
from app.core.config import get_settings
from app.core.email_utils import send_email
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from app.crud.user import get_user_by_email, get_user_by_id
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    validate_password_strength,
)
from app.services.auth.rate_limiter import can_request_reset, mark_reset_requested
from app.services.permissions import user_has_permission

settings = get_settings()
RESET_LINK_BASE = settings.RESET_LINK_BASE
RESET_TOKEN_LIFETIME_MINUTES = settings.RESET_TOKEN_LIFETIME_MINUTES
ONE_TIME_PASSWORD = settings.ONE_TIME_PASSWORD


async def authenticate_user(email: EmailStr, password: str, session: AsyncSession):
    normalized_email = str(email).lower().strip()
    result = await session.execute(select(User).where(User.email == normalized_email))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if user.must_change_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password reset required. Please change your password.")

    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

async def send_reset_password_token(email: EmailStr, session: AsyncSession):
    normalized_email = str(email).lower().strip()
    if not await can_request_reset(normalized_email):
        raise HTTPException(status_code=429, detail="Too many password reset requests. Please wait before retrying.")
    user = await get_user_by_email( session ,normalized_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate secure token
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_LIFETIME_MINUTES)
    # Save token in DB
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
    )
    session.add(reset_token)
    await session.commit()

    reset_url = f"{RESET_LINK_BASE}{token}"
    subject = "Password Reset Request"
    body = (
        f"Hello {user.full_name},\n\n"
        f"To reset your password, Click the link below to reset your password: (valid for {RESET_TOKEN_LIFETIME_MINUTES} minutes):\n\n"
        f"{reset_url}\n\n"
        "If you didn’t request this, you can ignore this email.\n\n"
        "Best regards,\nYour Support Team"
    )

    await send_email(subject=subject, to_email=user.email, body=body)
    # Mark reset as requested
    await mark_reset_requested(normalized_email)
    return {"message": "Reset token sent to your email"}

async def reset_user_password(token: str, new_password: str, session: AsyncSession):
    validate_password_strength(new_password)
    user = await get_user_by_reset_token(token, session)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    user.hashed_password = hash_password(new_password)
    # Delete all reset tokens for this user
    await session.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))# type: ignore

    await session.commit()
    return {"message": "Password reset successful"}

async def change_password_after_reset(new_password: str,current_user: User, session: AsyncSession):
    validate_password_strength(new_password)
    user = await get_user_by_id(session, current_user,current_user.id)
    user.hashed_password = hash_password(new_password)
    # Delete all reset tokens for this user
    await session.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))# type: ignore

    await session.commit()
    return {"message": "Password reset successful"}



async def get_user_by_reset_token(token: str, session: AsyncSession) -> User | None:
    result = await session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        )
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        return None

    user_result = await session.execute(
        select(User).where(User.id == token_record.user_id)
    )
    return user_result.scalar_one_or_none()

async def perform_admin_password_reset(user_id: UUID, current_user: User,session: AsyncSession) -> dict:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        # Apply visibility rules
    if not user_has_permission(current_user, user):
        raise HTTPException(
            status_code=403,
            detail="Unauthorized access"
        )
    # Set new one-time password
    one_time_password = ONE_TIME_PASSWORD
    user.hashed_password = hash_password(one_time_password)
    user.must_change_password = True

    await session.commit()

    # Send email notification
    await send_email(
        subject="Your password was reset by an admin",
        to_email=user.email,
        body=(
            f"Hello {user.full_name},\n\n"
            "Your account password has been reset by an administrator.\n"
            f"Your new one-time password is: {one_time_password}\n\n"
            "You must change your password after logging in.\n\n"
            "Best regards,\n"
            "Your CMS Team"
        )
    )

    return {"message": f"Password for user {user.email} reset successfully."}