from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    senior_editor = "senior_editor"  # Formerly: editor_admin
    editor = "editor"  # Formerly: editor_user
    category_editor = "category_editor"  # Formerly: editor_one_category
