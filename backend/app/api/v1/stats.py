from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.core.constants import RequestStatus, RequestCategory
from app.models.request import Request
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["الإحصائيات - Statistics"])


@router.get("/overview")
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات عامة عن المنصة."""
    # Total requests
    total_result = await db.execute(select(func.count(Request.id)))
    total_requests = total_result.scalar()

    # By status
    status_result = await db.execute(
        select(Request.status, func.count(Request.id))
        .group_by(Request.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}

    # By category
    category_result = await db.execute(
        select(Request.category, func.count(Request.id))
        .group_by(Request.category)
    )
    by_category = {row[0].value: row[1] for row in category_result.all()}

    # Average delivery time
    avg_delivery = await db.execute(
        select(
            func.avg(
                func.extract("epoch", Request.delivered_at - Request.created_at) / 3600
            )
        ).where(
            Request.status == RequestStatus.DELIVERED,
            Request.delivered_at.is_not(None),
        )
    )
    avg_hours = avg_delivery.scalar()

    return {
        "data": {
            "total_requests": total_requests or 0,
            "by_status": by_status,
            "by_category": by_category,
            "avg_delivery_time_hours": round(avg_hours, 1) if avg_hours else None,
        }
    }


@router.get("/by-region")
async def get_by_region(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """إحصائيات حسب المنطقة."""
    result = await db.execute(
        select(
            Request.region_code,
            func.count(Request.id).label("total"),
            func.count(case(
                (Request.status.in_([
                    RequestStatus.NEW,
                    RequestStatus.PENDING_VERIFICATION,
                    RequestStatus.VERIFIED,
                ]), 1)
            )).label("pending"),
        )
        .where(Request.region_code.is_not(None))
        .group_by(Request.region_code)
    )

    regions = []
    for row in result.all():
        regions.append({
            "code": row[0],
            "total": row[1],
            "pending": row[2],
        })

    return {
        "data": {
            "regions": regions,
        }
    }
