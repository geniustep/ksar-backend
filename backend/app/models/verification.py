import uuid

from sqlalchemy import Column, Integer, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.constants import VerificationResult


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    coordinator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    result = Column(Enum(VerificationResult), nullable=False)
    notes = Column(Text, nullable=True)
    priority_override = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    request = relationship("Request", back_populates="verifications")
    coordinator = relationship("User")
