"""
Main deployment manager orchestrating all cloud providers
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from .base import CloudProvider, InfrastructureResource, DeploymentConfig, DeploymentStatus
from .aws_manager import AWSManager
from .kubernetes_manager import KubernetesManager
from .docker_manager import DockerManager

logger = logging.getLogger(__name__)

class DeploymentManager:
    """Main deployment manager orchestrating all providers"""
    
    def __init__(self):
        self.providers = {}
        self.active_deployments = {}
    
    def register_provider(self, provider: CloudProvider, config: Dict[str, Any]):
        """Register a cloud provider"""
        if provider == CloudProvider.AWS:
            self.providers[provider] = AWSManager(config)
        elif provider == CloudProvider.KUBERNETES:
            self.providers[provider] = KubernetesManager(config)
        elif provider == CloudProvider.DOCKER:
            self.providers[provider] = DockerManager(config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def create_deployment(
        self,
        deployment_config: DeploymentConfig
    ) -> str:
        """Create a new deployment"""
        deployment_id = deployment_config.deployment_id
        
        try:
            logger.info(f"Starting deployment {deployment_id}")
            
            # Update deployment status
            self.active_deployments[deployment_id] = DeploymentStatus(
                deployment_id=deployment_id,
                status="creating",
                created_resources=[],
                error_message=None
            )
            
            # Get provider manager
            provider = deployment_config.provider
            if provider not in self.providers:
                raise ValueError(f"Provider {provider} not registered")
            
            manager = self.providers[provider]
            
            # Create infrastructure resources
            resources = await manager.create_infrastructure(
                deployment_config.resources,
                deployment_config.tags
            )
            
            # Update deployment status
            self.active_deployments[deployment_id].status = "completed"
            self.active_deployments[deployment_id].created_resources = resources
            
            logger.info(f"Deployment {deployment_id} completed successfully")
            return deployment_id
            
        except Exception as e:
            error_msg = f"Deployment {deployment_id} failed: {str(e)}"
            logger.error(error_msg)
            
            # Update deployment status
            if deployment_id in self.active_deployments:
                self.active_deployments[deployment_id].status = "failed"
                self.active_deployments[deployment_id].error_message = error_msg
            
            raise
    
    async def destroy_deployment(self, deployment_id: str) -> bool:
        """Destroy an existing deployment"""
        try:
            if deployment_id not in self.active_deployments:
                logger.error(f"Deployment {deployment_id} not found")
                return False
            
            deployment_status = self.active_deployments[deployment_id]
            
            # Group resources by provider
            provider_resources = {}
            for resource in deployment_status.created_resources:
                provider = resource.provider
                if provider not in provider_resources:
                    provider_resources[provider] = []
                provider_resources[provider].append(resource.resource_id)
            
            # Destroy resources by provider
            success = True
            for provider, resource_ids in provider_resources.items():
                if provider in self.providers:
                    manager = self.providers[provider]
                    result = await manager.destroy_infrastructure(resource_ids)
                    success = success and result
            
            # Remove from active deployments
            if success:
                del self.active_deployments[deployment_id]
                logger.info(f"Deployment {deployment_id} destroyed successfully")
            else:
                logger.error(f"Failed to destroy deployment {deployment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error destroying deployment {deployment_id}: {e}")
            return False
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentStatus]:
        """Get status of a deployment"""
        if deployment_id not in self.active_deployments:
            return None
        
        deployment_status = self.active_deployments[deployment_id]
        
        # Update resource statuses
        for resource in deployment_status.created_resources:
            if resource.provider in self.providers:
                manager = self.providers[resource.provider]
                current_status = await manager.get_resource_status(resource.resource_id)
                resource.status = current_status
        
        return deployment_status
    
    async def scale_deployment(
        self,
        deployment_id: str,
        resource_name: str,
        scale_config: Dict[str, Any]
    ) -> bool:
        """Scale a specific resource in a deployment"""
        try:
            if deployment_id not in self.active_deployments:
                logger.error(f"Deployment {deployment_id} not found")
                return False
            
            deployment_status = self.active_deployments[deployment_id]
            
            # Find the resource to scale
            target_resource = None
            for resource in deployment_status.created_resources:
                if resource.name == resource_name:
                    target_resource = resource
                    break
            
            if not target_resource:
                logger.error(f"Resource {resource_name} not found in deployment {deployment_id}")
                return False
            
            # Scale the resource
            if target_resource.provider in self.providers:
                manager = self.providers[target_resource.provider]
                return await manager.scale_resource(target_resource.resource_id, scale_config)
            
            return False
            
        except Exception as e:
            logger.error(f"Error scaling resource {resource_name} in deployment {deployment_id}: {e}")
            return False
    
    async def list_deployments(self) -> List[str]:
        """List all active deployments"""
        return list(self.active_deployments.keys())
    
    async def health_check(self, deployment_id: str) -> Dict[str, Any]:
        """Perform health check on deployment"""
        try:
            if deployment_id not in self.active_deployments:
                return {"status": "not_found", "healthy": False}
            
            deployment_status = self.active_deployments[deployment_id]
            health_status = {
                "status": deployment_status.status,
                "healthy": True,
                "resources": []
            }
            
            # Check health of each resource
            for resource in deployment_status.created_resources:
                if resource.provider in self.providers:
                    manager = self.providers[resource.provider]
                    resource_status = await manager.get_resource_status(resource.resource_id)
                    
                    resource_health = {
                        "name": resource.name,
                        "type": resource.resource_type.value,
                        "status": resource_status,
                        "healthy": resource_status in ["running", "available", "active"]
                    }
                    
                    health_status["resources"].append(resource_health)
                    
                    if not resource_health["healthy"]:
                        health_status["healthy"] = False
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking health of deployment {deployment_id}: {e}")
            return {"status": "error", "healthy": False, "error": str(e)}
    
    async def backup_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Create backup of deployment configuration"""
        try:
            if deployment_id not in self.active_deployments:
                return {"success": False, "error": "Deployment not found"}
            
            deployment_status = self.active_deployments[deployment_id]
            
            backup_data = {
                "deployment_id": deployment_id,
                "created_at": deployment_status.created_resources[0].metadata.get("created_at") if deployment_status.created_resources else None,
                "resources": [
                    {
                        "name": resource.name,
                        "type": resource.resource_type.value,
                        "provider": resource.provider.value,
                        "config": resource.config,
                        "metadata": resource.metadata
                    }
                    for resource in deployment_status.created_resources
                ]
            }
            
            return {"success": True, "backup_data": backup_data}
            
        except Exception as e:
            logger.error(f"Error backing up deployment {deployment_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def restore_deployment(self, backup_data: Dict[str, Any]) -> str:
        """Restore deployment from backup"""
        try:
            deployment_id = backup_data["deployment_id"]
            resources = backup_data["resources"]
            
            # Group resources by provider
            provider_resources = {}
            for resource_data in resources:
                provider = CloudProvider(resource_data["provider"])
                if provider not in provider_resources:
                    provider_resources[provider] = []
                provider_resources[provider].append(resource_data["config"])
            
            # Restore resources by provider
            created_resources = []
            for provider, resource_configs in provider_resources.items():
                if provider in self.providers:
                    manager = self.providers[provider]
                    resources = await manager.create_infrastructure(resource_configs)
                    created_resources.extend(resources)
            
            # Update deployment status
            self.active_deployments[deployment_id] = DeploymentStatus(
                deployment_id=deployment_id,
                status="completed",
                created_resources=created_resources,
                error_message=None
            )
            
            logger.info(f"Deployment {deployment_id} restored successfully")
            return deployment_id
            
        except Exception as e:
            logger.error(f"Error restoring deployment: {e}")
            raise
