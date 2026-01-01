from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# ===== 요청 스키마 =====

class UserCreate(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)


class UserLogin(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """사용자 정보 수정"""
    nickname: Optional[str] = Field(None, max_length=50)
    profile_image_url: Optional[str] = None


# ===== 응답 스키마 =====

class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: UUID
    email: str
    nickname: Optional[str]
    profile_image_url: Optional[str]
    is_active: bool
    is_premium: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
