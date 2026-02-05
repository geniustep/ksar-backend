from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import UserRole, UserStatus


class ResidentProfileBase(BaseModel):
    family_size: int = Field(default=1, ge=1, le=50)
    special_cases: List[str] = Field(default=[])
    location_text: Optional[str] = Field(default=None, max_length=500)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    national_id: Optional[str] = Field(default=None, max_length=20)


class ResidentProfileUpdate(BaseModel):
    family_size: Optional[int] = Field(default=None, ge=1, le=50)
    special_cases: Optional[List[str]] = None
    location_text: Optional[str] = Field(default=None, max_length=500)
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    national_id: Optional[str] = Field(default=None, max_length=20)


class ResidentProfileResponse(ResidentProfileBase):
    id: UUID
    user_id: UUID

    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    language: str = Field(default="ar", max_length=5)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    language: Optional[str] = Field(default=None, max_length=5)


class UserResponse(UserBase):
    id: UUID
    phone: str
    role: UserRole
    status: UserStatus
    phone_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserWithProfileResponse(UserResponse):
    profile: Optional[ResidentProfileResponse] = None

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    id: UUID
    phone: str
    role: UserRole
    full_name: Optional[str]
    language: str
    status: UserStatus
    phone_verified: bool
    profile: Optional[ResidentProfileResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}
