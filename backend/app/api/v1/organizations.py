"""
واجهة المؤسسات - التكفل بالطلبات
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_organization
from app.models.request import Request
from app.models.assignment import Assignment
from app.models.organization import Organization
from app.models.user import User
from app.schemas.request import RequestResponse, PaginatedRequests
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentWithRequestResponse,
    PaginatedAssignments,
)
from app.core.constants import RequestStatus, RequestCategory, AssignmentStatus

router = APIRouter(prefix="/org", tags=["المؤسسات - Organizations"])


# === الطلبات المتاحة ===

@router.get("/requests/available", response_model=PaginatedRequests)
async def get_available_requests(
    category: Optional[RequestCategory] = Query(default=None),
    region: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
):
    """عرض الطلبات المتاحة للتكفل"""
    query = select(Request).where(Request.status == RequestStatus.NEW)
    
    if category:
        query = query.where(Request.category == category)
    if region:
        query = query.where(Request.region == region)
    
    # العدد الإجمالي
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # الترتيب حسب الأولوية والاستعجال
    query = query.order_by(Request.is_urgent.desc(), Request.priority_score.desc(), Request.created_at.asc())
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


@router.get("/requests/{request_id}")
async def get_request_detail(
    request_id: UUID,
    current_user: User = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
):
    """تفاصيل طلب للتكفل به"""
    result = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    request = result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    return RequestResponse.model_validate(request)


# === التكفل بالطلبات ===

@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    body: AssignmentCreate,
    current_user: User = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
):
    """التكفل بطلب"""
    # الحصول على المؤسسة
    org_result = await db.execute(
        select(Organization).where(Organization.user_id == current_user.id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=403, detail="لم يتم العثور على بيانات المؤسسة")
    
    # التحقق من الطلب
    request_result = await db.execute(
        select(Request).where(Request.id == body.request_id)
    )
    request = request_result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    
    if request.status != RequestStatus.NEW:
        raise HTTPException(status_code=400, detail="الطلب غير متاح للتكفل")
    
    # التحقق من عدم وجود تكفل سابق
    existing = await db.execute(
        select(Assignment).where(
            Assignment.request_id == body.request_id,
            Assignment.org_id == org.id,
            Assignment.status != AssignmentStatus.FAILED,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="لديك تكفل سابق بهذا الطلب")
    
    # إنشاء التكفل
    assignment = Assignment(
        request_id=body.request_id,
        org_id=org.id,
        status=AssignmentStatus.PLEDGED,
        notes=body.notes,
    )
    db.add(assignment)
    
    # تحديث حالة الطلب
    request.status = RequestStatus.ASSIGNED
    
    await db.commit()
    await db.refresh(assignment)
    
    return AssignmentResponse.model_validate(assignment)


@router.get("/assignments", response_model=PaginatedAssignments)
async def get_my_assignments(
    status: Optional[AssignmentStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
):
    """قائمة تكفلاتي"""
    # الحصول على المؤسسة
    org_result = await db.execute(
        select(Organization).where(Organization.user_id == current_user.id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=403, detail="لم يتم العثور على بيانات المؤسسة")
    
    query = select(Assignment).where(Assignment.org_id == org.id)
    
    if status:
        query = query.where(Assignment.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    query = query.order_by(Assignment.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    assignments = result.scalars().all()
    
    return PaginatedAssignments(
        items=[AssignmentResponse.model_validate(a) for a in assignments],
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.get("/assignments/{assignment_id}")
async def get_assignment_detail(
    assignment_id: UUID,
    current_user: User = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
):
    """تفاصيل تكفل مع بيانات الطلب"""
    # الحصول على المؤسسة
    org_result = await db.execute(
        select(Organization).where(Organization.user_id == current_user.id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=403, detail="لم يتم العثور على بيانات المؤسسة")
    
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.org_id == org.id,
        )
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="التكفل غير موجود")
    
    # الحصول على الطلب
    request_result = await db.execute(
        select(Request).where(Request.id == assignment.request_id)
    )
    request = request_result.scalar_one_or_none()
    
    return {
        "assignment": AssignmentResponse.model_validate(assignment),
        "request": {
            "id": str(request.id),
            "requester_name": request.requester_name,
            "requester_phone": request.requester_phone,
            "category": request.category.value,
            "description": request.description,
            "quantity": request.quantity,
            "family_members": request.family_members,
            "address": request.address,
            "city": request.city,
            "region": request.region,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "is_urgent": request.is_urgent,
        },
    }


@router.patch("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    body: AssignmentUpdate,
    current_user: User = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
):
    """تحديث حالة التكفل"""
    # الحصول على المؤسسة
    org_result = await db.execute(
        select(Organization).where(Organization.user_id == current_user.id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=403, detail="لم يتم العثور على بيانات المؤسسة")
    
    result = await db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.org_id == org.id,
        )
    )
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="التكفل غير موجود")
    
    # تحديث الحالة
    assignment.status = body.status
    
    if body.completion_notes:
        assignment.completion_notes = body.completion_notes
    
    if body.failure_reason:
        assignment.failure_reason = body.failure_reason
    
    # تحديث حالة الطلب
    request_result = await db.execute(
        select(Request).where(Request.id == assignment.request_id)
    )
    request = request_result.scalar_one_or_none()
    
    if body.status == AssignmentStatus.IN_PROGRESS:
        request.status = RequestStatus.IN_PROGRESS
        
    elif body.status == AssignmentStatus.COMPLETED:
        assignment.completed_at = datetime.now(timezone.utc)
        request.status = RequestStatus.COMPLETED
        request.completed_at = datetime.now(timezone.utc)
        # تحديث إحصائيات المؤسسة
        org.total_completed = (org.total_completed or 0) + 1
        
    elif body.status == AssignmentStatus.FAILED:
        # إعادة الطلب للحالة الجديدة
        request.status = RequestStatus.NEW
    
    await db.commit()
    await db.refresh(assignment)
    
    return AssignmentResponse.model_validate(assignment)


# === إحصائيات المؤسسة ===

@router.get("/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات المؤسسة"""
    org_result = await db.execute(
        select(Organization).where(Organization.user_id == current_user.id)
    )
    org = org_result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=403, detail="لم يتم العثور على بيانات المؤسسة")
    
    # إجمالي التكفلات
    total = (await db.execute(
        select(func.count(Assignment.id)).where(Assignment.org_id == org.id)
    )).scalar()
    
    # حسب الحالة
    status_result = await db.execute(
        select(Assignment.status, func.count(Assignment.id))
        .where(Assignment.org_id == org.id)
        .group_by(Assignment.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}
    
    return {
        "data": {
            "total_assignments": total or 0,
            "by_status": by_status,
            "total_completed": org.total_completed or 0,
        }
    }
