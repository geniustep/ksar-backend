"""
واجهة الإدارة - مراقبة الطلبات والتحليلات
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_admin
from app.models.request import Request
from app.models.assignment import Assignment
from app.models.organization import Organization
from app.models.user import User
from app.schemas.request import (
    RequestResponse,
    RequestDetailResponse,
    RequestAdminUpdate,
    PaginatedRequests,
)
from app.schemas.assignment import AssignmentBriefResponse
from app.core.constants import RequestStatus, RequestCategory, AssignmentStatus, UserRole, UserStatus
from app.core.security import hash_password
from app.schemas.inspector import (
    InspectorCreateRequest,
    InspectorResponse,
    InspectorCreatedResponse,
    InspectorListResponse,
)

router = APIRouter(prefix="/admin", tags=["الإدارة - Admin"])


# === الطلبات ===

@router.get("/requests", response_model=PaginatedRequests)
async def get_all_requests(
    status: Optional[RequestStatus] = Query(default=None),
    category: Optional[RequestCategory] = Query(default=None),
    region: Optional[str] = Query(default=None),
    is_urgent: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None, description="بحث بالاسم أو الهاتف"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """عرض جميع الطلبات مع الفلترة"""
    query = select(Request)
    
    # الفلاتر
    if status:
        query = query.where(Request.status == status)
    if category:
        query = query.where(Request.category == category)
    if region:
        query = query.where(Request.region == region)
    if is_urgent is not None:
        query = query.where(Request.is_urgent == (1 if is_urgent else 0))
    if search:
        query = query.where(
            (Request.requester_name.ilike(f"%{search}%")) |
            (Request.requester_phone.ilike(f"%{search}%"))
        )
    
    # العدد الإجمالي
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # الترتيب والتصفح
    query = query.order_by(Request.is_urgent.desc(), Request.priority_score.desc(), Request.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    requests = result.scalars().all()
    
    return PaginatedRequests(
        items=[RequestResponse.model_validate(r) for r in requests],
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.get("/requests/{request_id}", response_model=RequestDetailResponse)
async def get_request_detail(
    request_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """تفاصيل طلب محدد"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # الحصول على التكفلات
    assignments_result = await db.execute(
        select(Assignment).where(Assignment.request_id == request_id)
    )
    assignments = assignments_result.scalars().all()

    # بناء الاستجابة يدوياً لتجنب تعبئة assignments من علاقة الـ ORM (تسبب خطأ تحقق)
    base = RequestResponse.model_validate(request)
    return RequestDetailResponse(
        **base.model_dump(),
        admin_notes=request.admin_notes,
        assignments=[AssignmentBriefResponse.model_validate(a) for a in assignments],
    )


@router.patch("/requests/{request_id}")
async def update_request(
    request_id: UUID,
    body: RequestAdminUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """تحديث طلب من الإدارة"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    if body.status is not None:
        request.status = body.status
        if body.status == RequestStatus.COMPLETED:
            request.completed_at = datetime.now(timezone.utc)
    
    if body.priority_score is not None:
        request.priority_score = body.priority_score
    
    if body.is_urgent is not None:
        request.is_urgent = 1 if body.is_urgent else 0
    
    if body.admin_notes is not None:
        request.admin_notes = body.admin_notes
    
    await db.commit()
    await db.refresh(request)
    
    return {"message": "تم تحديث الطلب", "data": RequestResponse.model_validate(request)}


@router.delete("/requests/{request_id}")
async def delete_request(
    request_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """حذف طلب"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    await db.delete(request)
    await db.commit()
    
    return {"message": "تم حذف الطلب"}


# === الإحصائيات والتحليلات ===

@router.get("/stats/overview")
async def get_overview_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات عامة"""
    # إجمالي الطلبات
    total = (await db.execute(select(func.count(Request.id)))).scalar()
    
    # حسب الحالة
    status_result = await db.execute(
        select(Request.status, func.count(Request.id))
        .group_by(Request.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}
    
    # حسب التصنيف
    category_result = await db.execute(
        select(Request.category, func.count(Request.id))
        .group_by(Request.category)
    )
    by_category = {row[0].value: row[1] for row in category_result.all()}
    
    # الطلبات المستعجلة
    urgent = (await db.execute(
        select(func.count(Request.id)).where(Request.is_urgent == 1)
    )).scalar()
    
    # متوسط وقت الإنجاز (بالساعات)
    avg_completion = (await db.execute(
        select(func.avg(
            func.extract("epoch", Request.completed_at - Request.created_at) / 3600
        )).where(
            Request.status == RequestStatus.COMPLETED,
            Request.completed_at.is_not(None)
        )
    )).scalar()
    
    # عدد المؤسسات النشطة
    org_count = (await db.execute(
        select(func.count(Organization.id)).where(Organization.status == "active")
    )).scalar()
    
    return {
        "data": {
            "total_requests": total or 0,
            "by_status": by_status,
            "by_category": by_category,
            "urgent_count": urgent or 0,
            "avg_completion_hours": round(avg_completion, 1) if avg_completion else None,
            "active_organizations": org_count or 0,
        }
    }


@router.get("/stats/daily")
async def get_daily_stats(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات يومية"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # الطلبات الجديدة يومياً
    result = await db.execute(
        select(
            func.date(Request.created_at).label("date"),
            func.count(Request.id).label("count")
        )
        .where(Request.created_at >= start_date)
        .group_by(func.date(Request.created_at))
        .order_by(func.date(Request.created_at))
    )
    
    daily_data = [{"date": str(row[0]), "count": row[1]} for row in result.all()]
    
    return {"data": daily_data}


@router.get("/stats/by-region")
async def get_regional_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات حسب المنطقة"""
    result = await db.execute(
        select(
            Request.region,
            func.count(Request.id).label("total"),
            func.count(case((Request.status == RequestStatus.NEW, 1))).label("new"),
            func.count(case((Request.status == RequestStatus.COMPLETED, 1))).label("completed"),
        )
        .where(Request.region.is_not(None))
        .group_by(Request.region)
        .order_by(func.count(Request.id).desc())
    )
    
    regions = [
        {
            "region": row[0],
            "total": row[1],
            "new": row[2],
            "completed": row[3],
        }
        for row in result.all()
    ]
    
    return {"data": regions}


@router.get("/stats/organizations")
async def get_organization_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات المؤسسات"""
    result = await db.execute(
        select(
            Organization.id,
            Organization.name,
            func.count(Assignment.id).label("total_assignments"),
            func.count(case((Assignment.status == AssignmentStatus.COMPLETED, 1))).label("completed"),
        )
        .outerjoin(Assignment, Assignment.org_id == Organization.id)
        .group_by(Organization.id, Organization.name)
        .order_by(func.count(Assignment.id).desc())
    )
    
    orgs = [
        {
            "id": str(row[0]),
            "name": row[1],
            "total_assignments": row[2],
            "completed": row[3],
        }
        for row in result.all()
    ]
    
    return {"data": orgs}


# === إدارة المؤسسات ===

@router.get("/organizations")
async def get_organizations(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """قائمة المؤسسات"""
    query = select(Organization)
    
    if status:
        query = query.where(Organization.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(Organization.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    orgs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(o.id),
                "name": o.name,
                "contact_phone": o.contact_phone,
                "contact_email": o.contact_email,
                "status": o.status.value,
                "total_completed": o.total_completed,
                "created_at": o.created_at.isoformat(),
            }
            for o in orgs
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.patch("/organizations/{org_id}/status")
async def update_organization_status(
    org_id: UUID,
    status: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """تحديث حالة مؤسسة"""
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="المؤسسة غير موجودة")
    
    from app.core.constants import OrganizationStatus
    org.status = OrganizationStatus(status)
    await db.commit()
    
    return {"message": "تم تحديث حالة المؤسسة"}


# === إدارة المراقبين ===

@router.post("/inspectors", response_model=InspectorCreatedResponse, status_code=201)
async def create_inspector(
    body: InspectorCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """إنشاء حساب مراقب جديد"""
    import secrets
    
    # تنظيف رقم الهاتف
    phone = body.phone.replace(' ', '').replace('-', '')
    
    # التحقق من عدم وجود الهاتف مسبقاً
    phone_result = await db.execute(
        select(User).where(User.phone == phone)
    )
    if phone_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="رقم الهاتف مستخدم بالفعل",
        )
    
    # توليد كود دخول من 6 أرقام
    access_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # إنشاء بريد إلكتروني وهمي فريد
    random_suffix = secrets.token_hex(4)
    temp_email = f"inspector_{phone}_{random_suffix}@inspector.ksar.local"
    
    # إنشاء المستخدم
    user = User(
        email=temp_email,
        password_hash=hash_password(access_code),
        full_name=body.full_name,
        phone=phone,
        role=UserRole.INSPECTOR,
        status=UserStatus.ACTIVE,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return InspectorCreatedResponse(
        message="تم إنشاء حساب المراقب بنجاح",
        inspector=InspectorResponse(
            id=str(user.id),
            full_name=user.full_name,
            phone=user.phone,
            status=user.status.value,
            created_at=user.created_at,
            last_login=user.last_login,
        ),
        access_code=access_code,
    )


@router.get("/inspectors", response_model=InspectorListResponse)
async def get_inspectors(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """قائمة المراقبين"""
    query = select(User).where(User.role == UserRole.INSPECTOR)
    
    if status:
        query = query.where(User.status == UserStatus(status))
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    inspectors = result.scalars().all()
    
    return InspectorListResponse(
        items=[
            InspectorResponse(
                id=str(u.id),
                full_name=u.full_name,
                phone=u.phone,
                status=u.status.value,
                created_at=u.created_at,
                last_login=u.last_login,
            )
            for u in inspectors
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.patch("/inspectors/{inspector_id}/status")
async def update_inspector_status(
    inspector_id: UUID,
    status: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """تعطيل/تفعيل مراقب"""
    result = await db.execute(
        select(User).where(User.id == inspector_id, User.role == UserRole.INSPECTOR)
    )
    inspector = result.scalar_one_or_none()
    
    if not inspector:
        raise HTTPException(status_code=404, detail="المراقب غير موجود")
    
    inspector.status = UserStatus(status)
    await db.commit()
    
    return {"message": "تم تحديث حالة المراقب"}


@router.post("/inspectors/{inspector_id}/regenerate-code")
async def regenerate_inspector_code(
    inspector_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """إعادة توليد كود دخول المراقب"""
    import secrets
    
    result = await db.execute(
        select(User).where(User.id == inspector_id, User.role == UserRole.INSPECTOR)
    )
    inspector = result.scalar_one_or_none()
    
    if not inspector:
        raise HTTPException(status_code=404, detail="المراقب غير موجود")
    
    # توليد كود جديد
    access_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    inspector.password_hash = hash_password(access_code)
    
    await db.commit()
    
    return {
        "message": "تم إعادة توليد كود الدخول",
        "access_code": access_code,
    }


@router.delete("/inspectors/{inspector_id}")
async def delete_inspector(
    inspector_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """حذف مراقب"""
    result = await db.execute(
        select(User).where(User.id == inspector_id, User.role == UserRole.INSPECTOR)
    )
    inspector = result.scalar_one_or_none()
    
    if not inspector:
        raise HTTPException(status_code=404, detail="المراقب غير موجود")
    
    await db.delete(inspector)
    await db.commit()
    
    return {"message": "تم حذف المراقب"}
