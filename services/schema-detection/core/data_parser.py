"""
Data Parsing and Format Detection Module

Handles parsing of various data formats including JSON, CSV, XML, etc.
"""
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np
import json
import csv
import re
from io import StringIO
import logging

try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False

logger = logging.getLogger(__name__)


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
                return value
        return str(value)
    except Exception:
        return value


class DataParser:
    """Handles parsing of various data formats"""
    
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'xml', 'yaml', 'tsv']
    
    def parse_data(self, data: str, file_format: str = None) -> List[Dict[str, Any]]:
        """Parse raw data into structured format."""
        if not data or not isinstance(data, str):
            return []
        
        data = data.strip()
        if not data:
            return []
        
        try:
            if file_format:
                file_format = file_format.lower()
                if file_format == 'json':
                    return self._parse_json(data)
                elif file_format in ['csv', 'tsv']:
                    delimiter = '\t' if file_format == 'tsv' else ','
                    return self._parse_csv(data, delimiter)
                elif file_format == 'xml':
                    return self._parse_xml(data)
                elif file_format == 'yaml':
                    return self._parse_yaml(data)
            
            # Auto-detect format if not specified
            return self._auto_detect_and_parse(data)
        
        except Exception as e:
            logger.error(f"Error parsing data: {e}")
            raise ValueError(f"Failed to parse data: {str(e)}")
    
    def _auto_detect_and_parse(self, data: str) -> List[Dict[str, Any]]:
        """Auto-detect format and parse data."""
        data = data.strip()
        
        # Try JSON first (most structured)
        if data.startswith(('{', '[')):
            try:
                return self._parse_json(data)
            except Exception:
                pass
        
        # Try CSV if it has comma-separated values
        if ',' in data and not data.startswith('<'):
            try:
                return self._parse_csv(data)
            except Exception:
                pass
        
        # Try TSV if it has tab-separated values
        if '\t' in data:
            try:
                return self._parse_csv(data, delimiter='\t')
            except Exception:
                pass
        
        # Try XML if it looks like XML
        if data.startswith('<') and data.endswith('>'):
            try:
                return self._parse_xml(data)
            except Exception:
                pass
        
        # Try YAML
        try:
            return self._parse_yaml(data)
        except Exception:
            pass
        
        # Fallback: treat as single text field
        return [{"text": data}]
    
    def _parse_json(self, data: str) -> List[Dict[str, Any]]:
        """Parse JSON data."""
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            if HAS_JSON5:
                try:
                    parsed = json5.loads(data)
                except Exception:
                    raise ValueError("Invalid JSON format")
            else:
                raise ValueError("Invalid JSON format")
        
        if isinstance(parsed, dict):
            return [parsed]
        elif isinstance(parsed, list):
            result = []
            for item in parsed:
                if isinstance(item, dict):
                    result.append(item)
                else:
                    result.append({"value": item})
            return result
        else:
            return [{"value": parsed}]
    
    def _parse_csv(self, data: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Parse CSV data."""
        try:
            # Handle different line endings
            data = data.replace('\r\n', '\n').replace('\r', '\n')
            reader = csv.DictReader(StringIO(data), delimiter=delimiter)
            result = []
            for row in reader:
                # Convert values to appropriate types
                converted_row = {}
                for key, value in row.items():
                    if key is not None:  # Skip None keys from malformed CSV
                        converted_row[key.strip()] = safe_convert_value(value)
                if converted_row:  # Only add non-empty rows
                    result.append(converted_row)
            return result
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
    
    def _parse_xml(self, data: str) -> List[Dict[str, Any]]:
        """Parse XML data."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            def xml_to_dict(element):
                result = {}
                
                # Add attributes
                if element.attrib:
                    for key, value in element.attrib.items():
                        result[f"@{key}"] = safe_convert_value(value)
                
                # Add text content
                if element.text and element.text.strip():
                    if len(element) == 0:  # No children, just text
                        return safe_convert_value(element.text.strip())
                    else:
                        result["#text"] = safe_convert_value(element.text.strip())
                
                # Add children
                for child in element:
                    child_data = xml_to_dict(child)
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data
                
                return result if result else None
            
            parsed = xml_to_dict(root)
            if isinstance(parsed, dict):
                return [parsed]
            elif isinstance(parsed, list):
                return parsed
            else:
                return [{"root": parsed}]
        
        except Exception as e:
            raise ValueError(f"Failed to parse XML: {str(e)}")
    
    def _parse_yaml(self, data: str) -> List[Dict[str, Any]]:
        """Parse YAML data."""
        try:
            import yaml
            parsed = yaml.safe_load(data)
            
            if isinstance(parsed, dict):
                return [parsed]
            elif isinstance(parsed, list):
                result = []
                for item in parsed:
                    if isinstance(item, dict):
                        result.append(item)
                    else:
                        result.append({"value": item})
                return result
            else:
                return [{"value": parsed}]
        
        except Exception as e:
            raise ValueError(f"Failed to parse YAML: {str(e)}")
    
    def detect_format(self, data: str) -> str:
        """Detect the format of the given data."""
        data = data.strip()
        
        if data.startswith(('{', '[')):
            return 'json'
        elif data.startswith('<') and data.endswith('>'):
            return 'xml'
        elif ',' in data and not data.startswith('<'):
            return 'csv'
        elif '\t' in data:
            return 'tsv'
        else:
            # Try to detect YAML patterns
            if ':' in data and not data.startswith('{'):
                return 'yaml'
            return 'text'
    
    def normalize_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize parsed data to ensure consistent structure."""
        if not data:
            return []
        
        # Get all unique keys across all records
        all_keys = set()
        for record in data:
            if isinstance(record, dict):
                all_keys.update(record.keys())
        
        # Normalize each record to have all keys
        normalized = []
        for record in data:
            if isinstance(record, dict):
                normalized_record = {}
                for key in all_keys:
                    normalized_record[key] = record.get(key, None)
                normalized.append(normalized_record)
            else:
                # Convert non-dict items to dict
                normalized.append({"value": record})
        
        return normalized
    
    def sample_data(self, data: List[Dict[str, Any]], max_rows: int = 1000) -> List[Dict[str, Any]]:
        """Sample data to limit processing for large datasets."""
        if len(data) <= max_rows:
            return data
        
        # Take first and last portions, plus some random samples from middle
        first_portion = data[:max_rows // 3]
        last_portion = data[-(max_rows // 3):]
        
        # Random sample from middle
        middle_start = max_rows // 3
        middle_end = len(data) - max_rows // 3
        if middle_end > middle_start:
            middle_indices = np.random.choice(
                range(middle_start, middle_end), 
                size=min(max_rows // 3, middle_end - middle_start),
                replace=False
            )
            middle_portion = [data[i] for i in sorted(middle_indices)]
        else:
            middle_portion = []
        
        return first_portion + middle_portion + last_portion
