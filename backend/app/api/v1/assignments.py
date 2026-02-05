from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_organization_user
from app.core.constants import AssignmentStatus
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdateStatus,
    AssignmentFailure,
    AssignmentResponse,
    AssignmentWithContactResponse,
    PaginatedAssignments,
)
from app.services.request_service import RequestService
from app.services.audit_service import AuditService
from app.models.user import User
from app.models.organization import Organization

router = APIRouter(prefix="/assignments", tags=["التبني والتنفيذ - Assignments"])


@router.post("", response_model=AssignmentWithContactResponse, status_code=201)
async def create_assignment(
    body: AssignmentCreate,
    current_user: User = Depends(get_current_organization_user),
    db: AsyncSession = Depends(get_db),
):
    """تبني طلب (المؤسسة تتعهد بالتنفيذ)."""
    org = current_user.organization
    if not org:
        raise ForbiddenError("يجب إكمال ملف المؤسسة أولاً")

    service = RequestService(db)
    assignment = await service.assign_request(body.request_id, org)

    # Get request details for response with contact info
    request = await service.get_request(body.request_id)
    user_result = await db.execute(
        select(User).where(User.id == request.created_by)
    )
    resident = user_result.scalar_one_or_none()

    # Audit log
    audit = AuditService(db)
    await audit.log(
        actor_id=current_user.id,
        action="assign",
        entity_type="assignment",
        entity_id=assignment.id,
        after_state={"request_id": str(body.request_id), "org_id": str(org.id)},
    )

    return AssignmentWithContactResponse(
        id=assignment.id,
        request_id=assignment.request_id,
        org_id=assignment.org_id,
        status=assignment.status,
        eta=assignment.eta,
        proof_note=assignment.proof_note,
        proof_media_url=assignment.proof_media_url,
        failure_reason=assignment.failure_reason,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        contact_phone=resident.phone if resident else None,
        location_text=request.location_text,
    )


@router.get("/mine", response_model=PaginatedAssignments)
async def get_my_assignments(
    status: Optional[AssignmentStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_organization_user),
    db: AsyncSession = Depends(get_db),
):
    """الحصول على تخصيصات مؤسستي."""
    org = current_user.organization
    if not org:
        raise ForbiddenError("يجب إكمال ملف المؤسسة أولاً")

    service = RequestService(db)
    items, total = await service.get_org_assignments(
        org_id=org.id,
        status=status,
        page=page,
        limit=limit,
    )
    return PaginatedAssignments(
        items=[AssignmentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    body: AssignmentUpdateStatus,
    current_user: User = Depends(get_current_organization_user),
    db: AsyncSession = Depends(get_db),
):
    """تحديث حالة التخصيص (تسليم، في الطريق...)."""
    org = current_user.organization
    if not org:
        raise ForbiddenError("يجب إكمال ملف المؤسسة أولاً")

    service = RequestService(db)
    assignment = await service.update_assignment(
        assignment_id=assignment_id,
        org_id=org.id,
        status=body.status,
        proof_note=body.proof_note,
        proof_media_url=body.proof_media_url,
        eta=body.eta,
    )

    audit = AuditService(db)
    await audit.log(
        actor_id=current_user.id,
        action="update_assignment",
        entity_type="assignment",
        entity_id=assignment.id,
        after_state={"status": assignment.status.value},
    )

    return AssignmentResponse.model_validate(assignment)


@router.patch("/{assignment_id}/fail", response_model=AssignmentResponse)
async def fail_assignment(
    assignment_id: UUID,
    body: AssignmentFailure,
    current_user: User = Depends(get_current_organization_user),
    db: AsyncSession = Depends(get_db),
):
    """تعذر التسليم."""
    org = current_user.organization
    if not org:
        raise ForbiddenError("يجب إكمال ملف المؤسسة أولاً")

    service = RequestService(db)
    assignment = await service.fail_assignment(
        assignment_id=assignment_id,
        org_id=org.id,
        failure_reason=body.failure_reason,
    )

    audit = AuditService(db)
    await audit.log(
        actor_id=current_user.id,
        action="fail_assignment",
        entity_type="assignment",
        entity_id=assignment.id,
        after_state={"failure_reason": body.failure_reason},
    )

    return AssignmentResponse.model_validate(assignment)
