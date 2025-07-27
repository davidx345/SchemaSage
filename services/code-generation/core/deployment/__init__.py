"""
Deployment module initialization
"""
from .base import (
    CloudProvider,
    InfrastructureType,
    InfrastructureResource,
    DeploymentConfig,
    DeploymentStatus,
    CloudProviderManager
)
from .deployment_manager import DeploymentManager
from .aws_manager import AWSManager
from .docker_manager import DockerManager

# Import kubernetes manager conditionally
try:
    from .kubernetes_manager import KubernetesManager
except ImportError:
    KubernetesManager = None

__all__ = [
    'CloudProvider',
    'InfrastructureType',
    'InfrastructureResource',
    'DeploymentConfig',
    'DeploymentStatus',
    'CloudProviderManager',
    'DeploymentManager',
    'AWSManager',
    'DockerManager',
    'KubernetesManager'
]
