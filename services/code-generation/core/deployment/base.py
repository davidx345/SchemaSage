"""
Base cloud provider interface and common types for deployment system
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

class DeploymentTarget(Enum):
    """Deployment target environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"

class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class InfrastructureType(Enum):
    """Types of infrastructure components"""
    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORK = "network"
    LOAD_BALANCER = "load_balancer"
    CONTAINER = "container"
    SERVERLESS = "serverless"

@dataclass
class InfrastructureResource:
    """Represents an infrastructure resource"""
    resource_id: str
    name: str
    resource_type: InfrastructureType
    provider: CloudProvider
    region: str
    config: Dict[str, Any]
    status: str = "unknown"
    endpoint: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentConfig:
    """Configuration for a deployment"""
    deployment_id: str
    name: str
    target: DeploymentTarget
    provider: CloudProvider
    region: str
    application_config: Dict[str, Any]
    infrastructure_config: Dict[str, Any]
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    scaling_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    backup_config: Dict[str, Any] = field(default_factory=dict)
    rollback_config: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    deployment_id: str
    status: DeploymentStatus
    resources_created: List[Dict[str, Any]] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

@dataclass
class Environment:
    """Represents a deployment environment"""
    environment_id: str
    name: str
    target: DeploymentTarget
    provider: CloudProvider
    region: str
    resources: List[InfrastructureResource] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    status: str = "unknown"
    created_at: datetime = field(default_factory=datetime.now)
    last_deployment: Optional[datetime] = None

class CloudProviderManager(ABC):
    """Base class for cloud provider managers"""
    
    def __init__(self, provider: CloudProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
    
    @abstractmethod
    async def create_infrastructure(
        self,
        resources: List[Dict[str, Any]],
        tags: Dict[str, str] = None
    ) -> List[InfrastructureResource]:
        """Create infrastructure resources"""
        pass
    
    @abstractmethod
    async def destroy_infrastructure(self, resource_ids: List[str]) -> bool:
        """Destroy infrastructure resources"""
        pass
    
    @abstractmethod
    async def get_resource_status(self, resource_id: str) -> str:
        """Get status of a resource"""
        pass
    
    @abstractmethod
    async def scale_resource(self, resource_id: str, scale_config: Dict[str, Any]) -> bool:
        """Scale a resource"""
        pass
