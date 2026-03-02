"""
Models for schema diff visualization endpoint.
Compares schemas and visualizes differences between source and target.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DiffType(str, Enum):
    """Type of difference detected"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class ChangeType(str, Enum):
    """Type of schema change"""
    TABLE = "table"
    COLUMN = "column"
    INDEX = "index"
    CONSTRAINT = "constraint"
    FOREIGN_KEY = "foreign_key"
    PRIMARY_KEY = "primary_key"
    UNIQUE_KEY = "unique_key"
    VIEW = "view"
    STORED_PROCEDURE = "stored_procedure"
    TRIGGER = "trigger"
    SEQUENCE = "sequence"


class ImpactLevel(str, Enum):
    """Impact level of schema change"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VisualizationFormat(str, Enum):
    """Output format for visualization"""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    DIFF = "diff"
    GRAPHICAL = "graphical"


class SchemaDefinition(BaseModel):
    """Schema definition for comparison"""
    tables: Dict[str, Dict[str, Any]] = Field(..., description="Table definitions")
    views: Optional[Dict[str, str]] = Field(None, description="View definitions")
    indexes: Optional[Dict[str, List[str]]] = Field(None, description="Index definitions")
    constraints: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="Constraint definitions")


class DiffRequest(BaseModel):
    """Request to compare and visualize schema differences"""
    source_schema: SchemaDefinition = Field(..., description="Source schema definition")
    target_schema: SchemaDefinition = Field(..., description="Target schema definition")
    output_format: VisualizationFormat = Field(
        default=VisualizationFormat.JSON,
        description="Desired output format"
    )
    show_unchanged: bool = Field(default=False, description="Include unchanged elements")
    detail_level: int = Field(default=2, ge=1, le=3, description="Level of detail (1=basic, 2=normal, 3=verbose)")
    compare_data_types: bool = Field(default=True, description="Compare data type differences")
    compare_constraints: bool = Field(default=True, description="Compare constraint differences")
    compare_indexes: bool = Field(default=True, description="Compare index differences")


class ColumnDiff(BaseModel):
    """Difference in column definition"""
    column_name: str = Field(..., description="Name of the column")
    diff_type: DiffType = Field(..., description="Type of difference")
    source_definition: Optional[Dict[str, Any]] = Field(None, description="Source column definition")
    target_definition: Optional[Dict[str, Any]] = Field(None, description="Target column definition")
    changes: List[str] = Field(default_factory=list, description="Specific changes detected")


class TableDiff(BaseModel):
    """Difference in table definition"""
    table_name: str = Field(..., description="Name of the table")
    diff_type: DiffType = Field(..., description="Type of difference")
    column_diffs: List[ColumnDiff] = Field(default_factory=list, description="Column-level differences")
    impact_level: ImpactLevel = Field(..., description="Impact level of changes")
    migration_complexity: str = Field(..., description="Estimated migration complexity")


class IndexDiff(BaseModel):
    """Difference in index definition"""
    index_name: str = Field(..., description="Name of the index")
    table_name: str = Field(..., description="Associated table")
    diff_type: DiffType = Field(..., description="Type of difference")
    source_columns: Optional[List[str]] = Field(None, description="Source index columns")
    target_columns: Optional[List[str]] = Field(None, description="Target index columns")
    impact_level: ImpactLevel = Field(..., description="Impact level")


class ConstraintDiff(BaseModel):
    """Difference in constraint definition"""
    constraint_name: str = Field(..., description="Name of the constraint")
    constraint_type: str = Field(..., description="Type of constraint (PK, FK, CHECK, etc)")
    table_name: str = Field(..., description="Associated table")
    diff_type: DiffType = Field(..., description="Type of difference")
    source_definition: Optional[str] = Field(None, description="Source constraint definition")
    target_definition: Optional[str] = Field(None, description="Target constraint definition")
    impact_level: ImpactLevel = Field(..., description="Impact level")


class ViewDiff(BaseModel):
    """Difference in view definition"""
    view_name: str = Field(..., description="Name of the view")
    diff_type: DiffType = Field(..., description="Type of difference")
    source_sql: Optional[str] = Field(None, description="Source view SQL")
    target_sql: Optional[str] = Field(None, description="Target view SQL")
    impact_level: ImpactLevel = Field(..., description="Impact level")


class MigrationAction(BaseModel):
    """Suggested migration action for a difference"""
    action_type: str = Field(..., description="Type of action (CREATE, DROP, ALTER, etc)")
    change_type: ChangeType = Field(..., description="Type of schema element")
    object_name: str = Field(..., description="Name of the object")
    sql_statement: str = Field(..., description="SQL statement to execute")
    order: int = Field(..., ge=1, description="Execution order")
    reversible: bool = Field(..., description="Whether action can be rolled back")
    risk_level: ImpactLevel = Field(..., description="Risk level of action")


class DiffStatistics(BaseModel):
    """Statistical summary of differences"""
    total_tables: int = Field(..., ge=0, description="Total tables compared")
    tables_added: int = Field(default=0, ge=0, description="Tables added in target")
    tables_removed: int = Field(default=0, ge=0, description="Tables removed from source")
    tables_modified: int = Field(default=0, ge=0, description="Tables with modifications")
    total_columns: int = Field(..., ge=0, description="Total columns compared")
    columns_added: int = Field(default=0, ge=0, description="Columns added")
    columns_removed: int = Field(default=0, ge=0, description="Columns removed")
    columns_modified: int = Field(default=0, ge=0, description="Columns modified")
    indexes_changed: int = Field(default=0, ge=0, description="Indexes with changes")
    constraints_changed: int = Field(default=0, ge=0, description="Constraints with changes")
    views_changed: int = Field(default=0, ge=0, description="Views with changes")


class DiffSummary(BaseModel):
    """Summary of schema comparison"""
    comparison_timestamp: str = Field(..., description="When comparison was performed")
    schemas_compatible: bool = Field(..., description="Whether schemas are compatible")
    compatibility_score: float = Field(..., ge=0.0, le=100.0, description="Compatibility percentage")
    critical_differences: int = Field(..., ge=0, description="Number of critical differences")
    migration_estimated_hours: float = Field(..., ge=0.0, description="Estimated migration effort")


class DiffResponse(BaseModel):
    """Response from schema diff endpoint"""
    summary: DiffSummary = Field(..., description="Summary of differences")
    statistics: DiffStatistics = Field(..., description="Statistical breakdown")
    table_diffs: List[TableDiff] = Field(default_factory=list, description="Table-level differences")
    index_diffs: List[IndexDiff] = Field(default_factory=list, description="Index-level differences")
    constraint_diffs: List[ConstraintDiff] = Field(default_factory=list, description="Constraint differences")
    view_diffs: List[ViewDiff] = Field(default_factory=list, description="View differences")
    migration_actions: List[MigrationAction] = Field(
        default_factory=list,
        description="Ordered list of migration actions"
    )
    visualization_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Visualization-specific data based on output format"
    )
    warnings: List[str] = Field(default_factory=list, description="Warnings about comparison")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for migration")
