"""
Recommendation engine for data cleaning actions
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple

from .base import (
    DataCleaningAction, CleaningRecommendation, QualityIssue, 
    DataQualityIssue, SeverityLevel
)

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Generates cleaning recommendations based on detected issues"""
    
    def __init__(self):
        self.action_generators = {
            DataQualityIssue.MISSING_VALUES: self._recommend_missing_values,
            DataQualityIssue.DUPLICATE_ROWS: self._recommend_duplicates,
            DataQualityIssue.INCORRECT_DATA_TYPE: self._recommend_type_conversion,
            DataQualityIssue.INVALID_FORMAT: self._recommend_format_fixing,
            DataQualityIssue.OUTLIERS: self._recommend_outlier_handling,
            DataQualityIssue.INCONSISTENT_CASE: self._recommend_case_normalization,
            DataQualityIssue.INCONSISTENT_NAMING: self._recommend_name_standardization,
            DataQualityIssue.ENCODING_ISSUES: self._recommend_encoding_fixes
        }
    
    def generate_recommendations(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate comprehensive cleaning recommendations"""
        
        recommendations = []
        
        # Group issues by type and column for better analysis
        issue_groups = self._group_issues(issues)
        
        for issue_type, issue_list in issue_groups.items():
            if issue_type in self.action_generators:
                type_recommendations = self.action_generators[issue_type](
                    df, issue_list, schema_hints
                )
                recommendations.extend(type_recommendations)
        
        # Sort recommendations by priority and impact
        recommendations = self._prioritize_recommendations(recommendations)
        
        # Add cross-column recommendations
        cross_column_recs = self._generate_cross_column_recommendations(df, issues)
        recommendations.extend(cross_column_recs)
        
        return recommendations
    
    def _group_issues(self, issues: List[QualityIssue]) -> Dict[DataQualityIssue, List[QualityIssue]]:
        """Group issues by type"""
        groups = {}
        for issue in issues:
            if issue.issue_type not in groups:
                groups[issue.issue_type] = []
            groups[issue.issue_type].append(issue)
        return groups
    
    def _recommend_missing_values(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for missing value issues"""
        
        recommendations = []
        
        for issue in issues:
            column = issue.column
            null_percentage = (df[column].isnull().sum() / len(df)) * 100
            
            # Strategy depends on percentage of missing values and data type
            if null_percentage > 75:
                # Recommend dropping column
                rec = CleaningRecommendation(
                    action=DataCleaningAction.DROP_COLUMNS,
                    column=column,
                    parameters={"columns": [column]},
                    impact_assessment={
                        "data_loss": "high",
                        "information_loss": "high",
                        "rows_affected": 0,
                        "columns_removed": 1
                    },
                    confidence_score=0.9,
                    reasoning=f"Column '{column}' has {null_percentage:.1f}% missing values, making it unreliable"
                )
                recommendations.append(rec)
                
            elif null_percentage > 50:
                # Investigate before action
                rec = CleaningRecommendation(
                    action=DataCleaningAction.FILL_MISSING,
                    column=column,
                    parameters={
                        "method": "investigate",
                        "note": "High missing percentage requires investigation"
                    },
                    impact_assessment={
                        "data_loss": "medium",
                        "information_loss": "medium",
                        "rows_affected": issue.affected_rows
                    },
                    confidence_score=0.6,
                    reasoning=f"Column '{column}' has {null_percentage:.1f}% missing values - investigate cause"
                )
                recommendations.append(rec)
                
            else:
                # Recommend appropriate filling strategy
                fill_method = self._determine_fill_method(df[column], schema_hints, column)
                
                rec = CleaningRecommendation(
                    action=DataCleaningAction.FILL_MISSING,
                    column=column,
                    parameters=fill_method,
                    impact_assessment={
                        "data_loss": "low",
                        "information_loss": "low",
                        "rows_affected": issue.affected_rows,
                        "estimated_accuracy": fill_method.get("accuracy", 0.7)
                    },
                    confidence_score=fill_method.get("confidence", 0.7),
                    reasoning=f"Fill {issue.affected_rows} missing values using {fill_method['method']}"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _recommend_duplicates(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for duplicate issues"""
        
        recommendations = []
        
        for issue in issues:
            if issue.issue_type == DataQualityIssue.DUPLICATE_ROWS:
                duplicate_count = issue.affected_rows
                
                rec = CleaningRecommendation(
                    action=DataCleaningAction.DROP_ROWS,
                    column="*",
                    parameters={
                        "method": "drop_duplicates",
                        "keep": "first",
                        "subset": None  # Consider all columns
                    },
                    impact_assessment={
                        "data_loss": "medium",
                        "information_loss": "low",
                        "rows_affected": duplicate_count,
                        "unique_rows_preserved": len(df) - duplicate_count
                    },
                    confidence_score=0.95,
                    reasoning=f"Remove {duplicate_count} duplicate rows to improve data quality"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _recommend_type_conversion(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for data type issues"""
        
        recommendations = []
        
        for issue in issues:
            column = issue.column
            current_dtype = str(df[column].dtype)
            
            # Infer target type
            target_dtype = self._infer_target_dtype(df[column], schema_hints, column)
            
            if target_dtype:
                conversion_strategy = self._plan_type_conversion(df[column], target_dtype)
                
                rec = CleaningRecommendation(
                    action=DataCleaningAction.CONVERT_TYPE,
                    column=column,
                    parameters={
                        "from_type": current_dtype,
                        "to_type": target_dtype,
                        "strategy": conversion_strategy
                    },
                    impact_assessment={
                        "data_loss": conversion_strategy.get("data_loss", "low"),
                        "conversion_errors": conversion_strategy.get("error_count", 0),
                        "success_rate": conversion_strategy.get("success_rate", 0.9)
                    },
                    confidence_score=conversion_strategy.get("confidence", 0.8),
                    reasoning=f"Convert column '{column}' from {current_dtype} to {target_dtype}"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _recommend_format_fixing(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for format issues"""
        
        recommendations = []
        
        for issue in issues:
            column = issue.column
            
            # Determine format standardization approach
            format_strategy = self._analyze_format_patterns(df[column])
            
            rec = CleaningRecommendation(
                action=DataCleaningAction.STANDARDIZE_FORMAT,
                column=column,
                parameters=format_strategy,
                impact_assessment={
                    "data_loss": "minimal",
                    "standardization_impact": "high",
                    "affected_values": issue.affected_rows
                },
                confidence_score=format_strategy.get("confidence", 0.7),
                reasoning=f"Standardize format in column '{column}' using {format_strategy.get('method', 'pattern analysis')}"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _recommend_outlier_handling(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for outlier issues"""
        
        recommendations = []
        
        for issue in issues:
            column = issue.column
            outlier_count = issue.affected_rows
            total_count = len(df[column].dropna())
            outlier_percentage = (outlier_count / total_count) * 100
            
            if outlier_percentage > 20:
                # Too many outliers - investigate data
                action = "investigate"
                reasoning = f"Column '{column}' has {outlier_percentage:.1f}% outliers - investigate data source"
                confidence = 0.6
            elif outlier_percentage > 5:
                # Cap outliers instead of removing
                action = "cap"
                reasoning = f"Cap {outlier_count} outliers in column '{column}' to preserve data"
                confidence = 0.8
            else:
                # Remove outliers
                action = "remove"
                reasoning = f"Remove {outlier_count} outliers from column '{column}'"
                confidence = 0.9
            
            rec = CleaningRecommendation(
                action=DataCleaningAction.REMOVE_OUTLIERS,
                column=column,
                parameters={
                    "method": action,
                    "threshold": "iqr",
                    "multiplier": 1.5
                },
                impact_assessment={
                    "data_loss": "low" if action == "cap" else "medium",
                    "outliers_affected": outlier_count,
                    "percentage_affected": outlier_percentage
                },
                confidence_score=confidence,
                reasoning=reasoning
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _recommend_case_normalization(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for case inconsistency issues"""
        
        recommendations = []
        
        for issue in issues:
            column = issue.column
            
            # Determine best case format
            case_analysis = self._analyze_case_distribution(df[column])
            target_case = case_analysis["recommended_case"]
            
            rec = CleaningRecommendation(
                action=DataCleaningAction.NORMALIZE_TEXT,
                column=column,
                parameters={
                    "operation": "case_normalization",
                    "target_case": target_case
                },
                impact_assessment={
                    "data_loss": "none",
                    "standardization_benefit": "high",
                    "affected_values": issue.affected_rows
                },
                confidence_score=0.9,
                reasoning=f"Normalize case in column '{column}' to {target_case}"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _recommend_name_standardization(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for naming inconsistency issues"""
        
        recommendations = []
        
        for issue in issues:
            column = issue.column
            
            # Extract standardization groups from issue
            standardization_groups = []
            for action in issue.suggested_actions:
                if action.get("action") == "standardize_values":
                    standardization_groups = action.get("groups", [])
                    break
            
            rec = CleaningRecommendation(
                action=DataCleaningAction.NORMALIZE_TEXT,
                column=column,
                parameters={
                    "operation": "value_standardization",
                    "standardization_groups": standardization_groups
                },
                impact_assessment={
                    "data_loss": "none",
                    "standardization_benefit": "high",
                    "affected_values": issue.affected_rows
                },
                confidence_score=0.8,
                reasoning=f"Standardize similar values in column '{column}'"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _recommend_encoding_fixes(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue], 
        schema_hints: Optional[Dict[str, Any]] = None
    ) -> List[CleaningRecommendation]:
        """Generate recommendations for encoding issues"""
        
        recommendations = []
        
        for issue in issues:
            column = issue.column
            
            rec = CleaningRecommendation(
                action=DataCleaningAction.STANDARDIZE_FORMAT,
                column=column,
                parameters={
                    "operation": "encoding_fix",
                    "target_encoding": "utf-8"
                },
                impact_assessment={
                    "data_loss": "minimal",
                    "encoding_improvement": "high",
                    "affected_characters": issue.affected_rows
                },
                confidence_score=0.7,
                reasoning=f"Fix encoding issues in column '{column}'"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_cross_column_recommendations(
        self, 
        df: pd.DataFrame, 
        issues: List[QualityIssue]
    ) -> List[CleaningRecommendation]:
        """Generate recommendations that affect multiple columns"""
        
        recommendations = []
        
        # Check for columns that could be merged
        merge_candidates = self._identify_merge_candidates(df)
        
        for candidate in merge_candidates:
            rec = CleaningRecommendation(
                action=DataCleaningAction.MERGE_COLUMNS,
                column=f"{candidate['columns'][0]}+{candidate['columns'][1]}",
                parameters={
                    "source_columns": candidate["columns"],
                    "target_column": candidate["suggested_name"],
                    "merge_strategy": candidate["strategy"]
                },
                impact_assessment={
                    "columns_reduced": len(candidate["columns"]) - 1,
                    "information_preserved": candidate["preservation_score"]
                },
                confidence_score=candidate["confidence"],
                reasoning=candidate["reasoning"]
            )
            recommendations.append(rec)
        
        # Check for columns that should be split
        split_candidates = self._identify_split_candidates(df)
        
        for candidate in split_candidates:
            rec = CleaningRecommendation(
                action=DataCleaningAction.SPLIT_COLUMNS,
                column=candidate["column"],
                parameters={
                    "source_column": candidate["column"],
                    "target_columns": candidate["target_columns"],
                    "split_strategy": candidate["strategy"]
                },
                impact_assessment={
                    "columns_added": len(candidate["target_columns"]) - 1,
                    "data_granularity": "improved"
                },
                confidence_score=candidate["confidence"],
                reasoning=candidate["reasoning"]
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _prioritize_recommendations(self, recommendations: List[CleaningRecommendation]) -> List[CleaningRecommendation]:
        """Sort recommendations by priority and impact"""
        
        def priority_score(rec: CleaningRecommendation) -> float:
            base_score = rec.confidence_score
            
            # Boost score based on action type priority
            action_priorities = {
                DataCleaningAction.DROP_COLUMNS: 0.9,  # High impact, do first
                DataCleaningAction.DROP_ROWS: 0.8,
                DataCleaningAction.CONVERT_TYPE: 0.7,
                DataCleaningAction.FILL_MISSING: 0.6,
                DataCleaningAction.STANDARDIZE_FORMAT: 0.5,
                DataCleaningAction.NORMALIZE_TEXT: 0.4,
                DataCleaningAction.REMOVE_OUTLIERS: 0.3
            }
            
            priority_boost = action_priorities.get(rec.action, 0.5)
            
            return base_score * priority_boost
        
        return sorted(recommendations, key=priority_score, reverse=True)
