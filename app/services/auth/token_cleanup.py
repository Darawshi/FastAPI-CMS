# app/services/token_cleanup.py
from typing import  Callable
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.password_reset_token import PasswordResetToken

async def delete_expired_tokens(session: AsyncSession) -> Callable[[], int]:
    stmt = delete(PasswordResetToken).where(
        PasswordResetToken.expires_at < func.now()
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount  # ✅ This is an intis is an int



