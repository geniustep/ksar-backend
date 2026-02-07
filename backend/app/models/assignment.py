import uuid

from sqlalchemy import Column, String, Boolean, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import AssignmentStatus


class Assignment(Base):
    """نموذج التكفل بالطلب"""
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # الحالة
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PLEDGED)
    
    # خصوصية الهاتف - هل يُسمح للمؤسسة برؤية رقم الهاتف
    allow_phone_access = Column(Boolean, default=False, nullable=False)
    
    # تفاصيل التنفيذ
    notes = Column(Text, nullable=True)                       # ملاحظات المؤسسة
    completion_notes = Column(Text, nullable=True)            # ملاحظات الإتمام
    failure_reason = Column(Text, nullable=True)              # سبب الفشل (إن وجد)
    
    # التواريخ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    request = relationship("Request", back_populates="assignments")
    organization = relationship("Organization", back_populates="assignments")
