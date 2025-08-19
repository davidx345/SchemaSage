"""File-related models."""

from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID
from .base import BaseModel


class FileType(str, Enum):
    """Supported file types."""
    
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    XML = "xml"
    SQL = "sql"
    PARQUET = "parquet"


class FileStatus(str, Enum):
    """File processing status."""
    
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class FileModel(BaseModel):
    """File model - enterprise grade with UUID support."""
    
    filename: str
    original_filename: str
    file_type: FileType
    file_size: int
    status: FileStatus = FileStatus.UPLOADED
    
    # File location
    file_path: Optional[str] = None
    storage_provider: str = "supabase"  # supabase, s3, etc.
    
    # Security and integrity
    file_hash: Optional[str] = None  # SHA256 hash for deduplication
    
    # Processing information
    upload_date: Optional[str] = None
    processed: bool = False
    processing_started_at: Optional[str] = None
    processing_completed_at: Optional[str] = None
    processing_error: Optional[str] = None
    
    # File metadata stored as JSONB
    metadata: Dict[str, Any] = {}
    
    # Enterprise features
    retention_until: Optional[str] = None  # Data retention
    search_vector: Optional[str] = None  # Full-text search
    
    # Associations
    project_id: UUID  # References projects(id)
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "customer_data.csv",
                "original_filename": "Customer_Export_2025.csv",
                "file_type": "csv",
                "file_size": 1048576,
                "metadata": {
                    "encoding": "utf-8",
                    "delimiter": ",",
                    "has_header": True,
                    "row_count": 5000,
                    "column_count": 12
                }
            }
        }


class FileResponse(BaseModel):
    """File response model."""
    
    file: FileModel
    preview_data: Optional[List[Dict[str, Any]]] = None
    schema_preview: Optional[Dict[str, Any]] = None


class FileUploadRequest(BaseModel):
    """File upload request."""
    
    project_id: UUID
    filename: str
    file_type: FileType
    options: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "data_export.csv",
                "file_type": "csv",
                "options": {
                    "encoding": "utf-8",
                    "delimiter": ",",
                    "has_header": True
                }
            }
        }


class FileProcessingRequest(BaseModel):
    """File processing request."""
    
    file_id: UUID
    options: Dict[str, Any] = {}


class FilePreviewResponse(BaseModel):
    """File preview response."""
    
    headers: List[str] = []
    data: List[List[Any]] = []
    total_rows: int = 0
    sample_size: int = 0
    detected_types: Dict[str, str] = {}
    statistics: Dict[str, Any] = {}
