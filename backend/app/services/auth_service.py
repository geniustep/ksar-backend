from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    generate_otp,
    hash_otp,
    verify_otp,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import OTPError, UnauthorizedError, RateLimitError
from app.core.constants import UserRole
from app.models.user import User, ResidentProfile

# In-memory OTP store for development. In production, use Redis.
_otp_store: dict = {}


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_otp(self, phone: str) -> int:
        """Send OTP to phone. Returns expiration time in seconds."""
        # Check rate limit on OTP requests
        store_key = f"otp:{phone}"
        if store_key in _otp_store:
            existing = _otp_store[store_key]
            if existing["attempts"] >= settings.OTP_MAX_ATTEMPTS:
                if datetime.now(timezone.utc) < existing["blocked_until"]:
                    raise RateLimitError()
                # Reset after block period
                del _otp_store[store_key]

        otp = generate_otp()
        hashed = hash_otp(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        _otp_store[store_key] = {
            "hashed_otp": hashed,
            "expires_at": expires_at,
            "attempts": _otp_store.get(store_key, {}).get("attempts", 0),
            "blocked_until": datetime.now(timezone.utc),
        }

        # Send OTP via SMS service
        from app.services.sms_service import sms_service
        await sms_service.send_otp(phone, otp)

        return settings.OTP_EXPIRE_MINUTES * 60

    async def verify_otp(self, phone: str, otp: str) -> Tuple[User, bool]:
        """Verify OTP and return (user, is_new_user)."""
        store_key = f"otp:{phone}"

        if store_key not in _otp_store:
            raise OTPError("لم يتم إرسال رمز التحقق لهذا الرقم")

        stored = _otp_store[store_key]

        # Check expiration
        if datetime.now(timezone.utc) > stored["expires_at"]:
            del _otp_store[store_key]
            raise OTPError("انتهت صلاحية رمز التحقق")

        # Check attempts
        stored["attempts"] += 1
        if stored["attempts"] > settings.OTP_MAX_ATTEMPTS:
            stored["blocked_until"] = datetime.now(timezone.utc) + timedelta(minutes=15)
            raise OTPError("تم تجاوز عدد المحاولات المسموح. يرجى المحاولة لاحقاً")

        # Verify OTP
        if not verify_otp(otp, stored["hashed_otp"]):
            raise OTPError("رمز التحقق غير صحيح")

        # OTP verified, clean up
        del _otp_store[store_key]

        # Find or create user
        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )
        user = result.scalar_one_or_none()
        is_new = False

        if not user:
            user = User(
                phone=phone,
                phone_verified=True,
                role=UserRole.RESIDENT,
            )
            self.db.add(user)
            await self.db.flush()

            # Create empty resident profile
            profile = ResidentProfile(user_id=user.id)
            self.db.add(profile)
            await self.db.flush()
            is_new = True
        else:
            user.phone_verified = True
            await self.db.flush()

        return user, is_new

    def create_tokens(self, user: User) -> Tuple[str, str]:
        """Create access and refresh tokens for user."""
        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token_str: str) -> Optional[str]:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("رمز التحديث غير صالح")

        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id:
            raise UnauthorizedError()

        token_data = {"sub": user_id, "role": role}
        return create_access_token(token_data)
