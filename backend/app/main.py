"""
تطبيق KSAR - منصة تنسيق المساعدات الإنسانية
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.router import api_router


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
    - **مؤسسة**: التكفل بالطلبات
    - **إدارة**: المراقبة والتحليلات
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# معالج الأخطاء العام
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "حدث خطأ داخلي. يرجى المحاولة لاحقاً."},
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
