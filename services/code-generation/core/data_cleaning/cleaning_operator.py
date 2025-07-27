"""
Data cleaning operations executor
"""
import pandas as pd
import numpy as np
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from scipy import stats

from .base import (
    CleaningOperation, CleaningResult, FillStrategy, 
    OutlierMethod, TextNormalization, CleaningStrategy
)

logger = logging.getLogger(__name__)

class CleaningOperator:
    """Executes data cleaning operations"""
    
    def __init__(self):
        self.operation_map = {
            CleaningOperation.REMOVE_DUPLICATES: self._remove_duplicates,
            CleaningOperation.FILL_MISSING_VALUES: self._fill_missing_values,
            CleaningOperation.STANDARDIZE_FORMAT: self._standardize_format,
            CleaningOperation.REMOVE_OUTLIERS: self._remove_outliers,
            CleaningOperation.CONVERT_DATA_TYPES: self._convert_data_types,
            CleaningOperation.NORMALIZE_TEXT: self._normalize_text,
            CleaningOperation.DROP_COLUMNS: self._drop_columns,
            CleaningOperation.MERGE_COLUMNS: self._merge_columns,
            CleaningOperation.SPLIT_COLUMNS: self._split_columns
        }
    
    def execute_operation(
        self, 
        df: pd.DataFrame, 
        operation: CleaningOperation,
        parameters: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, CleaningResult]:
        """Execute a single cleaning operation"""
        
        start_time = time.time()
        before_stats = self._calculate_stats(df)
        warnings = []
        errors = []
        
        try:
            if operation not in self.operation_map:
                raise ValueError(f"Unsupported operation: {operation}")
            
            # Execute the operation
            cleaned_df, op_warnings = self.operation_map[operation](df, parameters)
            warnings.extend(op_warnings)
            
            # Calculate results
            after_stats = self._calculate_stats(cleaned_df)
            execution_time = time.time() - start_time
            
            # Determine affected rows and columns
            rows_affected = abs(len(df) - len(cleaned_df))
            columns_affected = list(set(df.columns) - set(cleaned_df.columns)) if len(df.columns) != len(cleaned_df.columns) else parameters.get('columns', [])
            
            result = CleaningResult(
                operation=operation,
                success=True,
                rows_affected=rows_affected,
                columns_affected=columns_affected,
                before_stats=before_stats,
                after_stats=after_stats,
                execution_time=execution_time,
                warnings=warnings,
                errors=errors
            )
            
            logger.info(f"Successfully executed {operation.value} in {execution_time:.2f}s")
            return cleaned_df, result
            
        except Exception as e:
            execution_time = time.time() - start_time
            errors.append(str(e))
            
            result = CleaningResult(
                operation=operation,
                success=False,
                rows_affected=0,
                columns_affected=[],
                before_stats=before_stats,
                after_stats=before_stats,
                execution_time=execution_time,
                warnings=warnings,
                errors=errors
            )
            
            logger.error(f"Failed to execute {operation.value}: {str(e)}")
            return df, result
    
    def _remove_duplicates(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Remove duplicate rows"""
        
        warnings = []
        
        subset = parameters.get('subset')  # Columns to consider for duplicates
        keep = parameters.get('keep', 'first')  # Which duplicates to keep
        
        initial_count = len(df)
        cleaned_df = df.drop_duplicates(subset=subset, keep=keep)
        removed_count = initial_count - len(cleaned_df)
        
        if removed_count > 0:
            warnings.append(f"Removed {removed_count} duplicate rows")
        else:
            warnings.append("No duplicate rows found")
        
        return cleaned_df, warnings
    
    def _fill_missing_values(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Fill missing values using specified strategy"""
        
        warnings = []
        cleaned_df = df.copy()
        
        strategy = parameters.get('strategy', FillStrategy.MEAN.value)
        columns = parameters.get('columns', list(df.columns))
        fill_value = parameters.get('fill_value')
        
        for column in columns:
            if column not in df.columns:
                warnings.append(f"Column '{column}' not found, skipping")
                continue
            
            null_count = df[column].isnull().sum()
            if null_count == 0:
                continue
            
            try:
                if strategy == FillStrategy.MEAN.value:
                    if pd.api.types.is_numeric_dtype(df[column]):
                        fill_val = df[column].mean()
                        cleaned_df[column] = cleaned_df[column].fillna(fill_val)
                    else:
                        warnings.append(f"Cannot compute mean for non-numeric column '{column}', using mode instead")
                        fill_val = df[column].mode().iloc[0] if len(df[column].mode()) > 0 else "Unknown"
                        cleaned_df[column] = cleaned_df[column].fillna(fill_val)
                
                elif strategy == FillStrategy.MEDIAN.value:
                    if pd.api.types.is_numeric_dtype(df[column]):
                        fill_val = df[column].median()
                        cleaned_df[column] = cleaned_df[column].fillna(fill_val)
                    else:
                        warnings.append(f"Cannot compute median for non-numeric column '{column}', using mode instead")
                        fill_val = df[column].mode().iloc[0] if len(df[column].mode()) > 0 else "Unknown"
                        cleaned_df[column] = cleaned_df[column].fillna(fill_val)
                
                elif strategy == FillStrategy.MODE.value:
                    mode_values = df[column].mode()
                    fill_val = mode_values.iloc[0] if len(mode_values) > 0 else "Unknown"
                    cleaned_df[column] = cleaned_df[column].fillna(fill_val)
                
                elif strategy == FillStrategy.FORWARD_FILL.value:
                    cleaned_df[column] = cleaned_df[column].fillna(method='ffill')
                
                elif strategy == FillStrategy.BACKWARD_FILL.value:
                    cleaned_df[column] = cleaned_df[column].fillna(method='bfill')
                
                elif strategy == FillStrategy.INTERPOLATE.value:
                    if pd.api.types.is_numeric_dtype(df[column]):
                        cleaned_df[column] = cleaned_df[column].interpolate()
                    else:
                        warnings.append(f"Cannot interpolate non-numeric column '{column}', using forward fill")
                        cleaned_df[column] = cleaned_df[column].fillna(method='ffill')
                
                elif strategy == FillStrategy.CONSTANT.value:
                    if fill_value is not None:
                        cleaned_df[column] = cleaned_df[column].fillna(fill_value)
                    else:
                        warnings.append(f"No fill_value provided for constant strategy, using 'Unknown'")
                        cleaned_df[column] = cleaned_df[column].fillna("Unknown")
                
                warnings.append(f"Filled {null_count} missing values in column '{column}' using {strategy}")
                
            except Exception as e:
                warnings.append(f"Error filling missing values in column '{column}': {str(e)}")
        
        return cleaned_df, warnings
    
    def _remove_outliers(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Remove outliers using specified method"""
        
        warnings = []
        cleaned_df = df.copy()
        
        method = parameters.get('method', OutlierMethod.IQR.value)
        columns = parameters.get('columns', list(df.select_dtypes(include=[np.number]).columns))
        threshold = parameters.get('threshold', 1.5)
        
        total_outliers_removed = 0
        
        for column in columns:
            if column not in df.columns:
                warnings.append(f"Column '{column}' not found, skipping")
                continue
            
            if not pd.api.types.is_numeric_dtype(df[column]):
                warnings.append(f"Column '{column}' is not numeric, skipping outlier removal")
                continue
            
            initial_count = len(cleaned_df)
            
            if method == OutlierMethod.IQR.value:
                Q1 = cleaned_df[column].quantile(0.25)
                Q3 = cleaned_df[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                outlier_mask = (cleaned_df[column] < lower_bound) | (cleaned_df[column] > upper_bound)
                cleaned_df = cleaned_df[~outlier_mask]
            
            elif method == OutlierMethod.Z_SCORE.value:
                z_scores = np.abs(stats.zscore(cleaned_df[column].dropna()))
                outlier_mask = z_scores > threshold
                valid_indices = cleaned_df[column].dropna().index
                cleaned_df = cleaned_df.drop(valid_indices[outlier_mask])
            
            outliers_removed = initial_count - len(cleaned_df)
            total_outliers_removed += outliers_removed
            
            if outliers_removed > 0:
                warnings.append(f"Removed {outliers_removed} outliers from column '{column}' using {method}")
        
        if total_outliers_removed > 0:
            warnings.append(f"Total outliers removed: {total_outliers_removed}")
        else:
            warnings.append("No outliers found")
        
        return cleaned_df, warnings
    
    def _convert_data_types(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Convert data types of specified columns"""
        
        warnings = []
        cleaned_df = df.copy()
        
        type_conversions = parameters.get('conversions', {})
        
        for column, target_type in type_conversions.items():
            if column not in df.columns:
                warnings.append(f"Column '{column}' not found, skipping")
                continue
            
            try:
                if target_type in ['int', 'int64']:
                    cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors='coerce').astype('Int64')
                elif target_type in ['float', 'float64']:
                    cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors='coerce')
                elif target_type in ['str', 'string', 'object']:
                    cleaned_df[column] = cleaned_df[column].astype(str)
                elif target_type in ['datetime', 'datetime64']:
                    cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors='coerce')
                elif target_type in ['bool', 'boolean']:
                    cleaned_df[column] = cleaned_df[column].astype(bool)
                else:
                    cleaned_df[column] = cleaned_df[column].astype(target_type)
                
                warnings.append(f"Converted column '{column}' to {target_type}")
                
            except Exception as e:
                warnings.append(f"Error converting column '{column}' to {target_type}: {str(e)}")
        
        return cleaned_df, warnings
    
    def _normalize_text(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Normalize text in specified columns"""
        
        warnings = []
        cleaned_df = df.copy()
        
        operations = parameters.get('operations', [])
        columns = parameters.get('columns', list(df.select_dtypes(include=['object']).columns))
        
        for column in columns:
            if column not in df.columns:
                warnings.append(f"Column '{column}' not found, skipping")
                continue
            
            original_column = cleaned_df[column].copy()
            
            for operation in operations:
                try:
                    if operation == TextNormalization.LOWERCASE.value:
                        cleaned_df[column] = cleaned_df[column].astype(str).str.lower()
                    
                    elif operation == TextNormalization.UPPERCASE.value:
                        cleaned_df[column] = cleaned_df[column].astype(str).str.upper()
                    
                    elif operation == TextNormalization.TITLE_CASE.value:
                        cleaned_df[column] = cleaned_df[column].astype(str).str.title()
                    
                    elif operation == TextNormalization.TRIM_WHITESPACE.value:
                        cleaned_df[column] = cleaned_df[column].astype(str).str.strip()
                    
                    elif operation == TextNormalization.REMOVE_SPECIAL_CHARS.value:
                        cleaned_df[column] = cleaned_df[column].astype(str).str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
                    
                except Exception as e:
                    warnings.append(f"Error applying {operation} to column '{column}': {str(e)}")
                    cleaned_df[column] = original_column  # Revert on error
            
            changes = (original_column != cleaned_df[column]).sum()
            if changes > 0:
                warnings.append(f"Applied text normalization to {changes} values in column '{column}'")
        
        return cleaned_df, warnings
    
    def _standardize_format(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Standardize format of specified columns"""
        
        warnings = []
        cleaned_df = df.copy()
        
        format_rules = parameters.get('format_rules', {})
        
        for column, rules in format_rules.items():
            if column not in df.columns:
                warnings.append(f"Column '{column}' not found, skipping")
                continue
            
            try:
                format_type = rules.get('type')
                
                if format_type == 'date':
                    date_format = rules.get('format', '%Y-%m-%d')
                    cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors='coerce').dt.strftime(date_format)
                
                elif format_type == 'phone':
                    # Remove all non-digits and format as (XXX) XXX-XXXX
                    cleaned_df[column] = cleaned_df[column].astype(str).str.replace(r'\D', '', regex=True)
                    mask = cleaned_df[column].str.len() == 10
                    cleaned_df.loc[mask, column] = cleaned_df.loc[mask, column].str.replace(
                        r'(\d{3})(\d{3})(\d{4})', r'(\1) \2-\3', regex=True
                    )
                
                elif format_type == 'email':
                    # Basic email standardization (lowercase)
                    cleaned_df[column] = cleaned_df[column].astype(str).str.lower().str.strip()
                
                warnings.append(f"Standardized format for column '{column}' as {format_type}")
                
            except Exception as e:
                warnings.append(f"Error standardizing format for column '{column}': {str(e)}")
        
        return cleaned_df, warnings
    
    def _drop_columns(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Drop specified columns"""
        
        warnings = []
        
        columns_to_drop = parameters.get('columns', [])
        existing_columns = [col for col in columns_to_drop if col in df.columns]
        missing_columns = [col for col in columns_to_drop if col not in df.columns]
        
        if missing_columns:
            warnings.append(f"Columns not found: {missing_columns}")
        
        if existing_columns:
            cleaned_df = df.drop(columns=existing_columns)
            warnings.append(f"Dropped columns: {existing_columns}")
        else:
            cleaned_df = df.copy()
            warnings.append("No columns to drop")
        
        return cleaned_df, warnings
    
    def _merge_columns(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Merge multiple columns into one"""
        
        warnings = []
        cleaned_df = df.copy()
        
        source_columns = parameters.get('source_columns', [])
        target_column = parameters.get('target_column', 'merged_column')
        separator = parameters.get('separator', ' ')
        drop_source = parameters.get('drop_source', True)
        
        # Check if source columns exist
        existing_columns = [col for col in source_columns if col in df.columns]
        missing_columns = [col for col in source_columns if col not in df.columns]
        
        if missing_columns:
            warnings.append(f"Source columns not found: {missing_columns}")
        
        if len(existing_columns) < 2:
            warnings.append("Need at least 2 existing columns to merge")
            return cleaned_df, warnings
        
        try:
            # Merge columns
            cleaned_df[target_column] = cleaned_df[existing_columns].astype(str).agg(separator.join, axis=1)
            
            # Drop source columns if requested
            if drop_source:
                cleaned_df = cleaned_df.drop(columns=existing_columns)
                warnings.append(f"Merged {len(existing_columns)} columns into '{target_column}' and dropped source columns")
            else:
                warnings.append(f"Merged {len(existing_columns)} columns into '{target_column}' (kept source columns)")
            
        except Exception as e:
            warnings.append(f"Error merging columns: {str(e)}")
        
        return cleaned_df, warnings
    
    def _split_columns(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Split a column into multiple columns"""
        
        warnings = []
        cleaned_df = df.copy()
        
        source_column = parameters.get('source_column')
        target_columns = parameters.get('target_columns', [])
        separator = parameters.get('separator', ' ')
        drop_source = parameters.get('drop_source', True)
        
        if source_column not in df.columns:
            warnings.append(f"Source column '{source_column}' not found")
            return cleaned_df, warnings
        
        try:
            # Split column
            split_data = cleaned_df[source_column].astype(str).str.split(separator, expand=True)
            
            # Assign to target columns
            for i, target_col in enumerate(target_columns):
                if i < split_data.shape[1]:
                    cleaned_df[target_col] = split_data.iloc[:, i]
                else:
                    cleaned_df[target_col] = None
                    warnings.append(f"Not enough split parts for column '{target_col}', filled with None")
            
            # Drop source column if requested
            if drop_source:
                cleaned_df = cleaned_df.drop(columns=[source_column])
                warnings.append(f"Split column '{source_column}' into {len(target_columns)} columns and dropped source")
            else:
                warnings.append(f"Split column '{source_column}' into {len(target_columns)} columns (kept source)")
            
        except Exception as e:
            warnings.append(f"Error splitting column: {str(e)}")
        
        return cleaned_df, warnings
    
    def _calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for a DataFrame"""
        
        return {
            "shape": df.shape,
            "memory_usage": df.memory_usage(deep=True).sum(),
            "null_count": df.isnull().sum().sum(),
            "null_percentage": (df.isnull().sum().sum() / df.size) * 100 if df.size > 0 else 0,
            "dtypes": df.dtypes.astype(str).to_dict()
        }
