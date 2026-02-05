import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service for sending OTPs and notifications."""

    async def send_otp(self, phone: str, otp: str) -> bool:
        """Send OTP code via SMS."""
        message = f"رمز التحقق الخاص بك في إغاثة: {otp}\nصالح لمدة {settings.OTP_EXPIRE_MINUTES} دقائق."
        return await self._send(phone, message)

    async def send_request_assigned(self, phone: str, category: str, org_name: str, language: str = "ar") -> bool:
        """Notify resident their request was assigned."""
        if language == "fr":
            message = f"Bonne nouvelle! Votre demande ({category}) a été prise en charge par {org_name}."
        else:
            message = f"بشرى سارة! تم تبني طلبك ({category}) من قبل {org_name}."
        return await self._send(phone, message)

    async def send_request_delivered(self, phone: str, category: str, language: str = "ar") -> bool:
        """Notify resident their request was delivered."""
        if language == "fr":
            message = f"Votre demande ({category}) a été livrée. Merci de confirmer la réception."
        else:
            message = f"تم تسليم طلبك ({category}). شكراً لتأكيد الاستلام."
        return await self._send(phone, message)

    async def send_request_verified(self, phone: str, category: str, language: str = "ar") -> bool:
        """Notify resident their request was verified."""
        if language == "fr":
            message = f"Votre demande ({category}) a été vérifiée et est maintenant visible aux organisations."
        else:
            message = f"تم التحقق من طلبك ({category}) وأصبح مرئياً للمؤسسات المانحة."
        return await self._send(phone, message)

    async def _send(self, phone: str, message: str) -> bool:
        """Send SMS via configured provider."""
        if settings.SMS_PROVIDER == "console":
            logger.info(f"[SMS -> {phone}] {message}")
            return True
        elif settings.SMS_PROVIDER == "twilio":
            return await self._send_twilio(phone, message)
        else:
            logger.warning(f"Unknown SMS provider: {settings.SMS_PROVIDER}")
            return False

    async def _send_twilio(self, phone: str, message: str) -> bool:
        """Send SMS via Twilio."""
        try:
            import httpx

            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={
                        "To": phone,
                        "From": settings.TWILIO_PHONE_NUMBER,
                        "Body": message,
                    },
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                )
                if response.status_code == 201:
                    logger.info(f"SMS sent to {phone}")
                    return True
                else:
                    logger.error(f"Twilio error: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False


sms_service = SMSService()
