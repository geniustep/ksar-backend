from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.core.constants import RequestCategory
from app.schemas.request import PaginatedMarketRequests, MarketRequestResponse
from app.services.request_service import RequestService
from app.models.user import User

router = APIRouter(prefix="/market", tags=["السوق - Market"])


@router.get("/requests", response_model=PaginatedMarketRequests)
async def get_market_requests(
    category: Optional[RequestCategory] = Query(default=None),
    region: Optional[str] = Query(default=None),
    priority_min: Optional[int] = Query(default=None, ge=0, le=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """عرض الطلبات المتاحة للمؤسسات (السوق)."""
    from app.core.exceptions import ForbiddenError
    from app.core.constants import UserRole

    if current_user.role not in (UserRole.ORGANIZATION, UserRole.COORDINATOR, UserRole.ADMIN):
        raise ForbiddenError("هذه الخدمة متاحة للمؤسسات والمنسقين فقط")

    service = RequestService(db)
    items, total = await service.get_market_requests(
        category=category,
        region=region,
        priority_min=priority_min,
        page=page,
        limit=limit,
    )
    return PaginatedMarketRequests(
        items=[MarketRequestResponse(**item) for item in items],
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total,
    )
