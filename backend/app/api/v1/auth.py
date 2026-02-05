"""
واجهة المصادقة - للجميع (الإدارة، المؤسسات، المواطنين)
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
    RegisterRequest,
    RegisterResponse,
    TokenRefreshResponse,
    UserResponse,
    UserProfileResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    decode_token,
)
from app.core.constants import UserRole, UserStatus

router = APIRouter(prefix="/auth", tags=["المصادقة - Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    تسجيل مستخدم جديد (مواطن)
    
    - متاح للجميع
    - يُنشئ حساب بدور "مواطن"
    """
    # التحقق من عدم وجود البريد مسبقاً
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مستخدم بالفعل",
        )
    
    # التحقق من رقم الهاتف
    phone_result = await db.execute(
        select(User).where(User.phone == body.phone)
    )
    existing_phone = phone_result.scalar_one_or_none()
    
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رقم الهاتف مستخدم بالفعل",
        )
    
    # إنشاء المستخدم
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        phone=body.phone,
        address=body.address,
        city=body.city,
        region=body.region,
        role=UserRole.CITIZEN,
        status=UserStatus.ACTIVE,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # إنشاء التوكن
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "org_id": None,
        }
    )
    
    return RegisterResponse(
        message="تم إنشاء الحساب بنجاح. يمكنك الآن تقديم طلباتك.",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
        ),
        access_token=access_token,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """تسجيل الدخول لجميع المستخدمين"""
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
            phone=user.phone,
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


@router.get("/me", response_model=UserProfileResponse)
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
    
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        address=user.address,
        city=user.city,
        region=user.region,
        role=user.role,
        organization_id=org_id,
        organization_name=org_name,
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    body: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """تحديث الملف الشخصي"""
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
    
    # تحديث الحقول المُرسلة فقط
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.phone is not None:
        # التحقق من عدم استخدام الرقم
        phone_check = await db.execute(
            select(User).where(User.phone == body.phone, User.id != user.id)
        )
        if phone_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="رقم الهاتف مستخدم بالفعل",
            )
        user.phone = body.phone
    if body.address is not None:
        user.address = body.address
    if body.city is not None:
        user.city = body.city
    if body.region is not None:
        user.region = body.region
    
    await db.commit()
    await db.refresh(user)
    
    org_id = payload.get("org_id")
    org_name = None
    if org_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = org_result.scalar_one_or_none()
        if org:
            org_name = org.name
    
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        address=user.address,
        city=user.city,
        region=user.region,
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
