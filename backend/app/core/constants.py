import enum


class UserRole(str, enum.Enum):
    RESIDENT = "resident"
    ORGANIZATION = "organization"
    COORDINATOR = "coordinator"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class RequestCategory(str, enum.Enum):
    FOOD = "food"
    WATER = "water"
    SHELTER = "shelter"
    MEDICINE = "medicine"
    CLOTHES = "clothes"
    HYGIENE = "hygiene"
    BABY_SUPPLIES = "baby_supplies"
    TRANSPORT = "transport"
    DOCUMENTS = "documents"
    OTHER = "other"


class RequestStatus(str, enum.Enum):
    NEW = "new"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class AssignmentStatus(str, enum.Enum):
    PLEDGED = "pledged"
    EN_ROUTE = "en_route"
    DELIVERED = "delivered"
    FAILED = "failed"


class VerificationResult(str, enum.Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"


class NotificationChannel(str, enum.Enum):
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class OrganizationStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


# Priority calculation weights
CATEGORY_WEIGHTS = {
    RequestCategory.MEDICINE: 25,
    RequestCategory.BABY_SUPPLIES: 20,
    RequestCategory.WATER: 20,
    RequestCategory.FOOD: 15,
    RequestCategory.SHELTER: 15,
    RequestCategory.HYGIENE: 10,
    RequestCategory.CLOTHES: 5,
    RequestCategory.DOCUMENTS: 5,
    RequestCategory.TRANSPORT: 5,
    RequestCategory.OTHER: 0,
}

SPECIAL_CASE_WEIGHTS = {
    "pregnant": 10,
    "disabled": 10,
    "chronic_illness": 10,
    "elderly": 8,
    "children": 5,
}

# Rate limiting
RATE_LIMITS = {
    "auth_start": "5/minute",
    "requests_create": "10/hour",
    "default": "100/minute",
}
