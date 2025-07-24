from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    editor_admin = "editor_admin"
    editor_user = "editor_user"
    editor_one_category = "editor_one_category"
