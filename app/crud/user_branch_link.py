# app/crud/user_branch_link.py
from typing import List
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.branch import Branch
from app.models.user import User
from app.models.user_branch_link import UserBranchLink

# Add link between user and branch
async def add_user_to_branch(session: AsyncSession, user_id: UUID, branch_id: UUID) -> UserBranchLink:
    # Ensure link doesn't already exist
    stmt = select(UserBranchLink).where(
        UserBranchLink.user_id == user_id,
        UserBranchLink.branch_id == branch_id
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing  # Or raise an HTTPException if you want to prevent duplicates

    link = UserBranchLink(user_id=user_id, branch_id=branch_id)
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link
# Remove link between user and branch
async def remove_user_from_branch(session: AsyncSession,user_id: UUID,branch_id: UUID) -> None:
    stmt = select(UserBranchLink).where(
        UserBranchLink.user_id == user_id,
        UserBranchLink.branch_id == branch_id
    )
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    if link:
        await session.delete(link)
        await session.commit()
# Get all branches for a user
async def get_branches_for_user(session: AsyncSession,user_id: UUID):
    stmt = select(Branch).join(UserBranchLink).where(UserBranchLink.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()
# Get all users in a branch
async def get_users_in_branch(session: AsyncSession, branch_id: UUID) -> List[User]:
    stmt = select(User).join(UserBranchLink).where(UserBranchLink.branch_id == branch_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())
# Check if a user is in a specific branch
async def is_user_in_branch(session: AsyncSession, user_id: UUID, branch_id: UUID) -> bool:
    stmt = select(UserBranchLink).where(
        UserBranchLink.user_id == user_id,
        UserBranchLink.branch_id == branch_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None
# Remove all branches for a user
async def remove_all_branches_for_user(session: AsyncSession, user_id: UUID) -> None:
    stmt = delete(UserBranchLink).where(UserBranchLink.user_id == user_id)
    await session.execute(stmt)
    await session.commit()