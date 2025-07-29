from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, Optional
from datetime import datetime, timezone
from app.models.user import User
from app.core.security import decode_access_token
from app.core.database import async_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
async def get_current_user(token: str = Depends(oauth2_scheme),session: AsyncSession = Depends(get_session)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Use session.execute() instead of session.exec()
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    user: Optional[User] = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    # 🔄 Update last_login
    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    return user
