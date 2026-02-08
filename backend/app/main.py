"""
تطبيق KSAR - منصة تنسيق المساعدات الإنسانية
"""
import logging
import traceback
from contextlib import asynccontextmanager

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    # Startup
    print("🚀 KSAR Backend is starting...")
    yield
    # Shutdown
    print("👋 KSAR Backend is shutting down...")


app = FastAPI(
    title="KSAR - منصة المساعدات الإنسانية",
    description="""
    ## منصة تنسيق المساعدات الإنسانية
    
    ### الميزات:
    - **تقديم الطلبات**: يمكن للمحتاجين تقديم طلبات المساعدة بدون تسجيل
    - **تتبع الطلبات**: متابعة حالة الطلب برمز التتبع
    - **إدارة المؤسسات**: التكفل بالطلبات وإتمامها
    - **لوحة الإدارة**: مراقبة وتحليل الطلبات
    
    ### الأدوار:
    - **عام**: تقديم وتتبع الطلبات
    - **مواطن**: إدارة طلباته الخاصة
    - **مؤسسة**: التكفل بالطلبات
    - **مراقب**: مراجعة وتفعيل الطلبات وربطها بالجمعيات
    - **إدارة**: المراقبة والتحليلات والتحكم الكامل
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# أصول CORS: من الإعدادات + قائمة ثابتة لضمان عمل kksar.ma و localhost حتى لو .env ناقص
_DEFAULT_ORIGINS = [
    "https://ksar.geniura.com",
    "https://www.kksar.ma",
    "https://kksar.ma",
    "http://www.kksar.ma",
    "http://kksar.ma",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:4500",
    "http://127.0.0.1:4500",
]
_CORS_ORIGINS = list(dict.fromkeys(settings.allowed_origins_list + _DEFAULT_ORIGINS))


def _cors_headers(origin: str) -> dict:
    """رؤوس CORS: نسمح بالأصل إن كان في القائمة، وإلا نعيد أول عنصر مسموح."""
    h = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Accept-Language",
        "Access-Control-Max-Age": "86400",
        "Access-Control-Allow-Credentials": "true",
    }
    if origin and origin in _CORS_ORIGINS:
        h["Access-Control-Allow-Origin"] = origin
    elif _CORS_ORIGINS:
        h["Access-Control-Allow-Origin"] = _CORS_ORIGINS[0]
    return h


# Middleware لطلبات Preflight (OPTIONS): يُضاف آخراً ليعمل أولاً على الطلب
class PreflightCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            origin = request.headers.get("origin", "")
            return Response(status_code=200, headers=_cors_headers(origin))
        response = await call_next(request)
        # ضمان وجود رؤوس CORS على الاستجابة (إن لم يضفها CORSMiddleware)
        if "Access-Control-Allow-Origin" not in response.headers:
            origin = request.headers.get("origin", "")
            for k, v in _cors_headers(origin).items():
                response.headers[k] = v
        return response


# الترتيب: آخر middleware يُضاف يُنفَّذ أولاً. نريد Preflight أولاً ثم CORS العادي.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(PreflightCORSMiddleware)


# معالج أخطاء التحقق (422) - تسجيل البيانات المرسلة لتسهيل التشخيص
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = exc.body
    logger.warning(
        "Validation error on %s %s\nBody received: %s\nErrors: %s",
        request.method,
        request.url.path,
        body,
        exc.errors(),
    )
    origin = request.headers.get("origin", "")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers=_cors_headers(origin),
    )


# معالج الأخطاء العام (مع إرجاع رؤوس CORS حتى عند 500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    origin = request.headers.get("origin", "")
    return JSONResponse(
        status_code=500,
        content={"detail": "حدث خطأ داخلي. يرجى المحاولة لاحقاً."},
        headers=_cors_headers(origin),
    )


# Health check
@app.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    return {"status": "healthy", "service": "ksar-backend", "version": "2.0.0"}


# Include API routes
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "name": "KSAR - منصة المساعدات الإنسانية",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }
