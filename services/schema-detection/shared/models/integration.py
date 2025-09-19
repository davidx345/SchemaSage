"""Integration models for external services."""

from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID
from .base import BaseModel


class IntegrationType(str, Enum):
    """Integration types."""
    
    DATABASE = "database"
    CLOUD_STORAGE = "cloud_storage"
    API = "api"
    WEBHOOK = "webhook"
    SSO = "sso"
    ANALYTICS = "analytics"
    NOTIFICATION = "notification"


class HealthStatus(str, Enum):
    """Health status for integrations."""
    
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    DISABLED = "disabled"


class IntegrationModel(BaseModel):
    """Integration model."""
    
    project_id: UUID  # References projects(id)
    integration_type: IntegrationType
    integration_name: Optional[str] = None
    
    # Configuration stored as JSONB
    config: Dict[str, Any] = {}
    
    # Security (encrypted credentials stored separately)
    encrypted_credentials: Optional[bytes] = None
    
    # Status and health
    is_active: bool = True
    last_health_check: Optional[str] = None
    health_status: HealthStatus = HealthStatus.UNKNOWN
    
    class Config:
        schema_extra = {
            "example": {
                "integration_type": "database",
                "integration_name": "Production PostgreSQL",
                "config": {
                    "host": "prod-db.example.com",
                    "port": 5432,
                    "database": "customer_db",
                    "ssl_mode": "require"
                },
                "is_active": True,
                "health_status": "healthy"
            }
        }


class IntegrationCreateRequest(BaseModel):
    """Request to create an integration."""
    
    project_id: UUID
    integration_type: IntegrationType
    integration_name: str
    config: Dict[str, Any]
    credentials: Optional[Dict[str, str]] = None  # Will be encrypted
    is_active: bool = True


class IntegrationUpdateRequest(BaseModel):
    """Request to update an integration."""
    
    integration_name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class IntegrationTestRequest(BaseModel):
    """Request to test an integration."""
    
    integration_id: UUID
    test_type: str = "connection"
    test_parameters: Dict[str, Any] = {}


class IntegrationTestResponse(BaseModel):
    """Response from integration test."""
    
    success: bool
    response_time_ms: int
    test_results: Dict[str, Any] = {}
    error_message: Optional[str] = None
    recommendations: List[str] = []


class IntegrationResponse(BaseModel):
    """Integration response."""
    
    integration: IntegrationModel
    connection_status: Optional[str] = None
    last_sync: Optional[str] = None
    usage_stats: Dict[str, Any] = {}
