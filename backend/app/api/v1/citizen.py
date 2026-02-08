"""
واجهة المواطنين - إدارة الطلبات الشخصية
"""
import hashlib
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_citizen
from app.models.request import Request
from app.models.assignment import Assignment
from app.models.organization import Organization
from app.models.user import User
from app.schemas.request import (
    RequestResponse,
    PaginatedRequests,
)
from app.core.constants import RequestStatus, RequestCategory, CATEGORY_WEIGHTS, AssignmentStatus


router = APIRouter(prefix="/citizen", tags=["المواطنون - Citizens"])


def generate_tracking_code(request_id: UUID) -> str:
    """توليد رمز متابعة قصير"""
    hash_obj = hashlib.sha256(str(request_id).encode())
    return hash_obj.hexdigest()[:8].upper()


def calculate_priority(category: RequestCategory, family_members: int, is_urgent: bool) -> int:
    """حساب نقاط الأولوية"""
    score = 50
    score += CATEGORY_WEIGHTS.get(category, 0)
    
    if family_members >= 6:
        score += 15
    elif family_members >= 4:
        score += 10
    elif family_members >= 2:
        score += 5
    
    if is_urgent:
        score += 20
    
    return min(score, 100)


def parse_images(images_json: Optional[str]) -> Optional[list[str]]:
    """تحويل الصور من JSON إلى قائمة"""
    import json
    if not images_json:
        return None
    try:
        return json.loads(images_json)
    except (json.JSONDecodeError, TypeError):
        return None


def get_status_arabic(status: RequestStatus) -> str:
    """ترجمة الحالة للعربية"""
    translations = {
        RequestStatus.PENDING: "معلق - في انتظار المراجعة",
        RequestStatus.NEW: "جديد - في انتظار التكفل",
        RequestStatus.ASSIGNED: "متكفل به",
        RequestStatus.IN_PROGRESS: "قيد التنفيذ",
        RequestStatus.COMPLETED: "مكتمل",
        RequestStatus.CANCELLED: "ملغي",
        RequestStatus.REJECTED: "مرفوض",
    }
    return translations.get(status, str(status.value))


# === Schemas خاصة بالمواطنين ===
from pydantic import BaseModel, Field, field_validator
import re


class CitizenRequestCreate(BaseModel):
    """إنشاء طلب من مواطن مسجل"""
    category: RequestCategory = Field(..., description="تصنيف الطلب")
    description: Optional[str] = Field(default=None, max_length=2000, description="وصف الاحتياج (اختياري)")
    quantity: int = Field(default=1, ge=1, le=100, description="الكمية المطلوبة")
    family_members: int = Field(default=1, ge=1, le=50, description="عدد أفراد الأسرة")
    
    # الموقع (اختياري - يمكن استخدام العنوان المحفوظ)
    address: Optional[str] = Field(default=None, max_length=500, description="العنوان التفصيلي")
    city: Optional[str] = Field(default=None, max_length=100, description="المدينة")
    region: Optional[str] = Field(default=None, max_length=100, description="المنطقة/الحي")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="خط العرض")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="خط الطول")
    
    # المرفقات (اختياري)
    audio_url: Optional[str] = Field(default=None, max_length=500, description="رابط الملف الصوتي")
    images: Optional[list[str]] = Field(default=None, max_length=5, description="روابط الصور (حد أقصى 5)")
    
    is_urgent: bool = Field(default=False, description="هل الطلب مستعجل؟")


class CitizenRequestUpdate(BaseModel):
    """تحديث طلب (قبل التكفل فقط)"""
    description: Optional[str] = Field(default=None, max_length=2000)
    quantity: Optional[int] = Field(default=None, ge=1, le=100)
    family_members: Optional[int] = Field(default=None, ge=1, le=50)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    audio_url: Optional[str] = Field(default=None, max_length=500)
    images: Optional[list[str]] = Field(default=None, max_length=5)
    is_urgent: Optional[bool] = None


class CitizenRequestResponse(BaseModel):
    """استجابة الطلب للمواطن"""
    id: UUID
    tracking_code: str
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
    images: Optional[list[str]]
    status: RequestStatus
    status_ar: str
    is_urgent: bool
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    organization_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class CitizenRequestCreatedResponse(BaseModel):
    """استجابة إنشاء طلب"""
    id: UUID
    tracking_code: str
    message: str


class CitizenRequestStats(BaseModel):
    """إحصائيات طلبات المواطن"""
    total_requests: int
    by_status: dict
    

# === نقاط النهاية ===

@router.post("/requests", response_model=CitizenRequestCreatedResponse, status_code=201)
async def create_request(
    body: CitizenRequestCreate,
    current_user: User = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    """
    تقديم طلب مساعدة جديد
    
    - يتطلب تسجيل الدخول كمواطن
    - يستخدم بيانات المستخدم تلقائياً
    """
    import json
    
    # استخدام عنوان المستخدم إذا لم يُحدد (العنوان اختياري الآن)
    address = body.address or current_user.address
    city = body.city or current_user.city
    region = body.region or current_user.region
    
    # حساب الأولوية
    priority = calculate_priority(body.category, body.family_members, body.is_urgent)
    
    # تحويل قائمة الصور إلى JSON string للتخزين
    images_json = json.dumps(body.images) if body.images else None
    
    # إنشاء الطلب
    request = Request(
        user_id=current_user.id,
        requester_name=current_user.full_name,
        requester_phone=current_user.phone,
        category=body.category,
        description=body.description or "",
        quantity=body.quantity,
        family_members=body.family_members,
        address=address or "",
        city=city,
        region=region,
        latitude=body.latitude,
        longitude=body.longitude,
        audio_url=body.audio_url,
        images=images_json,
        priority_score=priority,
        is_urgent=1 if body.is_urgent else 0,
        status=RequestStatus.PENDING,
    )
    
    db.add(request)
    await db.commit()
    await db.refresh(request)
    
    tracking_code = generate_tracking_code(request.id)
    
    return CitizenRequestCreatedResponse(
        id=request.id,
        tracking_code=tracking_code,
        message=f"تم استلام طلبك بنجاح. رمز المتابعة: {tracking_code}",
    )


@router.get("/requests", response_model=List[CitizenRequestResponse])
async def get_my_requests(
    status: Optional[RequestStatus] = Query(default=None, description="تصفية حسب الحالة"),
    current_user: User = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    """
    عرض جميع طلباتي
    """
    query = select(Request).where(Request.user_id == current_user.id)
    
    if status:
        query = query.where(Request.status == status)
    
    query = query.order_by(Request.created_at.desc())
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    # تجهيز الاستجابة مع أسماء المؤسسات
    responses = []
    for req in requests:
        # الحصول على المؤسسة المتكفلة
        org_name = None
        assignment_result = await db.execute(
            select(Assignment).where(
                Assignment.request_id == req.id,
                Assignment.status != AssignmentStatus.FAILED
            )
        )
        assignment = assignment_result.scalar_one_or_none()
        if assignment:
            org_result = await db.execute(
                select(Organization).where(Organization.id == assignment.org_id)
            )
            org = org_result.scalar_one_or_none()
            if org:
                org_name = org.name
        
        responses.append(CitizenRequestResponse(
            id=req.id,
            tracking_code=generate_tracking_code(req.id),
            category=req.category,
            description=req.description,
            quantity=req.quantity,
            family_members=req.family_members,
            address=req.address,
            city=req.city,
            region=req.region,
            latitude=req.latitude,
            longitude=req.longitude,
            audio_url=req.audio_url,
            images=parse_images(req.images),
            status=req.status,
            status_ar=get_status_arabic(req.status),
            is_urgent=bool(req.is_urgent),
            created_at=req.created_at,
            updated_at=req.updated_at,
            completed_at=req.completed_at,
            organization_name=org_name,
        ))
    
    return responses


@router.get("/requests/{request_id}", response_model=CitizenRequestResponse)
async def get_request_detail(
    request_id: UUID,
    current_user: User = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    """
    تفاصيل طلب معين
    """
    result = await db.execute(
        select(Request).where(
            Request.id == request_id,
            Request.user_id == current_user.id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود",
        )
    
    # الحصول على المؤسسة المتكفلة
    org_name = None
    assignment_result = await db.execute(
        select(Assignment).where(
            Assignment.request_id == request.id,
            Assignment.status != AssignmentStatus.FAILED
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if assignment:
        org_result = await db.execute(
            select(Organization).where(Organization.id == assignment.org_id)
        )
        org = org_result.scalar_one_or_none()
        if org:
            org_name = org.name
    
    return CitizenRequestResponse(
        id=request.id,
        tracking_code=generate_tracking_code(request.id),
        category=request.category,
        description=request.description,
        quantity=request.quantity,
        family_members=request.family_members,
        address=request.address,
        city=request.city,
        region=request.region,
        latitude=request.latitude,
        longitude=request.longitude,
        audio_url=request.audio_url,
        images=parse_images(request.images),
        status=request.status,
        status_ar=get_status_arabic(request.status),
        is_urgent=bool(request.is_urgent),
        created_at=request.created_at,
        updated_at=request.updated_at,
        completed_at=request.completed_at,
        organization_name=org_name,
    )


@router.patch("/requests/{request_id}", response_model=CitizenRequestResponse)
async def update_request(
    request_id: UUID,
    body: CitizenRequestUpdate,
    current_user: User = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    """
    تحديث طلب (فقط إذا كان في حالة 'جديد')
    """
    result = await db.execute(
        select(Request).where(
            Request.id == request_id,
            Request.user_id == current_user.id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود",
        )
    
    if request.status not in (RequestStatus.PENDING, RequestStatus.NEW):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يمكن تعديل الطلب بعد التكفل به",
        )
    
    # تحديث الحقول
    if body.description is not None:
        request.description = body.description
    if body.quantity is not None:
        request.quantity = body.quantity
    if body.family_members is not None:
        request.family_members = body.family_members
    if body.address is not None:
        request.address = body.address
    if body.city is not None:
        request.city = body.city
    if body.region is not None:
        request.region = body.region
    if body.audio_url is not None:
        request.audio_url = body.audio_url
    if body.images is not None:
        import json
        request.images = json.dumps(body.images)
    if body.is_urgent is not None:
        request.is_urgent = 1 if body.is_urgent else 0
        # إعادة حساب الأولوية
        request.priority_score = calculate_priority(
            request.category,
            request.family_members,
            body.is_urgent
        )
    
    await db.commit()
    await db.refresh(request)
    
    return CitizenRequestResponse(
        id=request.id,
        tracking_code=generate_tracking_code(request.id),
        category=request.category,
        description=request.description,
        quantity=request.quantity,
        family_members=request.family_members,
        address=request.address,
        city=request.city,
        region=request.region,
        latitude=request.latitude,
        longitude=request.longitude,
        audio_url=request.audio_url,
        images=parse_images(request.images),
        status=request.status,
        status_ar=get_status_arabic(request.status),
        is_urgent=bool(request.is_urgent),
        created_at=request.created_at,
        updated_at=request.updated_at,
        completed_at=request.completed_at,
        organization_name=None,
    )


@router.delete("/requests/{request_id}")
async def cancel_request(
    request_id: UUID,
    current_user: User = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    """
    إلغاء طلب (فقط إذا كان في حالة 'جديد')
    """
    result = await db.execute(
        select(Request).where(
            Request.id == request_id,
            Request.user_id == current_user.id
        )
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطلب غير موجود",
        )
    
    if request.status not in (RequestStatus.PENDING, RequestStatus.NEW):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يمكن إلغاء الطلب بعد التكفل به",
        )
    
    request.status = RequestStatus.CANCELLED
    await db.commit()
    
    return {"message": "تم إلغاء الطلب بنجاح"}


@router.get("/stats", response_model=CitizenRequestStats)
async def get_my_stats(
    current_user: User = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    """
    إحصائيات طلباتي
    """
    # العدد الإجمالي
    total_result = await db.execute(
        select(func.count(Request.id)).where(Request.user_id == current_user.id)
    )
    total = total_result.scalar() or 0
    
    # حسب الحالة
    status_counts = {}
    for s in RequestStatus:
        count_result = await db.execute(
            select(func.count(Request.id)).where(
                Request.user_id == current_user.id,
                Request.status == s
            )
        )
        count = count_result.scalar() or 0
        if count > 0:
            status_counts[s.value] = count
    
    return CitizenRequestStats(
        total_requests=total,
        by_status=status_counts,
    )
