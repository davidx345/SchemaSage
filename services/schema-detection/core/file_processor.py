"""File processing module for schema detection."""
from typing import Dict, List, Any
import pandas as pd
import json
import json5
from fastapi import UploadFile
from ..models.schemas import FileType, DataProfile, SchemaValidationError

class FileProcessor:
    """Handles processing of different file types."""
    
    def __init__(self, max_sample_rows: int = 10000):
        self.max_sample_rows = max_sample_rows
        
    async def process_file(self, file: UploadFile) -> tuple[Dict[str, Any], DataProfile]:
        """Process uploaded file and return schema and profile."""
        file_type = self._detect_file_type(file.filename)
        content = await self._read_file_content(file, file_type)
        
        if file_type == FileType.CSV:
            df = pd.read_csv(content, nrows=self.max_sample_rows)
        elif file_type == FileType.JSON:
            data = json.loads(content) if not self._is_json5(content) else json5.loads(content)
            df = pd.json_normalize(data)
        elif file_type == FileType.EXCEL:
            df = pd.read_excel(content, nrows=self.max_sample_rows)
        else:
            raise SchemaValidationError(f"Unsupported file type: {file_type}")
            
        schema = self._infer_schema(df)
        profile = self._create_profile(df)
        
        return schema, profile
        
    def _detect_file_type(self, filename: str) -> FileType:
        """Detect file type from filename."""
        ext = filename.lower().split('.')[-1]
        return {
            'csv': FileType.CSV,
            'json': FileType.JSON,
            'xls': FileType.EXCEL,
            'xlsx': FileType.EXCEL
        }.get(ext, FileType.UNKNOWN)
        
    async def _read_file_content(self, file: UploadFile, file_type: FileType) -> bytes:
        """Read file content."""
        return await file.read()
        
    def _infer_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Infer schema from DataFrame."""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for column in df.columns:
            dtype = df[column].dtype
            schema["properties"][column] = self._map_dtype_to_json_schema(dtype)
            if df[column].notna().all():
                schema["required"].append(column)
                
        return schema
        
    def _create_profile(self, df: pd.DataFrame) -> DataProfile:
        """Create data profile from DataFrame."""
        profile = DataProfile(
            total_rows=len(df),
            columns={}
        )
        
        for column in df.columns:
            profile.columns[column] = {
                "unique_count": df[column].nunique(),
                "missing_count": df[column].isna().sum(),
                "sample_values": df[column].dropna().head(5).tolist(),
                "type_consistency": self._check_type_consistency(df[column])
            }
            
        return profile
        
    def _map_dtype_to_json_schema(self, dtype) -> Dict[str, Any]:
        """Map pandas dtype to JSON Schema type."""
        type_map = {
            'int64': {"type": "integer"},
            'float64': {"type": "number"},
            'bool': {"type": "boolean"},
            'datetime64[ns]': {"type": "string", "format": "date-time"},
            'object': {"type": "string"}
        }
        return type_map.get(str(dtype), {"type": "string"})
        
    def _check_type_consistency(self, series: pd.Series) -> float:
        """Check type consistency in a series."""
        try:
            dominant_type = series.dtype
            consistent_count = series.apply(lambda x: isinstance(x, type(dominant_type))).sum()
            return consistent_count / len(series)
        except:
            return 1.0
            
    def _is_json5(self, content: bytes) -> bool:
        """Check if content might be JSON5."""
        try:
            json.loads(content)
            return False
        except:
            try:
                json5.loads(content)
                return True
            except:
                return False
