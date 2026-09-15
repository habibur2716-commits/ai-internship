from pydantic import BaseModel, EmailStr
from typing import Optional

# Signup ke liye
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

# Response mein user data
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True

# Login ke liye
class LoginRequest(BaseModel):
    email: str
    password: str

# Token response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Naya access token (refresh ke baad)
class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Password change ke liye
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Forgot password ke liye
class ForgotPasswordRequest(BaseModel):
    email: str

# Reset password ke liye
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str