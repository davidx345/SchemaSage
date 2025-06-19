"""Schema models for Schema Detection Service."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ColumnStatistics(BaseModel):
    """Statistics for a column."""
    total_count: int = 0
    null_count: int = 0
    unique_count: int = 0
    unique_percentage: float = 0.0
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_length: Optional[float] = None


class ColumnInfo(BaseModel):
    """Information about a database column."""
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    unique: bool = False
    default: Optional[Any] = None
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    format: Optional[str] = None
    validation: Optional[str] = None
    description: Optional[str] = None


class TableInfo(BaseModel):
    """Information about a database table."""
    name: str
    columns: List[ColumnInfo] = []
    primary_keys: List[str] = []
    foreign_keys: List[Dict[str, str]] = []
    indexes: List[str] = []
    statistics: Dict[str, ColumnStatistics] = {}
    estimated_rows: Optional[int] = None
    description: Optional[str] = None


class RelationshipType(str, Enum):
    """Types of relationships between tables."""
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"


class Relationship(BaseModel):
    """Relationship between tables."""
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    description: Optional[str] = None


class SchemaSettings(BaseModel):
    """Settings for schema detection."""
    detect_relations: bool = True
    infer_types: bool = True
    generate_nullable: bool = True
    generate_indexes: bool = True
    max_sample_size: int = 1000
    confidence_threshold: float = 0.7


class SchemaResponse(BaseModel):
    """Complete schema detection response."""
    tables: List[TableInfo] = []
    relationships: List[Relationship] = []
    metadata: Dict[str, Any] = {}
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    processing_time: Optional[float] = None
    warnings: List[str] = []


class DetectionRequest(BaseModel):
    """Request for schema detection."""
    data: str
    settings: Optional[SchemaSettings] = None
    format_hint: Optional[str] = None  # json, csv, etc.


class DetectionResponse(BaseModel):
    """Response from schema detection."""
    schema: SchemaResponse
    success: bool = True
    message: Optional[str] = None
    errors: List[str] = []
