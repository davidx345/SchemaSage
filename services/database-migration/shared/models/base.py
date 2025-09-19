"""Base models for all services."""

from typing import Optional, Any, Dict, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    """Base model with common fields."""
    
    id: Optional[UUID] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    archived_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BaseResponse(PydanticBaseModel):
    """Base response model."""
    
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Error response model."""
    
    success: bool = False
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class PaginationParams(PydanticBaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="asc", regex="^(asc|desc)$")


class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    
    items: List[Any] = []
    total: int = 0
    page: int = 1
    limit: int = 10
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class ApiHealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
