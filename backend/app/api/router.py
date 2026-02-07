"""
تجميع جميع مسارات API
"""
from fastapi import APIRouter

from app.api.v1 import public, auth, admin, organizations, citizen, inspector

api_router = APIRouter(prefix="/api/v1")

# المسارات العامة (بدون تسجيل) - للتصفح فقط
api_router.include_router(public.router)

# المصادقة (تسجيل + دخول)
api_router.include_router(auth.router)

# الإدارة
api_router.include_router(admin.router)

# المؤسسات
api_router.include_router(organizations.router)

# المواطنون (مقدمو الطلبات)
api_router.include_router(citizen.router)

# المراقبون
api_router.include_router(inspector.router)
