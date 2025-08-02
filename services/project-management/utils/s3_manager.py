"""
AWS S3 utilities for file upload and management
"""
import os
import logging
from typing import Optional, BinaryIO

# Try to import boto3, fallback to None if not available
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    _boto3_available = True
except ImportError:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception
    _boto3_available = False

from config import settings

logger = logging.getLogger(__name__)

class S3Manager:
    """Handle S3 operations for file uploads"""
    
    def __init__(self):
        if not _boto3_available:
            logger.warning("boto3 not available - S3 operations will be disabled")
            self.s3_client = None
            self.bucket_name = None
            return
            
        if settings.USE_S3:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                self.bucket_name = settings.S3_BUCKET_NAME
                logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
            except NoCredentialsError:
                logger.error("AWS credentials not found")
                self.s3_client = None
        else:
            self.s3_client = None
            logger.info("S3 not configured, using local storage fallback")
    
    def upload_file(self, file_obj: BinaryIO, key: str, content_type: str = None) -> Optional[str]:
        """
        Upload a file to S3 bucket
        
        Args:
            file_obj: File object to upload
            key: S3 key (path) for the file
            content_type: MIME type of the file
            
        Returns:
            S3 URL of uploaded file or None if failed
        """
        if not self.s3_client:
            logger.error("S3 client not available")
            return None
            
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
                
            self.s3_client.upload_fileobj(
                file_obj, 
                self.bucket_name, 
                key,
                ExtraArgs=extra_args
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
            logger.info(f"File uploaded successfully to S3: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return None
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3 bucket
        
        Args:
            key: S3 key of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not available")
            return False
            
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"File deleted from S3: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file
        
        Args:
            key: S3 key of the file
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL or None if failed
        """
        if not self.s3_client:
            logger.error("S3 client not available")
            return None
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

# Global S3 manager instance
s3_manager = S3Manager()
