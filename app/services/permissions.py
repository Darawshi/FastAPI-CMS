# app/services/permissions.py
from typing import List
from uuid import UUID

from fastapi import HTTPException, status, Depends
from sqlalchemy import case, and_, true, ColumnElement
from sqlalchemy.sql.elements import Case

from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.user import UserCreate


def get_role_order() -> Case:
    """Returns case statement for role-based ordering"""
    return case(
        {
            UserRole.admin: 0,
            UserRole.senior_editor: 1,
            UserRole.editor: 2,
            UserRole.category_editor: 3
        },
        value=User.role
    )

def validate_user_creation_permissions(current_user: User, new_user: UserCreate):
    if current_user.role == UserRole.senior_editor:
        if new_user.role not in {UserRole.senior_editor, UserRole.editor}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Senior editors can only create senior editor or editor users"
            )
    elif current_user.role == UserRole.editor:
        if new_user.role not in {UserRole.category_editor}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Editors can only create category_editor users"
            )
    elif current_user.role == UserRole.category_editor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Category editors cannot create users"
        )

def validate_user_update_permissions(current_user: User, target_user: User):
    if current_user.role == UserRole.senior_editor :
        if target_user.role not in {UserRole.editor, UserRole.category_editor}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Senior editors can only update editor or category_editor users"
            )

def validate_user_deactivate_reactivate(current_user: User, target_user: User):
    if current_user.role == UserRole.senior_editor:
        if target_user.role not in {UserRole.editor, UserRole.category_editor}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Senior editors can only manage editor or category_editor users"
            )

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:  # Use enum comparison
        raise HTTPException(status_code=403, detail="Admins only")
    return user

def require_admin_or_senior_editor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.admin, UserRole.senior_editor}:
        raise HTTPException(status_code=403, detail="Admins or Senior Editors only")
    return current_user

def require_admin_or_senior_editor_or_editor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.admin, UserRole.senior_editor, UserRole.editor}:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return current_user

def require_admin_or_senior_editor_or_editor_or_category_editor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.admin, UserRole.senior_editor, UserRole.editor , UserRole.category_editor}:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return current_user

def prevent_self_action_on_user(current_user: User, target_user_id: UUID):
    if current_user.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot perform this action on your own account.",
        )

def get_user_visibility_condition(current_user: User) -> ColumnElement[bool]:
    """Returns SQLAlchemy condition for user visibility based on role"""
    if current_user.role == UserRole.admin:
        return true()  # SQLAlchemy "true" condition

    elif current_user.role == UserRole.senior_editor:
        return User.role.in_([# type: ignore
            UserRole.senior_editor,
            UserRole.editor,
            UserRole.category_editor
        ])

    elif current_user.role == UserRole.editor:
        return and_(
            User.role == UserRole.category_editor,
            User.created_by_id == current_user.id
        )

    else:  # This handles UserRole.category_editor and any unknown roles
        return and_(
             current_user.role == UserRole.category_editor,
             User.role == UserRole.category_editor,
            User.created_by_id == current_user.created_by_id
        )

def user_has_permission(current_user: User, target_user: User) -> bool:
    """Checks if current user can view target user"""
    if current_user.role == UserRole.admin:
        return True

    elif current_user.role == UserRole.senior_editor:
        return target_user.role in [
            UserRole.senior_editor,
            UserRole.editor,
            UserRole.category_editor
        ]

    elif current_user.role == UserRole.editor:
        return (
                target_user.role == UserRole.category_editor and
                target_user.created_by_id == current_user.id
        )
    else:  # This handles UserRole.category_editor and any unknown roles
        return (
            current_user.role == UserRole.category_editor and
            target_user.role == UserRole.category_editor and
            target_user.created_by_id == current_user.created_by_id
        )

def filter_users_by_role_viewer(viewer: User, users: List[User]) -> List[User]:
    if viewer.role == UserRole.senior_editor:
        allowed_roles = {UserRole.senior_editor,UserRole.editor, UserRole.category_editor}
        return [u for u in users if u.role in allowed_roles]
    return users  # admin sees all