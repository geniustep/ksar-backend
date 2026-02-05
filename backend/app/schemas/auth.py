from pydantic import BaseModel, Field
import re


class PhoneNumber(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20, examples=["+212612345678"])

    @classmethod
    def validate_phone(cls, v: str) -> str:
        pattern = r"^\+?[1-9]\d{8,14}$"
        if not re.match(pattern, v):
            raise ValueError("رقم الهاتف غير صالح")
        return v


class OTPStartRequest(PhoneNumber):
    pass


class OTPStartResponse(BaseModel):
    message: str = "تم إرسال رمز التحقق"
    expires_in: int = 300


class OTPVerifyRequest(PhoneNumber):
    otp: str = Field(..., min_length=4, max_length=8)


class OTPVerifyResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
