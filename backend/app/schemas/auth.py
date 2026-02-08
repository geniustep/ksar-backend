from typing import Optional
import re
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.core.constants import UserRole


class LoginRequest(BaseModel):
    """طلب تسجيل الدخول"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UnifiedLoginRequest(BaseModel):
    """طلب تسجيل الدخول الموحد - بريد أو هاتف + كلمة مرور/كود"""
    identifier: str = Field(..., min_length=4, description="البريد الإلكتروني أو رقم الهاتف")
    password: str = Field(..., min_length=4, description="كلمة المرور أو كود الدخول")

    def is_email(self) -> bool:
        """تحقق هل المُدخل بريد إلكتروني"""
        return '@' in self.identifier

    def get_clean_phone(self) -> str:
        """تنظيف رقم الهاتف"""
        return re.sub(r'[\s\-]', '', self.identifier)


class RegisterRequest(BaseModel):
    """طلب تسجيل مستخدم جديد (مواطن)"""
    email: EmailStr
    password: str = Field(..., min_length=6, description="كلمة المرور (6 أحرف على الأقل)")
    full_name: str = Field(..., min_length=2, max_length=100, description="الاسم الكامل")
    phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف")
    address: Optional[str] = Field(default=None, max_length=500, description="العنوان")
    city: Optional[str] = Field(default=None, max_length=100, description="المدينة")
    region: Optional[str] = Field(default=None, max_length=100, description="المنطقة/الحي")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


class RegisterResponse(BaseModel):
    """استجابة التسجيل"""
    message: str = "تم إنشاء الحساب بنجاح"
    user: "UserResponse"
    access_token: str
    token_type: str = "bearer"


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
    phone: Optional[str] = None
    role: UserRole
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    """بيانات الملف الشخصي الكاملة"""
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    region: Optional[str]
    role: UserRole
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """تحديث الملف الشخصي"""
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


class ChangePasswordRequest(BaseModel):
    """تغيير كلمة المرور"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class PhoneRegisterRequest(BaseModel):
    """طلب تسجيل مواطن برقم الهاتف فقط (مؤقت - بدون OTP)"""
    phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف")
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100, description="الاسم (اختياري)")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


class PhoneRegisterResponse(BaseModel):
    """استجابة التسجيل برقم الهاتف"""
    message: str = "تم التسجيل بنجاح"
    user: "UserResponse"
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = True


class InspectorLoginResponse(BaseModel):
    """استجابة تسجيل دخول المراقب"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


LoginResponse.model_rebuild()
RegisterResponse.model_rebuild()
PhoneRegisterResponse.model_rebuild()
InspectorLoginResponse.model_rebuild()
