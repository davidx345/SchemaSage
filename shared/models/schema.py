"""Schema-related models."""

from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from uuid import UUID
from .base import BaseModel


class DataType(str, Enum):
    """Data types supported by SchemaSage."""
    
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"
    TEXT = "text"
    DECIMAL = "decimal"
    TIMESTAMPTZ = "timestamptz"
    JSONB = "jsonb"
    BYTEA = "bytea"


class ColumnModel(BaseModel):
    """Column model."""
    
    name: str
    data_type: DataType
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    unique: bool = False
    default_value: Optional[Any] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    description: Optional[str] = None
    constraints: List[str] = []
    
    # Statistics from data profiling
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    null_count: int = 0
    unique_count: int = 0
    sample_values: List[Any] = []


class TableModel(BaseModel):
    """Table model."""
    
    name: str
    columns: List[ColumnModel] = []
    primary_keys: List[str] = []
    foreign_keys: List[str] = []
    indexes: List[str] = []
    description: Optional[str] = None
    row_count: int = 0
    
    # Visual positioning for ER diagrams
    position_x: float = 0
    position_y: float = 0


class RelationshipType(str, Enum):
    """Relationship types."""
    
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class RelationshipModel(BaseModel):
    """Relationship model."""
    
    name: str
    from_table: str
    to_table: str
    from_column: str
    to_column: str
    relationship_type: RelationshipType
    description: Optional[str] = None
    on_delete: str = "CASCADE"
    on_update: str = "CASCADE"


class SchemaModel(BaseModel):
    """Complete schema model - enterprise grade."""
    
    schema_name: str
    schema_type: str = "database"
    schema_version: int = 1
    tables: List[TableModel] = []
    relationships: List[RelationshipModel] = []
    description: Optional[str] = None
    database_type: str = "postgresql"
    
    # Schema data stored as JSONB
    schema_data: Dict[str, Any] = {}
    
    # AI/ML metadata
    confidence_score: Optional[float] = None
    detection_model: Optional[str] = None
    detection_metadata: Dict[str, Any] = {}
    
    # Associations
    project_id: Optional[UUID] = None
    file_id: Optional[UUID] = None
    
    # Enterprise features
    search_vector: Optional[str] = None
    compressed_schema_data: Optional[bytes] = None
    
    class Config:
        schema_extra = {
            "example": {
                "schema_name": "customer_database",
                "schema_type": "relational",
                "schema_version": 1,
                "schema_data": {
                    "tables": ["customers", "orders", "products"],
                    "total_columns": 25,
                    "relationships": 3
                },
                "confidence_score": 0.95,
                "detection_model": "advanced_v2.1"
            }
        }


class CodeGenerationRequest(BaseModel):
    """Request for code generation."""
    
    schema_id: UUID
    project_id: UUID
    code_type: str = "python"  # python, sql, json_schema, typescript
    framework: Optional[str] = None  # fastapi, django, etc.
    template_used: Optional[str] = None
    options: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "code_type": "python",
                "framework": "fastapi",
                "template_used": "sqlalchemy_models",
                "options": {
                    "include_relationships": True,
                    "use_uuid_primary_keys": True,
                    "add_timestamps": True
                }
            }
        }


class CodeGenerationResponse(BaseModel):
    """Response from code generation."""
    
    id: UUID
    code_type: str
    framework: Optional[str] = None
    generated_code: str
    template_used: Optional[str] = None
    template_version: Optional[str] = None
    generation_model: Optional[str] = None
    generation_parameters: Dict[str, Any] = {}
    generation_duration_ms: Optional[int] = None
    code_hash: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "code_type": "python",
                "framework": "fastapi",
                "generated_code": "# Generated SQLAlchemy models...",
                "template_used": "sqlalchemy_models_v2",
                "generation_duration_ms": 1250
            }
        }
