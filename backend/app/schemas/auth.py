from typing import Optional
from pydantic import BaseModel, Field, EmailStr

from app.core.constants import UserRole


class LoginRequest(BaseModel):
    """طلب تسجيل الدخول"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """استجابة تسجيل الدخول"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenRefreshResponse(BaseModel):
    """استجابة تحديث التوكن"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """بيانات المستخدم"""
    id: str
    email: str
    full_name: str
    role: UserRole
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class ChangePasswordRequest(BaseModel):
    """تغيير كلمة المرور"""
    current_password: str
    new_password: str = Field(..., min_length=6)


LoginResponse.model_rebuild()
