"""
Data Quality Analyzer - Main Module
AI-powered data quality assessment and cleaning recommendations
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import DataQualityReport, QualityIssue, CleaningRecommendation
from .issue_detector import IssueDetector
from .statistical_analyzer import StatisticalAnalyzer
from .recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

class DataQualityAnalyzer:
    """Main data quality analyzer that orchestrates the analysis process"""
    
    def __init__(self):
        self.issue_detector = IssueDetector()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.ai_enhanced = False  # Would integrate with AI service
    
    def analyze_dataframe(
        self, 
        df: pd.DataFrame, 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> DataQualityReport:
        """Analyze data quality of a pandas DataFrame"""
        logger.info(f"Analyzing data quality for DataFrame with {len(df)} rows and {len(df.columns)} columns")
        
        try:
            # Calculate comprehensive statistics
            statistics = self.statistical_analyzer.calculate_comprehensive_statistics(df)
            
            # Create column profiles
            column_profiles = self.statistical_analyzer.create_column_profiles(df)
            
            # Detect all types of issues
            issues = self._detect_all_issues(df, schema_hints)
            
            # Generate cleaning recommendations
            recommendations = self.recommendation_engine.generate_recommendations(
                df, issues, schema_hints
            )
            
            # Calculate overall quality score
            overall_score = self.statistical_analyzer.calculate_quality_score(issues, statistics)
            
            # Compile metadata
            metadata = self._compile_metadata(df, issues, column_profiles)
            
            return DataQualityReport(
                overall_score=overall_score,
                issues=issues,
                recommendations=recommendations,
                statistics=statistics,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error during data quality analysis: {str(e)}")
            raise
    
    def analyze_csv_file(
        self, 
        file_path: str, 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> DataQualityReport:
        """Analyze data quality of a CSV file"""
        try:
            # Try different encodings to read the file
            df = self._read_csv_with_encoding(file_path)
            
            if df is None:
                raise ValueError("Could not read CSV file with any supported encoding")
            
            logger.info(f"Successfully loaded CSV file: {file_path}")
            return self.analyze_dataframe(df, schema_hints)
            
        except Exception as e:
            logger.error(f"Error analyzing CSV file {file_path}: {str(e)}")
            raise
    
    def analyze_excel_file(
        self, 
        file_path: str, 
        sheet_name: Optional[str] = None,
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> DataQualityReport:
        """Analyze data quality of an Excel file"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Successfully loaded Excel file: {file_path}")
            return self.analyze_dataframe(df, schema_hints)
            
        except Exception as e:
            logger.error(f"Error analyzing Excel file {file_path}: {str(e)}")
            raise
    
    def analyze_json_file(
        self, 
        file_path: str, 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> DataQualityReport:
        """Analyze data quality of a JSON file"""
        try:
            df = pd.read_json(file_path)
            logger.info(f"Successfully loaded JSON file: {file_path}")
            return self.analyze_dataframe(df, schema_hints)
            
        except Exception as e:
            logger.error(f"Error analyzing JSON file {file_path}: {str(e)}")
            raise
    
    def _detect_all_issues(
        self, 
        df: pd.DataFrame, 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[QualityIssue]:
        """Detect all types of data quality issues"""
        
        all_issues = []
        
        try:
            # Missing value issues
            missing_issues = self.issue_detector.detect_missing_values(df)
            all_issues.extend(missing_issues)
            logger.debug(f"Detected {len(missing_issues)} missing value issues")
            
            # Duplicate issues
            duplicate_issues = self.issue_detector.detect_duplicates(df)
            all_issues.extend(duplicate_issues)
            logger.debug(f"Detected {len(duplicate_issues)} duplicate issues")
            
            # Data type issues
            type_issues = self.issue_detector.detect_data_type_issues(df, schema_hints)
            all_issues.extend(type_issues)
            logger.debug(f"Detected {len(type_issues)} data type issues")
            
            # Format issues
            format_issues = self.issue_detector.detect_format_issues(df)
            all_issues.extend(format_issues)
            logger.debug(f"Detected {len(format_issues)} format issues")
            
            # Outlier issues
            outlier_issues = self.issue_detector.detect_outliers(df)
            all_issues.extend(outlier_issues)
            logger.debug(f"Detected {len(outlier_issues)} outlier issues")
            
            # Consistency issues
            consistency_issues = self.issue_detector.detect_inconsistencies(df)
            all_issues.extend(consistency_issues)
            logger.debug(f"Detected {len(consistency_issues)} consistency issues")
            
            logger.info(f"Total issues detected: {len(all_issues)}")
            
        except Exception as e:
            logger.error(f"Error detecting issues: {str(e)}")
            raise
        
        return all_issues
    
    def _read_csv_with_encoding(self, file_path: str) -> Optional[pd.DataFrame]:
        """Try to read CSV with different encodings"""
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Successfully read CSV with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                logger.debug(f"Failed to read with {encoding} encoding")
                continue
            except Exception as e:
                logger.debug(f"Error reading with {encoding}: {str(e)}")
                continue
        
        return None
    
    def _compile_metadata(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue],
        column_profiles: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile comprehensive metadata about the analysis"""
        
        severity_counts = {}
        issue_type_counts = {}
        
        for issue in issues:
            # Count by severity
            if issue.severity in severity_counts:
                severity_counts[issue.severity] += 1
            else:
                severity_counts[issue.severity] = 1
            
            # Count by issue type
            issue_type = issue.issue_type.value if hasattr(issue.issue_type, 'value') else str(issue.issue_type)
            if issue_type in issue_type_counts:
                issue_type_counts[issue_type] += 1
            else:
                issue_type_counts[issue_type] = 1
        
        return {
            "analyzed_at": datetime.now().isoformat(),
            "dataset_info": {
                "row_count": len(df),
                "column_count": len(df.columns),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
                "column_names": list(df.columns)
            },
            "analysis_summary": {
                "total_issues": len(issues),
                "severity_distribution": severity_counts,
                "issue_type_distribution": issue_type_counts,
                "columns_with_issues": len(set(issue.column for issue in issues if issue.column != "*")),
                "clean_columns": len(df.columns) - len(set(issue.column for issue in issues if issue.column != "*"))
            },
            "column_profiles": {
                name: {
                    "dtype": profile.dtype,
                    "null_percentage": profile.null_percentage,
                    "unique_count": profile.unique_count,
                    "cardinality_ratio": profile.cardinality_ratio
                }
                for name, profile in column_profiles.items()
            },
            "recommendations_count": 0,  # Will be updated after recommendations are generated
            "analysis_version": "1.0.0"
        }
    
    def generate_quality_report_summary(self, report: DataQualityReport) -> Dict[str, Any]:
        """Generate a human-readable summary of the quality report"""
        
        # Categorize issues by severity
        critical_issues = [i for i in report.issues if i.severity == "critical"]
        high_issues = [i for i in report.issues if i.severity == "high"]
        medium_issues = [i for i in report.issues if i.severity == "medium"]
        low_issues = [i for i in report.issues if i.severity == "low"]
        
        # Calculate affected data percentage
        total_cells = report.metadata["dataset_info"]["row_count"] * report.metadata["dataset_info"]["column_count"]
        affected_cells = sum(issue.affected_rows for issue in report.issues)
        affected_percentage = (affected_cells / total_cells) * 100 if total_cells > 0 else 0
        
        # Quality grade
        score = report.overall_score
        if score >= 90:
            grade = "Excellent"
        elif score >= 80:
            grade = "Good"
        elif score >= 70:
            grade = "Fair"
        elif score >= 60:
            grade = "Poor"
        else:
            grade = "Critical"
        
        return {
            "overall_assessment": {
                "quality_score": report.overall_score,
                "quality_grade": grade,
                "affected_data_percentage": affected_percentage,
                "total_issues": len(report.issues)
            },
            "issue_breakdown": {
                "critical": len(critical_issues),
                "high": len(high_issues),
                "medium": len(medium_issues),
                "low": len(low_issues)
            },
            "top_issues": [
                {
                    "type": issue.issue_type.value if hasattr(issue.issue_type, 'value') else str(issue.issue_type),
                    "column": issue.column,
                    "severity": issue.severity,
                    "description": issue.description
                }
                for issue in sorted(report.issues, key=lambda x: {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.severity, 0), reverse=True)[:5]
            ],
            "recommended_actions": len(report.recommendations),
            "priority_recommendations": [
                {
                    "action": rec.action.value if hasattr(rec.action, 'value') else str(rec.action),
                    "column": rec.column,
                    "reasoning": rec.reasoning,
                    "confidence": rec.confidence_score
                }
                for rec in report.recommendations[:3]  # Top 3 recommendations
            ]
        }
    
    def validate_schema_compliance(
        self, 
        df: pd.DataFrame, 
        schema_definition: Dict[str, Any]
    ) -> List[QualityIssue]:
        """Validate DataFrame against a schema definition"""
        
        issues = []
        
        # Check column presence
        required_columns = schema_definition.get("required_columns", [])
        missing_columns = set(required_columns) - set(df.columns)
        
        for col in missing_columns:
            issue = QualityIssue(
                issue_type="missing_required_column",
                column=col,
                severity="critical",
                affected_rows=len(df),
                description=f"Required column '{col}' is missing from the dataset",
                sample_values=[],
                suggested_actions=[{
                    "action": "add_column",
                    "description": f"Add missing column '{col}'"
                }],
                confidence_score=1.0
            )
            issues.append(issue)
        
        # Check data types
        column_types = schema_definition.get("column_types", {})
        for col, expected_type in column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if actual_type != expected_type:
                    issue = QualityIssue(
                        issue_type="incorrect_data_type",
                        column=col,
                        severity="medium",
                        affected_rows=len(df),
                        description=f"Column '{col}' has type '{actual_type}' but expected '{expected_type}'",
                        sample_values=df[col].head(5).tolist(),
                        suggested_actions=[{
                            "action": "convert_type",
                            "from_type": actual_type,
                            "to_type": expected_type
                        }],
                        confidence_score=0.9
                    )
                    issues.append(issue)
        
        # Check constraints
        constraints = schema_definition.get("constraints", {})
        for col, constraint_list in constraints.items():
            if col in df.columns:
                for constraint in constraint_list:
                    constraint_issues = self._validate_constraint(df[col], constraint, col)
                    issues.extend(constraint_issues)
        
        return issues
    
    def _validate_constraint(self, series: pd.Series, constraint: Dict[str, Any], column: str) -> List[QualityIssue]:
        """Validate a single constraint against a series"""
        
        issues = []
        constraint_type = constraint.get("type")
        
        if constraint_type == "not_null":
            null_count = series.isnull().sum()
            if null_count > 0:
                issue = QualityIssue(
                    issue_type="constraint_violation",
                    column=column,
                    severity="high",
                    affected_rows=null_count,
                    description=f"Column '{column}' violates NOT NULL constraint",
                    sample_values=[],
                    suggested_actions=[{
                        "action": "handle_nulls",
                        "constraint": "not_null"
                    }],
                    confidence_score=1.0
                )
                issues.append(issue)
        
        elif constraint_type == "unique":
            duplicate_count = len(series) - series.nunique()
            if duplicate_count > 0:
                issue = QualityIssue(
                    issue_type="constraint_violation",
                    column=column,
                    severity="high",
                    affected_rows=duplicate_count,
                    description=f"Column '{column}' violates UNIQUE constraint",
                    sample_values=series[series.duplicated()].head(5).tolist(),
                    suggested_actions=[{
                        "action": "handle_duplicates",
                        "constraint": "unique"
                    }],
                    confidence_score=1.0
                )
                issues.append(issue)
        
        elif constraint_type == "range":
            min_val = constraint.get("min")
            max_val = constraint.get("max")
            
            violations = 0
            if min_val is not None:
                violations += (series < min_val).sum()
            if max_val is not None:
                violations += (series > max_val).sum()
            
            if violations > 0:
                issue = QualityIssue(
                    issue_type="constraint_violation",
                    column=column,
                    severity="medium",
                    affected_rows=violations,
                    description=f"Column '{column}' has {violations} values outside range [{min_val}, {max_val}]",
                    sample_values=[],
                    suggested_actions=[{
                        "action": "clip_values",
                        "constraint": "range",
                        "min": min_val,
                        "max": max_val
                    }],
                    confidence_score=0.9
                )
                issues.append(issue)
        
        return issues
