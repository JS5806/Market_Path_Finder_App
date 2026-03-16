"""
사용자 관련 Pydantic 스키마
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# ── 회원가입 ──
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    user_name: str = Field(..., min_length=1, max_length=50)
    age_group: Optional[str] = None
    preferred_categories: Optional[list[str]] = None


# ── 로그인 ──
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ── 토큰 응답 ──
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    user_name: str
    role: str = "customer"


# ── 사용자 프로필 응답 ──
class UserOut(BaseModel):
    user_id: UUID
    email: str
    user_name: str
    role: str = "customer"
    age_group: Optional[str] = None
    preferred_categories: Optional[list[str]] = None
    preferred_store_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
