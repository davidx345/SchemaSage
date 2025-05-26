from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Union, Any, Tuple
import uuid
from datetime import datetime

# Removed circular import: from .schemas import ...
# The models are defined below in this file.

from .orm_models import (
    Project as ORMProject,
    SchemaStorage as ORMSchemaStorage,
)  # SQLAlchemy ORM models


class CodeGenFormat(str, Enum):
    SQLALCHEMY = "sqlalchemy"
    SQL = "sql"
    JSON = "json"
    DBML = "dbml"
    PYTHON_DATACLASSES = "python_dataclasses"


class SchemaSettings(BaseModel):
    detect_relations: bool = True
    infer_types: bool = True
    generate_nullable: bool = True
    generate_indexes: bool = True

    class Config:
        validate_by_name = True


class ColumnStatistics(BaseModel):
    total_count: int
    null_count: int
    unique_count: int
    unique_percentage: float
    sample_values: Optional[List[Any]] = Field(default_factory=list)

    @field_validator("unique_percentage")
    def validate_percentage(cls, v: float) -> float:
        return round(max(0.0, min(100.0, v)), 2)


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    format: Optional[str] = None
    validation: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None
    description: Optional[str] = None
    statistics: Optional[ColumnStatistics] = None


class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]
    statistics: Optional[Dict[str, ColumnStatistics]] = None
    indexes: Optional[List[str]] = None


class Relationship(BaseModel):
    source_table: str
    target_table: str
    source_column: str
    target_column: str
    type: str = "many-to-one"
    confidence: float = 1.0

    @field_validator("confidence")
    def validate_confidence(cls, v: float) -> float:
        return round(max(0.0, min(1.0, v)), 2)


class SchemaResponse(BaseModel):
    tables: List[TableInfo]
    relationships: Optional[List[Relationship]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SchemaRequest(BaseModel):
    input: str
    settings: Optional[SchemaSettings] = None


class ChatRequest(BaseModel):
    schema_data: SchemaResponse
    messages: List[Dict[str, str]]


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None


class CodeGenRequest(BaseModel):
    schema_data: SchemaResponse
    format: CodeGenFormat
    options: Optional[Dict[str, Any]] = None


class CodeGenResponse(BaseModel):
    code: str
    language: str
    metadata: Optional[Dict[str, Any]] = None


# Pydantic models for API requests/responses that might involve ORM Project data
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic V1
        # from_attributes = True # Pydantic V2


class SchemaStorageResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    schema_data: SchemaResponse  # Re-use your existing detailed SchemaResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic V1
        # from_attributes = True # Pydantic V2


class ProjectDetailResponse(ProjectResponse):
    schemas: List[SchemaStorageResponse] = []
