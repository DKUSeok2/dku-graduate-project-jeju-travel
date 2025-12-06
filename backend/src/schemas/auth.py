"""
Authentication Schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_admin: bool
    provider: str
    profile_image: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdateProfile(BaseModel):
    """사용자 프로필 업데이트 (이름 변경)"""
    name: str


class UserUpdatePassword(BaseModel):
    """비밀번호 변경"""
    current_password: str
    new_password: str


