"""
واجهة المراقب - مراجعة وتفعيل وفلترة الطلبات وربطها بالجمعيات
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_inspector
from app.models.request import Request
from app.models.assignment import Assignment
from app.models.organization import Organization
from app.models.user import User
from app.schemas.request import RequestResponse, PaginatedRequests
from app.schemas.inspector import (
    InspectorRequestUpdate,
    InspectorAssignRequest,
    InspectorRejectRequest,
    InspectorRequestResponse,
    InspectorStatsResponse,
)
from app.schemas.organization import InspectorAssignOrgRequest, PhoneCountResponse
from app.core.constants import RequestStatus, RequestCategory, AssignmentStatus, OrganizationStatus

router = APIRouter(prefix="/inspector", tags=["المراقب - Inspector"])


# === الطلبات ===

@router.get("/requests", response_model=PaginatedRequests)
async def get_requests(
    status: Optional[RequestStatus] = Query(default=None),
    category: Optional[RequestCategory] = Query(default=None),
    region: Optional[str] = Query(default=None),
    is_urgent: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None, description="بحث بالاسم أو الهاتف"),
    mine_only: Optional[bool] = Query(default=None, description="عرض الطلبات المسندة لي فقط"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """عرض الطلبات مع الفلترة"""
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
    if mine_only:
        query = query.where(Request.inspector_id == current_user.id)
    
    # العدد الإجمالي
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # الترتيب: المعلقة أولاً، ثم المستعجلة، ثم الأحدث
    query = query.order_by(
        case(
            (Request.status == RequestStatus.PENDING, 0),
            else_=1
        ),
        Request.is_urgent.desc(),
        Request.priority_score.desc(),
        Request.created_at.desc(),
    )
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


@router.get("/requests/{request_id}", response_model=InspectorRequestResponse)
async def get_request_detail(
    request_id: UUID,
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """تفاصيل طلب محدد"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    return InspectorRequestResponse.model_validate(req)


@router.patch("/requests/{request_id}/activate")
async def activate_request(
    request_id: UUID,
    body: Optional[InspectorRequestUpdate] = None,
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """تفعيل طلب (معلق → جديد)"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    if req.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="يمكن تفعيل الطلبات المعلقة فقط"
        )
    
    req.status = RequestStatus.NEW
    req.inspector_id = current_user.id
    
    if body and body.inspector_notes is not None:
        req.inspector_notes = body.inspector_notes
    
    await db.commit()
    await db.refresh(req)
    
    return {"message": "تم تفعيل الطلب بنجاح", "data": RequestResponse.model_validate(req)}


@router.patch("/requests/{request_id}/reject")
async def reject_request(
    request_id: UUID,
    body: Optional[InspectorRejectRequest] = None,
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """رفض طلب (معلق → مرفوض)"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    if req.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="يمكن رفض الطلبات المعلقة فقط"
        )
    
    req.status = RequestStatus.REJECTED
    req.inspector_id = current_user.id
    
    if body and body.reason:
        req.inspector_notes = body.reason
    
    await db.commit()
    await db.refresh(req)
    
    return {"message": "تم رفض الطلب", "data": RequestResponse.model_validate(req)}


@router.patch("/requests/{request_id}/assign")
async def assign_request_to_org(
    request_id: UUID,
    body: InspectorAssignRequest,
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """ربط طلب بجمعية"""
    # التحقق من وجود الطلب
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # يمكن الربط من حالة pending أو new
    if req.status not in (RequestStatus.PENDING, RequestStatus.NEW):
        raise HTTPException(
            status_code=400,
            detail="يمكن ربط الطلبات المعلقة أو الجديدة فقط بجمعية"
        )
    
    # التحقق من وجود الجمعية
    org_result = await db.execute(
        select(Organization).where(Organization.id == body.organization_id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="الجمعية غير موجودة")
    
    if org.status != OrganizationStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="الجمعية غير نشطة")
    
    # التحقق من عدم وجود تكفل نشط
    existing = await db.execute(
        select(Assignment).where(
            Assignment.request_id == request_id,
            Assignment.status.in_([AssignmentStatus.PLEDGED, AssignmentStatus.IN_PROGRESS])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="هذا الطلب مرتبط بجمعية بالفعل")
    
    # إنشاء التكفل
    assignment = Assignment(
        request_id=request_id,
        org_id=org.id,
        status=AssignmentStatus.PLEDGED,
        notes=body.notes,
    )
    db.add(assignment)
    
    # تحديث حالة الطلب
    req.status = RequestStatus.ASSIGNED
    req.inspector_id = current_user.id
    
    await db.commit()
    
    return {"message": f"تم ربط الطلب بجمعية {org.name} بنجاح"}


@router.patch("/requests/{request_id}")
async def update_request_notes(
    request_id: UUID,
    body: InspectorRequestUpdate,
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """تحديث ملاحظات المراقب على الطلب"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    if body.inspector_notes is not None:
        req.inspector_notes = body.inspector_notes
    
    # ربط المراقب بالطلب إن لم يكن مربوطاً
    if not req.inspector_id:
        req.inspector_id = current_user.id
    
    await db.commit()
    await db.refresh(req)
    
    return {"message": "تم تحديث الملاحظات", "data": RequestResponse.model_validate(req)}


@router.delete("/requests/{request_id}")
async def delete_request(
    request_id: UUID,
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """حذف طلب"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # لا يمكن حذف طلب مرتبط بجمعية أو مكتمل
    if req.status in (RequestStatus.ASSIGNED, RequestStatus.IN_PROGRESS, RequestStatus.COMPLETED):
        raise HTTPException(
            status_code=400,
            detail="لا يمكن حذف طلب مرتبط بجمعية أو قيد التنفيذ أو مكتمل"
        )
    
    await db.delete(req)
    await db.commit()
    
    return {"message": "تم حذف الطلب"}


# === إضافة مواطن لجمعية ===

@router.post("/requests/{request_id}/assign-org")
async def assign_request_to_org_with_access(
    request_id: UUID,
    body: InspectorAssignOrgRequest,
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """إضافة مواطن لجمعية مع التحكم بخصوصية الهاتف"""
    # التحقق من وجود الطلب
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    req = result.scalar_one_or_none()
    
    if not req:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    # يمكن الربط من حالة pending أو new
    if req.status not in (RequestStatus.PENDING, RequestStatus.NEW):
        raise HTTPException(
            status_code=400,
            detail="يمكن ربط الطلبات المعلقة أو الجديدة فقط بجمعية"
        )
    
    # التحقق من وجود الجمعية
    org_result = await db.execute(
        select(Organization).where(Organization.id == body.organization_id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="الجمعية غير موجودة")
    
    if org.status != OrganizationStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="الجمعية غير نشطة")
    
    # التحقق من عدم وجود تكفل نشط
    existing = await db.execute(
        select(Assignment).where(
            Assignment.request_id == request_id,
            Assignment.status.in_([AssignmentStatus.PLEDGED, AssignmentStatus.IN_PROGRESS])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="هذا الطلب مرتبط بجمعية بالفعل")
    
    # إنشاء التكفل مع خصوصية الهاتف
    assignment = Assignment(
        request_id=request_id,
        org_id=org.id,
        status=AssignmentStatus.PLEDGED,
        notes=body.notes,
        allow_phone_access=body.allow_phone_access or False,
    )
    db.add(assignment)
    
    # تحديث حالة الطلب
    if req.status == RequestStatus.PENDING:
        req.status = RequestStatus.NEW
    req.status = RequestStatus.ASSIGNED
    req.inspector_id = current_user.id
    
    await db.commit()
    
    return {"message": f"تم ربط الطلب بجمعية {org.name} بنجاح"}


@router.get("/phone-count", response_model=PhoneCountResponse)
async def get_phone_request_count(
    phone: str = Query(..., description="رقم الهاتف للبحث"),
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """عدد الطلبات لرقم هاتف معين"""
    # تنظيف رقم الهاتف
    clean_phone = phone.replace(' ', '').replace('-', '')
    
    count_result = await db.execute(
        select(func.count(Request.id)).where(Request.requester_phone == clean_phone)
    )
    count = count_result.scalar() or 0
    
    return PhoneCountResponse(phone=clean_phone, count=count)


# === الإحصائيات ===

@router.get("/stats", response_model=InspectorStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات المراقب"""
    # إجمالي الطلبات المعلقة
    pending_count = (await db.execute(
        select(func.count(Request.id)).where(Request.status == RequestStatus.PENDING)
    )).scalar() or 0
    
    # الطلبات التي راجعها هذا المراقب
    my_reviewed = await db.execute(
        select(Request.status, func.count(Request.id))
        .where(Request.inspector_id == current_user.id)
        .group_by(Request.status)
    )
    reviewed_by_status = {row[0].value: row[1] for row in my_reviewed.all()}
    
    total_reviewed = sum(reviewed_by_status.values())
    activated_count = reviewed_by_status.get("new", 0) + reviewed_by_status.get("assigned", 0) + reviewed_by_status.get("in_progress", 0) + reviewed_by_status.get("completed", 0)
    rejected_count = reviewed_by_status.get("rejected", 0)
    assigned_count = reviewed_by_status.get("assigned", 0) + reviewed_by_status.get("in_progress", 0) + reviewed_by_status.get("completed", 0)
    
    return InspectorStatsResponse(
        total_reviewed=total_reviewed,
        pending_count=pending_count,
        activated_count=activated_count,
        rejected_count=rejected_count,
        assigned_count=assigned_count,
    )


# === الجمعيات المتاحة ===

@router.get("/organizations")
async def get_available_organizations(
    current_user: User = Depends(get_current_inspector),
    db: AsyncSession = Depends(get_db),
):
    """قائمة الجمعيات النشطة"""
    result = await db.execute(
        select(Organization)
        .where(Organization.status == OrganizationStatus.ACTIVE)
        .order_by(Organization.name)
    )
    orgs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(o.id),
                "name": o.name,
                "contact_phone": o.contact_phone,
                "contact_email": o.contact_email,
                "service_types": o.service_types,
                "coverage_areas": o.coverage_areas,
                "total_completed": o.total_completed,
            }
            for o in orgs
        ]
    }
