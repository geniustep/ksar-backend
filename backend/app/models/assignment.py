import uuid

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import AssignmentStatus


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.PLEDGED)

    eta = Column(DateTime(timezone=True), nullable=True)
    proof_note = Column(Text, nullable=True)
    proof_media_url = Column(String(500), nullable=True)
    failure_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    request = relationship("Request", back_populates="assignments")
    organization = relationship("Organization", back_populates="assignments")
