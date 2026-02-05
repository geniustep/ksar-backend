import enum


class UserRole(str, enum.Enum):
    """أدوار المستخدمين"""
    ADMIN = "admin"           # الإدارة
    ORGANIZATION = "organization"  # المؤسسات


class UserStatus(str, enum.Enum):
    """حالة المستخدم"""
    ACTIVE = "active"
    SUSPENDED = "suspended"


class RequestCategory(str, enum.Enum):
    """تصنيفات الطلبات"""
    FOOD = "food"                 # غذاء
    WATER = "water"               # ماء
    SHELTER = "shelter"           # مأوى
    MEDICINE = "medicine"         # دواء
    CLOTHES = "clothes"           # ملابس
    BLANKETS = "blankets"         # أغطية
    BABY_SUPPLIES = "baby_supplies"  # مستلزمات أطفال
    HYGIENE = "hygiene"           # نظافة
    FINANCIAL = "financial"       # مساعدة مالية
    OTHER = "other"               # أخرى


class RequestStatus(str, enum.Enum):
    """حالات الطلب - مبسطة"""
    NEW = "new"                   # جديد - في انتظار التكفل
    ASSIGNED = "assigned"         # متكفل به - مؤسسة تعهدت بالتنفيذ
    IN_PROGRESS = "in_progress"   # قيد التنفيذ
    COMPLETED = "completed"       # مكتمل - تم التسليم
    CANCELLED = "cancelled"       # ملغي


class AssignmentStatus(str, enum.Enum):
    """حالات التكفل"""
    PLEDGED = "pledged"           # تعهد
    IN_PROGRESS = "in_progress"   # قيد التنفيذ  
    COMPLETED = "completed"       # مكتمل
    FAILED = "failed"             # فشل


class OrganizationStatus(str, enum.Enum):
    """حالة المؤسسة"""
    ACTIVE = "active"
    SUSPENDED = "suspended"


# أوزان الأولوية حسب التصنيف
CATEGORY_WEIGHTS = {
    RequestCategory.MEDICINE: 25,
    RequestCategory.BABY_SUPPLIES: 20,
    RequestCategory.WATER: 20,
    RequestCategory.FOOD: 15,
    RequestCategory.SHELTER: 15,
    RequestCategory.BLANKETS: 10,
    RequestCategory.HYGIENE: 10,
    RequestCategory.CLOTHES: 5,
    RequestCategory.FINANCIAL: 5,
    RequestCategory.OTHER: 0,
}

# Rate limiting
RATE_LIMITS = {
    "requests_create": "20/hour",
    "default": "100/minute",
}
