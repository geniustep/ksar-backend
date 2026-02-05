import hashlib
import random
import string
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_otp(length: int = None) -> str:
    length = length or settings.OTP_LENGTH
    return "".join(random.choices(string.digits, k=length))


def hash_otp(otp: str) -> str:
    return pwd_context.hash(otp)


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    return pwd_context.verify(plain_otp, hashed_otp)


def normalize_arabic(text: str) -> str:
    """Remove Arabic diacritics and normalize text for comparison."""
    # Remove tashkeel (diacritics)
    text = re.sub(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]", "", text)
    # Normalize alef variants
    text = re.sub(r"[إأآا]", "ا", text)
    # Normalize taa marbuta
    text = text.replace("ة", "ه")
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_duplicate_hash(phone: str, category: str, location_text: str) -> str:
    normalized_location = normalize_arabic(location_text)[:50]
    data = f"{phone}:{category}:{normalized_location}"
    return hashlib.sha256(data.encode()).hexdigest()
