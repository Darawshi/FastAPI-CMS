# File: app/schemas/password.py
# This module defines the schemas for password reset requests and email sending functionality.
from __future__ import annotations
from pydantic import BaseModel, EmailStr, model_validator
from .common import PasswordType


class PasswordResetRequest(BaseModel):
    email: EmailStr

class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str


class PasswordAdminReset(BaseModel):
    new_password:str= PasswordType
    new_password_confirm:str= PasswordType
    @model_validator(mode="after")
    def check_passwords_match(self) -> "PasswordAdminReset":
        if self.new_password != self.new_password_confirm:
            raise ValueError("Passwords do not match")
        return self

class PasswordResetConfirm(PasswordAdminReset):
    token: str


