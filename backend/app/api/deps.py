from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.core.constants import UserRole
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("رمز الوصول غير صالح أو منتهي الصلاحية")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError()

    result = await db.execute(
        select(User)
        .options(selectinload(User.resident_profile))
        .options(selectinload(User.organization))
        .where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("المستخدم غير موجود")

    if user.status.value == "suspended":
        raise ForbiddenError("تم تعليق حسابك")

    return user


async def get_current_resident(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.RESIDENT:
        raise ForbiddenError("هذه الخدمة متاحة للساكنة فقط")
    return current_user


async def get_current_organization_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ORGANIZATION:
        raise ForbiddenError("هذه الخدمة متاحة للمؤسسات فقط")
    return current_user


async def get_current_coordinator(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.COORDINATOR, UserRole.ADMIN):
        raise ForbiddenError("هذه الخدمة متاحة للمنسقين فقط")
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("هذه الخدمة متاحة للمشرفين فقط")
    return current_user


async def get_idempotency_key(
    x_idempotency_key: Optional[str] = Header(default=None),
) -> Optional[str]:
    return x_idempotency_key
