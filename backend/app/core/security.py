"""
وحدة الأمان - تشفير كلمات المرور وإدارة التوكنات
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

# مكونات الكود القوي
_UPPER = 'ABCDEFGHJKMNPQRSTUVWXYZ'
_LOWER = 'abcdefghjkmnpqrstuvwxyz'
_DIGITS = '23456789'
_SYMBOLS = '@#$%&*!?'
_ALL_CHARS = _UPPER + _LOWER + _DIGITS + _SYMBOLS


def generate_strong_code(length: int = 10) -> str:
    """
    توليد كود دخول قوي يحتوي إجباريا على:
    - حرف كبير (Majuscule)
    - حرف صغير (Minuscule)
    - رقم
    - رمز خاص
    """
    while True:
        # ضمان وجود حرف واحد على الأقل من كل نوع
        code_chars = [
            secrets.choice(_UPPER),
            secrets.choice(_LOWER),
            secrets.choice(_DIGITS),
            secrets.choice(_SYMBOLS),
        ]
        # ملء باقي الكود بأحرف عشوائية من الكل
        code_chars += [secrets.choice(_ALL_CHARS) for _ in range(length - 4)]
        # خلط الترتيب
        result = list(code_chars)
        secrets.SystemRandom().shuffle(result)
        code = ''.join(result)
        # تأكد إضافي
        has_upper = any(c in _UPPER for c in code)
        has_lower = any(c in _LOWER for c in code)
        has_digit = any(c in _DIGITS for c in code)
        has_symbol = any(c in _SYMBOLS for c in code)
        if has_upper and has_lower and has_digit and has_symbol:
            return code

# إعداد تشفير كلمات المرور
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """تشفير كلمة المرور"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """إنشاء رمز الوصول JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """فك تشفير التوكن"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
