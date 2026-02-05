from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_duplicate_hash
from app.core.constants import RequestStatus
from app.models.request import Request


class DuplicateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_duplicate(
        self, phone: str, category: str, location_text: str
    ) -> Optional[Request]:
        """Check if a similar request exists in the last 7 days."""
        dup_hash = generate_duplicate_hash(phone, category, location_text)

        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        excluded_statuses = [
            RequestStatus.CANCELLED,
            RequestStatus.REJECTED,
            RequestStatus.DELIVERED,
        ]

        result = await self.db.execute(
            select(Request).where(
                and_(
                    Request.duplicate_hash == dup_hash,
                    Request.created_at > cutoff,
                    Request.status.not_in(excluded_statuses),
                )
            )
        )
        return result.scalar_one_or_none()

    def compute_hash(self, phone: str, category: str, location_text: str) -> str:
        return generate_duplicate_hash(phone, category, location_text)
