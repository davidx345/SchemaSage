"""
Database Connection Models
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from enum import Enum

class DatabaseType(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"

class SSLMode(str, Enum):
    DISABLE = "disable"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"

class DatabaseConnection(BaseModel):
    """Database connection configuration model."""
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    db_type: DatabaseType
    host: str = Field(..., min_length=1)
    port: Optional[int] = None
    database: Optional[str] = None
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ssl_mode: Optional[SSLMode] = SSLMode.DISABLE
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    connection_params: Optional[Dict[str, Any]] = {}

    @validator('port', pre=True, always=True)
    def set_default_port(cls, v, values):
        if v is None and 'db_type' in values:
            defaults = {
                DatabaseType.MYSQL: 3306,
                DatabaseType.POSTGRESQL: 5432,
                DatabaseType.MONGODB: 27017,
                DatabaseType.SQLSERVER: 1433,
                DatabaseType.ORACLE: 1521
            }
            return defaults.get(values['db_type'])
        return v

class ConnectionTestResult(BaseModel):
    """Result of connection test."""
    success: bool
    message: str
    response_time_ms: Optional[float] = None
    server_version: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

class DatabaseSchema(BaseModel):
    """Database schema information."""
    database_name: str
    tables: List[Dict[str, Any]] = []
    views: List[Dict[str, Any]] = []
    procedures: List[Dict[str, Any]] = []
    functions: List[Dict[str, Any]] = []
    indexes: List[Dict[str, Any]] = []
    constraints: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

class TableSchema(BaseModel):
    """Table schema information."""
    name: str
    schema: Optional[str] = None
    columns: List[Dict[str, Any]] = []
    primary_key: Optional[List[str]] = []
    foreign_keys: List[Dict[str, Any]] = []
    indexes: List[Dict[str, Any]] = []
    constraints: List[Dict[str, Any]] = []
    row_count: Optional[int] = None
    table_size_bytes: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ColumnSchema(BaseModel):
    """Column schema information."""
    name: str
    data_type: str
    is_nullable: bool = True
    default_value: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    comment: Optional[str] = None
