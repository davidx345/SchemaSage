"""
Docker infrastructure manager for deployment system
"""
import docker
import logging
from typing import Dict, List, Any, Optional
from .base import CloudProviderManager, CloudProvider, InfrastructureResource, InfrastructureType

logger = logging.getLogger(__name__)

class DockerManager(CloudProviderManager):
    """Docker infrastructure manager"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(CloudProvider.DOCKER, config)
        
        # Initialize Docker client
        self.client = docker.from_env()
        
        # Docker configuration
        self.network_name = config.get("network_name", "schemasage-network")
        self.volume_prefix = config.get("volume_prefix", "schemasage")
    
    async def create_infrastructure(
        self,
        resources: List[Dict[str, Any]],
        tags: Dict[str, str] = None
    ) -> List[InfrastructureResource]:
        """Create Docker resources"""
        
        created_resources = []
        
        # Ensure network exists
        await self._ensure_network()
        
        for resource_config in resources:
            resource_type = InfrastructureType(resource_config["type"])
            
            try:
                if resource_type == InfrastructureType.COMPUTE:
                    resource = await self._create_container(resource_config, tags)
                elif resource_type == InfrastructureType.STORAGE:
                    resource = await self._create_volume(resource_config, tags)
                elif resource_type == InfrastructureType.NETWORK:
                    resource = await self._create_network(resource_config, tags)
                else:
                    logger.warning(f"Unsupported Docker resource type: {resource_type}")
                    continue
                
                created_resources.append(resource)
                
            except Exception as e:
                logger.error(f"Failed to create Docker resource {resource_config['name']}: {e}")
                raise
        
        return created_resources
    
    async def destroy_infrastructure(self, resource_ids: List[str]) -> bool:
        """Destroy Docker resources"""
        try:
            for resource_id in resource_ids:
                if resource_id.startswith("container:"):
                    container_id = resource_id.replace("container:", "")
                    container = self.client.containers.get(container_id)
                    container.stop()
                    container.remove()
                elif resource_id.startswith("volume:"):
                    volume_id = resource_id.replace("volume:", "")
                    volume = self.client.volumes.get(volume_id)
                    volume.remove()
                elif resource_id.startswith("network:"):
                    network_id = resource_id.replace("network:", "")
                    network = self.client.networks.get(network_id)
                    network.remove()
            
            return True
        except Exception as e:
            logger.error(f"Failed to destroy Docker resources: {e}")
            return False
    
    async def get_resource_status(self, resource_id: str) -> str:
        """Get status of Docker resource"""
        try:
            if resource_id.startswith("container:"):
                container_id = resource_id.replace("container:", "")
                container = self.client.containers.get(container_id)
                return container.status
            elif resource_id.startswith("volume:"):
                volume_id = resource_id.replace("volume:", "")
                volume = self.client.volumes.get(volume_id)
                return "available"
            elif resource_id.startswith("network:"):
                network_id = resource_id.replace("network:", "")
                network = self.client.networks.get(network_id)
                return "available"
            
            return "unknown"
        except Exception as e:
            logger.error(f"Failed to get Docker resource status: {e}")
            return "unknown"
    
    async def scale_resource(self, resource_id: str, scale_config: Dict[str, Any]) -> bool:
        """Scale Docker resource (create additional containers)"""
        try:
            if not resource_id.startswith("container:"):
                logger.error("Scaling only supported for containers")
                return False
            
            container_id = resource_id.replace("container:", "")
            container = self.client.containers.get(container_id)
            
            # Get container configuration
            image = container.image.tags[0] if container.image.tags else container.image.id
            env = container.attrs["Config"]["Env"]
            
            # Create additional replicas
            replicas = scale_config.get("replicas", 1)
            for i in range(replicas):
                replica_name = f"{container.name}-replica-{i}"
                self.client.containers.run(
                    image=image,
                    name=replica_name,
                    environment=env,
                    network=self.network_name,
                    detach=True
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to scale Docker resource: {e}")
            return False
    
    async def _ensure_network(self):
        """Ensure the Docker network exists"""
        try:
            self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.client.networks.create(
                self.network_name,
                driver="bridge"
            )
    
    async def _create_container(
        self,
        config: Dict[str, Any],
        tags: Dict[str, str] = None
    ) -> InfrastructureResource:
        """Create Docker container"""
        
        name = config["name"]
        image = config["image"]
        
        # Container configuration
        container_config = {
            "image": image,
            "name": name,
            "environment": config.get("environment", {}),
            "ports": config.get("ports", {}),
            "volumes": config.get("volumes", {}),
            "network": self.network_name,
            "detach": True
        }
        
        # Add CPU and memory limits
        if "cpu_limit" in config or "memory_limit" in config:
            container_config["mem_limit"] = config.get("memory_limit", "512m")
            container_config["cpu_period"] = 100000
            container_config["cpu_quota"] = int(float(config.get("cpu_limit", "0.5")) * 100000)
        
        # Add labels
        labels = {"managed_by": "schemasage"}
        if tags:
            labels.update(tags)
        container_config["labels"] = labels
        
        # Create container
        container = self.client.containers.run(**container_config)
        
        return InfrastructureResource(
            resource_id=f"container:{container.id}",
            name=name,
            resource_type=InfrastructureType.COMPUTE,
            provider=CloudProvider.DOCKER,
            region="local",
            config=config,
            status=container.status,
            metadata={
                "container_id": container.id,
                "image": image,
                "network": self.network_name
            }
        )
    
    async def _create_volume(
        self,
        config: Dict[str, Any],
        tags: Dict[str, str] = None
    ) -> InfrastructureResource:
        """Create Docker volume"""
        
        name = config["name"]
        
        # Volume configuration
        volume_config = {
            "name": f"{self.volume_prefix}-{name}",
            "driver": config.get("driver", "local")
        }
        
        # Add labels
        labels = {"managed_by": "schemasage"}
        if tags:
            labels.update(tags)
        volume_config["labels"] = labels
        
        # Create volume
        volume = self.client.volumes.create(**volume_config)
        
        return InfrastructureResource(
            resource_id=f"volume:{volume.id}",
            name=name,
            resource_type=InfrastructureType.STORAGE,
            provider=CloudProvider.DOCKER,
            region="local",
            config=config,
            status="available",
            metadata={
                "volume_id": volume.id,
                "mount_point": volume.attrs["Mountpoint"],
                "driver": volume.attrs["Driver"]
            }
        )
    
    async def _create_network(
        self,
        config: Dict[str, Any],
        tags: Dict[str, str] = None
    ) -> InfrastructureResource:
        """Create Docker network"""
        
        name = config["name"]
        
        # Network configuration
        network_config = {
            "name": name,
            "driver": config.get("driver", "bridge"),
            "scope": config.get("scope", "local")
        }
        
        # Add labels
        labels = {"managed_by": "schemasage"}
        if tags:
            labels.update(tags)
        network_config["labels"] = labels
        
        # Create network
        network = self.client.networks.create(**network_config)
        
        return InfrastructureResource(
            resource_id=f"network:{network.id}",
            name=name,
            resource_type=InfrastructureType.NETWORK,
            provider=CloudProvider.DOCKER,
            region="local",
            config=config,
            status="available",
            metadata={
                "network_id": network.id,
                "driver": network.attrs["Driver"],
                "scope": network.attrs["Scope"]
            }
        )
