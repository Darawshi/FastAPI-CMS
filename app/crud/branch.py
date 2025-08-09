#app/crud/branch.py

from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.branch import Branch
from app.models.user import User
from app.models.user_branch_link import UserBranchLink
from app.schemas.branch import BranchCreate, BranchUpdate


async def create_branch(session: AsyncSession, branch_in: BranchCreate, current_user: User) -> Branch:
    branch = Branch.model_validate(branch_in)
    branch.created_by_id = current_user.id  # NEW
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch

async def get_branch_by_id(session: AsyncSession, branch_id: UUID) -> Branch:
    result = await session.execute(
        select(Branch).where(Branch.id == branch_id)
    )
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch

async def get_all_branches(session: AsyncSession) -> list[Branch]:
    result = await session.execute(select(Branch))
    return list(result.scalars().all())

async def update_branch(session: AsyncSession, branch_id: UUID, branch_in: BranchUpdate) -> Branch:
    branch = await get_branch_by_id(session, branch_id)
    branch_data = branch_in.model_dump(exclude_unset=True)
    for key, value in branch_data.items():
        setattr(branch, key, value)
    session.add(branch)
    await session.commit()
    await session.refresh(branch)
    return branch

async def delete_branch(session: AsyncSession, branch_id: UUID) -> None:
    # Check if branch exists
    branch = await get_branch_by_id(session, branch_id)

    # Check for linked users
    result = await session.execute(
        select(UserBranchLink).where(UserBranchLink.branch_id == branch_id)
    )
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete branch with linked users"
        )

    await session.delete(branch)
    await session.commit()
