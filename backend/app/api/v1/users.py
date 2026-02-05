from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import (
    MeResponse,
    UserUpdate,
    ResidentProfileUpdate,
    ResidentProfileResponse,
)
from app.models.user import User, ResidentProfile
from app.core.constants import UserRole

router = APIRouter(tags=["المستخدمون - Users"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """الحصول على بيانات المستخدم الحالي."""
    profile = None
    if current_user.role == UserRole.RESIDENT and current_user.resident_profile:
        profile = ResidentProfileResponse.model_validate(current_user.resident_profile)

    return MeResponse(
        id=current_user.id,
        phone=current_user.phone,
        role=current_user.role,
        full_name=current_user.full_name,
        language=current_user.language,
        status=current_user.status,
        phone_verified=current_user.phone_verified,
        profile=profile,
        created_at=current_user.created_at,
    )


@router.patch("/me", response_model=MeResponse)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """تحديث بيانات المستخدم الحالي."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.language is not None:
        current_user.language = body.language

    await db.flush()

    profile = None
    if current_user.role == UserRole.RESIDENT and current_user.resident_profile:
        profile = ResidentProfileResponse.model_validate(current_user.resident_profile)

    return MeResponse(
        id=current_user.id,
        phone=current_user.phone,
        role=current_user.role,
        full_name=current_user.full_name,
        language=current_user.language,
        status=current_user.status,
        phone_verified=current_user.phone_verified,
        profile=profile,
        created_at=current_user.created_at,
    )


@router.patch("/me/profile", response_model=ResidentProfileResponse)
async def update_profile(
    body: ResidentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """تحديث ملف الساكن."""
    from app.core.exceptions import ForbiddenError, NotFoundError

    if current_user.role != UserRole.RESIDENT:
        raise ForbiddenError("هذه الخدمة متاحة للساكنة فقط")

    profile = current_user.resident_profile
    if not profile:
        raise NotFoundError("ملف الساكن")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.flush()
    return ResidentProfileResponse.model_validate(profile)
