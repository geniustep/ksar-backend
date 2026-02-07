import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import UserRole, UserStatus


class User(Base):
    """نموذج المستخدم - للإدارة والمؤسسات والمواطنين"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # بيانات الدخول
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # البيانات الأساسية
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    
    # العنوان (للمواطنين)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    
    # الدور والحالة
    role = Column(Enum(UserRole), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    
    # التواريخ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="user", uselist=False)
    requests = relationship("Request", back_populates="user", foreign_keys="Request.user_id")
    inspected_requests = relationship("Request", back_populates="inspector", foreign_keys="Request.inspector_id")
