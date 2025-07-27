"""
File processing module for data cleaning service
"""
import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from io import StringIO, BytesIO
import time

from .base import DataFormatType, FileProcessingResult, CleaningResult, validate_dataframe

logger = logging.getLogger(__name__)

class FileProcessor:
    """Handles file loading and initial processing"""
    
    def __init__(self):
        self.supported_formats = {
            DataFormatType.CSV: self._process_csv,
            DataFormatType.EXCEL: self._process_excel,
            DataFormatType.JSON: self._process_json,
            DataFormatType.TSV: self._process_tsv,
            DataFormatType.PARQUET: self._process_parquet
        }
        
        self.encoding_options = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    def load_file(
        self, 
        file_content: bytes, 
        file_type: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Load file content into a DataFrame"""
        
        start_time = time.time()
        warnings = []
        
        try:
            # Normalize file type
            format_type = self._normalize_file_type(file_type)
            
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_type}")
            
            # Process file
            df, process_warnings = self.supported_formats[format_type](file_content, options or {})
            warnings.extend(process_warnings)
            
            # Validate result
            validation_issues = validate_dataframe(df)
            if validation_issues:
                warnings.extend([f"Validation issue: {issue}" for issue in validation_issues])
            
            processing_time = time.time() - start_time
            logger.info(f"Loaded {file_type} file: {df.shape} in {processing_time:.2f}s")
            
            return df, warnings
            
        except Exception as e:
            logger.error(f"Error loading {file_type} file: {str(e)}")
            raise
    
    def _normalize_file_type(self, file_type: str) -> DataFormatType:
        """Normalize file type string to DataFormatType enum"""
        
        type_mapping = {
            'csv': DataFormatType.CSV,
            'xlsx': DataFormatType.EXCEL,
            'xls': DataFormatType.EXCEL,
            'json': DataFormatType.JSON,
            'tsv': DataFormatType.TSV,
            'tab': DataFormatType.TSV,
            'parquet': DataFormatType.PARQUET
        }
        
        normalized = file_type.lower().strip('.')
        
        if normalized in type_mapping:
            return type_mapping[normalized]
        else:
            raise ValueError(f"Unknown file type: {file_type}")
    
    def _process_csv(self, file_content: bytes, options: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Process CSV file content"""
        
        warnings = []
        content_str = None
        used_encoding = None
        
        # Try different encodings
        for encoding in self.encoding_options:
            try:
                content_str = file_content.decode(encoding)
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if content_str is None:
            raise ValueError("Could not decode file with any supported encoding")
        
        if used_encoding != 'utf-8':
            warnings.append(f"File decoded using {used_encoding} encoding instead of utf-8")
        
        # Parse CSV options
        csv_options = {
            'sep': options.get('separator', ','),
            'header': options.get('header', 0),
            'skiprows': options.get('skip_rows', 0),
            'nrows': options.get('max_rows'),
            'encoding': used_encoding
        }
        
        # Remove None values
        csv_options = {k: v for k, v in csv_options.items() if v is not None}
        
        try:
            df = pd.read_csv(StringIO(content_str), **csv_options)
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty or contains no data")
        except pd.errors.ParserError as e:
            raise ValueError(f"CSV parsing error: {str(e)}")
        
        return df, warnings
    
    def _process_excel(self, file_content: bytes, options: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Process Excel file content"""
        
        warnings = []
        
        excel_options = {
            'sheet_name': options.get('sheet_name', 0),
            'header': options.get('header', 0),
            'skiprows': options.get('skip_rows', 0),
            'nrows': options.get('max_rows')
        }
        
        # Remove None values
        excel_options = {k: v for k, v in excel_options.items() if v is not None}
        
        try:
            df = pd.read_excel(BytesIO(file_content), **excel_options)
        except Exception as e:
            raise ValueError(f"Excel processing error: {str(e)}")
        
        return df, warnings
    
    def _process_json(self, file_content: bytes, options: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Process JSON file content"""
        
        warnings = []
        
        try:
            content_str = file_content.decode('utf-8')
            data = json.loads(content_str)
            
            # Handle different JSON structures
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Check if it's a single record or contains data array
                if 'data' in data and isinstance(data['data'], list):
                    df = pd.DataFrame(data['data'])
                    warnings.append("Extracted data from 'data' key in JSON")
                else:
                    # Treat as single record
                    df = pd.DataFrame([data])
                    warnings.append("Converted single JSON object to DataFrame")
            else:
                raise ValueError("JSON must contain an object or array of objects")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"JSON processing error: {str(e)}")
        
        return df, warnings
    
    def _process_tsv(self, file_content: bytes, options: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Process TSV (Tab-Separated Values) file content"""
        
        # TSV is just CSV with tab separator
        options['separator'] = '\t'
        return self._process_csv(file_content, options)
    
    def _process_parquet(self, file_content: bytes, options: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
        """Process Parquet file content"""
        
        warnings = []
        
        try:
            df = pd.read_parquet(BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Parquet processing error: {str(e)}")
        
        return df, warnings
    
    def export_dataframe(
        self, 
        df: pd.DataFrame, 
        format_type: DataFormatType,
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export DataFrame to specified format"""
        
        options = options or {}
        
        if format_type == DataFormatType.CSV:
            return self._export_csv(df, options)
        elif format_type == DataFormatType.EXCEL:
            return self._export_excel(df, options)
        elif format_type == DataFormatType.JSON:
            return self._export_json(df, options)
        elif format_type == DataFormatType.TSV:
            return self._export_tsv(df, options)
        elif format_type == DataFormatType.PARQUET:
            return self._export_parquet(df, options)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_csv(self, df: pd.DataFrame, options: Dict[str, Any]) -> bytes:
        """Export DataFrame as CSV"""
        
        csv_options = {
            'sep': options.get('separator', ','),
            'index': options.get('include_index', False),
            'encoding': options.get('encoding', 'utf-8')
        }
        
        csv_string = df.to_csv(**csv_options)
        return csv_string.encode(csv_options['encoding'])
    
    def _export_excel(self, df: pd.DataFrame, options: Dict[str, Any]) -> bytes:
        """Export DataFrame as Excel"""
        
        buffer = BytesIO()
        
        excel_options = {
            'index': options.get('include_index', False),
            'sheet_name': options.get('sheet_name', 'Sheet1')
        }
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, **excel_options)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _export_json(self, df: pd.DataFrame, options: Dict[str, Any]) -> bytes:
        """Export DataFrame as JSON"""
        
        json_options = {
            'orient': options.get('orient', 'records'),
            'date_format': options.get('date_format', 'iso'),
            'indent': options.get('indent', 2)
        }
        
        json_string = df.to_json(**json_options)
        return json_string.encode('utf-8')
    
    def _export_tsv(self, df: pd.DataFrame, options: Dict[str, Any]) -> bytes:
        """Export DataFrame as TSV"""
        
        options['separator'] = '\t'
        return self._export_csv(df, options)
    
    def _export_parquet(self, df: pd.DataFrame, options: Dict[str, Any]) -> bytes:
        """Export DataFrame as Parquet"""
        
        buffer = BytesIO()
        df.to_parquet(buffer, index=options.get('include_index', False))
        buffer.seek(0)
        return buffer.getvalue()
    
    def detect_file_format(self, file_content: bytes, filename: Optional[str] = None) -> DataFormatType:
        """Attempt to detect file format from content and filename"""
        
        # First try filename extension
        if filename:
            extension = filename.split('.')[-1].lower()
            if extension in ['csv']:
                return DataFormatType.CSV
            elif extension in ['xlsx', 'xls']:
                return DataFormatType.EXCEL
            elif extension in ['json']:
                return DataFormatType.JSON
            elif extension in ['tsv', 'tab']:
                return DataFormatType.TSV
            elif extension in ['parquet']:
                return DataFormatType.PARQUET
        
        # Try to detect from content
        try:
            # Check if it's JSON
            content_str = file_content[:1000].decode('utf-8')
            json.loads(content_str)
            return DataFormatType.JSON
        except:
            pass
        
        try:
            # Check if it looks like CSV
            content_str = file_content[:1000].decode('utf-8')
            lines = content_str.split('\n')
            if len(lines) > 1:
                first_line = lines[0]
                if ',' in first_line and len(first_line.split(',')) > 1:
                    return DataFormatType.CSV
                elif '\t' in first_line and len(first_line.split('\t')) > 1:
                    return DataFormatType.TSV
        except:
            pass
        
        # Check if it's Excel (binary format detection is complex, so we fallback)
        if file_content.startswith(b'PK'):  # Excel files are ZIP-based
            return DataFormatType.EXCEL
        
        # Default fallback
        return DataFormatType.CSV
    
    def get_file_preview(
        self, 
        df: pd.DataFrame, 
        num_rows: int = 10
    ) -> Dict[str, Any]:
        """Generate a preview of the loaded data"""
        
        preview_data = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "head": df.head(num_rows).to_dict('records'),
            "null_counts": df.isnull().sum().to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "summary_stats": {}
        }
        
        # Add summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            preview_data["summary_stats"] = df[numeric_cols].describe().to_dict()
        
        return preview_data
