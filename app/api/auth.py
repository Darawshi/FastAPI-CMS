from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.user import UserCreate, UserRead, UserLogin
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.database import async_session
from sqlmodel import select
from app.schemas.password import ForgotPasswordRequest, ResetPasswordRequest
from datetime import timedelta


router = APIRouter()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@router.post("/register", response_model=UserRead)
async def register(user_create: UserCreate, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email == user_create.email)
    result = await session.exec(statement)
    existing_user = result.first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hash_password(user_create.password),
        role=user_create.role or "editor_user"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login")
async def login(user_login: UserLogin, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email == user_login.email)
    result = await session.exec(statement)
    user = result.first()

    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.email == data.email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token(
        data={"sub": str(user.id), "purpose": "reset"},
        expires_delta=timedelta(minutes=15)
    )

    # In real app: send this token via email
    return {"reset_token": token, "expires_in": 900}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    payload = decode_access_token(data.token)
    if not payload or payload.get("purpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token")

    result = await session.exec(select(User).where(User.id == user_id))
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    session.add(user)
    await session.commit()

    return {"message": "Password reset successful"}
