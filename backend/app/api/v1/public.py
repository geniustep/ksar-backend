"""
واجهة عامة - لتقديم الطلبات بدون تسجيل
"""
import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.request import Request
from app.schemas.request import (
    PublicRequestCreate,
    PublicRequestCreatedResponse,
    RequestTrackResponse,
)
from app.core.constants import RequestStatus, RequestCategory, CATEGORY_WEIGHTS

router = APIRouter(prefix="/public", tags=["عام - Public"])


def generate_tracking_code(request_id: UUID) -> str:
    """توليد رمز متابعة قصير"""
    hash_obj = hashlib.sha256(str(request_id).encode())
    return hash_obj.hexdigest()[:8].upper()


def calculate_priority(category: RequestCategory, family_members: int, is_urgent: bool) -> int:
    """حساب نقاط الأولوية"""
    score = 50  # الأساس
    
    # إضافة وزن التصنيف
    score += CATEGORY_WEIGHTS.get(category, 0)
    
    # إضافة نقاط حسب حجم الأسرة
    if family_members >= 6:
        score += 15
    elif family_members >= 4:
        score += 10
    elif family_members >= 2:
        score += 5
    
    # إضافة نقاط الاستعجال
    if is_urgent:
        score += 20
    
    return min(score, 100)  # الحد الأقصى 100


def get_status_arabic(status: RequestStatus) -> str:
    """ترجمة الحالة للعربية"""
    translations = {
        RequestStatus.NEW: "جديد - في انتظار التكفل",
        RequestStatus.ASSIGNED: "متكفل به",
        RequestStatus.IN_PROGRESS: "قيد التنفيذ",
        RequestStatus.COMPLETED: "مكتمل",
        RequestStatus.CANCELLED: "ملغي",
    }
    return translations.get(status, str(status.value))


@router.post("/requests", response_model=PublicRequestCreatedResponse, status_code=201)
async def create_public_request(
    body: PublicRequestCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    تقديم طلب مساعدة جديد
    
    - لا يتطلب تسجيل دخول
    - يُعاد رمز متابعة للتتبع
    """
    # حساب الأولوية
    priority = calculate_priority(body.category, body.family_members, body.is_urgent)
    
    # إنشاء الطلب
    request = Request(
        requester_name=body.requester_name,
        requester_phone=body.requester_phone,
        category=body.category,
        description=body.description,
        quantity=body.quantity,
        family_members=body.family_members,
        address=body.address,
        city=body.city,
        region=body.region,
        latitude=body.latitude,
        longitude=body.longitude,
        priority_score=priority,
        is_urgent=1 if body.is_urgent else 0,
        status=RequestStatus.NEW,
    )
    
    db.add(request)
    await db.commit()
    await db.refresh(request)
    
    # توليد رمز المتابعة
    tracking_code = generate_tracking_code(request.id)
    
    return PublicRequestCreatedResponse(
        id=request.id,
        tracking_code=tracking_code,
        message="تم استلام طلبك بنجاح. سيتم التواصل معك قريباً. رمز المتابعة: " + tracking_code,
    )


@router.get("/requests/track/{tracking_code}", response_model=RequestTrackResponse)
async def track_request(
    tracking_code: str,
    phone: str,
    db: AsyncSession = Depends(get_db),
):
    """
    تتبع حالة الطلب
    
    - يتطلب رمز المتابعة + رقم الهاتف للتحقق
    """
    # البحث عن الطلبات بالهاتف
    result = await db.execute(
        select(Request).where(Request.requester_phone == phone)
    )
    requests = result.scalars().all()
    
    # البحث عن الطلب برمز المتابعة
    for req in requests:
        if generate_tracking_code(req.id) == tracking_code.upper():
            # الحصول على اسم المؤسسة المتكفلة
            org_name = None
            if req.assignments:
                from app.models.assignment import Assignment
                from app.models.organization import Organization
                
                assignment_result = await db.execute(
                    select(Assignment).where(
                        Assignment.request_id == req.id,
                        Assignment.status != "failed"
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
            
            return RequestTrackResponse(
                id=req.id,
                status=req.status,
                status_ar=get_status_arabic(req.status),
                category=req.category,
                created_at=req.created_at,
                updated_at=req.updated_at,
                organization_name=org_name,
            )
    
    raise HTTPException(status_code=404, detail="لم يتم العثور على الطلب. تأكد من رمز المتابعة ورقم الهاتف.")


@router.get("/categories")
async def get_categories():
    """الحصول على قائمة التصنيفات"""
    categories = [
        {"value": "food", "label": "غذاء", "label_ar": "غذاء"},
        {"value": "water", "label": "ماء", "label_ar": "ماء"},
        {"value": "shelter", "label": "مأوى", "label_ar": "مأوى"},
        {"value": "medicine", "label": "دواء", "label_ar": "دواء"},
        {"value": "clothes", "label": "ملابس", "label_ar": "ملابس"},
        {"value": "blankets", "label": "أغطية", "label_ar": "أغطية"},
        {"value": "baby_supplies", "label": "مستلزمات أطفال", "label_ar": "مستلزمات أطفال"},
        {"value": "hygiene", "label": "مستلزمات نظافة", "label_ar": "مستلزمات نظافة"},
        {"value": "financial", "label": "مساعدة مالية", "label_ar": "مساعدة مالية"},
        {"value": "other", "label": "أخرى", "label_ar": "أخرى"},
    ]
    return {"data": categories}
