from datetime import datetime, timezone
from typing import Optional, Tuple, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import RequestStatus, RequestCategory, AssignmentStatus
from app.core.exceptions import (
    NotFoundError,
    ForbiddenError,
    DuplicateError,
    InvalidStatusTransition,
    ValidationError,
)
from app.models.request import Request
from app.models.assignment import Assignment
from app.models.user import User, ResidentProfile
from app.models.organization import Organization
from app.services.priority_service import calculate_priority
from app.services.duplicate_service import DuplicateService


class RequestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(
        self,
        user: User,
        category: RequestCategory,
        location_text: str,
        description: Optional[str] = None,
        quantity: int = 1,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None,
        region_code: Optional[str] = None,
    ) -> Request:
        # Check for duplicates
        dup_service = DuplicateService(self.db)
        existing = await dup_service.check_duplicate(user.phone, category.value, location_text)

        if existing:
            raise DuplicateError(
                message="يوجد طلب مشابه مسجل مسبقاً",
                details={"existing_request_id": str(existing.id)},
            )

        # Create the request
        request = Request(
            created_by=user.id,
            category=category,
            description=description,
            quantity=quantity,
            location_text=location_text,
            location_lat=location_lat,
            location_lng=location_lng,
            region_code=region_code,
            duplicate_hash=dup_service.compute_hash(user.phone, category.value, location_text),
        )

        self.db.add(request)
        await self.db.flush()

        # Calculate priority
        profile = user.resident_profile
        request.priority_score = calculate_priority(request, profile)
        await self.db.flush()
        await self.db.refresh(request)

        return request

    async def get_request(self, request_id: UUID) -> Request:
        result = await self.db.execute(
            select(Request)
            .options(selectinload(Request.assignments))
            .where(Request.id == request_id)
        )
        request = result.scalar_one_or_none()
        if not request:
            raise NotFoundError("الطلب", str(request_id))
        return request

    async def get_user_requests(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Request], int]:
        query = select(Request).where(Request.created_by == user_id)

        if status == "active":
            active_statuses = [
                RequestStatus.NEW,
                RequestStatus.PENDING_VERIFICATION,
                RequestStatus.VERIFIED,
                RequestStatus.ASSIGNED,
                RequestStatus.IN_PROGRESS,
            ]
            query = query.where(Request.status.in_(active_statuses))
        elif status:
            query = query.where(Request.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # Paginate
        query = query.order_by(Request.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_request(
        self,
        request_id: UUID,
        user_id: UUID,
        **kwargs,
    ) -> Request:
        request = await self.get_request(request_id)

        if request.created_by != user_id:
            raise ForbiddenError("لا يمكنك تعديل طلب شخص آخر")

        editable_statuses = [RequestStatus.NEW, RequestStatus.PENDING_VERIFICATION, RequestStatus.VERIFIED]
        if request.status not in editable_statuses:
            raise InvalidStatusTransition(
                request.status.value,
                "edit",
            )

        for key, value in kwargs.items():
            if value is not None and hasattr(request, key):
                setattr(request, key, value)

        await self.db.flush()
        await self.db.refresh(request)
        return request

    async def cancel_request(self, request_id: UUID, user_id: UUID) -> Request:
        request = await self.get_request(request_id)

        if request.created_by != user_id:
            raise ForbiddenError("لا يمكنك إلغاء طلب شخص آخر")

        if request.status == RequestStatus.DELIVERED:
            raise InvalidStatusTransition(RequestStatus.DELIVERED.value, RequestStatus.CANCELLED.value)

        request.status = RequestStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(request)
        return request

    async def get_market_requests(
        self,
        category: Optional[RequestCategory] = None,
        region: Optional[str] = None,
        priority_min: Optional[int] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[dict], int]:
        """Get verified requests for the market (organizations view)."""
        query = select(Request).where(Request.status == RequestStatus.VERIFIED)

        if category:
            query = query.where(Request.category == category)
        if region:
            query = query.where(Request.region_code == region)
        if priority_min is not None:
            query = query.where(Request.priority_score >= priority_min)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # Paginate, ordered by priority
        query = query.order_by(Request.priority_score.desc(), Request.created_at.asc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        requests = list(result.scalars().all())

        # Enrich with special_cases from resident profiles
        items = []
        for req in requests:
            profile_result = await self.db.execute(
                select(ResidentProfile).where(ResidentProfile.user_id == req.created_by)
            )
            profile = profile_result.scalar_one_or_none()

            items.append({
                "id": req.id,
                "category": req.category,
                "description": req.description,
                "quantity": req.quantity,
                "priority_score": req.priority_score,
                "location_text": req.location_text,
                "region_code": req.region_code,
                "created_at": req.created_at,
                "special_cases": profile.special_cases if profile else [],
            })

        return items, total

    async def assign_request(
        self,
        request_id: UUID,
        org: Organization,
    ) -> Assignment:
        """Organization pledges to fulfill a request."""
        request = await self.get_request(request_id)

        if request.status != RequestStatus.VERIFIED:
            raise InvalidStatusTransition(request.status.value, RequestStatus.ASSIGNED.value)

        # Check if already assigned
        existing = await self.db.execute(
            select(Assignment).where(
                and_(
                    Assignment.request_id == request_id,
                    Assignment.status.not_in([AssignmentStatus.FAILED]),
                )
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateError("هذا الطلب مخصص لمؤسسة أخرى بالفعل")

        assignment = Assignment(
            request_id=request_id,
            org_id=org.id,
        )
        self.db.add(assignment)

        request.status = RequestStatus.ASSIGNED
        await self.db.flush()

        # Send SMS notification to resident
        user_result = await self.db.execute(
            select(User).where(User.id == request.created_by)
        )
        user = user_result.scalar_one_or_none()
        if user:
            from app.services.sms_service import sms_service
            await sms_service.send_request_assigned(
                user.phone, request.category.value, org.name, user.language
            )

        return assignment

    async def update_assignment(
        self,
        assignment_id: UUID,
        org_id: UUID,
        status: Optional[AssignmentStatus] = None,
        proof_note: Optional[str] = None,
        proof_media_url: Optional[str] = None,
        eta=None,
    ) -> Assignment:
        result = await self.db.execute(
            select(Assignment)
            .options(selectinload(Assignment.request))
            .where(Assignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise NotFoundError("التخصيص", str(assignment_id))
        if assignment.org_id != org_id:
            raise ForbiddenError("لا يمكنك تعديل تخصيص مؤسسة أخرى")

        if status:
            assignment.status = status

            if status == AssignmentStatus.DELIVERED:
                assignment.request.status = RequestStatus.DELIVERED
                assignment.request.delivered_at = datetime.now(timezone.utc)

                # Notify resident
                user_result = await self.db.execute(
                    select(User).where(User.id == assignment.request.created_by)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    from app.services.sms_service import sms_service
                    await sms_service.send_request_delivered(
                        user.phone, assignment.request.category.value, user.language
                    )

            elif status == AssignmentStatus.EN_ROUTE:
                assignment.request.status = RequestStatus.IN_PROGRESS

        if proof_note is not None:
            assignment.proof_note = proof_note
        if proof_media_url is not None:
            assignment.proof_media_url = proof_media_url
        if eta is not None:
            assignment.eta = eta

        await self.db.flush()
        return assignment

    async def fail_assignment(
        self,
        assignment_id: UUID,
        org_id: UUID,
        failure_reason: str,
    ) -> Assignment:
        result = await self.db.execute(
            select(Assignment)
            .options(selectinload(Assignment.request))
            .where(Assignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise NotFoundError("التخصيص", str(assignment_id))
        if assignment.org_id != org_id:
            raise ForbiddenError("لا يمكنك تعديل تخصيص مؤسسة أخرى")

        assignment.status = AssignmentStatus.FAILED
        assignment.failure_reason = failure_reason

        # Return request to verified state
        assignment.request.status = RequestStatus.VERIFIED

        await self.db.flush()
        return assignment

    async def get_org_assignments(
        self,
        org_id: UUID,
        status: Optional[AssignmentStatus] = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Assignment], int]:
        query = select(Assignment).where(Assignment.org_id == org_id)

        if status:
            query = query.where(Assignment.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        query = query.order_by(Assignment.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
