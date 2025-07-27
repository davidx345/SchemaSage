"""
Schema Analysis and Inference Module

Handles column type detection, statistics calculation, and schema inference.
"""
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np
import re
from datetime import datetime
import logging
from collections import Counter

from ..models.schemas import ColumnInfo, ColumnStatistics, TableInfo

logger = logging.getLogger(__name__)


class SchemaAnalyzer:
    """Analyzes data to infer schema information"""
    
    def __init__(self):
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        ]
        
        self.time_patterns = [
            r'\d{2}:\d{2}:\d{2}',  # HH:MM:SS
            r'\d{2}:\d{2}',        # HH:MM
        ]
        
        self.email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.url_pattern = r'^https?://[^\s]+$'
        self.phone_pattern = r'^[\+]?[1-9]?[\d\s\-\(\)]{7,15}$'
    
    def analyze_column(self, values: List[Any], column_name: str) -> ColumnInfo:
        """Analyze a column and return its information."""
        # Filter out None values for analysis
        non_null_values = [v for v in values if v is not None]
        
        if not non_null_values:
            return ColumnInfo(
                name=column_name,
                data_type="null",
                nullable=True,
                statistics=ColumnStatistics()
            )
        
        # Infer data type
        data_type = self._infer_data_type(non_null_values)
        
        # Calculate statistics
        statistics = self._calculate_statistics(non_null_values, data_type)
        
        # Check if nullable
        nullable = len(non_null_values) < len(values)
        
        # Detect patterns and constraints
        constraints = self._detect_constraints(non_null_values, data_type)
        
        return ColumnInfo(
            name=column_name,
            data_type=data_type,
            nullable=nullable,
            constraints=constraints,
            statistics=statistics
        )
    
    def _infer_data_type(self, values: List[Any]) -> str:
        """Infer the data type of a column based on its values."""
        if not values:
            return "null"
        
        # Sample up to 100 values for type inference
        sample_values = values[:100] if len(values) > 100 else values
        
        type_counts = {
            'integer': 0,
            'float': 0,
            'boolean': 0,
            'date': 0,
            'datetime': 0,
            'time': 0,
            'email': 0,
            'url': 0,
            'phone': 0,
            'string': 0
        }
        
        for value in sample_values:
            detected_type = self._detect_value_type(value)
            type_counts[detected_type] += 1
        
        # Find the most common type (excluding string as fallback)
        non_string_types = {k: v for k, v in type_counts.items() if k != 'string' and v > 0}
        
        if non_string_types:
            # If more than 80% of values match a specific type, use that type
            max_type = max(non_string_types, key=non_string_types.get)
            if non_string_types[max_type] / len(sample_values) >= 0.8:
                return max_type
        
        # Special handling for numeric types
        if type_counts['integer'] + type_counts['float'] > len(sample_values) * 0.8:
            if type_counts['float'] > 0:
                return 'float'
            else:
                return 'integer'
        
        # Check for boolean
        if type_counts['boolean'] > len(sample_values) * 0.8:
            return 'boolean'
        
        # Check for date/time types
        if type_counts['datetime'] > len(sample_values) * 0.8:
            return 'datetime'
        elif type_counts['date'] > len(sample_values) * 0.8:
            return 'date'
        elif type_counts['time'] > len(sample_values) * 0.8:
            return 'time'
        
        # Check for special string types
        if type_counts['email'] > len(sample_values) * 0.8:
            return 'email'
        elif type_counts['url'] > len(sample_values) * 0.8:
            return 'url'
        elif type_counts['phone'] > len(sample_values) * 0.8:
            return 'phone'
        
        # Default to string
        return 'string'
    
    def _detect_value_type(self, value: Any) -> str:
        """Detect the type of a single value."""
        if value is None:
            return 'null'
        
        # Convert to string for pattern matching
        str_value = str(value).strip()
        
        if isinstance(value, bool):
            return 'boolean'
        
        if isinstance(value, int):
            return 'integer'
        
        if isinstance(value, float):
            return 'float'
        
        # Try to parse as number
        try:
            if '.' in str_value:
                float(str_value)
                return 'float'
            else:
                int(str_value)
                return 'integer'
        except ValueError:
            pass
        
        # Check boolean patterns
        if str_value.lower() in ('true', 'false', 'yes', 'no', 't', 'f', 'y', 'n', '1', '0'):
            return 'boolean'
        
        # Check date patterns
        for pattern in self.date_patterns:
            if re.match(pattern, str_value):
                return 'date'
        
        # Check datetime patterns (date + time)
        for date_pattern in self.date_patterns:
            for time_pattern in self.time_patterns:
                datetime_pattern = f"{date_pattern}[ T]{time_pattern}"
                if re.match(datetime_pattern, str_value):
                    return 'datetime'
        
        # Check time patterns
        for pattern in self.time_patterns:
            if re.match(pattern, str_value):
                return 'time'
        
        # Check email pattern
        if re.match(self.email_pattern, str_value):
            return 'email'
        
        # Check URL pattern
        if re.match(self.url_pattern, str_value):
            return 'url'
        
        # Check phone pattern
        if re.match(self.phone_pattern, str_value):
            return 'phone'
        
        return 'string'
    
    def _calculate_statistics(self, values: List[Any], data_type: str) -> ColumnStatistics:
        """Calculate statistics for a column."""
        stats = ColumnStatistics()
        
        if not values:
            return stats
        
        stats.count = len(values)
        stats.unique_count = len(set(str(v) for v in values))
        stats.null_count = 0  # Already filtered nulls
        
        # Calculate min/max length for strings
        if data_type in ['string', 'email', 'url', 'phone']:
            lengths = [len(str(v)) for v in values]
            stats.min_length = min(lengths)
            stats.max_length = max(lengths)
            stats.avg_length = sum(lengths) / len(lengths)
        
        # Calculate numeric statistics
        if data_type in ['integer', 'float']:
            try:
                numeric_values = [float(v) for v in values if v is not None]
                if numeric_values:
                    stats.min_value = min(numeric_values)
                    stats.max_value = max(numeric_values)
                    stats.mean = sum(numeric_values) / len(numeric_values)
                    
                    # Calculate standard deviation
                    if len(numeric_values) > 1:
                        variance = sum((x - stats.mean) ** 2 for x in numeric_values) / len(numeric_values)
                        stats.std_dev = variance ** 0.5
            except (ValueError, TypeError):
                pass
        
        # Sample values (up to 10)
        stats.sample_values = list(set(str(v) for v in values[:10]))
        
        # Value distribution (top 10 most common values)
        value_counts = Counter(str(v) for v in values)
        stats.value_distribution = dict(value_counts.most_common(10))
        
        return stats
    
    def _detect_constraints(self, values: List[Any], data_type: str) -> Dict[str, Any]:
        """Detect constraints for a column."""
        constraints = {}
        
        if not values:
            return constraints
        
        # Check if all values are unique (potential primary key)
        unique_values = set(str(v) for v in values)
        if len(unique_values) == len(values):
            constraints['unique'] = True
        
        # Check for patterns
        if data_type == 'string':
            # Check if all values match a pattern
            str_values = [str(v) for v in values]
            
            # Check for consistent length
            lengths = set(len(v) for v in str_values)
            if len(lengths) == 1:
                constraints['fixed_length'] = list(lengths)[0]
            
            # Check for common patterns
            if all(re.match(r'^[A-Z]{2,3}\d+$', v) for v in str_values):
                constraints['pattern'] = 'alphanumeric_code'
            elif all(re.match(r'^\d+$', v) for v in str_values):
                constraints['pattern'] = 'numeric_string'
            elif all(re.match(r'^[A-Z]+$', v) for v in str_values):
                constraints['pattern'] = 'uppercase_alpha'
            elif all(re.match(r'^[a-z]+$', v) for v in str_values):
                constraints['pattern'] = 'lowercase_alpha'
        
        # Check for enum-like behavior (limited set of values)
        unique_count = len(set(str(v) for v in values))
        if unique_count <= 10 and unique_count < len(values) * 0.1:
            constraints['enum_like'] = True
            constraints['possible_values'] = list(set(str(v) for v in values))
        
        return constraints
    
    def analyze_table(self, data: List[Dict[str, Any]], table_name: str = "detected_table") -> TableInfo:
        """Analyze a table and return its information."""
        if not data:
            return TableInfo(name=table_name, columns=[], row_count=0)
        
        # Get all column names
        all_columns = set()
        for row in data:
            if isinstance(row, dict):
                all_columns.update(row.keys())
        
        # Analyze each column
        columns = []
        for col_name in sorted(all_columns):
            col_values = []
            for row in data:
                if isinstance(row, dict):
                    col_values.append(row.get(col_name))
                else:
                    col_values.append(None)
            
            column_info = self.analyze_column(col_values, col_name)
            columns.append(column_info)
        
        # Detect potential relationships and keys
        primary_key_candidates = []
        for column in columns:
            if (column.constraints and 
                column.constraints.get('unique') and 
                column.statistics and 
                column.statistics.null_count == 0):
                primary_key_candidates.append(column.name)
        
        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=len(data),
            primary_key_candidates=primary_key_candidates
        )
    
    def suggest_improvements(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Suggest improvements for the detected schema."""
        suggestions = []
        
        for column in table_info.columns:
            # Suggest indexing for unique columns
            if column.constraints and column.constraints.get('unique'):
                suggestions.append({
                    'type': 'index',
                    'column': column.name,
                    'reason': 'Column has unique values, consider adding index',
                    'priority': 'medium'
                })
            
            # Suggest constraints for enum-like columns
            if column.constraints and column.constraints.get('enum_like'):
                suggestions.append({
                    'type': 'constraint',
                    'column': column.name,
                    'reason': 'Column has limited values, consider CHECK constraint',
                    'priority': 'low',
                    'values': column.constraints.get('possible_values', [])
                })
            
            # Suggest NOT NULL for columns with no nulls
            if not column.nullable and column.statistics and column.statistics.null_count == 0:
                suggestions.append({
                    'type': 'constraint',
                    'column': column.name,
                    'reason': 'Column has no null values, consider NOT NULL constraint',
                    'priority': 'medium'
                })
            
            # Suggest data type optimization
            if column.data_type == 'string' and column.constraints and column.constraints.get('fixed_length'):
                suggestions.append({
                    'type': 'optimization',
                    'column': column.name,
                    'reason': f'Column has fixed length, consider CHAR({column.constraints["fixed_length"]}) instead of VARCHAR',
                    'priority': 'low'
                })
        
        return suggestions
