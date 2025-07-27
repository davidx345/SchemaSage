"""
Statistical analyzer for data quality assessment
"""
import pandas as pd
import numpy as np
import statistics
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
import re
from scipy import stats
import logging

from .base import ColumnProfile, ValidationRule

logger = logging.getLogger(__name__)

class StatisticalAnalyzer:
    """Performs statistical analysis for data quality assessment"""
    
    def __init__(self):
        self.outlier_methods = {
            'iqr': self._detect_outliers_iqr,
            'zscore': self._detect_outliers_zscore,
            'isolation_forest': self._detect_outliers_isolation_forest
        }
    
    def calculate_comprehensive_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive statistics for the dataset"""
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "null_percentages": (df.isnull().sum() / len(df) * 100).to_dict(),
            "unique_counts": df.nunique().to_dict(),
            "cardinality_ratios": (df.nunique() / len(df)).to_dict()
        }
        
        # Numeric statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats["numeric_stats"] = df[numeric_cols].describe().to_dict()
            stats["correlation_matrix"] = df[numeric_cols].corr().to_dict()
        
        # String statistics
        string_cols = df.select_dtypes(include=['object']).columns
        if len(string_cols) > 0:
            stats["string_stats"] = {}
            for col in string_cols:
                stats["string_stats"][col] = self._calculate_string_stats(df[col])
        
        # Data type distribution
        stats["dtype_distribution"] = df.dtypes.value_counts().to_dict()
        
        return stats
    
    def create_column_profiles(self, df: pd.DataFrame) -> Dict[str, ColumnProfile]:
        """Create detailed profiles for each column"""
        profiles = {}
        
        for column in df.columns:
            series = df[column]
            
            profile = ColumnProfile(
                name=column,
                dtype=str(series.dtype),
                null_count=series.isnull().sum(),
                null_percentage=(series.isnull().sum() / len(series)) * 100,
                unique_count=series.nunique(),
                cardinality_ratio=series.nunique() / len(series)
            )
            
            # Add type-specific statistics
            if pd.api.types.is_numeric_dtype(series):
                profile = self._add_numeric_profile(profile, series)
            elif pd.api.types.is_string_dtype(series) or series.dtype == 'object':
                profile = self._add_string_profile(profile, series)
            elif pd.api.types.is_datetime64_any_dtype(series):
                profile = self._add_datetime_profile(profile, series)
            elif pd.api.types.is_bool_dtype(series):
                profile = self._add_boolean_profile(profile, series)
            
            profiles[column] = profile
        
        return profiles
    
    def _add_numeric_profile(self, profile: ColumnProfile, series: pd.Series) -> ColumnProfile:
        """Add numeric-specific statistics to column profile"""
        non_null_series = series.dropna()
        
        if len(non_null_series) > 0:
            profile.min_value = float(non_null_series.min())
            profile.max_value = float(non_null_series.max())
            profile.mean_value = float(non_null_series.mean())
            profile.median_value = float(non_null_series.median())
            profile.std_deviation = float(non_null_series.std())
            
            # Quartiles
            profile.quartiles = {
                "q1": float(non_null_series.quantile(0.25)),
                "q2": float(non_null_series.quantile(0.50)),
                "q3": float(non_null_series.quantile(0.75)),
                "iqr": float(non_null_series.quantile(0.75) - non_null_series.quantile(0.25))
            }
            
            # Outlier detection
            outliers = self._detect_outliers_iqr(non_null_series)
            profile.pattern_analysis = {
                "outliers_count": len(outliers),
                "outliers_percentage": (len(outliers) / len(non_null_series)) * 100,
                "skewness": float(stats.skew(non_null_series)),
                "kurtosis": float(stats.kurtosis(non_null_series))
            }
        
        return profile
    
    def _add_string_profile(self, profile: ColumnProfile, series: pd.Series) -> ColumnProfile:
        """Add string-specific statistics to column profile"""
        non_null_series = series.dropna()
        
        if len(non_null_series) > 0:
            # Value counts (top 10)
            value_counts = non_null_series.value_counts().head(10)
            profile.value_counts = value_counts.to_dict()
            profile.mode_value = value_counts.index[0] if len(value_counts) > 0 else None
            
            # String length statistics
            lengths = non_null_series.astype(str).str.len()
            profile.min_value = int(lengths.min())
            profile.max_value = int(lengths.max())
            profile.mean_value = float(lengths.mean())
            profile.median_value = float(lengths.median())
            
            # Pattern analysis
            profile.pattern_analysis = self._analyze_string_patterns(non_null_series)
        
        return profile
    
    def _add_datetime_profile(self, profile: ColumnProfile, series: pd.Series) -> ColumnProfile:
        """Add datetime-specific statistics to column profile"""
        non_null_series = series.dropna()
        
        if len(non_null_series) > 0:
            profile.min_value = non_null_series.min()
            profile.max_value = non_null_series.max()
            
            # Time range
            time_range = profile.max_value - profile.min_value
            profile.pattern_analysis = {
                "time_range_days": time_range.days,
                "date_format": self._detect_date_format(series),
                "frequency_analysis": self._analyze_datetime_frequency(non_null_series)
            }
        
        return profile
    
    def _add_boolean_profile(self, profile: ColumnProfile, series: pd.Series) -> ColumnProfile:
        """Add boolean-specific statistics to column profile"""
        non_null_series = series.dropna()
        
        if len(non_null_series) > 0:
            value_counts = non_null_series.value_counts()
            profile.value_counts = value_counts.to_dict()
            
            if True in value_counts and False in value_counts:
                true_percentage = (value_counts[True] / len(non_null_series)) * 100
                profile.pattern_analysis = {
                    "true_percentage": true_percentage,
                    "false_percentage": 100 - true_percentage,
                    "balance_ratio": min(true_percentage, 100 - true_percentage) / max(true_percentage, 100 - true_percentage)
                }
        
        return profile
    
    def _calculate_string_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Calculate statistics for string columns"""
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return {}
        
        # Convert to string and calculate lengths
        str_series = non_null_series.astype(str)
        lengths = str_series.str.len()
        
        stats = {
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max()),
            "avg_length": float(lengths.mean()),
            "median_length": float(lengths.median()),
            "most_common": str_series.value_counts().head(5).to_dict(),
            "empty_strings": (str_series == "").sum(),
            "whitespace_only": str_series.str.strip().eq("").sum()
        }
        
        # Pattern analysis
        stats["patterns"] = self._analyze_string_patterns(str_series)
        
        return stats
    
    def _analyze_string_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze patterns in string data"""
        patterns = {
            "has_numbers": series.str.contains(r'\d', na=False).sum(),
            "has_letters": series.str.contains(r'[a-zA-Z]', na=False).sum(),
            "has_special_chars": series.str.contains(r'[^a-zA-Z0-9\s]', na=False).sum(),
            "all_uppercase": series.str.isupper().sum(),
            "all_lowercase": series.str.islower().sum(),
            "title_case": series.str.istitle().sum(),
            "starts_with_space": series.str.startswith(' ', na=False).sum(),
            "ends_with_space": series.str.endswith(' ', na=False).sum()
        }
        
        # Common patterns
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        
        patterns["email_format"] = series.str.match(email_pattern, na=False).sum()
        patterns["phone_format"] = series.str.match(phone_pattern, na=False).sum()
        patterns["url_format"] = series.str.match(url_pattern, na=False).sum()
        
        return patterns
    
    def _detect_outliers_iqr(self, series: pd.Series, multiplier: float = 1.5) -> List[Any]:
        """Detect outliers using IQR method"""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        return outliers.tolist()
    
    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 3.0) -> List[Any]:
        """Detect outliers using Z-score method"""
        z_scores = np.abs(stats.zscore(series))
        outliers = series[z_scores > threshold]
        return outliers.tolist()
    
    def _detect_outliers_isolation_forest(self, series: pd.Series) -> List[Any]:
        """Detect outliers using Isolation Forest (placeholder for sklearn)"""
        # This would require sklearn - simplified implementation
        # For now, fall back to IQR method
        return self._detect_outliers_iqr(series)
    
    def _detect_date_format(self, series: pd.Series) -> str:
        """Detect the date format used in a series"""
        # Common date formats to check
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%d-%m-%Y',
            '%Y%m%d'
        ]
        
        sample = series.dropna().head(100).astype(str)
        
        for fmt in formats:
            try:
                parsed_count = 0
                for value in sample:
                    try:
                        pd.to_datetime(value, format=fmt)
                        parsed_count += 1
                    except:
                        pass
                
                if parsed_count / len(sample) > 0.8:  # 80% success rate
                    return fmt
            except:
                continue
        
        return "unknown"
    
    def _analyze_datetime_frequency(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze frequency patterns in datetime data"""
        # Extract components
        years = series.dt.year.value_counts()
        months = series.dt.month.value_counts()
        days_of_week = series.dt.dayofweek.value_counts()
        hours = series.dt.hour.value_counts() if hasattr(series.dt, 'hour') else {}
        
        return {
            "year_distribution": years.head(10).to_dict(),
            "month_distribution": months.to_dict(),
            "day_of_week_distribution": days_of_week.to_dict(),
            "hour_distribution": hours.head(24).to_dict() if hours else {},
            "most_common_year": years.index[0] if len(years) > 0 else None,
            "most_common_month": months.index[0] if len(months) > 0 else None
        }
    
    def calculate_quality_score(self, issues: List, statistics: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        base_score = 100.0
        
        # Deduct points based on issues
        for issue in issues:
            if issue.severity == "critical":
                base_score -= 20
            elif issue.severity == "high":
                base_score -= 10
            elif issue.severity == "medium":
                base_score -= 5
            elif issue.severity == "low":
                base_score -= 2
        
        # Adjust based on completeness
        if "null_percentages" in statistics:
            avg_null_percentage = np.mean(list(statistics["null_percentages"].values()))
            base_score -= avg_null_percentage * 0.5  # Penalize missing data
        
        # Adjust based on uniqueness (for categorical data)
        if "cardinality_ratios" in statistics:
            # Penalize very low cardinality in non-categorical seeming columns
            low_cardinality_penalty = sum(
                1 for ratio in statistics["cardinality_ratios"].values() 
                if ratio < 0.1
            ) * 2
            base_score -= low_cardinality_penalty
        
        return max(0.0, min(100.0, base_score))
    
    def detect_statistical_outliers(self, series: pd.Series) -> Dict[str, Any]:
        """Comprehensive outlier detection"""
        if not pd.api.types.is_numeric_dtype(series):
            return {"count": 0, "extreme_count": 0, "sample_values": [], "confidence": 0.0}
        
        non_null_series = series.dropna()
        if len(non_null_series) < 4:  # Need at least 4 values for meaningful statistics
            return {"count": 0, "extreme_count": 0, "sample_values": [], "confidence": 0.0}
        
        # IQR method
        iqr_outliers = self._detect_outliers_iqr(non_null_series)
        
        # Z-score method
        zscore_outliers = self._detect_outliers_zscore(non_null_series)
        
        # Combine results
        all_outliers = list(set(iqr_outliers + zscore_outliers))
        
        # Extreme outliers (beyond 3 IQR)
        extreme_outliers = self._detect_outliers_iqr(non_null_series, multiplier=3.0)
        
        # Sample outliers for reporting
        sample_outliers = all_outliers[:10] if len(all_outliers) > 10 else all_outliers
        
        # Confidence based on agreement between methods
        iqr_set = set(iqr_outliers)
        zscore_set = set(zscore_outliers)
        agreement = len(iqr_set.intersection(zscore_set)) / len(iqr_set.union(zscore_set)) if iqr_set.union(zscore_set) else 1.0
        
        return {
            "count": len(all_outliers),
            "extreme_count": len(extreme_outliers),
            "sample_values": sample_outliers,
            "confidence": agreement,
            "methods_agreement": agreement,
            "iqr_outliers": len(iqr_outliers),
            "zscore_outliers": len(zscore_outliers)
        }
