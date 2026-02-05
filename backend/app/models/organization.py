import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import OrganizationStatus


class Organization(Base):
    """نموذج المؤسسة/الجمعية"""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # بيانات المؤسسة
    name = Column(String(200), nullable=False)                # اسم المؤسسة
    description = Column(Text, nullable=True)                 # وصف المؤسسة
    logo_url = Column(String(500), nullable=True)             # شعار المؤسسة
    
    # معلومات الاتصال
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    
    # نطاق العمل
    service_types = Column(JSON, default=[])                  # أنواع الخدمات المقدمة
    coverage_areas = Column(JSON, default=[])                 # مناطق التغطية
    
    # الحالة
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE)
    
    # إحصائيات
    total_completed = Column(Integer, default=0)              # إجمالي الطلبات المكتملة
    
    # التواريخ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="organization")
    assignments = relationship("Assignment", back_populates="organization")
