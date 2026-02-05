from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    OTPStartRequest,
    OTPStartResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    TokenRefreshResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["المصادقة - Authentication"])
security = HTTPBearer()


@router.post("/start", response_model=OTPStartResponse)
async def start_otp(
    body: OTPStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """إرسال رمز التحقق OTP إلى رقم الهاتف."""
    service = AuthService(db)
    expires_in = await service.start_otp(body.phone)
    return OTPStartResponse(expires_in=expires_in)


@router.post("/verify", response_model=OTPVerifyResponse)
async def verify_otp(
    body: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """التحقق من رمز OTP وتسجيل الدخول."""
    service = AuthService(db)
    user, is_new = await service.verify_otp(body.phone, body.otp)
    access_token, refresh_token = service.create_tokens(user)

    return OTPVerifyResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        is_new_user=is_new,
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """تحديث رمز الوصول باستخدام رمز التحديث."""
    service = AuthService(db)
    new_access = await service.refresh_access_token(credentials.credentials)
    return TokenRefreshResponse(access_token=new_access)
