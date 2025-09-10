"""
Cloud Provider Management Module

Handles connections, authentication, and operations for major cloud providers.
"""
import os
import boto3
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.resource import ResourceManagementClient
from google.cloud import sql_v1
from google.oauth2 import service_account
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CloudCost:
    """Cloud cost information"""
    monthly_estimate: float
    currency: str
    breakdown: Dict[str, float]
    recommendations: List[str]


@dataclass
class CloudResource:
    """Cloud resource information"""
    resource_id: str
    resource_type: str
    region: str
    size: str
    cost_per_hour: float
    specifications: Dict[str, Any]


class CloudProvider:
    """Base class for cloud provider implementations"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.authenticated = False
        
    async def authenticate(self) -> Tuple[bool, str]:
        """Authenticate with cloud provider"""
        raise NotImplementedError
        
    async def test_connection(self) -> Tuple[bool, str]:
        """Test connection to cloud provider"""
        raise NotImplementedError
        
    async def list_database_services(self) -> List[Dict[str, Any]]:
        """List available database services"""
        raise NotImplementedError
        
    async def estimate_costs(self, workload: Dict[str, Any]) -> CloudCost:
        """Estimate costs for given workload"""
        raise NotImplementedError
        
    async def create_database_instance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create database instance"""
        raise NotImplementedError


class AWSProvider(CloudProvider):
    """AWS cloud provider implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.region = credentials.get('region', 'us-east-1')
        
    async def authenticate(self) -> Tuple[bool, str]:
        """Authenticate with AWS"""
        try:
            # Use provided credentials or environment
            if 'access_key_id' in self.credentials:
                self.session = boto3.Session(
                    aws_access_key_id=self.credentials['access_key_id'],
                    aws_secret_access_key=self.credentials['secret_access_key'],
                    region_name=self.region
                )
            else:
                # Use default credential chain
                self.session = boto3.Session(region_name=self.region)
            
            # Test credentials by listing regions
            ec2 = self.session.client('ec2')
            regions = ec2.describe_regions()
            
            self.authenticated = True
            return True, f"Successfully authenticated with AWS. Found {len(regions['Regions'])} regions."
            
        except Exception as e:
            logger.error(f"AWS authentication failed: {e}")
            return False, f"Authentication failed: {str(e)}"
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test AWS connection"""
        if not self.authenticated:
            auth_result = await self.authenticate()
            if not auth_result[0]:
                return auth_result
        
        try:
            rds = self.session.client('rds')
            instances = rds.describe_db_instances()
            return True, f"Connection successful. Found {len(instances['DBInstances'])} RDS instances."
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    async def list_database_services(self) -> List[Dict[str, Any]]:
        """List AWS RDS database services"""
        try:
            rds = self.session.client('rds')
            instances = rds.describe_db_instances()
            
            services = []
            for instance in instances['DBInstances']:
                services.append({
                    'id': instance['DBInstanceIdentifier'],
                    'engine': instance['Engine'],
                    'engine_version': instance['EngineVersion'],
                    'instance_class': instance['DBInstanceClass'],
                    'status': instance['DBInstanceStatus'],
                    'endpoint': instance.get('Endpoint', {}).get('Address'),
                    'port': instance.get('Endpoint', {}).get('Port'),
                    'availability_zone': instance['AvailabilityZone'],
                    'multi_az': instance['MultiAZ'],
                    'storage_type': instance['StorageType'],
                    'allocated_storage': instance['AllocatedStorage']
                })
            
            return services
        except Exception as e:
            logger.error(f"Failed to list AWS database services: {e}")
            return []
    
    async def estimate_costs(self, workload: Dict[str, Any]) -> CloudCost:
        """Estimate AWS RDS costs"""
        try:
            # Mock cost calculation - in real implementation, use AWS Pricing API
            instance_type = workload.get('instance_type', 'db.t3.medium')
            storage_gb = workload.get('storage_gb', 100)
            backup_retention = workload.get('backup_retention_days', 7)
            
            # Sample pricing (replace with real AWS Pricing API)
            instance_costs = {
                'db.t3.micro': 0.017,
                'db.t3.small': 0.034,
                'db.t3.medium': 0.068,
                'db.t3.large': 0.136,
                'db.t3.xlarge': 0.272
            }
            
            instance_cost_hourly = instance_costs.get(instance_type, 0.068)
            instance_cost_monthly = instance_cost_hourly * 24 * 30
            
            storage_cost_monthly = storage_gb * 0.115  # gp2 storage
            backup_cost_monthly = storage_gb * backup_retention * 0.095 / 30
            
            total_monthly = instance_cost_monthly + storage_cost_monthly + backup_cost_monthly
            
            recommendations = []
            if instance_cost_monthly > 100:
                recommendations.append("Consider Reserved Instances for 30-60% savings")
            if storage_gb > 1000:
                recommendations.append("Consider moving cold data to S3 for 80% storage savings")
            
            return CloudCost(
                monthly_estimate=total_monthly,
                currency="USD",
                breakdown={
                    "instance": instance_cost_monthly,
                    "storage": storage_cost_monthly,
                    "backup": backup_cost_monthly
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"AWS cost estimation failed: {e}")
            return CloudCost(0.0, "USD", {}, [f"Cost estimation failed: {str(e)}"])


class AzureProvider(CloudProvider):
    """Azure cloud provider implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.subscription_id = credentials.get('subscription_id')
        
    async def authenticate(self) -> Tuple[bool, str]:
        """Authenticate with Azure"""
        try:
            self.credential = DefaultAzureCredential()
            self.sql_client = SqlManagementClient(self.credential, self.subscription_id)
            self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            
            # Test by listing resource groups
            resource_groups = list(self.resource_client.resource_groups.list())
            
            self.authenticated = True
            return True, f"Successfully authenticated with Azure. Found {len(resource_groups)} resource groups."
            
        except Exception as e:
            logger.error(f"Azure authentication failed: {e}")
            return False, f"Authentication failed: {str(e)}"
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test Azure connection"""
        if not self.authenticated:
            auth_result = await self.authenticate()
            if not auth_result[0]:
                return auth_result
        
        try:
            servers = list(self.sql_client.servers.list())
            return True, f"Connection successful. Found {len(servers)} SQL servers."
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    async def list_database_services(self) -> List[Dict[str, Any]]:
        """List Azure SQL database services"""
        try:
            services = []
            servers = list(self.sql_client.servers.list())
            
            for server in servers:
                databases = list(self.sql_client.databases.list_by_server(
                    server.resource_group, server.name
                ))
                
                for db in databases:
                    if db.name != 'master':  # Skip system database
                        services.append({
                            'id': f"{server.name}/{db.name}",
                            'server_name': server.name,
                            'database_name': db.name,
                            'edition': db.edition,
                            'service_objective': db.service_level_objective,
                            'status': db.status,
                            'location': server.location,
                            'resource_group': server.resource_group,
                            'creation_date': db.creation_date.isoformat() if db.creation_date else None
                        })
            
            return services
        except Exception as e:
            logger.error(f"Failed to list Azure database services: {e}")
            return []
    
    async def estimate_costs(self, workload: Dict[str, Any]) -> CloudCost:
        """Estimate Azure SQL costs"""
        try:
            service_tier = workload.get('service_tier', 'S2')
            storage_gb = workload.get('storage_gb', 100)
            
            # Sample pricing (replace with real Azure Pricing API)
            tier_costs = {
                'S0': 15,
                'S1': 20,
                'S2': 30,
                'S3': 60,
                'P1': 465,
                'P2': 930
            }
            
            compute_cost_monthly = tier_costs.get(service_tier, 30)
            storage_cost_monthly = max(0, storage_gb - 250) * 0.25  # First 250GB included
            
            total_monthly = compute_cost_monthly + storage_cost_monthly
            
            recommendations = []
            if compute_cost_monthly > 100:
                recommendations.append("Consider Azure Hybrid Benefit for up to 40% savings")
            if workload.get('read_heavy', False):
                recommendations.append("Consider read replicas for better performance")
            
            return CloudCost(
                monthly_estimate=total_monthly,
                currency="USD",
                breakdown={
                    "compute": compute_cost_monthly,
                    "storage": storage_cost_monthly
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Azure cost estimation failed: {e}")
            return CloudCost(0.0, "USD", {}, [f"Cost estimation failed: {str(e)}"])


class GCPProvider(CloudProvider):
    """Google Cloud Platform provider implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.project_id = credentials.get('project_id')
        
    async def authenticate(self) -> Tuple[bool, str]:
        """Authenticate with GCP"""
        try:
            if 'service_account_key' in self.credentials:
                self.credentials_obj = service_account.Credentials.from_service_account_info(
                    self.credentials['service_account_key']
                )
            else:
                # Use default credentials
                self.credentials_obj = None
            
            self.sql_client = sql_v1.SqlInstancesServiceClient(credentials=self.credentials_obj)
            
            # Test by listing instances
            request = sql_v1.SqlInstancesListRequest(project=self.project_id)
            instances = self.sql_client.list(request=request)
            
            self.authenticated = True
            return True, f"Successfully authenticated with GCP project: {self.project_id}"
            
        except Exception as e:
            logger.error(f"GCP authentication failed: {e}")
            return False, f"Authentication failed: {str(e)}"
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test GCP connection"""
        if not self.authenticated:
            auth_result = await self.authenticate()
            if not auth_result[0]:
                return auth_result
        
        try:
            request = sql_v1.SqlInstancesListRequest(project=self.project_id)
            instances = list(self.sql_client.list(request=request))
            return True, f"Connection successful. Found {len(instances)} Cloud SQL instances."
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    async def list_database_services(self) -> List[Dict[str, Any]]:
        """List GCP Cloud SQL database services"""
        try:
            request = sql_v1.SqlInstancesListRequest(project=self.project_id)
            instances = list(self.sql_client.list(request=request))
            
            services = []
            for instance in instances:
                services.append({
                    'id': instance.name,
                    'name': instance.name,
                    'database_version': instance.database_version,
                    'tier': instance.settings.tier,
                    'state': instance.state.name,
                    'region': instance.region,
                    'backend_type': instance.backend_type.name,
                    'ip_addresses': [ip.ip_address for ip in instance.ip_addresses],
                    'creation_time': instance.create_time.isoformat() if instance.create_time else None
                })
            
            return services
        except Exception as e:
            logger.error(f"Failed to list GCP database services: {e}")
            return []
    
    async def estimate_costs(self, workload: Dict[str, Any]) -> CloudCost:
        """Estimate GCP Cloud SQL costs"""
        try:
            machine_type = workload.get('machine_type', 'db-n1-standard-1')
            storage_gb = workload.get('storage_gb', 100)
            
            # Sample pricing (replace with real GCP Pricing API)
            machine_costs = {
                'db-f1-micro': 7.67,
                'db-g1-small': 24.27,
                'db-n1-standard-1': 51.75,
                'db-n1-standard-2': 103.50,
                'db-n1-standard-4': 207.00
            }
            
            compute_cost_monthly = machine_costs.get(machine_type, 51.75)
            storage_cost_monthly = storage_gb * 0.17  # SSD storage
            
            total_monthly = compute_cost_monthly + storage_cost_monthly
            
            recommendations = []
            if compute_cost_monthly > 50:
                recommendations.append("Consider committed use discounts for up to 57% savings")
            if workload.get('variable_load', False):
                recommendations.append("Consider automatic storage increase for cost optimization")
            
            return CloudCost(
                monthly_estimate=total_monthly,
                currency="USD",
                breakdown={
                    "compute": compute_cost_monthly,
                    "storage": storage_cost_monthly
                },
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"GCP cost estimation failed: {e}")
            return CloudCost(0.0, "USD", {}, [f"Cost estimation failed: {str(e)}"])


class CloudProviderManager:
    """Manager for all cloud providers"""
    
    def __init__(self):
        self.providers = {}
        
    def add_provider(self, name: str, provider: CloudProvider):
        """Add a cloud provider"""
        self.providers[name] = provider
        
    def get_provider(self, name: str) -> Optional[CloudProvider]:
        """Get a cloud provider by name"""
        return self.providers.get(name)
        
    async def test_all_providers(self) -> Dict[str, Tuple[bool, str]]:
        """Test connections to all configured providers"""
        results = {}
        for name, provider in self.providers.items():
            results[name] = await provider.test_connection()
        return results
        
    async def get_cost_comparison(self, workload: Dict[str, Any]) -> Dict[str, CloudCost]:
        """Compare costs across all providers"""
        costs = {}
        for name, provider in self.providers.items():
            if provider.authenticated:
                costs[name] = await provider.estimate_costs(workload)
        return costs
        
    def get_supported_providers(self) -> List[str]:
        """Get list of supported provider names"""
        return ['aws', 'azure', 'gcp', 'digitalocean']
        
    def create_provider(self, provider_type: str, credentials: Dict[str, Any]) -> CloudProvider:
        """Factory method to create provider instances"""
        if provider_type.lower() == 'aws':
            return AWSProvider(credentials)
        elif provider_type.lower() == 'azure':
            return AzureProvider(credentials)
        elif provider_type.lower() == 'gcp':
            return GCPProvider(credentials)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")


# Global instance
cloud_manager = CloudProviderManager()
