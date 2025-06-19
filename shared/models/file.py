"""File-related models."""

from typing import Optional, Dict, Any, List
from enum import Enum
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
    """File model."""
    
    filename: str
    original_filename: str
    file_type: FileType
    file_size: int
    status: FileStatus = FileStatus.UPLOADED
    
    # File location
    storage_path: str
    storage_provider: str = "local"  # local, s3, etc.
    
    # Processing information
    processing_started_at: Optional[str] = None
    processing_completed_at: Optional[str] = None
    processing_error: Optional[str] = None
    
    # File metadata
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    delimiter: Optional[str] = None  # for CSV files
    has_header: bool = True  # for CSV files
    sheet_names: List[str] = []  # for Excel files
    
    # Processing results
    row_count: int = 0
    column_count: int = 0
    detected_schema: Optional[Dict[str, Any]] = None
    
    # User and project association
    user_id: str
    project_id: Optional[str] = None


class FileResponse(BaseModel):
    """File response model."""
    
    file: FileModel
    preview_data: Optional[List[Dict[str, Any]]] = None
    schema_preview: Optional[Dict[str, Any]] = None


class FileUploadRequest(BaseModel):
    """File upload request."""
    
    project_id: Optional[str] = None
    options: Dict[str, Any] = {}


class FileProcessingRequest(BaseModel):
    """File processing request."""
    
    file_id: str
    options: Dict[str, Any] = {}


class FilePreviewResponse(BaseModel):
    """File preview response."""
    
    headers: List[str] = []
    data: List[List[Any]] = []
    total_rows: int = 0
    sample_size: int = 0
    detected_types: Dict[str, str] = {}
    statistics: Dict[str, Any] = {}
