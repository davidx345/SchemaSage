"""
Base types and enums for data quality analysis
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

class DataQualityIssue(Enum):
    """Types of data quality issues"""
    MISSING_VALUES = "missing_values"
    DUPLICATE_ROWS = "duplicate_rows"
    INVALID_FORMAT = "invalid_format"
    OUTLIERS = "outliers"
    INCONSISTENT_NAMING = "inconsistent_naming"
    INCORRECT_DATA_TYPE = "incorrect_data_type"
    INVALID_RELATIONSHIPS = "invalid_relationships"
    CONSTRAINT_VIOLATIONS = "constraint_violations"
    ENCODING_ISSUES = "encoding_issues"
    INCONSISTENT_CASE = "inconsistent_case"

class DataCleaningAction(Enum):
    """Types of cleaning actions"""
    DROP_ROWS = "drop_rows"
    DROP_COLUMNS = "drop_columns"
    FILL_MISSING = "fill_missing"
    STANDARDIZE_FORMAT = "standardize_format"
    REMOVE_OUTLIERS = "remove_outliers"
    NORMALIZE_TEXT = "normalize_text"
    CONVERT_TYPE = "convert_type"
    MERGE_COLUMNS = "merge_columns"
    SPLIT_COLUMNS = "split_columns"
    VALIDATE_CONSTRAINTS = "validate_constraints"

class SeverityLevel(Enum):
    """Severity levels for data quality issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class QualityIssue:
    """Represents a data quality issue"""
    issue_type: DataQualityIssue
    column: str
    severity: str
    affected_rows: int
    description: str
    sample_values: List[Any]
    suggested_actions: List[Dict[str, Any]]
    confidence_score: float

@dataclass
class CleaningRecommendation:
    """Represents a cleaning recommendation"""
    action: DataCleaningAction
    column: str
    parameters: Dict[str, Any]
    impact_assessment: Dict[str, Any]
    confidence_score: float
    reasoning: str

@dataclass
class DataQualityReport:
    """Complete data quality assessment report"""
    overall_score: float
    issues: List[QualityIssue]
    recommendations: List[CleaningRecommendation]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class ColumnProfile:
    """Statistical profile of a column"""
    name: str
    dtype: str
    null_count: int
    null_percentage: float
    unique_count: int
    cardinality_ratio: float
    min_value: Any = None
    max_value: Any = None
    mean_value: Any = None
    median_value: Any = None
    mode_value: Any = None
    std_deviation: Any = None
    quartiles: Optional[Dict[str, Any]] = None
    value_counts: Optional[Dict[str, int]] = None
    pattern_analysis: Optional[Dict[str, Any]] = None

@dataclass
class ValidationRule:
    """Data validation rule"""
    name: str
    column: str
    rule_type: str
    parameters: Dict[str, Any]
    description: str
    severity: str = "medium"

class ValidatorType(Enum):
    """Types of data validators"""
    FORMAT = "format"
    RANGE = "range"
    PATTERN = "pattern"
    UNIQUENESS = "uniqueness"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    REFERENTIAL_INTEGRITY = "referential_integrity"
