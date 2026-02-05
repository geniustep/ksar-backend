from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import AssignmentStatus


class AssignmentCreate(BaseModel):
    request_id: UUID


class AssignmentUpdateStatus(BaseModel):
    status: AssignmentStatus
    proof_note: Optional[str] = Field(default=None, max_length=2000)
    proof_media_url: Optional[str] = Field(default=None, max_length=500)
    eta: Optional[datetime] = None


class AssignmentFailure(BaseModel):
    failure_reason: str = Field(..., min_length=5, max_length=2000)


class AssignmentResponse(BaseModel):
    id: UUID
    request_id: UUID
    org_id: UUID
    status: AssignmentStatus
    eta: Optional[datetime]
    proof_note: Optional[str]
    proof_media_url: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AssignmentWithContactResponse(AssignmentResponse):
    """Response that includes contact info after pledge."""
    contact_phone: Optional[str] = None
    location_text: Optional[str] = None


class PaginatedAssignments(BaseModel):
    items: List[AssignmentResponse]
    total: int
    page: int
    limit: int
    has_more: bool
