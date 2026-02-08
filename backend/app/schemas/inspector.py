"""
Schemas خاصة بالمراقبين
"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_validator

from app.core.constants import RequestCategory, RequestStatus


# === تسجيل الدخول ===

class InspectorLoginRequest(BaseModel):
    """طلب تسجيل دخول المراقب"""
    phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف")
    code: str = Field(..., min_length=4, max_length=8, description="كود الدخول")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


# === إدارة المراقبين (أدمين) ===

class InspectorCreateRequest(BaseModel):
    """إنشاء مراقب جديد"""
    full_name: str = Field(..., min_length=2, max_length=100, description="الاسم الكامل")
    phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


class InspectorResponse(BaseModel):
    """بيانات المراقب"""
    id: str
    full_name: str
    phone: Optional[str] = None
    status: str
    access_code: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InspectorCreatedResponse(BaseModel):
    """استجابة إنشاء مراقب"""
    message: str = "تم إنشاء حساب المراقب بنجاح"
    inspector: InspectorResponse
    access_code: str  # الكود يُعرض مرة واحدة فقط


class InspectorListResponse(BaseModel):
    """قائمة المراقبين"""
    items: List[InspectorResponse]
    total: int
    page: int
    limit: int


# === إجراءات المراقب على الطلبات ===

class InspectorRequestUpdate(BaseModel):
    """تحديث ملاحظات المراقب"""
    inspector_notes: Optional[str] = Field(default=None, max_length=2000)


class InspectorRequestStatusUpdate(BaseModel):
    """تحديث حالة الطلب وأهميته"""
    status: Optional[RequestStatus] = Field(default=None, description="الحالة الجديدة")
    is_urgent: Optional[int] = Field(default=None, ge=0, le=1, description="مستعجل (0 أو 1)")


class InspectorAssignRequest(BaseModel):
    """ربط طلب بجمعية"""
    organization_id: str = Field(..., description="معرف الجمعية")
    notes: Optional[str] = Field(default=None, max_length=2000, description="ملاحظات")


class InspectorRejectRequest(BaseModel):
    """رفض طلب"""
    reason: Optional[str] = Field(default=None, max_length=2000, description="سبب الرفض")


class InspectorRequestResponse(BaseModel):
    """استجابة طلب من منظور المراقب"""
    id: UUID
    requester_name: str
    requester_phone: str
    category: RequestCategory
    description: Optional[str]
    quantity: int
    family_members: int
    address: Optional[str]
    city: Optional[str]
    region: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    audio_url: Optional[str]
    images: Optional[str]
    status: RequestStatus
    priority_score: int
    is_urgent: int
    inspector_id: Optional[UUID]
    inspector_notes: Optional[str]
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class InspectorStatsResponse(BaseModel):
    """إحصائيات المراقب"""
    total_reviewed: int
    pending_count: int
    activated_count: int
    rejected_count: int
    assigned_count: int
