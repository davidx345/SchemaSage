"""
Cloud storage integration implementations
"""
import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
from google.cloud import storage as gcs
from google.cloud.exceptions import GoogleCloudError

from .base import BaseIntegration, IntegrationConfig, IntegrationType, AuthenticationType

logger = logging.getLogger(__name__)

class CloudStorageIntegration(BaseIntegration):
    """Base class for cloud storage integrations"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.client = None
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files in storage"""
        raise NotImplementedError
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to storage"""
        raise NotImplementedError
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from storage"""
        raise NotImplementedError
    
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from storage"""
        raise NotImplementedError
    
    async def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata"""
        raise NotImplementedError

class AWSStorageIntegration(CloudStorageIntegration):
    """Integration for AWS S3"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.s3_client = None
        self.bucket_name = config.settings.get("bucket_name")
    
    async def connect(self) -> bool:
        """Establish AWS S3 connection"""
        try:
            creds = self.config.credentials.credentials
            
            if self.config.credentials.auth_type == AuthenticationType.AWS_IAM:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=creds.get("access_key_id"),
                    aws_secret_access_key=creds.get("secret_access_key"),
                    region_name=self.config.settings.get("region", "us-east-1")
                )
            elif self.config.credentials.auth_type == AuthenticationType.AWS_ROLE:
                # Assume role authentication
                sts_client = boto3.client('sts')
                assumed_role = sts_client.assume_role(
                    RoleArn=creds.get("role_arn"),
                    RoleSessionName=f"schemasage-{int(time.time())}"
                )
                
                credentials = assumed_role['Credentials']
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken'],
                    region_name=self.config.settings.get("region", "us-east-1")
                )
            else:
                # Use default credentials
                self.s3_client = boto3.client('s3')
            
            # Test connection by listing buckets
            self.s3_client.list_buckets()
            
            self.is_connected = True
            logger.info(f"Connected to AWS S3: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to AWS S3 {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close AWS S3 connection"""
        self.s3_client = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test AWS S3 connection"""
        start_time = time.time()
        
        try:
            if not self.s3_client:
                await self.connect()
            
            # Test by listing buckets
            response = self.s3_client.list_buckets()
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "AWS S3 connection successful",
                "response_time": response_time,
                "buckets_count": len(response.get('Buckets', []))
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"AWS S3 connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files in S3 bucket"""
        try:
            if not self.s3_client or not self.bucket_name:
                return []
            
            kwargs = {
                'Bucket': self.bucket_name,
                'MaxKeys': limit
            }
            
            if prefix:
                kwargs['Prefix'] = prefix
            
            response = self.s3_client.list_objects_v2(**kwargs)
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'name': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in S3: {str(e)}")
            return []
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to S3"""
        try:
            if not self.s3_client or not self.bucket_name:
                return False
            
            self.s3_client.upload_file(local_path, self.bucket_name, remote_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from S3"""
        try:
            if not self.s3_client or not self.bucket_name:
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, remote_path, local_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from S3: {str(e)}")
            return False
    
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3"""
        try:
            if not self.s3_client or not self.bucket_name:
                return False
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=remote_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {str(e)}")
            return False
    
    async def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get S3 object metadata"""
        try:
            if not self.s3_client or not self.bucket_name:
                return None
            
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=remote_path)
            
            return {
                'name': remote_path,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info from S3: {str(e)}")
            return None

class AzureStorageIntegration(CloudStorageIntegration):
    """Integration for Azure Blob Storage"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.blob_service_client = None
        self.container_name = config.settings.get("container_name")
    
    async def connect(self) -> bool:
        """Establish Azure Blob Storage connection"""
        try:
            creds = self.config.credentials.credentials
            
            if self.config.credentials.auth_type == AuthenticationType.AZURE_AD:
                # Use Azure AD authentication
                from azure.identity import DefaultAzureCredential
                credential = DefaultAzureCredential()
                
                account_url = f"https://{self.config.settings.get('account_name')}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential
                )
            else:
                # Use connection string or account key
                connection_string = creds.get("connection_string")
                if connection_string:
                    self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                else:
                    account_name = self.config.settings.get("account_name")
                    account_key = creds.get("account_key")
                    account_url = f"https://{account_name}.blob.core.windows.net"
                    
                    self.blob_service_client = BlobServiceClient(
                        account_url=account_url,
                        credential=account_key
                    )
            
            # Test connection
            list(self.blob_service_client.list_containers(max_results=1))
            
            self.is_connected = True
            logger.info(f"Connected to Azure Blob Storage: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Azure Blob Storage {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close Azure Blob Storage connection"""
        if self.blob_service_client:
            self.blob_service_client.close()
            self.blob_service_client = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Azure Blob Storage connection"""
        start_time = time.time()
        
        try:
            if not self.blob_service_client:
                await self.connect()
            
            # Test by listing containers
            containers = list(self.blob_service_client.list_containers(max_results=1))
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "Azure Blob Storage connection successful",
                "response_time": response_time,
                "account_info": "Connected successfully"
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"Azure Blob Storage connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List blobs in Azure container"""
        try:
            if not self.blob_service_client or not self.container_name:
                return []
            
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            kwargs = {'max_results': limit}
            if prefix:
                kwargs['name_starts_with'] = prefix
            
            blobs = container_client.list_blobs(**kwargs)
            
            files = []
            for blob in blobs:
                files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat(),
                    'etag': blob.etag.strip('"'),
                    'content_type': blob.content_settings.content_type if blob.content_settings else None
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in Azure Blob Storage: {str(e)}")
            return []
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Azure Blob Storage"""
        try:
            if not self.blob_service_client or not self.container_name:
                return False
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=remote_path
            )
            
            with open(local_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to Azure Blob Storage: {str(e)}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Azure Blob Storage"""
        try:
            if not self.blob_service_client or not self.container_name:
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=remote_path
            )
            
            with open(local_path, 'wb') as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from Azure Blob Storage: {str(e)}")
            return False
    
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from Azure Blob Storage"""
        try:
            if not self.blob_service_client or not self.container_name:
                return False
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=remote_path
            )
            
            blob_client.delete_blob()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from Azure Blob Storage: {str(e)}")
            return False
    
    async def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get Azure blob metadata"""
        try:
            if not self.blob_service_client or not self.container_name:
                return None
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=remote_path
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                'name': remote_path,
                'size': properties.size,
                'last_modified': properties.last_modified.isoformat(),
                'etag': properties.etag.strip('"'),
                'content_type': properties.content_settings.content_type if properties.content_settings else None,
                'metadata': properties.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info from Azure Blob Storage: {str(e)}")
            return None

class GCPStorageIntegration(CloudStorageIntegration):
    """Integration for Google Cloud Storage"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.client = None
        self.bucket_name = config.settings.get("bucket_name")
    
    async def connect(self) -> bool:
        """Establish GCP Storage connection"""
        try:
            creds = self.config.credentials.credentials
            
            if self.config.credentials.auth_type == AuthenticationType.GCP_SERVICE_ACCOUNT:
                # Use service account key
                key_file = creds.get("service_account_key_file")
                if key_file:
                    self.client = gcs.Client.from_service_account_json(key_file)
                else:
                    # Use service account info
                    service_account_info = creds.get("service_account_info")
                    self.client = gcs.Client.from_service_account_info(service_account_info)
            else:
                # Use default credentials
                self.client = gcs.Client()
            
            # Test connection by listing buckets
            list(self.client.list_buckets(max_results=1))
            
            self.is_connected = True
            logger.info(f"Connected to Google Cloud Storage: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Cloud Storage {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close GCP Storage connection"""
        self.client = None
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test GCP Storage connection"""
        start_time = time.time()
        
        try:
            if not self.client:
                await self.connect()
            
            # Test by listing buckets
            buckets = list(self.client.list_buckets(max_results=1))
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "Google Cloud Storage connection successful",
                "response_time": response_time,
                "project_id": self.client.project
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"Google Cloud Storage connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List objects in GCS bucket"""
        try:
            if not self.client or not self.bucket_name:
                return []
            
            bucket = self.client.bucket(self.bucket_name)
            
            kwargs = {'max_results': limit}
            if prefix:
                kwargs['prefix'] = prefix
            
            blobs = bucket.list_blobs(**kwargs)
            
            files = []
            for blob in blobs:
                files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.time_created.isoformat(),
                    'etag': blob.etag,
                    'content_type': blob.content_type,
                    'storage_class': blob.storage_class
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in Google Cloud Storage: {str(e)}")
            return []
    
    async def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to GCS"""
        try:
            if not self.client or not self.bucket_name:
                return False
            
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_path)
            
            blob.upload_from_filename(local_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to Google Cloud Storage: {str(e)}")
            return False
    
    async def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from GCS"""
        try:
            if not self.client or not self.bucket_name:
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_path)
            
            blob.download_to_filename(local_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from Google Cloud Storage: {str(e)}")
            return False
    
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from GCS"""
        try:
            if not self.client or not self.bucket_name:
                return False
            
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_path)
            
            blob.delete()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from Google Cloud Storage: {str(e)}")
            return False
    
    async def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get GCS object metadata"""
        try:
            if not self.client or not self.bucket_name:
                return None
            
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(remote_path)
            
            # Reload to get latest metadata
            blob.reload()
            
            return {
                'name': remote_path,
                'size': blob.size,
                'last_modified': blob.time_created.isoformat(),
                'etag': blob.etag,
                'content_type': blob.content_type,
                'storage_class': blob.storage_class,
                'metadata': blob.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info from Google Cloud Storage: {str(e)}")
            return None
