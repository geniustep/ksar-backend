import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Float, Integer, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    phone_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String(100), nullable=True)
    language = Column(String(5), default="ar")
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    resident_profile = relationship("ResidentProfile", back_populates="user", uselist=False)
    organization = relationship("Organization", back_populates="user", uselist=False)
    requests = relationship("Request", back_populates="created_by_user", foreign_keys="Request.created_by")


class ResidentProfile(Base):
    __tablename__ = "resident_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    family_size = Column(Integer, default=1)
    special_cases = Column(JSON, default=[])
    location_text = Column(String(500), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    national_id = Column(String(20), nullable=True)

    # Relationships
    user = relationship("User", back_populates="resident_profile")
