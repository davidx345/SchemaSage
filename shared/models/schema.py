"""Schema-related models."""

from typing import List, Optional, Dict, Any, Literal
from enum import Enum
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
    """Complete schema model."""
    
    name: str
    tables: List[TableModel] = []
    relationships: List[RelationshipModel] = []
    description: Optional[str] = None
    version: str = "1.0.0"
    database_type: str = "postgresql"
    
    # Metadata
    source_file: Optional[str] = None
    file_type: Optional[str] = None
    processing_stats: Dict[str, Any] = {}


class CodeGenerationRequest(BaseModel):
    """Request for code generation."""
    
    schema: SchemaModel
    output_format: Literal["sqlalchemy", "sql_ddl", "python_dataclass", "json_schema", "typescript"]
    options: Dict[str, Any] = {}


class CodeGenerationResponse(BaseModel):
    """Response from code generation."""
    
    code: str
    format: str
    filename: str
    metadata: Dict[str, Any] = {}
