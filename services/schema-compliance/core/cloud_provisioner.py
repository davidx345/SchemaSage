"""
Cloud Provisioner Module
Handles provisioning of cloud database instances across AWS, GCP, and Azure
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
import secrets
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudProvisionerError(Exception):
    """Base exception for cloud provisioning errors"""
    pass


class AWSProvisioner:
    """Handles AWS RDS provisioning"""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize AWS provisioner
        
        Args:
            credentials: Dict with access_key, secret_key, region
        """
        self.access_key = credentials.get('access_key') or credentials.get('accessKey')
        self.secret_key = credentials.get('secret_key') or credentials.get('secretKey')
        self.region = credentials.get('region', 'us-east-1')
        
        if not self.access_key or not self.secret_key:
            raise CloudProvisionerError("AWS credentials missing")
        
        self.rds_client = None
        self.sts_client = None
        self.ec2_client = None
    
    def _get_rds_client(self):
        """Get or create RDS client"""
        if not self.rds_client:
            self.rds_client = boto3.client(
                'rds',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
        return self.rds_client
    
    def _get_sts_client(self):
        """Get or create STS client"""
        if not self.sts_client:
            self.sts_client = boto3.client(
                'sts',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
        return self.sts_client
    
    def _get_ec2_client(self):
        """Get or create EC2 client"""
        if not self.ec2_client:
            self.ec2_client = boto3.client(
                'ec2',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
        return self.ec2_client
    
    async def validate_credentials(self) -> Dict[str, Any]:
        """
        Validate AWS credentials
        
        Returns:
            Dict with validation result
        """
        try:
            sts = self._get_sts_client()
            identity = sts.get_caller_identity()
            
            # Test RDS permissions
            rds = self._get_rds_client()
            rds.describe_db_instances(MaxRecords=1)
            
            return {
                "valid": True,
                "account_id": identity['Account'],
                "permissions": [
                    "rds:CreateDBInstance",
                    "rds:DescribeDBInstances",
                    "rds:ModifyDBInstance"
                ],
                "message": "AWS credentials validated successfully"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidClientTokenId':
                return {
                    "valid": False,
                    "error": "Invalid AWS access key"
                }
            elif error_code == 'SignatureDoesNotMatch':
                return {
                    "valid": False,
                    "error": "Invalid AWS secret key"
                }
            else:
                return {
                    "valid": False,
                    "error": f"AWS error: {e.response['Error']['Message']}"
                }
        except Exception as e:
            logger.error(f"AWS credential validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def create_database_instance(
        self,
        deployment_id: str,
        database_type: str,
        instance_config: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create AWS RDS database instance
        
        Args:
            deployment_id: Unique deployment identifier
            database_type: postgresql, mysql, etc.
            instance_config: Instance configuration dict
            schema: Database schema
            
        Returns:
            Dict with instance details
        """
        try:
            rds = self._get_rds_client()
            
            # Generate unique instance ID
            instance_id = f"schemasage-{deployment_id[:8]}"
            
            # Generate secure password
            master_password = secrets.token_urlsafe(16)
            
            # Map database type to engine
            engine_map = {
                'postgresql': 'postgres',
                'mysql': 'mysql',
                'mariadb': 'mariadb'
            }
            engine = engine_map.get(database_type.lower(), 'postgres')
            
            # Get instance type
            instance_type = instance_config.get('instance_type') or instance_config.get('instanceType', 'db.t3.micro')
            storage = instance_config.get('storage', 20)
            backup_enabled = instance_config.get('backup_enabled') or instance_config.get('backupEnabled', True)
            multi_az = instance_config.get('multi_az') or instance_config.get('multiAz', False)
            public_access = instance_config.get('public_access') or instance_config.get('publicAccess', True)
            
            # Create DB instance
            logger.info(f"Creating RDS instance: {instance_id}")
            
            response = rds.create_db_instance(
                DBInstanceIdentifier=instance_id,
                DBInstanceClass=instance_type,
                Engine=engine,
                EngineVersion=self._get_engine_version(engine),
                MasterUsername='schemasage_admin',
                MasterUserPassword=master_password,
                AllocatedStorage=storage,
                StorageType='gp3',
                StorageEncrypted=True,
                BackupRetentionPeriod=7 if backup_enabled else 0,
                PubliclyAccessible=public_access,
                MultiAZ=multi_az,
                Tags=[
                    {'Key': 'ManagedBy', 'Value': 'SchemaSage'},
                    {'Key': 'DeploymentId', 'Value': deployment_id}
                ]
            )
            
            db_instance = response['DBInstance']
            
            return {
                "instance_id": instance_id,
                "status": "creating",
                "endpoint": None,  # Will be available after instance is ready
                "port": db_instance.get('DbInstancePort', 5432),
                "username": 'schemasage_admin',
                "password": master_password,
                "database": 'postgres',  # Default database
                "engine": engine
            }
            
        except ClientError as e:
            logger.error(f"Failed to create RDS instance: {e}")
            raise CloudProvisionerError(f"AWS RDS creation failed: {e.response['Error']['Message']}")
        except Exception as e:
            logger.error(f"Unexpected error creating RDS instance: {e}")
            raise CloudProvisionerError(f"Failed to create RDS instance: {str(e)}")
    
    def _get_engine_version(self, engine: str) -> str:
        """Get default engine version"""
        versions = {
            'postgres': '15.3',
            'mysql': '8.0.33',
            'mariadb': '10.11.4'
        }
        return versions.get(engine, '15.3')
    
    async def wait_for_instance_ready(self, instance_id: str, max_wait_seconds: int = 1200) -> Dict[str, Any]:
        """
        Wait for RDS instance to be available
        
        Args:
            instance_id: RDS instance identifier
            max_wait_seconds: Maximum time to wait (default 20 minutes)
            
        Returns:
            Dict with instance details when ready
        """
        try:
            rds = self._get_rds_client()
            
            waiter = rds.get_waiter('db_instance_available')
            
            logger.info(f"Waiting for RDS instance {instance_id} to be ready...")
            
            waiter.wait(
                DBInstanceIdentifier=instance_id,
                WaiterConfig={
                    'Delay': 30,  # Check every 30 seconds
                    'MaxAttempts': max_wait_seconds // 30
                }
            )
            
            # Get instance details
            response = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            db_instance = response['DBInstances'][0]
            
            endpoint = db_instance.get('Endpoint', {})
            
            return {
                "status": "ready",
                "endpoint": endpoint.get('Address'),
                "port": endpoint.get('Port', 5432),
                "engine": db_instance['Engine'],
                "storage": db_instance['AllocatedStorage']
            }
            
        except Exception as e:
            logger.error(f"Error waiting for RDS instance: {e}")
            raise CloudProvisionerError(f"Instance creation timeout or failed: {str(e)}")
    
    async def delete_database_instance(self, instance_id: str) -> bool:
        """
        Delete RDS instance
        
        Args:
            instance_id: RDS instance identifier
            
        Returns:
            True if deletion initiated successfully
        """
        try:
            rds = self._get_rds_client()
            
            rds.delete_db_instance(
                DBInstanceIdentifier=instance_id,
                SkipFinalSnapshot=True,
                DeleteAutomatedBackups=True
            )
            
            logger.info(f"RDS instance {instance_id} deletion initiated")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'DBInstanceNotFound':
                logger.warning(f"RDS instance {instance_id} not found")
                return True
            else:
                logger.error(f"Failed to delete RDS instance: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error deleting RDS instance: {e}")
            return False


class GCPProvisioner:
    """Handles GCP Cloud SQL provisioning"""
    
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize GCP provisioner"""
        self.project_id = credentials.get('project_id') or credentials.get('projectId')
        self.credentials_json = credentials.get('credentials_json') or credentials.get('credentialsJson')
        self.region = credentials.get('region', 'us-central1')
        
        if not self.project_id:
            raise CloudProvisionerError("GCP project_id missing")
        
        try:
            from google.cloud import sql_v1
            from google.oauth2 import service_account
            import json
            
            # Parse credentials
            if isinstance(self.credentials_json, str):
                creds_dict = json.loads(self.credentials_json)
            else:
                creds_dict = self.credentials_json
            
            # Create credentials
            self.credentials = service_account.Credentials.from_service_account_info(creds_dict)
            self.sql_client = sql_v1.SqlInstancesServiceClient(credentials=self.credentials)
            
        except ImportError:
            logger.error("GCP libraries not installed. Install: pip install google-cloud-sql")
            raise CloudProvisionerError("GCP SDK not available")
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            raise CloudProvisionerError(f"GCP initialization failed: {str(e)}")
    
    async def validate_credentials(self) -> Dict[str, Any]:
        """Validate GCP credentials"""
        try:
            # Try to list instances (will fail if credentials invalid)
            request = {
                "project": self.project_id
            }
            list(self.sql_client.list(request=request))
            
            return {
                "valid": True,
                "project_id": self.project_id,
                "permissions": ["cloudsql.instances.create", "cloudsql.instances.list"],
                "message": "GCP credentials validated successfully"
            }
            
        except Exception as e:
            logger.error(f"GCP credential validation failed: {e}")
            return {
                "valid": False,
                "error": f"GCP validation failed: {str(e)}"
            }
    
    async def create_database_instance(
        self,
        deployment_id: str,
        database_type: str,
        instance_config: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create GCP Cloud SQL instance"""
        try:
            from google.cloud.sql_v1.types import DatabaseInstance, Settings, IpConfiguration
            import secrets
            
            # Generate unique instance name
            instance_name = f"schemasage-{deployment_id[:8]}"
            
            # Generate secure password
            master_password = secrets.token_urlsafe(16)
            
            # Map database type
            engine_map = {
                'postgresql': 'POSTGRES_15',
                'mysql': 'MYSQL_8_0',
            }
            database_version = engine_map.get(database_type.lower(), 'POSTGRES_15')
            
            # Get tier (instance type)
            tier = instance_config.get('instance_type', 'db-f1-micro')
            storage_gb = instance_config.get('storage', 10)
            
            # Create instance configuration
            instance = DatabaseInstance(
                name=instance_name,
                database_version=database_version,
                region=self.region,
                settings=Settings(
                    tier=tier,
                    data_disk_size_gb=storage_gb,
                    ip_configuration=IpConfiguration(
                        ipv4_enabled=True,
                        authorized_networks=[]  # Allow all for now
                    ),
                    backup_configuration={
                        "enabled": instance_config.get('backup_enabled', True)
                    }
                ),
                root_password=master_password
            )
            
            # Create instance
            request = {
                "project": self.project_id,
                "instance": instance
            }
            
            operation = self.sql_client.insert(request=request)
            
            logger.info(f"Created GCP Cloud SQL instance: {instance_name}")
            
            return {
                "instance_id": instance_name,
                "status": "creating",
                "endpoint": None,  # Will be available after creation
                "port": 5432 if 'postgres' in database_type.lower() else 3306,
                "username": "postgres" if 'postgres' in database_type.lower() else "root",
                "password": master_password,
                "database": "postgres" if 'postgres' in database_type.lower() else "mysql",
                "engine": database_type
            }
            
        except Exception as e:
            logger.error(f"Failed to create GCP instance: {e}")
            raise CloudProvisionerError(f"GCP instance creation failed: {str(e)}")
    
    async def wait_for_instance_ready(self, instance_id: str, max_wait_seconds: int = 1200) -> Dict[str, Any]:
        """Wait for GCP instance to be ready"""
        try:
            import time
            
            start_time = time.time()
            
            while time.time() - start_time < max_wait_seconds:
                # Get instance
                request = {
                    "project": self.project_id,
                    "instance": instance_id
                }
                instance = self.sql_client.get(request=request)
                
                if instance.state == "RUNNABLE":
                    # Get IP address
                    ip_address = None
                    if instance.ip_addresses:
                        ip_address = instance.ip_addresses[0].ip_address
                    
                    return {
                        "status": "ready",
                        "endpoint": ip_address,
                        "port": 5432 if 'POSTGRES' in instance.database_version else 3306,
                        "engine": instance.database_version
                    }
                
                await asyncio.sleep(30)
            
            raise CloudProvisionerError("Instance creation timeout")
            
        except Exception as e:
            logger.error(f"Error waiting for GCP instance: {e}")
            raise CloudProvisionerError(f"Instance wait failed: {str(e)}")
    
    async def delete_database_instance(self, instance_id: str) -> bool:
        """Delete GCP instance"""
        try:
            request = {
                "project": self.project_id,
                "instance": instance_id
            }
            self.sql_client.delete(request=request)
            
            logger.info(f"GCP instance {instance_id} deletion initiated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete GCP instance: {e}")
            return False


class AzureProvisioner:
    """Handles Azure Database provisioning"""
    
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize Azure provisioner"""
        self.subscription_id = credentials.get('subscription_id') or credentials.get('subscriptionId')
        self.tenant_id = credentials.get('tenant_id') or credentials.get('tenantId')
        self.client_id = credentials.get('client_id') or credentials.get('clientId')
        self.client_secret = credentials.get('client_secret') or credentials.get('clientSecret')
        self.region = credentials.get('region', 'eastus')
        
        if not all([self.subscription_id, self.tenant_id, self.client_id, self.client_secret]):
            raise CloudProvisionerError("Azure credentials incomplete")
        
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient
            from azure.mgmt.rdbms.mysql_flexibleservers import MySQLManagementClient
            
            # Create credential
            self.credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Create clients (will be selected based on database type)
            self.pg_client = None
            self.mysql_client = None
            
        except ImportError:
            logger.error("Azure libraries not installed. Install: pip install azure-mgmt-rdbms azure-identity")
            raise CloudProvisionerError("Azure SDK not available")
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            raise CloudProvisionerError(f"Azure initialization failed: {str(e)}")
    
    async def validate_credentials(self) -> Dict[str, Any]:
        """Validate Azure credentials"""
        try:
            from azure.mgmt.resource import ResourceManagementClient
            
            # Test credentials by listing resource groups
            resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            list(resource_client.resource_groups.list())
            
            return {
                "valid": True,
                "subscription_id": self.subscription_id,
                "permissions": ["Microsoft.DBforPostgreSQL/flexibleServers/write"],
                "message": "Azure credentials validated successfully"
            }
            
        except Exception as e:
            logger.error(f"Azure credential validation failed: {e}")
            return {
                "valid": False,
                "error": f"Azure validation failed: {str(e)}"
            }
    
    async def create_database_instance(
        self,
        deployment_id: str,
        database_type: str,
        instance_config: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Azure Database instance"""
        try:
            from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient
            from azure.mgmt.rdbms.postgresql_flexibleservers.models import Server, Sku, Storage
            import secrets
            
            # Generate names
            resource_group = f"schemasage-{deployment_id[:8]}"
            server_name = f"schemasage-{deployment_id[:8]}"
            
            # Generate secure password
            admin_password = secrets.token_urlsafe(16) + "!A1"  # Azure requires complex password
            
            # Get SKU
            sku_name = instance_config.get('instance_type', 'Standard_B1ms')
            storage_gb = instance_config.get('storage', 32)
            
            # Create PostgreSQL client
            if 'postgres' in database_type.lower():
                from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient
                from azure.mgmt.rdbms.postgresql_flexibleservers.models import (
                    Server, Sku, Storage, Backup, HighAvailability
                )
                
                pg_client = PostgreSQLManagementClient(self.credential, self.subscription_id)
                
                # Create resource group first
                from azure.mgmt.resource import ResourceManagementClient
                resource_client = ResourceManagementClient(self.credential, self.subscription_id)
                resource_client.resource_groups.create_or_update(
                    resource_group,
                    {"location": self.region}
                )
                
                # Create server
                server_params = Server(
                    location=self.region,
                    sku=Sku(name=sku_name, tier="Burstable"),
                    administrator_login="schemasage_admin",
                    administrator_login_password=admin_password,
                    storage=Storage(storage_size_gb=storage_gb),
                    backup=Backup(
                        backup_retention_days=7 if instance_config.get('backup_enabled') else 1
                    ),
                    version="15",
                    high_availability=HighAvailability(mode="Disabled")
                )
                
                # Start creation (async operation)
                poller = pg_client.servers.begin_create(
                    resource_group_name=resource_group,
                    server_name=server_name,
                    parameters=server_params
                )
                
                logger.info(f"Created Azure PostgreSQL server: {server_name}")
                
                return {
                    "instance_id": f"{resource_group}/{server_name}",
                    "status": "creating",
                    "endpoint": None,
                    "port": 5432,
                    "username": "schemasage_admin",
                    "password": admin_password,
                    "database": "postgres",
                    "engine": "postgresql",
                    "_poller": poller  # Store for waiting
                }
            else:
                raise CloudProvisionerError(f"Azure support for {database_type} not yet implemented")
                
        except Exception as e:
            logger.error(f"Failed to create Azure instance: {e}")
            raise CloudProvisionerError(f"Azure instance creation failed: {str(e)}")
    
    async def wait_for_instance_ready(self, instance_id: str, max_wait_seconds: int = 1200) -> Dict[str, Any]:
        """Wait for Azure instance to be ready"""
        try:
            from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient
            
            # Parse instance_id
            resource_group, server_name = instance_id.split('/')
            
            pg_client = PostgreSQLManagementClient(self.credential, self.subscription_id)
            
            import time
            start_time = time.time()
            
            while time.time() - start_time < max_wait_seconds:
                # Get server
                server = pg_client.servers.get(resource_group, server_name)
                
                if server.state == "Ready":
                    return {
                        "status": "ready",
                        "endpoint": server.fully_qualified_domain_name,
                        "port": 5432,
                        "engine": "postgresql"
                    }
                
                await asyncio.sleep(30)
            
            raise CloudProvisionerError("Instance creation timeout")
            
        except Exception as e:
            logger.error(f"Error waiting for Azure instance: {e}")
            raise CloudProvisionerError(f"Instance wait failed: {str(e)}")
    
    async def delete_database_instance(self, instance_id: str) -> bool:
        """Delete Azure instance"""
        try:
            from azure.mgmt.rdbms.postgresql_flexibleservers import PostgreSQLManagementClient
            from azure.mgmt.resource import ResourceManagementClient
            
            # Parse instance_id
            resource_group, server_name = instance_id.split('/')
            
            pg_client = PostgreSQLManagementClient(self.credential, self.subscription_id)
            
            # Delete server
            pg_client.servers.begin_delete(resource_group, server_name).result()
            
            # Delete resource group
            resource_client = ResourceManagementClient(self.credential, self.subscription_id)
            resource_client.resource_groups.begin_delete(resource_group).result()
            
            logger.info(f"Azure instance {instance_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Azure instance: {e}")
            return False


class CloudProvisioner:
    """
    Main cloud provisioner - routes to appropriate provider
    """
    
    @staticmethod
    def get_provisioner(provider: str, credentials: Dict[str, Any]):
        """
        Get provisioner for specified provider
        
        Args:
            provider: 'aws', 'gcp', or 'azure'
            credentials: Provider credentials
            
        Returns:
            Provider-specific provisioner instance
        """
        provider = provider.lower()
        
        if provider == 'aws':
            return AWSProvisioner(credentials)
        elif provider == 'gcp':
            return GCPProvisioner(credentials)
        elif provider == 'azure':
            return AzureProvisioner(credentials)
        else:
            raise CloudProvisionerError(f"Unsupported provider: {provider}")
    
    @staticmethod
    async def validate_credentials(provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credentials for any provider"""
        provisioner = CloudProvisioner.get_provisioner(provider, credentials)
        return await provisioner.validate_credentials()
    
    @staticmethod
    async def provision_database(
        provider: str,
        credentials: Dict[str, Any],
        deployment_id: str,
        database_type: str,
        instance_config: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provision database on any provider"""
        provisioner = CloudProvisioner.get_provisioner(provider, credentials)
        
        # Create instance
        instance_info = await provisioner.create_database_instance(
            deployment_id,
            database_type,
            instance_config,
            schema
        )
        
        # Wait for ready
        ready_info = await provisioner.wait_for_instance_ready(instance_info['instance_id'])
        
        # Merge info
        result = {**instance_info, **ready_info}
        
        # Build connection string
        result['connection_string'] = build_connection_string(
            database_type,
            result.get('endpoint'),
            result.get('port'),
            result.get('database', 'postgres'),
            result.get('username'),
            result.get('password')
        )
        
        return result
    
    @staticmethod
    async def delete_database(provider: str, credentials: Dict[str, Any], instance_id: str) -> bool:
        """Delete database on any provider"""
        provisioner = CloudProvisioner.get_provisioner(provider, credentials)
        return await provisioner.delete_database_instance(instance_id)


def build_connection_string(
    database_type: str,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str
) -> str:
    """Build database connection string"""
    
    if database_type.lower() in ['postgresql', 'postgres']:
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    elif database_type.lower() == 'mysql':
        return f"mysql://{username}:{password}@{host}:{port}/{database}"
    elif database_type.lower() == 'mongodb':
        return f"mongodb://{username}:{password}@{host}:{port}/{database}"
    else:
        return f"{database_type}://{username}:{password}@{host}:{port}/{database}"
