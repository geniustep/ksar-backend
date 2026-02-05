from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import RequestCategory, RequestStatus


class RequestCreate(BaseModel):
    category: RequestCategory
    description: Optional[str] = Field(default=None, max_length=2000)
    quantity: int = Field(default=1, ge=1, le=100)
    location_text: str = Field(..., min_length=5, max_length=500)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    region_code: Optional[str] = Field(default=None, max_length=50)


class RequestUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=2000)
    quantity: Optional[int] = Field(default=None, ge=1, le=100)
    location_text: Optional[str] = Field(default=None, min_length=5, max_length=500)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None


class RequestResponse(BaseModel):
    id: UUID
    category: RequestCategory
    description: Optional[str]
    quantity: int
    priority_score: int
    status: RequestStatus
    location_text: str
    location_lat: Optional[float]
    location_lng: Optional[float]
    region_code: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    verified_at: Optional[datetime]
    delivered_at: Optional[datetime]

    model_config = {"from_attributes": True}


class RequestDetailResponse(RequestResponse):
    created_by: UUID
    duplicate_of: Optional[UUID]
    assignments: List["AssignmentBriefResponse"] = []

    model_config = {"from_attributes": True}


class MarketRequestResponse(BaseModel):
    """Request view for organizations - no personal data."""
    id: UUID
    category: RequestCategory
    description: Optional[str]
    quantity: int
    priority_score: int
    location_text: str
    region_code: Optional[str]
    created_at: datetime
    special_cases: List[str] = []

    model_config = {"from_attributes": True}


class RequestCancelResponse(BaseModel):
    id: UUID
    status: RequestStatus

    model_config = {"from_attributes": True}


class AssignmentBriefResponse(BaseModel):
    id: UUID
    org_id: UUID
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedRequests(BaseModel):
    items: List[RequestResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class PaginatedMarketRequests(BaseModel):
    items: List[MarketRequestResponse]
    total: int
    page: int
    limit: int
    has_more: bool


# Resolve forward reference
RequestDetailResponse.model_rebuild()
