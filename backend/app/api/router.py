from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.requests import router as requests_router
from app.api.v1.organizations import router as market_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.verification import router as verification_router
from app.api.v1.stats import router as stats_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(requests_router)
api_router.include_router(market_router)
api_router.include_router(assignments_router)
api_router.include_router(verification_router)
api_router.include_router(stats_router)
