from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re

from app.core.constants import RequestCategory, RequestStatus


# === طلب المساعدة - إنشاء (عام بدون تسجيل) ===
class PublicRequestCreate(BaseModel):
    """إنشاء طلب جديد - متاح للجميع بدون تسجيل"""
    
    # بيانات صاحب الطلب
    requester_name: str = Field(..., min_length=2, max_length=100, description="اسم صاحب الطلب")
    requester_phone: str = Field(..., min_length=10, max_length=20, description="رقم الهاتف")
    
    # تفاصيل الطلب
    category: RequestCategory = Field(..., description="تصنيف الطلب")
    description: str = Field(..., min_length=10, max_length=2000, description="وصف الاحتياج")
    quantity: int = Field(default=1, ge=1, le=100, description="الكمية المطلوبة")
    family_members: int = Field(default=1, ge=1, le=50, description="عدد أفراد الأسرة")
    
    # الموقع
    address: str = Field(..., min_length=5, max_length=500, description="العنوان التفصيلي")
    city: Optional[str] = Field(default=None, max_length=100, description="المدينة")
    region: Optional[str] = Field(default=None, max_length=100, description="المنطقة/الحي")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="خط العرض")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="خط الطول")
    
    # استعجال
    is_urgent: bool = Field(default=False, description="هل الطلب مستعجل؟")
    
    @field_validator('requester_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # إزالة المسافات والشرطات
        phone = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+?[0-9]{10,15})$', phone):
            raise ValueError('رقم الهاتف غير صالح')
        return phone


# === الاستجابات ===
class RequestResponse(BaseModel):
    """استجابة الطلب"""
    id: UUID
    requester_name: str
    requester_phone: str
    category: RequestCategory
    description: str
    quantity: int
    family_members: int
    address: str
    city: Optional[str]
    region: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    status: RequestStatus
    priority_score: int
    is_urgent: int
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class RequestBriefResponse(BaseModel):
    """استجابة مختصرة للطلب"""
    id: UUID
    requester_name: str
    category: RequestCategory
    status: RequestStatus
    city: Optional[str]
    region: Optional[str]
    is_urgent: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PublicRequestCreatedResponse(BaseModel):
    """استجابة بعد إنشاء الطلب"""
    id: UUID
    message: str = "تم استلام طلبك بنجاح. سيتم التواصل معك قريباً."
    tracking_code: str  # رمز متابعة الطلب
    

class RequestTrackResponse(BaseModel):
    """استجابة تتبع الطلب"""
    id: UUID
    status: RequestStatus
    status_ar: str  # الحالة بالعربية
    category: RequestCategory
    created_at: datetime
    updated_at: Optional[datetime]
    organization_name: Optional[str] = None  # اسم المؤسسة المتكفلة
    

# === للإدارة ===
class RequestAdminUpdate(BaseModel):
    """تحديث الطلب من الإدارة"""
    status: Optional[RequestStatus] = None
    priority_score: Optional[int] = Field(default=None, ge=0, le=100)
    is_urgent: Optional[bool] = None
    admin_notes: Optional[str] = Field(default=None, max_length=2000)
    

class RequestDetailResponse(RequestResponse):
    """تفاصيل الطلب الكاملة (للإدارة والمؤسسات)"""
    admin_notes: Optional[str]
    assignments: List["AssignmentBriefResponse"] = []
    

# === التصفح والبحث ===
class PaginatedRequests(BaseModel):
    """قائمة طلبات مع التصفح"""
    items: List[RequestResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class RequestFilters(BaseModel):
    """فلاتر البحث"""
    status: Optional[RequestStatus] = None
    category: Optional[RequestCategory] = None
    region: Optional[str] = None
    is_urgent: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Forward reference
from app.schemas.assignment import AssignmentBriefResponse
RequestDetailResponse.model_rebuild()
