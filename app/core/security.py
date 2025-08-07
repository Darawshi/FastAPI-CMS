# app/core/security.py

import re
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from typing import Optional
from starlette.status import HTTP_400_BAD_REQUEST
from app.core.config import get_settings


settings = get_settings()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60000)


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "validate_password_strength",
]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta  # Use timezone.utc
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def validate_password_strength(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter.",
        )

    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter.",
        )

    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit.",
        )

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character.",
        )