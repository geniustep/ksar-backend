from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import OrganizationStatus


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    contact_email: Optional[str] = Field(default=None, max_length=100)
    service_types: List[str] = Field(default=[])
    coverage_areas: List[str] = Field(default=[])


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    contact_email: Optional[str] = Field(default=None, max_length=100)
    service_types: Optional[List[str]] = None
    coverage_areas: Optional[List[str]] = None


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    contact_phone: Optional[str]
    contact_email: Optional[str]
    service_types: List[str]
    coverage_areas: List[str]
    verification_level: int
    status: OrganizationStatus
    created_at: datetime

    model_config = {"from_attributes": True}
