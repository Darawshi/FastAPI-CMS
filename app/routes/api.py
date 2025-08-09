# app/routes/api.py
from fastapi import APIRouter

from app.routes import auth, users, branch, user_branch_link

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/user", tags=["users"])
api_router.include_router(branch.router, prefix="/branch", tags=["branches"])
api_router.include_router(user_branch_link.router, prefix="/user-branch-link", tags=["user branch links"])
