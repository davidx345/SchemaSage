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
    model_config = {"protected_namespaces": ()}
    
    detected_schema: SchemaResponse = Field(..., alias="schema")
    success: bool = True
    message: Optional[str] = None
    errors: List[str] = []


class RelationshipSuggestionRequest(BaseModel):
    """Request for AI-assisted relationship suggestions."""
    tables: List[TableInfo]
    settings: Optional[SchemaSettings] = None
    context: Optional[Dict[str, Any]] = None


class RelationshipSuggestionResponse(BaseModel):
    """Response with suggested relationships."""
    relationships: List[Relationship]
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    message: Optional[str] = None
    warnings: List[str] = []


class CrossDatasetRelationshipRequest(BaseModel):
    """Request for cross-dataset relationship inference."""
    datasets: List[List[TableInfo]]
    settings: Optional[SchemaSettings] = None
    context: Optional[Dict[str, Any]] = None


class CrossDatasetRelationshipResponse(BaseModel):
    """Response with cross-dataset relationship suggestions."""
    relationships: List[Relationship]
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    message: Optional[str] = None
    warnings: List[str] = []


class LineageNodeModel(BaseModel):
    id: str
    table: str
    column: Optional[str] = None


class LineageEdgeModel(BaseModel):
    source: str
    target: str
    relationship: Optional[Relationship] = None


class TableLineageResponse(BaseModel):
    table: str
    upstream: List[str]
    downstream: List[str]
    business_term: Optional[dict] = None
    context: Optional[Any] = None


class ColumnLineageResponse(BaseModel):
    column: str
    upstream: List[str]
    downstream: List[str]
    business_term: Optional[dict] = None
    context: Optional[Any] = None


class ImpactAnalysisResponse(BaseModel):
    changed: str
    impacted: List[str]
    business_term: Optional[dict] = None
    context: Optional[Any] = None


class SchemaSnapshotModel(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    id: str
    timestamp: str
    snapshot_schema: SchemaResponse = Field(..., alias="schema")


class SchemaHistoryResponse(BaseModel):
    history: List[SchemaSnapshotModel]


class SchemaDiffResponse(BaseModel):
    tables_added: List[str]
    tables_removed: List[str]
    columns_added: List[Any]
    columns_removed: List[Any]
    relationships_added: List[Any]
    relationships_removed: List[Any]
    error: Optional[str] = None


class DocumentationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    request_schema: SchemaResponse = Field(..., alias="schema")
    table: Optional[str] = None
    column: Optional[str] = None
    relationship: Optional[dict] = None
    glossary_term: Optional[str] = None
    regenerate: bool = False
    context: Optional[Any] = None


class DocumentationResponse(BaseModel):
    object_type: str  # table, column, relationship, glossary
    object_id: str
    documentation: str
    generated: bool = True
    last_updated: Optional[str] = None
    warnings: Optional[List[str]] = None


class DataCleaningRequest(BaseModel):
    table: str
    data: List[dict]
    columns: Optional[List[str]] = None
    context: Optional[Any] = None


class CleaningSuggestion(BaseModel):
    column: str
    issue: str
    suggestion: str
    fix_code: Optional[str] = None  # SQL or Python code
    confidence: float = 1.0


class DataCleaningResponse(BaseModel):
    table: str
    suggestions: List[CleaningSuggestion]
    warnings: Optional[List[str]] = None


class ApplyCleaningRequest(BaseModel):
    table: str
    data: List[dict]
    actions: List[dict]  # e.g., [{column, action, params}]


class ApplyCleaningResponse(BaseModel):
    table: str
    cleaned_data: List[dict]
    applied_actions: List[dict]
    warnings: Optional[List[str]] = None
