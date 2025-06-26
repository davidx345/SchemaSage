"""Schema Detection Core Logic."""

from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np
import json
import csv
import re
from io import StringIO
import os
from datetime import datetime
import time
import logging
import httpx
from models.schemas import (
    SchemaResponse, TableInfo, ColumnInfo, ColumnStatistics, 
    Relationship, SchemaSettings, RelationshipType,
    RelationshipSuggestionResponse, CrossDatasetRelationshipResponse
)
from config import get_settings

try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False

logger = logging.getLogger(__name__)
settings = get_settings()


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
    """Schema validation error."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}


class SchemaDetector:
    """Advanced schema detection with AI-powered inference."""
    
    def __init__(self, detection_settings: Optional[SchemaSettings] = None):
        self.settings = detection_settings or SchemaSettings()
        self.processing_start_time = None
        
    def build_schema_inference_prompt(
        data: str,
        tables: Optional[List[TableInfo]] = None,
        datasets: Optional[List[List[TableInfo]]] = None,
        glossary: Optional[List[dict]] = None,
        context: Optional[dict] = None,
        max_data_chars: int = 2000
    ) -> str:
        """
        Build a highly detailed, robust, and efficient prompt for schema, relationship, and context inference.
        """
        prompt = [
            "You are an expert data architect and database designer. Your task is to infer the most accurate, business-relevant, and normalized database schema from the provided data and context.",
            "",
            "Instructions:",
            "1. Analyze the data and context to identify tables, columns, data types, primary keys, foreign keys, and all possible relationships (one-to-one, one-to-many, many-to-many, etc.).",
            "2. For each relationship, provide:",
            "   - source_table, source_column, target_table, target_column, type (one-to-one, one-to-many, many-to-one, many-to-many), confidence (0.0-1.0), and a concise business-oriented description.",
            "3. Use glossary terms (if provided) to improve naming, context, and business meaning. Match columns/tables to glossary terms where possible.",
            "4. If datasets are provided, infer cross-dataset relationships and highlight any business or referential links.",
            "5. If context is provided, use it to improve accuracy and relevance.",
            "6. Output only valid, minified JSON (no markdown, no explanations, no comments).",
            "7. The output JSON schema MUST be:",
            "   {",
            "     tables: [",
            "       { name: string, columns: [ { name: string, type: string, nullable: bool, primary_key: bool, foreign_key: string|null, unique: bool, default: any|null, length: int|null, precision: int|null, scale: int|null, format: string|null, validation: string|null, description: string|null } ], primary_keys: [string], foreign_keys: [ { column: string, references: { table: string, column: string } } ], indexes: [string], statistics: object, estimated_rows: int|null, description: string|null }",
            "     ],",
            "     relationships: [",
            "       { source_table: string, source_column: string, target_table: string, target_column: string, type: string, confidence: float, description: string }",
            "     ],",
            "     metadata: object,",
            "     confidence: float,",
            "     processing_time: float|null,",
            "     warnings: [string]",
            "   }",
            "8. If you are unsure, use best practices and reasonable defaults. Never hallucinate columns or relationships not supported by the data/context.",
            "9. If any error or ambiguity is detected, include a warning in the 'warnings' array and proceed with best effort.",
            "10. Be efficient: do not repeat information, and keep the output as concise as possible while fully representing the schema and relationships.",
            "",
        ]
        if glossary:
            prompt.append("Glossary terms (use for business context and naming):\n" + json.dumps(glossary, indent=2))
        if context:
            prompt.append("Additional context:\n" + json.dumps(context, indent=2))
        if datasets:
            prompt.append("Infer relationships across the following datasets. Each dataset is an array of tables. Consider cross-dataset keys and business meaning.")
            for i, ds in enumerate(datasets):
                prompt.append(f"Dataset {i+1}:\n" + json.dumps([t.dict() for t in ds], indent=2))
        elif tables:
            prompt.append("Tables:\n" + json.dumps([t.dict() for t in tables], indent=2))
        else:
            prompt.append("Data sample:\n" + data[:max_data_chars] + ("..." if len(data) > max_data_chars else ""))
        prompt.append("\nReturn only valid, minified JSON. Do not include explanations, markdown, or comments. Output must match the schema above exactly.")
        return "\n".join(prompt)

    async def _call_gemini(self, data: str, tables: Optional[List[TableInfo]] = None, datasets: Optional[List[List[TableInfo]]] = None, glossary: Optional[List[dict]] = None, context: Optional[dict] = None) -> dict:
        """Call Gemini API to infer schema, relationships, and context."""
        from config import settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            raise SchemaValidationError("No Gemini API key configured for AI fallback.")
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}
        prompt = build_schema_inference_prompt(
            data=data,
            tables=tables,
            datasets=datasets,
            glossary=glossary,
            context=context
        )
        data_json = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, params=params, json=data_json, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            try:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            except Exception:
                raise SchemaValidationError("Gemini API response parsing failed.", {"response": result})

    async def detect_schema(self, data: str, format_hint: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point for schema detection."""
        self.processing_start_time = time.time()
        warnings = []
        try:
            if not data or not data.strip():
                raise SchemaValidationError("Input data cannot be empty")
            
            # Detect data format and parse
            parsed_data = await self._parse_data(data, format_hint)
            
            # Detect schema structure
            schema_result = await self._analyze_data_structure(parsed_data)
            
            # Add processing metadata
            processing_time = time.time() - self.processing_start_time
            schema_result['processing_time'] = processing_time
            schema_result['metadata'] = {
                'data_size_bytes': len(data),
                'format_detected': self._detect_format(data),
                'processing_timestamp': datetime.utcnow().isoformat(),
                'service_version': settings.VERSION
            }
            schema_result['warnings'] = warnings
            return schema_result
            
        except SchemaValidationError as e:
            warnings.append(str(e))
            return {
                'tables': [],
                'relationships': [],
                'metadata': {},
                'confidence': 0.0,
                'processing_time': time.time() - self.processing_start_time,
                'warnings': warnings
            }
        except Exception as e:
            logger.error(f"Schema detection failed: {str(e)}")
            # Fallback to Gemini if enabled
            from config import settings
            if getattr(settings, 'GEMINI_API_KEY', None):
                logger.info("Falling back to Gemini API for schema detection.")
                return await self._call_gemini(data)
            raise SchemaValidationError(f"Schema detection failed: {str(e)}")
    
    async def _parse_data(self, data: str, format_hint: Optional[str] = None) -> Any:
        """Parse raw data into structured format."""
        if format_hint == 'json':
            return await self._parse_json(data)
        elif format_hint == 'csv':
            return await self._parse_csv(data)
        elif format_hint == 'excel' or format_hint == 'xlsx':
            import pandas as pd
            from io import BytesIO
            try:
                df = pd.read_excel(BytesIO(data.encode('utf-8')))
                return df.to_dict('records')
            except Exception as e:
                raise SchemaValidationError(f"Invalid Excel file: {str(e)}")
        else:
            # Auto-detect format
            return await self._auto_parse(data)
    
    async def _auto_parse(self, data: str) -> Any:
        """Auto-detect format and parse data."""
        json_error = None
        csv_error = None
        
        # Try JSON5 first (more lenient)
        if HAS_JSON5 and settings.ENABLE_JSON5:
            try:
                return json5.loads(data)
            except Exception as e:
                json_error = str(e)
        
        # Try standard JSON
        try:
            return json.loads(data)
        except Exception as e:
            if not json_error:
                json_error = str(e)
        
        # Try CSV
        try:
            return await self._parse_csv(data)
        except Exception as e:
            csv_error = str(e)
        
        # All parsing failed
        raise SchemaValidationError(
            "Unable to parse data - not valid JSON or CSV",
            {
                "json_error": json_error,
                "csv_error": csv_error,
                "data_preview": data[:200] + "..." if len(data) > 200 else data
            }
        )
    
    async def _parse_json(self, data: str) -> Any:
        """Parse JSON data."""
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            if HAS_JSON5:
                try:
                    return json5.loads(data)
                except Exception:
                    pass
            raise SchemaValidationError(f"Invalid JSON: {str(e)}")
    
    async def _parse_csv(self, data: str) -> List[Dict[str, Any]]:
        """Parse CSV data."""
        try:
            # Try different delimiters
            for delimiter in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(StringIO(data), delimiter=delimiter, nrows=self.settings.max_sample_size)
                    if len(df.columns) > 1:  # Successfully detected multiple columns
                        return df.to_dict('records')
                except:
                    continue
            
            # Fallback to comma delimiter
            df = pd.read_csv(StringIO(data), nrows=self.settings.max_sample_size)
            return df.to_dict('records')
            
        except Exception as e:
            raise SchemaValidationError(f"Invalid CSV: {str(e)}")
    
    async def _analyze_data_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze parsed data and extract schema."""
        if isinstance(data, list):
            if not data:
                raise SchemaValidationError("Empty array provided")
            return await self._analyze_array(data)
        elif isinstance(data, dict):
            return await self._analyze_object(data)
        else:
            raise SchemaValidationError("Data must be an object or array of objects")
    
    async def _analyze_array(self, data: List[Any]) -> Dict[str, Any]:
        warnings = []
        if not data:
            warnings.append("Empty array provided.")
            raise SchemaValidationError("Empty array provided")
        
        # Sample data if too large
        sample = data[:self.settings.max_sample_size] if len(data) > self.settings.max_sample_size else data
        
        # Extract all unique keys
        all_keys = set()
        for item in sample:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        if not all_keys:
            raise SchemaValidationError("No valid objects found in array")
        
        # Analyze each column
        columns = {}
        statistics = {}
        
        for key in all_keys:
            values = [safe_convert_value(item.get(key)) for item in sample if isinstance(item, dict)]
            column_info = await self._analyze_column(key, values)
            columns[key] = column_info
            statistics[key] = self._calculate_statistics(values)
        
        # Create table info
        table = TableInfo(
            name="main_table",
            columns=[ColumnInfo(name=k, **v) for k, v in columns.items()],
            statistics=statistics,
            estimated_rows=len(data)
        )
        
        # Detect relationships
        relationships = []
        if self.settings.detect_relations and settings.ENABLE_RELATIONSHIP_DETECTION:
            relationships = await self._detect_relationships(sample, columns)
        
        # Add warning for high null columns
        for key, stats in statistics.items():
            if stats.null_count > 0 and stats.null_count / stats.total_count > 0.3:
                warnings.append(f"Column '{key}' has more than 30% missing values.")
        
        # Add confidence indicator
        confidence = 1.0
        if len(data) < 10:
            confidence = 0.5
            warnings.append("Low sample size, confidence reduced.")
        
        return {
            'tables': [table],
            'relationships': relationships,
            'metadata': {},
            'confidence': confidence,
            'processing_time': time.time() - self.processing_start_time,
            'warnings': warnings
        }
    
    async def _analyze_object(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single object."""
        return await self._analyze_array([data])
    
    async def _analyze_column(self, name: str, values: List[Any]) -> Dict[str, Any]:
        """Analyze a single column."""
        non_null_values = [v for v in values if v is not None]
        nullable = len(non_null_values) < len(values)
        
        if not non_null_values:
            return {
                "type": "String",
                "nullable": True,
                "confidence": 0.1
            }
        
        # Infer type
        type_info = await self._infer_column_type(name, non_null_values)
        
        # Detect constraints
        constraints = await self._detect_constraints(name, non_null_values)
        
        return {
            **type_info,
            **constraints,
            "nullable": nullable if self.settings.generate_nullable else False
        }
    
    async def _infer_column_type(self, name: str, values: List[Any]) -> Dict[str, Any]:
        """Infer the data type of a column with confidence scoring."""
        if not values:
            return {"type": "String", "confidence": 0.1}
        
        sample = values[0]
        type_confidence = 1.0
        
        # Check type consistency
        consistent_type = all(type(v) == type(sample) for v in values[:100])  # Check first 100
        if not consistent_type:
            type_confidence *= 0.7
        
        # Type inference with pattern recognition
        if isinstance(sample, bool):
            return {"type": "Boolean", "confidence": type_confidence}
        elif isinstance(sample, int):
            # Check if it's actually an ID
            if name.lower().endswith('_id') or name.lower() == 'id':
                return {"type": "Integer", "primary_key": name.lower() == 'id', "confidence": type_confidence}
            return {"type": "Integer", "confidence": type_confidence}
        elif isinstance(sample, float):
            return {"type": "Float", "confidence": type_confidence}
        elif isinstance(sample, str):
            return await self._analyze_string_type(name, values, type_confidence)
        elif isinstance(sample, (dict, list)):
            return {"type": "JSON", "confidence": type_confidence * 0.8}
        
        return {"type": "String", "confidence": 0.5}
    
    async def _analyze_string_type(self, name: str, values: List[str], base_confidence: float) -> Dict[str, Any]:
        """Analyze string values for specific patterns."""
        sample_values = values[:100]  # Analyze first 100 values
        
        # Pattern analysis
        date_count = sum(1 for v in sample_values if self._is_date(str(v)))
        email_count = sum(1 for v in sample_values if self._is_email(str(v)))
        url_count = sum(1 for v in sample_values if self._is_url(str(v)))
        uuid_count = sum(1 for v in sample_values if self._is_uuid(str(v)))
        
        total_count = len(sample_values)
        
        # Date detection
        if date_count / total_count > 0.8:
            return {
                "type": "DateTime",
                "format": "date",
                "confidence": base_confidence * (date_count / total_count)
            }
        
        # Email detection
        if email_count / total_count > 0.8:
            return {
                "type": "String",
                "format": "email",
                "validation": "email",
                "confidence": base_confidence * (email_count / total_count)
            }
        
        # URL detection
        if url_count / total_count > 0.8:
            return {
                "type": "String",
                "format": "uri",
                "validation": "url",
                "confidence": base_confidence * (url_count / total_count)
            }
        
        # UUID detection
        if uuid_count / total_count > 0.8:
            return {
                "type": "UUID",
                "confidence": base_confidence * (uuid_count / total_count)
            }
        
        # Text vs String based on length
        avg_length = sum(len(str(v)) for v in sample_values) / len(sample_values)
        if avg_length > 255:
            return {"type": "Text", "confidence": base_confidence}
        
        return {"type": "String", "confidence": base_confidence}
    
    async def _detect_constraints(self, name: str, values: List[Any]) -> Dict[str, Any]:
        """Detect column constraints."""
        constraints = {}
        
        # Unique constraint
        unique_count = len(set(str(v) for v in values))
        if unique_count == len(values):
            constraints["unique"] = True
        
        # Primary key detection
        if (name.lower() == 'id' or name.lower().endswith('_id')) and constraints.get("unique", False):
            constraints["primary_key"] = name.lower() == 'id'
        
        return constraints
    
    async def _detect_relationships(self, data: List[Dict[str, Any]], columns: Dict[str, Dict[str, Any]]) -> List[Relationship]:
        """Detect potential relationships between columns."""
        relationships = []
        
        for col_name, col_info in columns.items():
            # Foreign key detection
            if col_name.lower().endswith('_id') and col_name.lower() != 'id':
                referenced_table = col_name.lower().replace('_id', '')
                
                # Calculate confidence based on data patterns
                confidence = 0.8
                if col_info.get("type") == "Integer":
                    confidence += 0.1
                
                relationships.append(Relationship(
                    source_table="main_table",
                    source_column=col_name,
                    target_table=referenced_table,
                    target_column="id",
                    type=RelationshipType.MANY_TO_ONE,
                    confidence=confidence
                ))
        
        return relationships
    
    async def suggest_relationships(self, tables: List[TableInfo], context: Optional[dict] = None) -> RelationshipSuggestionResponse:
        """Suggest relationships between tables using heuristics and AI extension points."""
        suggestions = []
        # Heuristic: match columns with similar names and types, e.g., id/user_id/project_id
        for i, table_a in enumerate(tables):
            for table_b in tables[i+1:]:
                for col_a in table_a.columns:
                    for col_b in table_b.columns:
                        if (
                            col_a.name.lower() == col_b.name.lower() or
                            col_a.name.lower().endswith('_id') and col_b.name.lower().endswith('_id')
                        ) and col_a.type == col_b.type:
                            suggestions.append(Relationship(
                                source_table=table_a.name,
                                source_column=col_a.name,
                                target_table=table_b.name,
                                target_column=col_b.name,
                                type=RelationshipType.ONE_TO_MANY,
                                confidence=0.7,
                                description=f"Heuristic match: {col_a.name} <-> {col_b.name}"
                            ))
        # TODO: Integrate AI prompt here for advanced suggestions
        return RelationshipSuggestionResponse(
            relationships=suggestions,
            confidence=0.7 if suggestions else 0.0,
            message="Heuristic relationship suggestions. AI extension point available.",
            warnings=[] if suggestions else ["No relationships found by heuristics."]
        )

    async def cross_dataset_relationships(self, datasets: List[List[TableInfo]], context: Optional[dict] = None) -> CrossDatasetRelationshipResponse:
        """Infer relationships across multiple datasets using heuristics and AI extension points."""
        suggestions = []
        # Heuristic: match columns with same name/type across datasets
        for i, tables_a in enumerate(datasets):
            for tables_b in datasets[i+1:]:
                for table_a in tables_a:
                    for table_b in tables_b:
                        for col_a in table_a.columns:
                            for col_b in table_b.columns:
                                if col_a.name.lower() == col_b.name.lower() and col_a.type == col_b.type:
                                    suggestions.append(Relationship(
                                        source_table=table_a.name,
                                        source_column=col_a.name,
                                        target_table=table_b.name,
                                        target_column=col_b.name,
                                        type=RelationshipType.ONE_TO_ONE,
                                        confidence=0.6,
                                        description=f"Cross-dataset match: {col_a.name} <-> {col_b.name}"
                                    ))
        # TODO: Integrate AI prompt here for advanced cross-dataset suggestions
        return CrossDatasetRelationshipResponse(
            relationships=suggestions,
            confidence=0.6 if suggestions else 0.0,
            message="Heuristic cross-dataset relationship suggestions. AI extension point available.",
            warnings=[] if suggestions else ["No cross-dataset relationships found by heuristics."]
        )
    
    def _calculate_statistics(self, values: List[Any]) -> ColumnStatistics:
        """Calculate comprehensive column statistics."""
        total_count = len(values)
        non_null_values = [v for v in values if v is not None]
        null_count = total_count - len(non_null_values)
        
        if not non_null_values:
            return ColumnStatistics(
                total_count=total_count,
                null_count=null_count,
                unique_count=0,
                unique_percentage=0.0
            )
        
        unique_values = list(set(str(v) for v in non_null_values))
        unique_count = len(unique_values)
        unique_percentage = (unique_count / len(non_null_values)) * 100
        
        # Calculate min/max for numeric values
        min_value = None
        max_value = None
        avg_length = None
        
        try:
            numeric_values = [v for v in non_null_values if isinstance(v, (int, float))]
            if numeric_values:
                min_value = min(numeric_values)
                max_value = max(numeric_values)
        except:
            pass
        
        # Calculate average length for strings
        try:
            string_values = [str(v) for v in non_null_values]
            if string_values:
                avg_length = sum(len(s) for s in string_values) / len(string_values)
        except:
            pass
        
        return ColumnStatistics(
            total_count=total_count,
            null_count=null_count,
            unique_count=unique_count,
            unique_percentage=unique_percentage,
            min_value=min_value,
            max_value=max_value,
            avg_length=avg_length
        )
    
    def _calculate_confidence(self, columns: Dict[str, Dict[str, Any]], statistics: Dict[str, ColumnStatistics]) -> float:
        """Calculate overall schema detection confidence."""
        if not columns:
            return 0.0
        
        confidences = []
        for col_name, col_info in columns.items():
            col_confidence = col_info.get("confidence", 0.5)
            
            # Boost confidence for well-structured data
            stats = statistics.get(col_name)
            if stats:
                if stats.null_count == 0:  # No nulls
                    col_confidence += 0.1
                if stats.unique_percentage > 90:  # High uniqueness
                    col_confidence += 0.1
            
            confidences.append(min(col_confidence, 1.0))
        
        return sum(confidences) / len(confidences)
    
    def _detect_format(self, data: str) -> str:
        """Detect the format of the input data."""
        data_stripped = data.strip()
        
        if data_stripped.startswith(('{', '[')):
            return 'json'
        elif ',' in data and '\n' in data:
            return 'csv'
        elif ';' in data and '\n' in data:
            return 'csv'
        elif '\t' in data and '\n' in data:
            return 'tsv'
        else:
            return 'unknown'
    
    @staticmethod
    def _is_date(value: str) -> bool:
        """Check if a string value looks like a date."""
        if not isinstance(value, str):
            return False
        
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{4}/\d{2}/\d{2}$',
            r'^\d{2}-\d{2}-\d{4}$',
            r'^\d{2}/\d{2}/\d{4}$',
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)
    
    @staticmethod
    def _is_email(value: str) -> bool:
        """Check if a string value looks like an email."""
        if not isinstance(value, str):
            return False
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, value))
    
    @staticmethod
    def _is_url(value: str) -> bool:
        """Check if a string value looks like a URL."""
        if not isinstance(value, str):
            return False
        url_pattern = r'^https?://(?:[\w-]+\.)+[\w-]+(?:/[\w-./?%&=]*)?$'
        return bool(re.match(url_pattern, value))
    
    @staticmethod
    def _is_uuid(value: str) -> bool:
        """Check if a string value looks like a UUID."""
        if not isinstance(value, str):
            return False
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value.lower()))
