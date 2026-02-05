import uuid

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import OrganizationStatus


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(100), nullable=True)
    service_types = Column(JSON, default=[])
    coverage_areas = Column(JSON, default=[])
    verification_level = Column(Integer, default=0)
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="organization")
    assignments = relationship("Assignment", back_populates="organization")
