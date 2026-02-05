import uuid

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import RequestCategory, RequestStatus


class Request(Base):
    __tablename__ = "requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    category = Column(Enum(RequestCategory), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=1)

    priority_score = Column(Integer, default=50)

    status = Column(Enum(RequestStatus), default=RequestStatus.NEW)

    location_text = Column(String(500), nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    region_code = Column(String(50), nullable=True, index=True)

    duplicate_hash = Column(String(64), nullable=True, index=True)
    duplicate_of = Column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    created_by_user = relationship("User", back_populates="requests", foreign_keys=[created_by])
    assignments = relationship("Assignment", back_populates="request")
    verifications = relationship("Verification", back_populates="request")
    duplicate_original = relationship("Request", remote_side="Request.id", foreign_keys=[duplicate_of])
