"""
Base types and utilities for data cleaning operations
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
import pandas as pd

class CleaningOperation(Enum):
    """Types of cleaning operations"""
    REMOVE_DUPLICATES = "remove_duplicates"
    FILL_MISSING_VALUES = "fill_missing_values"
    STANDARDIZE_FORMAT = "standardize_format"
    REMOVE_OUTLIERS = "remove_outliers"
    CONVERT_DATA_TYPES = "convert_data_types"
    NORMALIZE_TEXT = "normalize_text"
    VALIDATE_CONSTRAINTS = "validate_constraints"
    DROP_COLUMNS = "drop_columns"
    MERGE_COLUMNS = "merge_columns"
    SPLIT_COLUMNS = "split_columns"

class CleaningStrategy(Enum):
    """Cleaning strategy options"""
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    CUSTOM = "custom"

@dataclass
class CleaningResult:
    """Result of a cleaning operation"""
    operation: CleaningOperation
    success: bool
    rows_affected: int
    columns_affected: List[str]
    before_stats: Dict[str, Any]
    after_stats: Dict[str, Any]
    execution_time: float
    warnings: List[str]
    errors: List[str]

@dataclass
class CleaningPlan:
    """Plan for cleaning operations"""
    operations: List[Dict[str, Any]]
    estimated_time: float
    estimated_impact: Dict[str, Any]
    strategy: CleaningStrategy
    validation_rules: List[Dict[str, Any]]

@dataclass
class FileProcessingResult:
    """Result of file processing and cleaning"""
    original_shape: tuple
    cleaned_shape: tuple
    operations_performed: List[CleaningResult]
    quality_score_before: float
    quality_score_after: float
    processing_time: float
    warnings: List[str]
    errors: List[str]

class DataFormatType(Enum):
    """Supported data format types"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PARQUET = "parquet"
    TSV = "tsv"

class FillStrategy(Enum):
    """Strategies for filling missing values"""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    INTERPOLATE = "interpolate"
    CONSTANT = "constant"
    DROP = "drop"

class OutlierMethod(Enum):
    """Methods for outlier detection and handling"""
    IQR = "iqr"
    Z_SCORE = "z_score"
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"

class TextNormalization(Enum):
    """Text normalization options"""
    LOWERCASE = "lowercase"
    UPPERCASE = "uppercase"
    TITLE_CASE = "title_case"
    TRIM_WHITESPACE = "trim_whitespace"
    REMOVE_SPECIAL_CHARS = "remove_special_chars"
    STANDARDIZE_ENCODING = "standardize_encoding"

def validate_dataframe(df: pd.DataFrame) -> List[str]:
    """Validate DataFrame for cleaning operations"""
    issues = []
    
    if df.empty:
        issues.append("DataFrame is empty")
    
    if len(df.columns) == 0:
        issues.append("DataFrame has no columns")
    
    # Check for completely null columns
    null_columns = df.columns[df.isnull().all()].tolist()
    if null_columns:
        issues.append(f"Columns with all null values: {null_columns}")
    
    # Check for duplicate column names
    duplicate_cols = df.columns[df.columns.duplicated()].tolist()
    if duplicate_cols:
        issues.append(f"Duplicate column names: {duplicate_cols}")
    
    return issues

def estimate_cleaning_impact(df: pd.DataFrame, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Estimate the impact of cleaning operations"""
    
    current_shape = df.shape
    estimated_shape = list(current_shape)
    estimated_memory_change = 0
    estimated_data_loss = 0
    
    for operation in operations:
        op_type = operation.get("type")
        
        if op_type == CleaningOperation.REMOVE_DUPLICATES.value:
            duplicate_rows = df.duplicated().sum()
            estimated_shape[0] -= duplicate_rows
            estimated_data_loss += duplicate_rows / current_shape[0]
        
        elif op_type == CleaningOperation.DROP_COLUMNS.value:
            columns_to_drop = operation.get("columns", [])
            estimated_shape[1] -= len(columns_to_drop)
            estimated_data_loss += len(columns_to_drop) / current_shape[1]
        
        elif op_type == CleaningOperation.REMOVE_OUTLIERS.value:
            # Estimate 5% outliers (rough estimate)
            estimated_outliers = int(current_shape[0] * 0.05)
            estimated_shape[0] -= estimated_outliers
            estimated_data_loss += estimated_outliers / current_shape[0]
    
    return {
        "original_shape": current_shape,
        "estimated_shape": tuple(estimated_shape),
        "estimated_data_loss_percentage": estimated_data_loss * 100,
        "estimated_memory_change": estimated_memory_change,
        "shape_change": {
            "rows": estimated_shape[0] - current_shape[0],
            "columns": estimated_shape[1] - current_shape[1]
        }
    }

def create_cleaning_summary(results: List[CleaningResult]) -> Dict[str, Any]:
    """Create a summary of cleaning operations performed"""
    
    total_rows_affected = sum(result.rows_affected for result in results)
    total_columns_affected = set()
    for result in results:
        total_columns_affected.update(result.columns_affected)
    
    total_time = sum(result.execution_time for result in results)
    successful_operations = len([r for r in results if r.success])
    failed_operations = len(results) - successful_operations
    
    all_warnings = []
    all_errors = []
    for result in results:
        all_warnings.extend(result.warnings)
        all_errors.extend(result.errors)
    
    return {
        "total_operations": len(results),
        "successful_operations": successful_operations,
        "failed_operations": failed_operations,
        "total_rows_affected": total_rows_affected,
        "total_columns_affected": len(total_columns_affected),
        "affected_columns": list(total_columns_affected),
        "total_execution_time": total_time,
        "warnings_count": len(all_warnings),
        "errors_count": len(all_errors),
        "all_warnings": all_warnings,
        "all_errors": all_errors,
        "operations_summary": [
            {
                "operation": result.operation.value,
                "success": result.success,
                "rows_affected": result.rows_affected,
                "execution_time": result.execution_time
            }
            for result in results
        ]
    }
