# app/routes/user_branch_link.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.models.user import User
from app.schemas.user import UserRead
from app.schemas.branch import BranchRead
from app.crud.user_branch_link import (
    add_user_to_branch,
    remove_user_from_branch,
    get_branches_for_user,
    get_users_in_branch,
    is_user_in_branch,
    remove_all_branches_for_user,
)
from app.schemas.user_branch_link import UserBranchLinkRead
from app.services.permissions import require_admin_or_senior_editor

router = APIRouter()


@router.post(
    "/add",
    response_model=UserBranchLinkRead,
    status_code=status.HTTP_201_CREATED,
    name="Add User to Branch"
)
async def add_link(
    user_id: UUID = Query(...),
    branch_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor),
):
    existing = await is_user_in_branch(session, user_id, branch_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already linked to this branch"
        )
    link = await add_user_to_branch(session, user_id, branch_id)
    return UserBranchLinkRead(user_id=link.user_id, branch_id=link.branch_id)


@router.delete(
    "/remove",
    response_model=UserBranchLinkRead,
    name="Remove User from Branch"
)
async def remove_link(
    user_id: UUID = Query(...),
    branch_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor),
):
    existing = await is_user_in_branch(session, user_id, branch_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not linked to this branch"
        )
    await remove_user_from_branch(session, user_id, branch_id)
    return UserBranchLinkRead(user_id=user_id, branch_id=branch_id)


@router.get(
    "/branches/{user_id}",
    response_model=List[BranchRead],
    name="Get Branches for User"
)
async def list_branches_for_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor),
):
    branches = await get_branches_for_user(session, user_id)
    return branches


@router.get(
    "/users/{branch_id}",
    response_model=List[UserRead],
    name="Get Users in Branch"
)
async def list_users_in_branch(
    branch_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor),
):
    users = await get_users_in_branch(session, branch_id)
    return users


@router.delete(
    "/remove-all/{user_id}",
    response_model=dict,
    name="Remove All Branches for User"
)
async def remove_all_branches(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin_or_senior_editor),
):
    await remove_all_branches_for_user(session, user_id)
    return {"detail": f"All branches removed for user {user_id}"}
