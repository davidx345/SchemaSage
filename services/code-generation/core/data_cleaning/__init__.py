"""
Data Cleaning Service - Main Module
Provides data cleaning operations and recommendations
"""
import pandas as pd
import logging
import time
from typing import Dict, List, Optional, Any, Tuple

from data_quality import DataQualityAnalyzer, DataQualityReport
from .base import (
    CleaningStrategy, CleaningPlan, FileProcessingResult, CleaningResult,
    create_cleaning_summary, estimate_cleaning_impact
)
from .file_processor import FileProcessor
from .cleaning_operator import CleaningOperator

logger = logging.getLogger(__name__)

class DataCleaningService:
    """Main service for data cleaning operations"""
    
    def __init__(self):
        self.quality_analyzer = DataQualityAnalyzer()
        self.file_processor = FileProcessor()
        self.cleaning_operator = CleaningOperator()
    
    async def analyze_file_quality(
        self, 
        file_content: bytes, 
        file_type: str = "csv",
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> DataQualityReport:
        """Analyze data quality of uploaded file"""
        
        try:
            logger.info(f"Analyzing {file_type} file quality")
            
            # Load file into DataFrame
            df, load_warnings = self.file_processor.load_file(file_content, file_type)
            
            # Analyze quality
            quality_report = self.quality_analyzer.analyze_dataframe(df, schema_hints)
            
            # Add file loading warnings to metadata
            if load_warnings:
                quality_report.metadata["file_loading_warnings"] = load_warnings
            
            logger.info(f"Quality analysis complete. Score: {quality_report.overall_score:.2f}")
            return quality_report
            
        except Exception as e:
            logger.error(f"Error analyzing file quality: {str(e)}")
            raise
    
    async def clean_file(
        self, 
        file_content: bytes, 
        file_type: str = "csv",
        cleaning_strategy: CleaningStrategy = CleaningStrategy.BALANCED,
        custom_operations: Optional[List[Dict[str, Any]]] = None,
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> FileProcessingResult:
        """Clean a file using specified strategy"""
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting file cleaning with {cleaning_strategy.value} strategy")
            
            # Load file
            df, load_warnings = self.file_processor.load_file(file_content, file_type)
            original_shape = df.shape
            
            # Analyze quality first
            quality_report = self.quality_analyzer.analyze_dataframe(df, schema_hints)
            quality_score_before = quality_report.overall_score
            
            # Create cleaning plan
            if custom_operations:
                operations = custom_operations
            else:
                operations = self._create_cleaning_plan_from_strategy(
                    quality_report, cleaning_strategy
                )
            
            # Execute cleaning operations
            cleaning_results, cleaned_df = await self._execute_cleaning_operations(df, operations)
            
            # Analyze quality after cleaning
            post_clean_report = self.quality_analyzer.analyze_dataframe(cleaned_df, schema_hints)
            quality_score_after = post_clean_report.overall_score
            
            # Compile results
            processing_time = time.time() - start_time
            
            result = FileProcessingResult(
                original_shape=original_shape,
                cleaned_shape=cleaned_df.shape,
                operations_performed=cleaning_results,
                quality_score_before=quality_score_before,
                quality_score_after=quality_score_after,
                processing_time=processing_time,
                warnings=load_warnings + [w for r in cleaning_results for w in r.warnings],
                errors=[e for r in cleaning_results for e in r.errors]
            )
            
            logger.info(f"File cleaning complete. Quality improved from {quality_score_before:.2f} to {quality_score_after:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning file: {str(e)}")
            raise
    
    async def preview_cleaning_plan(
        self, 
        file_content: bytes, 
        file_type: str = "csv",
        cleaning_strategy: CleaningStrategy = CleaningStrategy.BALANCED,
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> CleaningPlan:
        """Preview what cleaning operations would be performed"""
        
        try:
            # Load file and analyze
            df, _ = self.file_processor.load_file(file_content, file_type)
            quality_report = self.quality_analyzer.analyze_dataframe(df, schema_hints)
            
            # Create operations plan
            operations = self._create_cleaning_plan_from_strategy(quality_report, cleaning_strategy)
            
            # Estimate impact
            impact = estimate_cleaning_impact(df, operations)
            
            # Estimate time (rough calculation)
            estimated_time = len(operations) * 0.5 + (df.shape[0] * df.shape[1]) / 100000
            
            plan = CleaningPlan(
                operations=operations,
                estimated_time=estimated_time,
                estimated_impact=impact,
                strategy=cleaning_strategy,
                validation_rules=[]
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating cleaning plan: {str(e)}")
            raise
    
    async def apply_custom_cleaning(
        self, 
        file_content: bytes, 
        operations: List[Dict[str, Any]],
        file_type: str = "csv"
    ) -> FileProcessingResult:
        """Apply custom cleaning operations"""
        
        return await self.clean_file(
            file_content=file_content,
            file_type=file_type,
            cleaning_strategy=CleaningStrategy.CUSTOM,
            custom_operations=operations
        )
    
    def export_cleaned_data(
        self, 
        cleaned_df: pd.DataFrame, 
        export_format: str = "csv",
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export cleaned DataFrame to specified format"""
        
        try:
            from .base import DataFormatType
            
            # Convert string format to enum
            format_map = {
                'csv': DataFormatType.CSV,
                'excel': DataFormatType.EXCEL,
                'json': DataFormatType.JSON,
                'tsv': DataFormatType.TSV,
                'parquet': DataFormatType.PARQUET
            }
            
            format_type = format_map.get(export_format.lower(), DataFormatType.CSV)
            
            return self.file_processor.export_dataframe(cleaned_df, format_type, options)
            
        except Exception as e:
            logger.error(f"Error exporting cleaned data: {str(e)}")
            raise
    
    def _create_cleaning_plan_from_strategy(
        self, 
        quality_report: DataQualityReport, 
        strategy: CleaningStrategy
    ) -> List[Dict[str, Any]]:
        """Create cleaning operations based on strategy and quality report"""
        
        operations = []
        
        if strategy == CleaningStrategy.AGGRESSIVE:
            operations = self._create_aggressive_plan(quality_report)
        elif strategy == CleaningStrategy.CONSERVATIVE:
            operations = self._create_conservative_plan(quality_report)
        elif strategy == CleaningStrategy.BALANCED:
            operations = self._create_balanced_plan(quality_report)
        else:
            logger.warning("Custom strategy specified but no custom operations provided")
        
        return operations
    
    def _create_aggressive_plan(self, quality_report: DataQualityReport) -> List[Dict[str, Any]]:
        """Create aggressive cleaning plan"""
        
        operations = []
        
        # Always remove duplicates
        operations.append({
            "type": "remove_duplicates",
            "parameters": {"keep": "first"}
        })
        
        # Drop columns with >50% missing values
        high_missing_columns = []
        for issue in quality_report.issues:
            if issue.issue_type.value == "missing_values" and issue.affected_rows > 0:
                null_percentage = (issue.affected_rows / quality_report.metadata["dataset_info"]["row_count"]) * 100
                if null_percentage > 50:
                    high_missing_columns.append(issue.column)
        
        if high_missing_columns:
            operations.append({
                "type": "drop_columns",
                "parameters": {"columns": high_missing_columns}
            })
        
        # Fill remaining missing values
        operations.append({
            "type": "fill_missing_values",
            "parameters": {"strategy": "mean"}
        })
        
        # Remove outliers
        operations.append({
            "type": "remove_outliers",
            "parameters": {"method": "iqr", "threshold": 1.5}
        })
        
        # Normalize text
        operations.append({
            "type": "normalize_text",
            "parameters": {"operations": ["lowercase", "trim_whitespace"]}
        })
        
        return operations
    
    def _create_conservative_plan(self, quality_report: DataQualityReport) -> List[Dict[str, Any]]:
        """Create conservative cleaning plan"""
        
        operations = []
        
        # Only remove exact duplicates
        operations.append({
            "type": "remove_duplicates",
            "parameters": {"keep": "first"}
        })
        
        # Only fill missing values where it's safe
        operations.append({
            "type": "fill_missing_values",
            "parameters": {"strategy": "mode"}  # Use mode for safety
        })
        
        # Only basic text normalization
        operations.append({
            "type": "normalize_text",
            "parameters": {"operations": ["trim_whitespace"]}
        })
        
        return operations
    
    def _create_balanced_plan(self, quality_report: DataQualityReport) -> List[Dict[str, Any]]:
        """Create balanced cleaning plan"""
        
        operations = []
        
        # Remove duplicates
        operations.append({
            "type": "remove_duplicates",
            "parameters": {"keep": "first"}
        })
        
        # Drop columns with >75% missing values
        very_high_missing_columns = []
        for issue in quality_report.issues:
            if issue.issue_type.value == "missing_values" and issue.affected_rows > 0:
                null_percentage = (issue.affected_rows / quality_report.metadata["dataset_info"]["row_count"]) * 100
                if null_percentage > 75:
                    very_high_missing_columns.append(issue.column)
        
        if very_high_missing_columns:
            operations.append({
                "type": "drop_columns",
                "parameters": {"columns": very_high_missing_columns}
            })
        
        # Fill missing values intelligently
        operations.append({
            "type": "fill_missing_values",
            "parameters": {"strategy": "median"}  # Balanced approach
        })
        
        # Remove extreme outliers only
        operations.append({
            "type": "remove_outliers",
            "parameters": {"method": "iqr", "threshold": 2.0}  # More lenient
        })
        
        # Standard text normalization
        operations.append({
            "type": "normalize_text",
            "parameters": {"operations": ["trim_whitespace", "standardize_encoding"]}
        })
        
        return operations
    
    async def _execute_cleaning_operations(
        self, 
        df: pd.DataFrame, 
        operations: List[Dict[str, Any]]
    ) -> Tuple[List[CleaningResult], pd.DataFrame]:
        """Execute a list of cleaning operations"""
        
        results = []
        current_df = df.copy()
        
        for operation_def in operations:
            op_type_str = operation_def.get("type")
            parameters = operation_def.get("parameters", {})
            
            try:
                # Convert string to enum
                from .base import CleaningOperation
                op_type = CleaningOperation(op_type_str)
                
                # Execute operation
                current_df, result = self.cleaning_operator.execute_operation(
                    current_df, op_type, parameters
                )
                
                results.append(result)
                
                if not result.success:
                    logger.warning(f"Operation {op_type_str} failed: {result.errors}")
                
            except ValueError as e:
                logger.error(f"Unknown operation type: {op_type_str}")
                # Create a failed result
                failed_result = CleaningResult(
                    operation=None,
                    success=False,
                    rows_affected=0,
                    columns_affected=[],
                    before_stats={},
                    after_stats={},
                    execution_time=0,
                    warnings=[],
                    errors=[f"Unknown operation type: {op_type_str}"]
                )
                results.append(failed_result)
            except Exception as e:
                logger.error(f"Error executing operation {op_type_str}: {str(e)}")
                failed_result = CleaningResult(
                    operation=None,
                    success=False,
                    rows_affected=0,
                    columns_affected=[],
                    before_stats={},
                    after_stats={},
                    execution_time=0,
                    warnings=[],
                    errors=[str(e)]
                )
                results.append(failed_result)
        
        return results, current_df
    
    def get_cleaning_summary(self, results: List[CleaningResult]) -> Dict[str, Any]:
        """Get a summary of cleaning operations performed"""
        return create_cleaning_summary(results)
    
    def validate_cleaning_results(
        self, 
        original_df: pd.DataFrame, 
        cleaned_df: pd.DataFrame,
        validation_rules: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Validate that cleaning results meet expectations"""
        
        validation_results = {
            "passed": True,
            "issues": [],
            "warnings": [],
            "statistics": {
                "original_shape": original_df.shape,
                "cleaned_shape": cleaned_df.shape,
                "rows_removed": original_df.shape[0] - cleaned_df.shape[0],
                "columns_removed": original_df.shape[1] - cleaned_df.shape[1],
                "data_loss_percentage": ((original_df.size - cleaned_df.size) / original_df.size) * 100
            }
        }
        
        # Check for excessive data loss
        if validation_results["statistics"]["data_loss_percentage"] > 50:
            validation_results["issues"].append("Excessive data loss (>50%)")
            validation_results["passed"] = False
        
        # Check if we still have data
        if cleaned_df.empty:
            validation_results["issues"].append("All data was removed during cleaning")
            validation_results["passed"] = False
        
        # Apply custom validation rules if provided
        if validation_rules:
            for rule in validation_rules:
                rule_result = self._apply_validation_rule(cleaned_df, rule)
                if not rule_result["passed"]:
                    validation_results["issues"].extend(rule_result["issues"])
                    validation_results["passed"] = False
                validation_results["warnings"].extend(rule_result.get("warnings", []))
        
        return validation_results
    
    def _apply_validation_rule(self, df: pd.DataFrame, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single validation rule"""
        
        rule_type = rule.get("type")
        result = {"passed": True, "issues": [], "warnings": []}
        
        try:
            if rule_type == "min_rows":
                min_rows = rule.get("value")
                if len(df) < min_rows:
                    result["passed"] = False
                    result["issues"].append(f"Dataset has {len(df)} rows, minimum required: {min_rows}")
            
            elif rule_type == "max_null_percentage":
                max_percentage = rule.get("value")
                null_percentage = (df.isnull().sum().sum() / df.size) * 100
                if null_percentage > max_percentage:
                    result["passed"] = False
                    result["issues"].append(f"Null percentage {null_percentage:.2f}% exceeds maximum {max_percentage}%")
            
            elif rule_type == "required_columns":
                required_cols = rule.get("value", [])
                missing_cols = set(required_cols) - set(df.columns)
                if missing_cols:
                    result["passed"] = False
                    result["issues"].append(f"Missing required columns: {list(missing_cols)}")
        
        except Exception as e:
            result["warnings"].append(f"Error applying validation rule {rule_type}: {str(e)}")
        
        return result
