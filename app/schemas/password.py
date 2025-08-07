# File: app/schemas/password.py
# This module defines the schemas for password reset requests and email sending functionality.

from pydantic import BaseModel, EmailStr
from .common import PasswordType


class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password:str= PasswordType

class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str