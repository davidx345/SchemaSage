"""
Issue detection module for data quality analysis
"""
import pandas as pd
import numpy as np
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter

from .base import (
    DataQualityIssue, QualityIssue, SeverityLevel, 
    ColumnProfile, ValidationRule, ValidatorType
)

logger = logging.getLogger(__name__)

class IssueDetector:
    """Detects various data quality issues in datasets"""
    
    def __init__(self):
        self.pattern_validators = self._init_pattern_validators()
        self.format_detectors = self._init_format_detectors()
    
    def _init_pattern_validators(self) -> Dict[str, Dict[str, str]]:
        """Initialize pattern validators"""
        return {
            "email": {
                "pattern": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                "description": "Valid email format"
            },
            "phone": {
                "pattern": r'^[\+]?[1-9][\d]{0,15}$',
                "description": "Valid phone number format"
            },
            "url": {
                "pattern": r'^https?://[^\s/$.?#].[^\s]*$',
                "description": "Valid URL format"
            },
            "credit_card": {
                "pattern": r'^[0-9]{13,19}$',
                "description": "Valid credit card number format"
            },
            "ssn": {
                "pattern": r'^\d{3}-\d{2}-\d{4}$',
                "description": "Valid SSN format (XXX-XX-XXXX)"
            },
            "zip_code": {
                "pattern": r'^\d{5}(-\d{4})?$',
                "description": "Valid US ZIP code format"
            }
        }
    
    def _init_format_detectors(self) -> Dict[str, callable]:
        """Initialize format detection functions"""
        return {
            "date": self._detect_date_format,
            "numeric": self._detect_numeric_format,
            "categorical": self._detect_categorical_format,
            "text": self._detect_text_format
        }
    
    def detect_missing_values(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect missing values in the dataset"""
        issues = []
        
        for column in df.columns:
            null_count = df[column].isnull().sum()
            null_percentage = (null_count / len(df)) * 100
            
            if null_count > 0:
                # Determine severity based on percentage of missing values
                if null_percentage >= 50:
                    severity = SeverityLevel.CRITICAL.value
                elif null_percentage >= 25:
                    severity = SeverityLevel.HIGH.value
                elif null_percentage >= 10:
                    severity = SeverityLevel.MEDIUM.value
                else:
                    severity = SeverityLevel.LOW.value
                
                # Analyze missing value patterns
                missing_patterns = self._analyze_missing_patterns(df, column)
                
                issue = QualityIssue(
                    issue_type=DataQualityIssue.MISSING_VALUES,
                    column=column,
                    severity=severity,
                    affected_rows=null_count,
                    description=f"Column '{column}' has {null_count} missing values ({null_percentage:.2f}%)",
                    sample_values=self._get_sample_non_null_values(df[column]),
                    suggested_actions=self._suggest_missing_value_actions(df, column, missing_patterns),
                    confidence_score=0.95
                )
                issues.append(issue)
        
        return issues
    
    def detect_duplicates(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect duplicate rows in the dataset"""
        issues = []
        
        # Check for exact duplicates
        duplicate_mask = df.duplicated()
        duplicate_count = duplicate_mask.sum()
        
        if duplicate_count > 0:
            duplicate_percentage = (duplicate_count / len(df)) * 100
            
            severity = SeverityLevel.HIGH.value if duplicate_percentage > 5 else SeverityLevel.MEDIUM.value
            
            # Get sample duplicate rows
            sample_duplicates = df[duplicate_mask].head(5).to_dict('records')
            
            issue = QualityIssue(
                issue_type=DataQualityIssue.DUPLICATE_ROWS,
                column="*",  # Affects all columns
                severity=severity,
                affected_rows=duplicate_count,
                description=f"Found {duplicate_count} duplicate rows ({duplicate_percentage:.2f}%)",
                sample_values=sample_duplicates,
                suggested_actions=[{
                    "action": "drop_duplicates",
                    "description": "Remove duplicate rows",
                    "parameters": {"keep": "first"}
                }],
                confidence_score=0.98
            )
            issues.append(issue)
        
        # Check for potential duplicates (similar but not exact)
        potential_duplicates = self._detect_potential_duplicates(df)
        if potential_duplicates:
            issues.extend(potential_duplicates)
        
        return issues
    
    def detect_data_type_issues(self, df: pd.DataFrame, schema_hints: Optional[Dict[str, Any]] = None) -> List[QualityIssue]:
        """Detect data type inconsistencies"""
        issues = []
        
        for column in df.columns:
            current_dtype = str(df[column].dtype)
            
            # Infer expected data type
            expected_dtype = self._infer_expected_dtype(df[column], schema_hints, column)
            
            if expected_dtype and expected_dtype != current_dtype:
                # Check conversion feasibility
                conversion_issues = self._check_type_conversion(df[column], expected_dtype)
                
                if conversion_issues:
                    issue = QualityIssue(
                        issue_type=DataQualityIssue.INCORRECT_DATA_TYPE,
                        column=column,
                        severity=SeverityLevel.MEDIUM.value,
                        affected_rows=len(conversion_issues),
                        description=f"Column '{column}' has type '{current_dtype}' but should be '{expected_dtype}'",
                        sample_values=conversion_issues[:10],
                        suggested_actions=self._suggest_type_conversion_actions(column, current_dtype, expected_dtype),
                        confidence_score=0.85
                    )
                    issues.append(issue)
        
        return issues
    
    def detect_format_issues(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect format inconsistencies"""
        issues = []
        
        for column in df.columns:
            if df[column].dtype == 'object':
                format_issues = self._analyze_format_consistency(df[column])
                
                if format_issues:
                    issue = QualityIssue(
                        issue_type=DataQualityIssue.INVALID_FORMAT,
                        column=column,
                        severity=format_issues['severity'],
                        affected_rows=format_issues['affected_count'],
                        description=format_issues['description'],
                        sample_values=format_issues['samples'],
                        suggested_actions=format_issues['suggestions'],
                        confidence_score=format_issues['confidence']
                    )
                    issues.append(issue)
        
        return issues
    
    def detect_outliers(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect statistical outliers"""
        issues = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            outliers = self._detect_statistical_outliers(df[column])
            
            if outliers['count'] > 0:
                severity = self._determine_outlier_severity(
                    outliers['count'], len(df), outliers['extreme_count']
                )
                
                issue = QualityIssue(
                    issue_type=DataQualityIssue.OUTLIERS,
                    column=column,
                    severity=severity,
                    affected_rows=outliers['count'],
                    description=f"Column '{column}' contains {outliers['count']} outliers",
                    sample_values=outliers['sample_values'],
                    suggested_actions=self._suggest_outlier_actions(outliers),
                    confidence_score=outliers['confidence']
                )
                issues.append(issue)
        
        return issues
    
    def detect_inconsistencies(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect various inconsistencies in the data"""
        issues = []
        
        # Case inconsistencies
        issues.extend(self._detect_case_inconsistencies(df))
        
        # Naming inconsistencies
        issues.extend(self._detect_naming_inconsistencies(df))
        
        # Encoding issues
        issues.extend(self._detect_encoding_issues(df))
        
        return issues
    
    def _analyze_missing_patterns(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Analyze patterns in missing values"""
        missing_mask = df[column].isnull()
        
        # Check if missing values correlate with other columns
        correlations = {}
        for other_col in df.columns:
            if other_col != column and df[other_col].dtype in ['object', 'bool']:
                correlation = self._calculate_missing_correlation(missing_mask, df[other_col])
                if correlation > 0.3:  # Significant correlation
                    correlations[other_col] = correlation
        
        # Check for patterns in row positions
        missing_positions = df.index[missing_mask].tolist()
        pattern_type = self._detect_missing_position_pattern(missing_positions)
        
        return {
            "correlations": correlations,
            "position_pattern": pattern_type,
            "consecutive_missing": self._find_consecutive_missing(missing_positions)
        }
    
    def _suggest_missing_value_actions(self, df: pd.DataFrame, column: str, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest actions for handling missing values"""
        actions = []
        
        null_percentage = (df[column].isnull().sum() / len(df)) * 100
        
        if null_percentage > 80:
            actions.append({
                "action": "drop_column",
                "description": f"Drop column '{column}' due to high missing percentage",
                "priority": "high"
            })
        elif null_percentage > 50:
            actions.append({
                "action": "investigate",
                "description": f"Investigate why column '{column}' has high missing percentage",
                "priority": "high"
            })
        
        # Data type specific suggestions
        if df[column].dtype in ['int64', 'float64']:
            actions.extend([
                {
                    "action": "fill_mean",
                    "description": "Fill with mean value",
                    "priority": "medium"
                },
                {
                    "action": "fill_median",
                    "description": "Fill with median value",
                    "priority": "medium"
                },
                {
                    "action": "interpolate",
                    "description": "Use interpolation for time series data",
                    "priority": "low"
                }
            ])
        elif df[column].dtype == 'object':
            actions.extend([
                {
                    "action": "fill_mode",
                    "description": "Fill with most frequent value",
                    "priority": "medium"
                },
                {
                    "action": "fill_unknown",
                    "description": "Fill with 'Unknown' or similar placeholder",
                    "priority": "low"
                }
            ])
        
        return actions
    
    def _get_sample_non_null_values(self, series: pd.Series, count: int = 5) -> List[Any]:
        """Get sample non-null values from a series"""
        non_null_values = series.dropna()
        if len(non_null_values) == 0:
            return []
        
        sample_size = min(count, len(non_null_values))
        return non_null_values.sample(sample_size).tolist()
    
    def _detect_potential_duplicates(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect potential duplicates using fuzzy matching"""
        issues = []
        
        # For string columns, check for similar values
        string_columns = df.select_dtypes(include=['object']).columns
        
        for column in string_columns:
            if df[column].dtype == 'object':
                similar_groups = self._find_similar_strings(df[column])
                
                if similar_groups:
                    issue = QualityIssue(
                        issue_type=DataQualityIssue.INCONSISTENT_NAMING,
                        column=column,
                        severity=SeverityLevel.MEDIUM.value,
                        affected_rows=sum(len(group) for group in similar_groups),
                        description=f"Column '{column}' contains {len(similar_groups)} groups of similar values",
                        sample_values=[list(group) for group in similar_groups[:3]],
                        suggested_actions=[{
                            "action": "standardize_values",
                            "description": "Standardize similar values to a canonical form",
                            "groups": similar_groups
                        }],
                        confidence_score=0.75
                    )
                    issues.append(issue)
        
        return issues
    
    def _detect_case_inconsistencies(self, df: pd.DataFrame) -> List[QualityIssue]:
        """Detect inconsistent case usage in string columns"""
        issues = []
        
        string_columns = df.select_dtypes(include=['object']).columns
        
        for column in string_columns:
            case_issues = self._analyze_case_consistency(df[column])
            
            if case_issues['inconsistent_count'] > 0:
                issue = QualityIssue(
                    issue_type=DataQualityIssue.INCONSISTENT_CASE,
                    column=column,
                    severity=SeverityLevel.LOW.value,
                    affected_rows=case_issues['inconsistent_count'],
                    description=f"Column '{column}' has inconsistent case usage",
                    sample_values=case_issues['examples'],
                    suggested_actions=[{
                        "action": "normalize_case",
                        "description": f"Convert to {case_issues['suggested_case']} case",
                        "target_case": case_issues['suggested_case']
                    }],
                    confidence_score=0.80
                )
                issues.append(issue)
        
        return issues
