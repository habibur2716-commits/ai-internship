from pydantic import BaseModel
from typing import Optional, List
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

# ===== CHAT SESSION & HISTORY SCHEMAS (NEWLY ADDED) =====

class ChatUpdateTitle(BaseModel):
    title: str

class MessageResponse(BaseModel):
    id: int
    session_id: int
    sender: str  # "user" or "assistant"
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ===== UPDATED CHAT REQUEST/RESPONSE =====

class ChatRequest(BaseModel):
    question: str
    session_id: int  # Link query to active chat session
    enable_web_search: bool = False

class ChatResponse(BaseModel):
    answer: str
    session_id: int
    doc_sources: List[str] = []
    web_sources: List[str] = []