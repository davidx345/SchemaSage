"""
Data models for Code Generation Service
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class CodeGenFormat(str, Enum):
    """Supported code generation formats"""
    SQLALCHEMY = "sqlalchemy"
    PRISMA = "prisma"
    TYPEORM = "typeorm"
    DJANGO_ORM = "django_orm"
    SQL = "sql"
    JSON = "json"
    PYTHON_DATACLASSES = "python_dataclasses"
    DBML = "dbml"
    TYPESCRIPT_INTERFACES = "typescript_interfaces"

class ColumnStatistics(BaseModel):
    """Statistics for a table column"""
    unique_count: int = Field(..., description="Number of unique values")
    unique_percentage: float = Field(..., description="Percentage of unique values")
    null_count: int = Field(..., description="Number of null values")
    null_percentage: float = Field(..., description="Percentage of null values")
    avg_length: Optional[float] = Field(None, description="Average length for string columns")
    min_length: Optional[int] = Field(None, description="Minimum length for string columns")
    max_length: Optional[int] = Field(None, description="Maximum length for string columns")

class ColumnInfo(BaseModel):
    """Information about a table column"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    nullable: bool = Field(True, description="Whether column can be null")
    is_primary_key: bool = Field(False, description="Whether column is a primary key")
    is_foreign_key: bool = Field(False, description="Whether column is a foreign key")
    default: Optional[Any] = Field(None, description="Default value for the column")
    unique: bool = Field(False, description="Whether column has unique constraint")
    format: Optional[str] = Field(None, description="Format hint for the column")
    validation: Optional[str] = Field(None, description="Validation rule for the column")
    statistics: Optional[ColumnStatistics] = Field(None, description="Statistical information")
    max_length: Optional[int] = Field(None, description="Maximum length for string columns")
    description: Optional[str] = Field(None, description="Column description")

class TableInfo(BaseModel):
    """Information about a table"""
    name: str = Field(..., description="Table name")
    columns: List[ColumnInfo] = Field(..., description="List of columns")
    primary_keys: List[str] = Field(default_factory=list, description="List of primary key column names")
    foreign_keys: Union[List[str], List[Dict[str, Any]]] = Field(default_factory=list, description="List of foreign key references (string names or objects)")
    indexes: Union[List[str], List[Dict[str, Any]]] = Field(default_factory=list, description="List of index names (string names or objects)")
    description: Optional[str] = Field(None, description="Table description")
    
    @field_validator('foreign_keys', mode='before')
    @classmethod
    def normalize_foreign_keys(cls, v):
        """Normalize foreign keys to list of strings"""
        if not v:
            return []
        
        # If already a list of strings, return as-is
        if isinstance(v, list) and all(isinstance(item, str) for item in v):
            return v
        
        # If list of dicts, extract the 'name' field
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [item.get('name', '') for item in v if item.get('name')]
        
        return v
    
    @field_validator('indexes', mode='before')
    @classmethod
    def normalize_indexes(cls, v):
        """Normalize indexes to list of strings"""
        if not v:
            return []
        
        # If already a list of strings, return as-is
        if isinstance(v, list) and all(isinstance(item, str) for item in v):
            return v
        
        # If list of dicts, extract the 'name' field
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return [item.get('name', '') for item in v if item.get('name')]
        
        return v

class Relationship(BaseModel):
    """Database relationship information"""
    source_table: str = Field(..., description="Source table name")
    source_column: str = Field(..., description="Source column name")
    target_table: str = Field(..., description="Target table name")
    target_column: str = Field(..., description="Target column name")
    type: str = Field(..., description="Relationship type (one-to-one, one-to-many, etc.)", alias="relationship_type")
    
    @field_validator('type', mode='before')
    @classmethod
    def normalize_relationship_type(cls, v, info):
        """Accept both 'type' and 'relationship_type' fields"""
        # If the value is provided, return it
        if v:
            return v
        
        # Check if 'relationship_type' exists in the raw data
        if hasattr(info, 'data') and 'relationship_type' in info.data:
            return info.data['relationship_type']
        
        # Default to 'many-to-one' if not provided
        return 'many-to-one'
    
    class Config:
        populate_by_name = True

class SchemaMetadata(BaseModel):
    """Metadata about the schema"""
    version: str = Field("1.0", description="Schema version")
    created_at: Optional[str] = Field(None, description="Schema creation timestamp")
    description: Optional[str] = Field(None, description="Schema description")
    source: Optional[str] = Field(None, description="Data source information")

class SchemaResponse(BaseModel):
    """Complete schema information"""
    tables: List[TableInfo] = Field(..., description="List of tables")
    relationships: List[Relationship] = Field(default_factory=list, description="Table relationships")
    metadata: Optional[SchemaMetadata] = Field(None, description="Schema metadata")

class CodeGenerationRequest(BaseModel):
    """Request for code generation"""
    schema: SchemaResponse = Field(..., description="Database schema to generate code from")
    format: CodeGenFormat = Field(..., description="Output format for generated code")
    options: Optional[Dict[str, Any]] = Field(None, description="Generation options")
    
    class Config:
        populate_by_name = True

class CodeGenerationResponse(BaseModel):
    """Response from code generation"""
    code: str = Field(..., description="Generated code")
    format: CodeGenFormat = Field(..., description="Format of generated code")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Generation metadata")

class ApiHealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    template_count: int = Field(..., description="Number of available templates")
    ai_enhanced: bool = Field(..., description="Whether AI enhancement is available")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    format: Optional[str] = Field(None, description="Format that caused the error")
    code: Optional[str] = Field(None, description="Error code")
