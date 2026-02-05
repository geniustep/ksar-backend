"""
واجهة المصادقة - للإدارة والمؤسسات
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshResponse,
    UserResponse,
    ChangePasswordRequest,
)
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["المصادقة - Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """تسجيل الدخول للإدارة والمؤسسات"""
    # البحث عن المستخدم
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
        )
    
    if user.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="الحساب معطل",
        )
    
    # تحديث وقت آخر دخول
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    # الحصول على بيانات المؤسسة إن وجدت
    org_id = None
    org_name = None
    if user.role.value == "organization":
        org_result = await db.execute(
            select(Organization).where(Organization.user_id == user.id)
        )
        org = org_result.scalar_one_or_none()
        if org:
            org_id = str(org.id)
            org_name = org.name
    
    # إنشاء التوكن
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "org_id": org_id,
        }
    )
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            organization_id=org_id,
            organization_name=org_name,
        ),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """تحديث رمز الوصول"""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز غير صالح",
        )
    
    # التحقق من المستخدم
    result = await db.execute(
        select(User).where(User.id == payload.get("sub"))
    )
    user = result.scalar_one_or_none()
    
    if not user or user.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="المستخدم غير موجود أو معطل",
        )
    
    # إنشاء توكن جديد
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "org_id": payload.get("org_id"),
        }
    )
    
    return TokenRefreshResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """الحصول على بيانات المستخدم الحالي"""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز غير صالح",
        )
    
    result = await db.execute(
        select(User).where(User.id == payload.get("sub"))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود",
        )
    
    org_id = payload.get("org_id")
    org_name = None
    if org_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = org_result.scalar_one_or_none()
        if org:
            org_name = org.name
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=org_id,
        organization_name=org_name,
    )


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """تغيير كلمة المرور"""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز غير صالح",
        )
    
    result = await db.execute(
        select(User).where(User.id == payload.get("sub"))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود",
        )
    
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الحالية غير صحيحة",
        )
    
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    
    return {"message": "تم تغيير كلمة المرور بنجاح"}
