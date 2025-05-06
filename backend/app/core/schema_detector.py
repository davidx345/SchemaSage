from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np
import json
import csv
import re
from io import StringIO
import os
from datetime import datetime
from fastapi import HTTPException
from ..models.schemas import SchemaResponse, TableInfo, ColumnInfo, ColumnStatistics, Relationship, SchemaSettings
from ..config import get_settings, Settings

try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False

def safe_convert_value(value: Any) -> Any:
    """Safely convert values to appropriate Python types."""
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str, list, dict)):
        return value
    try:
        # Try to convert string numbers to numeric
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ('true', 'yes', 'on', '1'):
                return True
            if value.lower() in ('false', 'no', 'off', '0'):
                return False
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                # Try to parse as date
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                return value
    except Exception:
        return str(value)
    return str(value)

class SchemaValidationError(Exception):
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}

class SchemaDetector:
    def __init__(self, settings: Optional[Dict[str, bool]] = None):
        try:
            self.config = get_settings()
            self.options = SchemaSettings(
                **settings if settings else {
                    'detect_relations': True,
                    'infer_types': True,
                    'generate_nullable': True,
                    'generate_indexes': True
                }
            )
        except Exception as e:
            raise SchemaValidationError(
                "Failed to initialize schema detector",
                {"error": str(e)}
            )

    async def detect_from_text(self, data: str) -> Dict[str, Any]:
        """Detect schema from raw text data with enhanced error handling"""
        if not data or not data.strip():
            raise SchemaValidationError("Input data cannot be empty")

        json_error = None
        csv_error = None

        # Try JSON5 (lenient JSON)
        if HAS_JSON5:
            try:
                parsed = json5.loads(data)
                return self.detect_from_json(parsed)
            except Exception as e:
                json_error = str(e)

        # Fallback to standard JSON
        try:
            parsed = json.loads(data)
            return self.detect_from_json(parsed)
        except Exception as e:
            if not json_error:
                json_error = str(e)

        # Try CSV
        try:
            f = StringIO(data)
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                return self.detect_from_csv(rows)
        except Exception as e:
            csv_error = str(e)

        # If all attempts fail, raise a detailed error (no AI fallback)
        raise SchemaValidationError(
            "Failed to detect schema from input data",
            {
                "json_error": json_error,
                "csv_error": csv_error,
                "suggestions": [
                    "Ensure input is valid JSON or CSV",
                    "Verify input data format and structure"
                ]
            }
        )

    async def _process_json_data(self, data: Any) -> Dict[str, Any]:
        """Process JSON data and detect schema."""
        if isinstance(data, list):
            if not data:
                raise SchemaValidationError("Empty array provided")
            return await self._detect_array_schema(data)
        elif isinstance(data, dict):
            return await self._detect_object_schema(data)
        else:
            raise SchemaValidationError("Input must be a JSON object or array of objects")

    async def _process_csv_data(self, data: str) -> Dict[str, Any]:
        """Process CSV data and detect schema."""
        try:
            df = pd.read_csv(StringIO(data))
            records = df.to_dict('records')
            return await self._detect_array_schema(records)
        except Exception as e:
            raise SchemaValidationError("Failed to process CSV data", {"error": str(e)})

    async def _detect_array_schema(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect schema from an array of objects."""
        if not data:
            raise SchemaValidationError("Empty array provided")

        columns = {}
        statistics = {}
        
        # Analyze each column
        for key in data[0].keys():
            values = [safe_convert_value(item.get(key)) for item in data]
            col_info = self._analyze_column(values)
            columns[key] = col_info
            statistics[key] = self._calculate_statistics(values)

        # Detect relationships if enabled
        relationships = []
        if self.options.detect_relations:
            relationships = self._detect_relationships(data, columns)

        # Generate indexes based on statistics
        indexes = []
        if self.options.generate_indexes:
            indexes = self._generate_indexes(columns, statistics)

        table_info = TableInfo(
            name="main_table",
            columns=[ColumnInfo(name=k, **v) for k, v in columns.items()],
            statistics=statistics,
            indexes=indexes
        )

        return {
            "tables": [table_info],
            "relationships": relationships
        }

    async def _detect_object_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect schema from a single object."""
        return await self._detect_array_schema([data])

    def _analyze_column(self, values: List[Any]) -> Dict[str, Any]:
        """Analyze a column's data type and constraints."""
        non_null_values = [v for v in values if v is not None]
        nullable = len(non_null_values) < len(values)
        
        if not non_null_values:
            return {"type": "String", "nullable": True}

        # Detect type
        if self.options.infer_types:
            type_info = self._infer_type(non_null_values)
        else:
            type_info = {"type": "String"}

        return {
            **type_info,
            "nullable": nullable if self.options.generate_nullable else False
        }

    def _infer_type(self, values: List[Any]) -> Dict[str, Any]:
        """Infer the data type of a column."""
        sample = values[0]
        
        if isinstance(sample, bool):
            return {"type": "Boolean"}
        elif isinstance(sample, int):
            return {"type": "Integer"}
        elif isinstance(sample, float):
            return {"type": "Float"}
        elif isinstance(sample, str):
            if self._is_date(sample):
                return {"type": "DateTime"}
            elif self._is_email(sample):
                return {
                    "type": "String",
                    "format": "email",
                    "validation": "email"
                }
            elif self._is_url(sample):
                return {
                    "type": "String",
                    "format": "uri",
                    "validation": "url"
                }
            elif len(sample) > 255:
                return {"type": "Text"}
            else:
                return {"type": "String"}
        elif isinstance(sample, dict):
            return {"type": "JSON"}
        elif isinstance(sample, list):
            return {"type": "JSON"}
        
        return {"type": "String"}

    def _calculate_statistics(self, values: List[Any]) -> ColumnStatistics:
        """Calculate column statistics."""
        total_count = len(values)
        non_null_values = [v for v in values if v is not None]
        unique_values = set(str(v) for v in non_null_values)
        
        return ColumnStatistics(
            total_count=total_count,
            null_count=total_count - len(non_null_values),
            unique_count=len(unique_values),
            unique_percentage=(len(unique_values) / len(non_null_values) * 100) if non_null_values else 0
        )

    def _detect_relationships(self, data: List[Dict[str, Any]], columns: Dict[str, Dict[str, Any]]) -> List[Relationship]:
        """Detect potential relationships between columns."""
        relationships = []
        
        for col_name, col_info in columns.items():
            if (col_name.lower().endswith('_id') or col_name.lower() == 'id') and col_name.lower() != 'id':
                referenced_table = col_name.lower().replace('_id', '')
                relationships.append(Relationship(
                    source_table="main_table",
                    source_column=col_name,
                    target_table=referenced_table,
                    target_column="id",
                    type="many-to-one",
                    confidence=0.8
                ))

        return relationships

    def _generate_indexes(self, columns: Dict[str, Dict[str, Any]], statistics: Dict[str, ColumnStatistics]) -> List[str]:
        """Generate recommended indexes based on column statistics."""
        indexes = []
        
        for col_name, stats in statistics.items():
            if stats.unique_percentage > 80:  # High uniqueness suggests index
                indexes.append(f"CREATE INDEX idx_{col_name} ON main_table ({col_name})")
                
        return indexes

    @staticmethod
    def _is_date(value: str) -> bool:
        """Check if a string value looks like a date."""
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{4}/\d{2}/\d{2}$',
            r'^\d{2}-\d{2}-\d{4}$',
            r'^\d{2}/\d{2}/\d{4}$'
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)

    @staticmethod
    def _is_email(value: str) -> bool:
        """Check if a string value looks like an email."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, value))

    @staticmethod
    def _is_url(value: str) -> bool:
        """Check if a string value looks like a URL."""
        url_pattern = r'^https?://(?:[\w-]+\.)+[\w-]+(?:/[\w-./?%&=]*)?$'
        return bool(re.match(url_pattern, value))