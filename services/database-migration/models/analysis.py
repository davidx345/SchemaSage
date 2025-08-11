"""
Schema Analysis Models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class DifferenceType(str, Enum):
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    TABLE_MODIFIED = "table_modified"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_MODIFIED = "column_modified"
    INDEX_ADDED = "index_added"
    INDEX_REMOVED = "index_removed"
    CONSTRAINT_ADDED = "constraint_added"
    CONSTRAINT_REMOVED = "constraint_removed"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_REMOVED = "relationship_removed"

class SchemaDifference(BaseModel):
    """Represents a difference between two schemas."""
    type: DifferenceType
    object_name: str
    schema_name: Optional[str] = None
    details: Dict[str, Any] = {}
    impact_level: str = Field(default="medium")  # low, medium, high, critical
    breaking_change: bool = False
    data_loss_risk: bool = False

class SchemaComparison(BaseModel):
    """Result of comparing two schemas."""
    source_schema: str
    target_schema: str
    differences: List[SchemaDifference] = []
    summary: Dict[str, int] = {}
    compatibility_score: float = Field(ge=0.0, le=1.0)
    migration_complexity: str = "low"  # low, medium, high, critical
    estimated_migration_time: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DataTypeMapping(BaseModel):
    """Data type mapping between databases."""
    source_type: str
    target_type: str
    conversion_required: bool = False
    data_loss_risk: bool = False
    conversion_notes: Optional[str] = None
    custom_conversion: Optional[str] = None

class CompatibilityMatrix(BaseModel):
    """Compatibility matrix between database types."""
    source_db: str
    target_db: str
    type_mappings: List[DataTypeMapping] = []
    supported_features: Dict[str, bool] = {}
    limitations: List[str] = []
    recommendations: List[str] = []
