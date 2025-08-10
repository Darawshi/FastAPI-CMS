#app/crud/branch.py
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.branch import Branch
from app.models.user import User
from app.models.user_branch_link import UserBranchLink
from app.schemas.branch import BranchCreate, BranchUpdate


# CRUD operations for Branch model

# Create a new branch
async def create_branch(session: AsyncSession, branch_in: BranchCreate, current_user: User) -> Branch:
    try:
        branch = Branch.model_validate(branch_in)
        branch.created_by_id = current_user.id
        session.add(branch)
        await session.commit()
        await session.refresh(branch)
        return branch
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch creation failed due to integrity error"
        ) from e
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during branch creation"
        ) from e
# Get a branch by its ID
async def get_branch_by_id(session: AsyncSession, branch_id: UUID) -> Branch:
    try:
        result = await session.execute(
            select(Branch).where(Branch.id == branch_id)
        )
        branch = result.scalar_one_or_none()
        if not branch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        return branch
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during branch retrieval"
        ) from e
# Get all branches
async def get_all_branches(session: AsyncSession) -> List[Branch]:
    try:
        result = await session.execute(select(Branch))
        return list(result.scalars().all())
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during retrieving branches"
        ) from e
# Update an existing branch
async def update_branch(session: AsyncSession, branch_id: UUID, branch_in: BranchUpdate) -> Branch:
    try:
        branch = await get_branch_by_id(session, branch_id)
        branch_data = branch_in.model_dump(exclude_unset=True)
        for key, value in branch_data.items():
            setattr(branch, key, value)
        session.add(branch)
        await session.commit()
        await session.refresh(branch)
        return branch
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch update failed due to integrity error"
        ) from e
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during branch update"
        ) from e
# Delete a branch
async def delete_branch(session: AsyncSession, branch_id: UUID) -> None:
    try:
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
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch deletion failed due to integrity error"
        ) from e
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during branch deletion"
        ) from e
