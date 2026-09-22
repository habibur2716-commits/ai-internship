from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ===== AUTH SCHEMAS =====
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# ===== DOCUMENT SCHEMAS =====
class DocumentResponse(BaseModel):
    id: int
    source_type: str
    source_name: str
    chunks_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class URLRequest(BaseModel):
    url: str

class YouTubeRequest(BaseModel):
    url: str

# ===== CHAT SCHEMAS =====
class ChatRequest(BaseModel):
    question: str
    enable_web_search: bool = False

class ChatResponse(BaseModel):
    answer: str
    doc_sources: list[str] = []
    web_sources: list[str] = []