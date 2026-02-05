from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import AssignmentStatus


class AssignmentCreate(BaseModel):
    """التكفل بطلب"""
    request_id: UUID
    notes: Optional[str] = Field(default=None, max_length=1000, description="ملاحظات")


class AssignmentUpdate(BaseModel):
    """تحديث التكفل"""
    status: AssignmentStatus
    completion_notes: Optional[str] = Field(default=None, max_length=2000)
    failure_reason: Optional[str] = Field(default=None, max_length=1000)


class AssignmentResponse(BaseModel):
    """استجابة التكفل"""
    id: UUID
    request_id: UUID
    org_id: UUID
    status: AssignmentStatus
    notes: Optional[str]
    completion_notes: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class AssignmentBriefResponse(BaseModel):
    """استجابة مختصرة للتكفل"""
    id: UUID
    org_id: UUID
    status: AssignmentStatus
    created_at: datetime
    
    model_config = {"from_attributes": True}


class AssignmentWithRequestResponse(AssignmentResponse):
    """التكفل مع تفاصيل الطلب"""
    request_name: str
    request_phone: str
    request_address: str
    request_category: str
    request_description: str


class PaginatedAssignments(BaseModel):
    """قائمة التكفلات مع التصفح"""
    items: List[AssignmentResponse]
    total: int
    page: int
    limit: int
    has_more: bool
