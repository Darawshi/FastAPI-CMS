from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select
from app.models.user import User
from app.core.security import decode_access_token
from app.core.database import async_session
from sqlmodel.ext.asyncio.session import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with async_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
