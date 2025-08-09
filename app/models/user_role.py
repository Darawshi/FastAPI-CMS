#app/models/user_role.py
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    senior_editor = "senior_editor"  # Formerly: editor_admin
    editor = "editor"  # Formerly: editor_user
    category_editor = "category_editor"  # Formerly: editor_one_category


    # Consider adding __str__ for better display
    def __str__(self):
        return self.value