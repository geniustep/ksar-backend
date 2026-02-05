from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.api.deps import get_current_coordinator
from app.core.constants import RequestStatus, RequestCategory, VerificationResult
from app.core.exceptions import NotFoundError, ValidationError
from app.models.request import Request
from app.models.user import User, ResidentProfile
from app.models.verification import Verification
from app.services.audit_service import AuditService
from app.services.sms_service import sms_service

router = APIRouter(prefix="/verify", tags=["التحقق - Verification"])


class VerifyQueueItem(BaseModel):
    id: UUID
    category: RequestCategory
    description: Optional[str]
    quantity: int
    priority_score: int
    location_text: str
    region_code: Optional[str]
    created_at: datetime
    resident_phone: Optional[str] = None
    family_size: Optional[int] = None
    special_cases: List[str] = []
    duplicate_warning: bool = False

    model_config = {"from_attributes": True}


class VerifyQueueResponse(BaseModel):
    items: List[VerifyQueueItem]
    total: int
    page: int
    limit: int
    has_more: bool


class VerifyRequest(BaseModel):
    result: VerificationResult
    notes: Optional[str] = Field(default=None, max_length=2000)
    priority_override: Optional[int] = Field(default=None, ge=0, le=100)


class MergeRequest(BaseModel):
    merge_into: UUID


@router.get("/queue", response_model=VerifyQueueResponse)
async def get_verification_queue(
    region: Optional[str] = Query(default=None),
    category: Optional[RequestCategory] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """قائمة الطلبات الجاهزة للتحقق."""
    query = select(Request).where(
        Request.status.in_([RequestStatus.NEW, RequestStatus.PENDING_VERIFICATION])
    )

    if region:
        query = query.where(Request.region_code == region)
    if category:
        query = query.where(Request.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Request.priority_score.desc(), Request.created_at.asc())
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    requests = list(result.scalars().all())

    items = []
    for req in requests:
        # Get resident info
        user_result = await db.execute(select(User).where(User.id == req.created_by))
        resident_user = user_result.scalar_one_or_none()

        profile_result = await db.execute(
            select(ResidentProfile).where(ResidentProfile.user_id == req.created_by)
        )
        profile = profile_result.scalar_one_or_none()

        # Check for duplicate warning
        has_dup = req.duplicate_hash is not None and await db.execute(
            select(func.count()).where(
                Request.duplicate_hash == req.duplicate_hash,
                Request.id != req.id,
            )
        )
        dup_count = has_dup.scalar() if has_dup else 0

        items.append(VerifyQueueItem(
            id=req.id,
            category=req.category,
            description=req.description,
            quantity=req.quantity,
            priority_score=req.priority_score,
            location_text=req.location_text,
            region_code=req.region_code,
            created_at=req.created_at,
            resident_phone=resident_user.phone if resident_user else None,
            family_size=profile.family_size if profile else None,
            special_cases=profile.special_cases if profile else [],
            duplicate_warning=dup_count > 0,
        ))

    return VerifyQueueResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.post("/{request_id}")
async def verify_request(
    request_id: UUID,
    body: VerifyRequest,
    current_user: User = Depends(get_current_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """التحقق من طلب أو رفضه."""
    result = await db.execute(select(Request).where(Request.id == request_id))
    request = result.scalar_one_or_none()

    if not request:
        raise NotFoundError("الطلب", str(request_id))

    # Create verification record
    verification = Verification(
        request_id=request_id,
        coordinator_id=current_user.id,
        result=body.result,
        notes=body.notes,
        priority_override=body.priority_override,
    )
    db.add(verification)

    # Update request status
    if body.result == VerificationResult.VERIFIED:
        request.status = RequestStatus.VERIFIED
        request.verified_at = datetime.now(timezone.utc)
        if body.priority_override is not None:
            request.priority_score = body.priority_override

        # Notify resident
        user_result = await db.execute(select(User).where(User.id == request.created_by))
        user = user_result.scalar_one_or_none()
        if user:
            await sms_service.send_request_verified(
                user.phone, request.category.value, user.language
            )

    elif body.result == VerificationResult.REJECTED:
        request.status = RequestStatus.REJECTED
    else:
        request.status = RequestStatus.PENDING_VERIFICATION

    await db.flush()

    # Audit
    audit = AuditService(db)
    await audit.log(
        actor_id=current_user.id,
        action="verify",
        entity_type="request",
        entity_id=request_id,
        after_state={
            "result": body.result.value,
            "status": request.status.value,
        },
    )

    return {
        "data": {
            "request_id": str(request_id),
            "result": body.result.value,
            "status": request.status.value,
        },
        "message": "تمت عملية التحقق بنجاح",
    }


@router.post("/requests/{request_id}/merge")
async def merge_requests(
    request_id: UUID,
    body: MergeRequest,
    current_user: User = Depends(get_current_coordinator),
    db: AsyncSession = Depends(get_db),
):
    """دمج طلب مكرر مع الطلب الأصلي."""
    # Get both requests
    source_result = await db.execute(select(Request).where(Request.id == request_id))
    source = source_result.scalar_one_or_none()
    if not source:
        raise NotFoundError("الطلب المصدر", str(request_id))

    target_result = await db.execute(select(Request).where(Request.id == body.merge_into))
    target = target_result.scalar_one_or_none()
    if not target:
        raise NotFoundError("الطلب الهدف", str(body.merge_into))

    # Mark source as duplicate
    source.duplicate_of = body.merge_into
    source.status = RequestStatus.CANCELLED

    # Increase target quantity
    target.quantity += source.quantity

    await db.flush()

    audit = AuditService(db)
    await audit.log(
        actor_id=current_user.id,
        action="merge",
        entity_type="request",
        entity_id=request_id,
        after_state={"merged_into": str(body.merge_into)},
    )

    return {
        "data": {
            "source_id": str(request_id),
            "merged_into": str(body.merge_into),
        },
        "message": "تم دمج الطلب بنجاح",
    }
