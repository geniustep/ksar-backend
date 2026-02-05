"""
تجميع جميع مسارات API
"""
from fastapi import APIRouter

from app.api.v1 import public, auth, admin, organizations

api_router = APIRouter(prefix="/api/v1")

# المسارات العامة (بدون تسجيل)
api_router.include_router(public.router)

# المصادقة
api_router.include_router(auth.router)

# الإدارة
api_router.include_router(admin.router)

# المؤسسات
api_router.include_router(organizations.router)
