import uuid

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import RequestCategory, RequestStatus


class Request(Base):
    """نموذج طلب المساعدة"""
    __tablename__ = "requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ربط بالمستخدم المسجل
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # بيانات صاحب الطلب (تُملأ من المستخدم أو يُدخلها)
    requester_name = Column(String(100), nullable=False)      # اسم صاحب الطلب
    requester_phone = Column(String(20), nullable=False, index=True)  # رقم الهاتف
    
    # تفاصيل الطلب
    category = Column(Enum(RequestCategory), nullable=False)
    description = Column(Text, nullable=True)                 # وصف الطلب/الاحتياج (اختياري)
    quantity = Column(Integer, default=1)                     # الكمية المطلوبة
    family_members = Column(Integer, default=1)               # عدد أفراد الأسرة
    
    # الموقع
    address = Column(String(500), nullable=True)              # العنوان التفصيلي (اختياري)
    city = Column(String(100), nullable=True)                 # المدينة
    region = Column(String(100), nullable=True, index=True)   # المنطقة/الحي
    latitude = Column(Float, nullable=True)                   # خط العرض
    longitude = Column(Float, nullable=True)                  # خط الطول
    
    # المرفقات - الصوت والصور
    audio_url = Column(String(500), nullable=True)            # رابط الملف الصوتي (تخزين خارجي)
    images = Column(Text, nullable=True)                      # روابط الصور (JSON array كنص)
    
    # الحالة والأولوية
    status = Column(Enum(RequestStatus), default=RequestStatus.NEW)
    priority_score = Column(Integer, default=50)              # نقاط الأولوية (0-100)
    is_urgent = Column(Integer, default=0)                    # علامة استعجال (0 أو 1)
    
    # ملاحظات الإدارة
    admin_notes = Column(Text, nullable=True)                 # ملاحظات داخلية
    
    # التواريخ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="requests", foreign_keys=[user_id])
    assignments = relationship("Assignment", back_populates="request")
