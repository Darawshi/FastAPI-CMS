# app/routes/branch.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.models.user import User
from app.schemas.branch import BranchCreate, BranchRead, BranchUpdate
from app.crud.branch import (
    create_branch, get_branch_by_id, get_all_branches,
    update_branch, delete_branch,
)
from app.services.permissions import require_admin_or_senior_editor

router = APIRouter()

@router.post("/", response_model=BranchRead, name="Create Branch")
async def create(branch_in: BranchCreate,session: AsyncSession = Depends(get_session),current_user: User = Depends(require_admin_or_senior_editor)):
    return await create_branch(session, branch_in, current_user)

@router.get("/", response_model=list[BranchRead], name="List Branches")
async def list_branches(session: AsyncSession = Depends(get_session),_current_user: User = Depends(require_admin_or_senior_editor)):
    return await get_all_branches(session)

@router.get("/{branch_id}", response_model=BranchRead, name="Get Branch")
async def get_branch(branch_id: UUID, session: AsyncSession = Depends(get_session),_current_user: User = Depends(require_admin_or_senior_editor)):
    branch = await get_branch_by_id(session, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch

@router.patch("/{branch_id}", response_model=BranchRead, name="Update Branch")
async def update(branch_id: UUID, update_data: BranchUpdate, session: AsyncSession = Depends(get_session),_current_user: User = Depends(require_admin_or_senior_editor)):
    branch = await get_branch_by_id(session, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return await update_branch(session, branch_id, update_data)

@router.delete("/{branch_id}", status_code=204, name="Delete Branch")
async def delete(branch_id: UUID, session: AsyncSession = Depends(get_session),_current_user: User = Depends(require_admin_or_senior_editor)):
    branch = await get_branch_by_id(session, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    await delete_branch(session, branch_id)