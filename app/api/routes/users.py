# app/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.schemas.user import UserRead
from app.core.dependencies import get_current_user
router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_own_profile(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = select(User).where(User.id == current_user.id)
    result = await session.exec(statement)
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
