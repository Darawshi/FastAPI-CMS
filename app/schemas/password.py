from pydantic import BaseModel, EmailStr


# app/schemas/password.py

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
