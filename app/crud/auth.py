# app/crud/auth.py
from sqlmodel import select
from app.core.email_utils import send_email
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    decode_access_token,
)


async def authenticate_user(email: str, password: str, session: AsyncSession):
    normalized_email = email.lower().strip()
    result = await session.execute(select(User).where(User.email == normalized_email))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    now = datetime.now(timezone.utc)
    user.last_login = now
    user.updated_at = now
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


async def send_reset_password_token(email: str, session: AsyncSession):
    normalized_email = email.lower().strip()
    result = await session.execute(select(User).where(User.email == normalized_email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token(
        data={"sub": str(user.id), "purpose": "reset"},
        expires_delta=timedelta(minutes=15)
    )

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


async def reset_user_password(token: str, new_password: str, session: AsyncSession):
    payload = decode_access_token(token)
    if not payload or payload.get("purpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_id_from_token = payload.get("sub")
    if not user_id_from_token:
        raise HTTPException(status_code=400, detail="Invalid token")

    try:
        user_id = UUID(user_id_from_token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_password)
    session.add(user)
    await session.commit()
    return {"message": "Password reset successful"}
