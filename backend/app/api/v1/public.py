"""
واجهة عامة - للاستعلام والتتبع (بدون تسجيل)
"""
import hashlib
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.request import Request
from app.models.assignment import Assignment
from app.models.organization import Organization
from app.models.user import User
from app.schemas.request import RequestTrackResponse
from app.schemas.organization import OrgRegisterRequest
from app.core.constants import RequestStatus, UserRole, UserStatus, OrganizationStatus
from app.core.security import hash_password

router = APIRouter(prefix="/public", tags=["عام - Public"])


def generate_tracking_code(request_id: UUID) -> str:
    """توليد رمز متابعة قصير"""
    hash_obj = hashlib.sha256(str(request_id).encode())
    return hash_obj.hexdigest()[:8].upper()


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


@router.get("/requests/track/{tracking_code}", response_model=RequestTrackResponse)
async def track_request(
    tracking_code: str,
    phone: str,
    db: AsyncSession = Depends(get_db),
):
    """
    تتبع حالة الطلب (بدون تسجيل)
    
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


@router.post("/org-register")
async def register_organization(
    body: OrgRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    تسجيل مؤسسة جديدة (عام - بدون تسجيل دخول)
    
    المؤسسة تُنشأ بحالة "معلقة" وتنتظر موافقة الأدمين.
    """
    # تنظيف رقم الهاتف
    phone = body.phone.replace(' ', '').replace('-', '')
    
    # التحقق من عدم وجود الهاتف مسبقاً
    phone_result = await db.execute(
        select(User).where(User.phone == phone)
    )
    if phone_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="رقم الهاتف مستخدم بالفعل. إذا كان لديك حساب، استخدم صفحة دخول المؤسسات.",
        )
    
    # التحقق من البريد الإلكتروني
    email = body.email
    if email:
        email = email.lower().strip()
        email_result = await db.execute(
            select(User).where(User.email == email)
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="البريد الإلكتروني مستخدم بالفعل",
            )
    else:
        random_suffix = secrets.token_hex(4)
        email = f"org_{phone}_{random_suffix}@org.ksar.local"
    
    # توليد كود دخول من 8 أحرف أبجدية رقمية (بدون أحرف ملتبسة)
    alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    access_code = ''.join(secrets.choice(alphabet) for _ in range(8))
    
    # إنشاء المستخدم بحالة معلقة
    user = User(
        email=email,
        password_hash=hash_password(access_code),
        access_code=access_code,
        full_name=body.responsible_name or body.name,
        phone=phone,
        city=body.city,
        region=body.region,
        role=UserRole.ORGANIZATION,
        status=UserStatus.SUSPENDED,  # معلق حتى يوافق الأدمين
    )
    
    db.add(user)
    await db.flush()
    
    # إنشاء سجل المؤسسة
    org = Organization(
        user_id=user.id,
        name=body.name,
        description=body.description,
        contact_phone=phone,
        contact_email=body.email,
        status=OrganizationStatus.SUSPENDED,  # معلقة حتى الموافقة
    )
    
    db.add(org)
    await db.commit()
    
    return {
        "message": "تم تسجيل المؤسسة بنجاح. سيتم مراجعة طلبك من الإدارة وسيتم إرسال بيانات الدخول عند الموافقة.",
        "organization_name": body.name,
    }
