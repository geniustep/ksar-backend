from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.error_code = code
        self.error_message = message
        self.error_details = details
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                }
            },
        )


class NotFoundError(AppException):
    def __init__(self, entity: str, entity_id: str = None):
        details = {"entity": entity}
        if entity_id:
            details["id"] = entity_id
        super().__init__(
            code="NOT_FOUND",
            message=f"{entity} غير موجود",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class DuplicateError(AppException):
    def __init__(self, message: str = "هذا العنصر موجود مسبقاً", details: dict = None):
        super().__init__(
            code="DUPLICATE",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "غير مصرح لك بهذا الإجراء"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "يرجى تسجيل الدخول"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ValidationError(AppException):
    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else None
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class RateLimitError(AppException):
    def __init__(self):
        super().__init__(
            code="RATE_LIMIT",
            message="تم تجاوز الحد المسموح. يرجى المحاولة لاحقاً",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class OTPError(AppException):
    def __init__(self, message: str = "رمز التحقق غير صالح"):
        super().__init__(
            code="OTP_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidStatusTransition(AppException):
    def __init__(self, current: str, target: str):
        super().__init__(
            code="INVALID_STATUS",
            message=f"لا يمكن تغيير الحالة من {current} إلى {target}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"current": current, "target": target},
        )
