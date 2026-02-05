from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_resident, get_idempotency_key
from app.schemas.request import (
    RequestCreate,
    RequestUpdate,
    RequestResponse,
    RequestDetailResponse,
    RequestCancelResponse,
    PaginatedRequests,
)
from app.services.request_service import RequestService
from app.services.audit_service import AuditService
from app.models.user import User

router = APIRouter(prefix="/requests", tags=["الطلبات - Requests"])


@router.post("", response_model=RequestResponse, status_code=201)
async def create_request(
    body: RequestCreate,
    current_user: User = Depends(get_current_resident),
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Depends(get_idempotency_key),
):
    """إنشاء طلب مساعدة جديد."""
    service = RequestService(db)
    request = await service.create_request(
        user=current_user,
        category=body.category,
        description=body.description,
        quantity=body.quantity,
        location_text=body.location_text,
        location_lat=body.location_lat,
        location_lng=body.location_lng,
        region_code=body.region_code,
    )

    # Audit log
    audit = AuditService(db)
    await audit.log(
        actor_id=current_user.id,
        action="create",
        entity_type="request",
        entity_id=request.id,
        after_state={"category": request.category.value, "status": request.status.value},
    )

    return RequestResponse.model_validate(request)


@router.get("/mine", response_model=PaginatedRequests)
async def get_my_requests(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_resident),
    db: AsyncSession = Depends(get_db),
):
    """الحصول على طلباتي."""
    service = RequestService(db)
    items, total = await service.get_user_requests(
        user_id=current_user.id,
        status=status,
        page=page,
        limit=limit,
    )
    return PaginatedRequests(
        items=[RequestResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.get("/{request_id}", response_model=RequestDetailResponse)
async def get_request(
    request_id: UUID,
    current_user: User = Depends(get_current_resident),
    db: AsyncSession = Depends(get_db),
):
    """الحصول على تفاصيل طلب."""
    service = RequestService(db)
    request = await service.get_request(request_id)

    from app.core.exceptions import ForbiddenError
    if request.created_by != current_user.id:
        raise ForbiddenError("لا يمكنك عرض طلب شخص آخر")

    return RequestDetailResponse.model_validate(request)


@router.patch("/{request_id}", response_model=RequestResponse)
async def update_request(
    request_id: UUID,
    body: RequestUpdate,
    current_user: User = Depends(get_current_resident),
    db: AsyncSession = Depends(get_db),
):
    """تحديث طلب (مسموح فقط قبل التبني)."""
    service = RequestService(db)
    request = await service.update_request(
        request_id=request_id,
        user_id=current_user.id,
        **body.model_dump(exclude_unset=True),
    )
    return RequestResponse.model_validate(request)


@router.post("/{request_id}/cancel", response_model=RequestCancelResponse)
async def cancel_request(
    request_id: UUID,
    current_user: User = Depends(get_current_resident),
    db: AsyncSession = Depends(get_db),
):
    """إلغاء طلب."""
    service = RequestService(db)
    request = await service.cancel_request(request_id, current_user.id)

    audit = AuditService(db)
    await audit.log(
        actor_id=current_user.id,
        action="cancel",
        entity_type="request",
        entity_id=request.id,
    )

    return RequestCancelResponse(id=request.id, status=request.status)
