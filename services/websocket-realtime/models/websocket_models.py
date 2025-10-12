"""
WebSocket and Dashboard Data Models
"""
from pydantic import BaseModel
from typing import Optional

class WebhookData(BaseModel):
    user: str
    timestamp: str
    project: Optional[str] = None
    project_name: Optional[str] = None
    schema_type: Optional[str] = None
    framework: Optional[str] = None
    tables_count: Optional[int] = None
    project_type: Optional[str] = None

class DashboardUpdate(BaseModel):
    type: str
    data: dict

class ActivityUpdate(BaseModel):
    id: str
    type: str
    description: str
    timestamp: str
    icon: Optional[str] = "activity"
    color: Optional[str] = "blue"

class StatIncrement(BaseModel):
    metric: str
    value: int = 1