"""
Schemas خاصة بإدارة المؤسسات
"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator


# === إنشاء مؤسسة (أدمين) ===

class OrganizationCreateRequest(BaseModel):
    """إنشاء مؤسسة جديدة من الأدمين"""
    name: str = Field(..., min_length=2, max_length=200, description="اسم المؤسسة")
    phone: str = Field(..., min_length=10, max_length=20, description="رقم هاتف المؤسسة")
    email: Optional[str] = Field(default=None, max_length=100, description="البريد الإلكتروني")
    description: Optional[str] = Field(default=None, max_length=2000, description="وصف المؤسسة")
    city: Optional[str] = Field(default=None, max_length=100, description="المدينة")
    region: Optional[str] = Field(default=None, max_length=100, description="المنطقة")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


class OrganizationResponse(BaseModel):
    """بيانات المؤسسة"""
    id: str
    name: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    description: Optional[str] = None
    status: str
    total_completed: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrganizationCreatedResponse(BaseModel):
    """استجابة إنشاء مؤسسة"""
    message: str = "تم إنشاء المؤسسة بنجاح"
    organization: OrganizationResponse
    access_code: str  # الكود يُعرض مرة واحدة فقط


class OrganizationListResponse(BaseModel):
    """قائمة المؤسسات"""
    items: List[OrganizationResponse]
    total: int
    page: int
    limit: int


# === تسجيل دخول المؤسسة ===

class OrgLoginRequest(BaseModel):
    """طلب تسجيل دخول المؤسسة بالهاتف + الكود"""
    phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف")
    code: str = Field(..., min_length=6, max_length=6, description="كود الدخول")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


# === إدارة المواطنين ===

class CitizenResponse(BaseModel):
    """بيانات مواطن"""
    id: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    status: str
    total_requests: int = 0
    supervisor_id: Optional[str] = None
    supervisor_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CitizenListResponse(BaseModel):
    """قائمة المواطنين"""
    items: List[CitizenResponse]
    total: int
    page: int
    limit: int


# === التحكم بخصوصية الهاتف ===

class OrgAccessRequest(BaseModel):
    """السماح/منع جمعية من رؤية رقم الهاتف"""
    request_id: str = Field(..., description="معرف الطلب")
    organization_id: str = Field(..., description="معرف المؤسسة")
    allow_phone_access: bool = Field(..., description="السماح برؤية رقم الهاتف")


# === ربط مواطن بجمعية (المراقب) ===

class InspectorAssignOrgRequest(BaseModel):
    """إضافة مواطن لجمعية من المراقب"""
    organization_id: str = Field(..., description="معرف الجمعية")
    allow_phone_access: Optional[bool] = Field(default=False, description="السماح برؤية رقم الهاتف")
    notes: Optional[str] = Field(default=None, max_length=2000, description="ملاحظات")


class PhoneCountResponse(BaseModel):
    """عدد الطلبات لرقم هاتف معين"""
    phone: str
    count: int
