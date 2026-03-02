"""
Data Health Score Monitoring System
Premium feature for continuous data quality monitoring and scoring
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from uuid import uuid4

from core.auth import get_current_user, get_optional_user
from core.database_service import SchemaDetectionDatabaseService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Data Health Score"])

# Initialize database service
db_service = SchemaDetectionDatabaseService()


# Models
class HealthScoreStatus(str, Enum):
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"            # 75-89
    FAIR = "fair"            # 60-74
    POOR = "poor"            # 40-59
    CRITICAL = "critical"    # 0-39


class HealthCategory(str, Enum):
    COMPLETENESS = "completeness"
    FRESHNESS = "freshness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    DUPLICATES = "duplicates"
    VALIDITY = "validity"


class HealthIssue(BaseModel):
    category: HealthCategory
    severity: str  # critical, high, medium, low
    description: str
    affected_tables: List[str]
    affected_rows: int
    recommendation: str


class HealthScoreBreakdown(BaseModel):
    completeness_score: float = Field(ge=0, le=100)
    freshness_score: float = Field(ge=0, le=100)
    consistency_score: float = Field(ge=0, le=100)
    accuracy_score: float = Field(ge=0, le=100)
    duplicates_score: float = Field(ge=0, le=100)
    validity_score: float = Field(ge=0, le=100)


class HealthScoreResult(BaseModel):
    score_id: str
    user_id: str
    overall_score: float = Field(ge=0, le=100)
    status: HealthScoreStatus
    breakdown: HealthScoreBreakdown
    issues: List[HealthIssue]
    total_tables_analyzed: int
    total_rows_analyzed: int
    analyzed_at: datetime
    improvement_potential: float


class HealthScoreRequest(BaseModel):
    schema_data: Dict[str, Any]
    table_names: Optional[List[str]] = None
    enable_monitoring: bool = False


class IndustryBenchmark(BaseModel):
    industry: str
    avg_score: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_90: float


class HealthAlert(BaseModel):
    alert_id: str
    user_id: str
    alert_type: str  # score_drop, critical_issue, threshold_breach
    message: str
    current_score: float
    previous_score: float
    triggered_at: datetime


# Health Score Calculation Engine
class HealthScoreEngine:
    """Calculate comprehensive data health scores"""
    
    def __init__(self):
        self.weights = {
            "completeness": 0.25,
            "freshness": 0.15,
            "consistency": 0.20,
            "accuracy": 0.20,
            "duplicates": 0.10,
            "validity": 0.10
        }
    
    def calculate_health_score(self, schema_data: Dict[str, Any]) -> HealthScoreResult:
        """Calculate comprehensive health score"""
        tables = schema_data.get("tables", {})
        
        # Calculate individual scores
        completeness_score = self._calculate_completeness(tables)
        freshness_score = self._calculate_freshness(tables)
        consistency_score = self._calculate_consistency(tables)
        accuracy_score = self._calculate_accuracy(tables)
        duplicates_score = self._calculate_duplicates(tables)
        validity_score = self._calculate_validity(tables)
        
        # Calculate weighted overall score
        overall_score = (
            completeness_score * self.weights["completeness"] +
            freshness_score * self.weights["freshness"] +
            consistency_score * self.weights["consistency"] +
            accuracy_score * self.weights["accuracy"] +
            duplicates_score * self.weights["duplicates"] +
            validity_score * self.weights["validity"]
        )
        
        # Determine status
        status = self._get_status(overall_score)
        
        # Identify issues
        issues = self._identify_issues(tables, {
            "completeness": completeness_score,
            "freshness": freshness_score,
            "consistency": consistency_score,
            "accuracy": accuracy_score,
            "duplicates": duplicates_score,
            "validity": validity_score
        })
        
        # Calculate improvement potential
        max_possible = 100
        improvement_potential = max_possible - overall_score
        
        # Count tables and rows
        total_tables = len(tables)
        total_rows = sum(table.get("row_count", 0) for table in tables.values())
        
        return HealthScoreResult(
            score_id=str(uuid4()),
            user_id="",  # Will be set by endpoint
            overall_score=round(overall_score, 2),
            status=status,
            breakdown=HealthScoreBreakdown(
                completeness_score=round(completeness_score, 2),
                freshness_score=round(freshness_score, 2),
                consistency_score=round(consistency_score, 2),
                accuracy_score=round(accuracy_score, 2),
                duplicates_score=round(duplicates_score, 2),
                validity_score=round(validity_score, 2)
            ),
            issues=issues,
            total_tables_analyzed=total_tables,
            total_rows_analyzed=total_rows,
            analyzed_at=datetime.now(),
            improvement_potential=round(improvement_potential, 2)
        )
    
    def _calculate_completeness(self, tables: Dict[str, Any]) -> float:
        """Calculate data completeness (% of non-null values)"""
        if not tables:
            return 100.0
        
        total_fields = 0
        complete_fields = 0
        
        for table in tables.values():
            columns = table.get("columns", {})
            for column in columns.values():
                total_fields += 1
                null_rate = column.get("null_percentage", 0)
                if null_rate < 10:  # Less than 10% null is considered complete
                    complete_fields += 1
        
        if total_fields == 0:
            return 100.0
        
        return (complete_fields / total_fields) * 100
    
    def _calculate_freshness(self, tables: Dict[str, Any]) -> float:
        """Calculate data freshness (how recently updated)"""
        if not tables:
            return 100.0
        
        # Look for timestamp columns
        now = datetime.now()
        scores = []
        
        for table in tables.values():
            columns = table.get("columns", {})
            has_timestamp = any(
                "created_at" in col.lower() or "updated_at" in col.lower() or "timestamp" in col.lower()
                for col in columns.keys()
            )
            
            if has_timestamp:
                # Assume recent if timestamp columns exist
                scores.append(85)
            else:
                # Penalize tables without timestamp tracking
                scores.append(60)
        
        return sum(scores) / len(scores) if scores else 80.0
    
    def _calculate_consistency(self, tables: Dict[str, Any]) -> float:
        """Calculate data consistency (format, type consistency)"""
        if not tables:
            return 100.0
        
        consistency_issues = 0
        total_columns = 0
        
        for table in tables.values():
            columns = table.get("columns", {})
            for column_name, column_data in columns.items():
                total_columns += 1
                
                # Check for mixed data types
                data_types = column_data.get("data_types", [])
                if len(data_types) > 1:
                    consistency_issues += 1
        
        if total_columns == 0:
            return 100.0
        
        consistency_rate = 1 - (consistency_issues / total_columns)
        return max(0, consistency_rate * 100)
    
    def _calculate_accuracy(self, tables: Dict[str, Any]) -> float:
        """Calculate data accuracy (valid formats, ranges)"""
        if not tables:
            return 100.0
        
        # Check for validation rules and constraints
        total_columns = 0
        validated_columns = 0
        
        for table in tables.values():
            columns = table.get("columns", {})
            for column_data in columns.values():
                total_columns += 1
                
                # Check if column has constraints or validation
                has_constraints = bool(column_data.get("constraints"))
                has_validation = column_data.get("validated", False)
                
                if has_constraints or has_validation:
                    validated_columns += 1
        
        if total_columns == 0:
            return 100.0
        
        # Assume 70% base accuracy, add bonus for validation
        base_score = 70
        validation_bonus = (validated_columns / total_columns) * 30
        
        return min(100, base_score + validation_bonus)
    
    def _calculate_duplicates(self, tables: Dict[str, Any]) -> float:
        """Calculate duplicate rate score"""
        if not tables:
            return 100.0
        
        # Check for primary keys and unique constraints
        tables_with_pk = 0
        total_tables = len(tables)
        
        for table in tables.values():
            columns = table.get("columns", {})
            has_pk = any(col.get("primary_key") for col in columns.values())
            
            if has_pk:
                tables_with_pk += 1
        
        # Tables with primary keys likely have fewer duplicates
        pk_rate = tables_with_pk / total_tables if total_tables > 0 else 0
        
        # Base score 80, bonus for PKs
        return min(100, 80 + (pk_rate * 20))
    
    def _calculate_validity(self, tables: Dict[str, Any]) -> float:
        """Calculate data validity (correct formats, domains)"""
        if not tables:
            return 100.0
        
        # Check for email, phone, date validation
        total_sensitive_fields = 0
        validated_fields = 0
        
        for table in tables.values():
            columns = table.get("columns", {})
            for column_name, column_data in columns.items():
                col_lower = column_name.lower()
                
                # Identify fields that should be validated
                if any(term in col_lower for term in ["email", "phone", "date", "url", "zip"]):
                    total_sensitive_fields += 1
                    
                    # Check if validated
                    if column_data.get("validated", False):
                        validated_fields += 1
        
        if total_sensitive_fields == 0:
            return 90.0  # No sensitive fields to validate
        
        validity_rate = validated_fields / total_sensitive_fields
        return validity_rate * 100
    
    def _get_status(self, score: float) -> HealthScoreStatus:
        """Determine health status from score"""
        if score >= 90:
            return HealthScoreStatus.EXCELLENT
        elif score >= 75:
            return HealthScoreStatus.GOOD
        elif score >= 60:
            return HealthScoreStatus.FAIR
        elif score >= 40:
            return HealthScoreStatus.POOR
        else:
            return HealthScoreStatus.CRITICAL
    
    def _identify_issues(self, tables: Dict[str, Any], scores: Dict[str, float]) -> List[HealthIssue]:
        """Identify specific data health issues"""
        issues = []
        
        # Completeness issues
        if scores["completeness"] < 70:
            incomplete_tables = []
            for table_name, table_data in tables.items():
                columns = table_data.get("columns", {})
                high_null_cols = [
                    col for col, data in columns.items()
                    if data.get("null_percentage", 0) > 30
                ]
                if high_null_cols:
                    incomplete_tables.append(table_name)
            
            if incomplete_tables:
                issues.append(HealthIssue(
                    category=HealthCategory.COMPLETENESS,
                    severity="high",
                    description=f"High null rates detected in {len(incomplete_tables)} tables",
                    affected_tables=incomplete_tables[:5],
                    affected_rows=0,
                    recommendation="Review and fill missing values or adjust schema design"
                ))
        
        # Consistency issues
        if scores["consistency"] < 70:
            inconsistent_tables = []
            for table_name, table_data in tables.items():
                columns = table_data.get("columns", {})
                mixed_type_cols = [
                    col for col, data in columns.items()
                    if len(data.get("data_types", [])) > 1
                ]
                if mixed_type_cols:
                    inconsistent_tables.append(table_name)
            
            if inconsistent_tables:
                issues.append(HealthIssue(
                    category=HealthCategory.CONSISTENCY,
                    severity="medium",
                    description=f"Mixed data types found in {len(inconsistent_tables)} tables",
                    affected_tables=inconsistent_tables[:5],
                    affected_rows=0,
                    recommendation="Standardize data types and enforce type constraints"
                ))
        
        # Duplicate issues
        if scores["duplicates"] < 80:
            tables_without_pk = [
                table_name for table_name, table_data in tables.items()
                if not any(col.get("primary_key") for col in table_data.get("columns", {}).values())
            ]
            
            if tables_without_pk:
                issues.append(HealthIssue(
                    category=HealthCategory.DUPLICATES,
                    severity="medium",
                    description=f"{len(tables_without_pk)} tables lack primary keys",
                    affected_tables=tables_without_pk[:5],
                    affected_rows=0,
                    recommendation="Add primary keys to prevent duplicate records"
                ))
        
        return issues


# Initialize engine
health_engine = HealthScoreEngine()


# API Endpoints
@router.post("/analyze")
async def analyze_health_score(
    request: HealthScoreRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Calculate comprehensive data health score
    
    **Premium Feature**: Analyze data quality across multiple dimensions
    """
    try:
        logger.info(f"Analyzing health score for user {user_id}")
        
        # Calculate health score
        result = health_engine.calculate_health_score(request.schema_data)
        result.user_id = user_id
        
        # Store result in database for history tracking
        # TODO: Save to database when model is ready
        
        # Enable monitoring if requested
        if request.enable_monitoring:
            logger.info(f"Monitoring enabled for user {user_id}")
            # TODO: Enable background monitoring
        
        return {
            "success": True,
            "data": {
                "health_score": result.dict(),
                "monitoring_enabled": request.enable_monitoring,
                "next_analysis_recommended": (datetime.now() + timedelta(days=7)).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Health score analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/history")
async def get_health_score_history(
    user_id: str = Depends(get_current_user),
    days: int = 30,
    limit: int = 50
):
    """
    Get historical health scores to track trends
    
    **Premium Feature**: View score trends over time
    """
    try:
        # TODO: Query from database
        # Mock data for now
        history = [
            {
                "score_id": str(uuid4()),
                "overall_score": 85.5,
                "status": "good",
                "analyzed_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "total_tables": 12,
                "issues_count": 3 - (i % 3)
            }
            for i in range(min(days, limit))
        ]
        
        # Calculate trend
        if len(history) >= 2:
            recent_avg = sum(h["overall_score"] for h in history[:7]) / 7
            older_avg = sum(h["overall_score"] for h in history[7:14]) / 7 if len(history) >= 14 else recent_avg
            trend = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "success": True,
            "data": {
                "history": history,
                "trend": trend,
                "total_analyses": len(history),
                "date_range": {
                    "from": (datetime.now() - timedelta(days=days)).isoformat(),
                    "to": datetime.now().isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get health score history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor")
async def enable_monitoring(
    schema_data: Dict[str, Any],
    user_id: str = Depends(get_current_user),
    frequency: str = "daily"  # daily, weekly, hourly
):
    """
    Enable continuous health score monitoring
    
    **Premium Feature**: Automatic monitoring with alerts
    """
    try:
        monitor_id = str(uuid4())
        
        # TODO: Store monitoring configuration in database
        # TODO: Schedule background job for monitoring
        
        return {
            "success": True,
            "data": {
                "monitor_id": monitor_id,
                "status": "active",
                "frequency": frequency,
                "next_check": (datetime.now() + timedelta(days=1 if frequency == "daily" else 7)).isoformat(),
                "alert_threshold": 75,  # Alert if score drops below this
                "message": f"Monitoring enabled with {frequency} checks"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to enable monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmarks")
async def get_industry_benchmarks(
    industry: Optional[str] = None,
    user_id: str = Depends(get_optional_user)
):
    """
    Get industry benchmark scores for comparison
    
    **Premium Feature**: Compare your score against industry standards
    """
    try:
        # Mock industry benchmarks
        benchmarks = {
            "e-commerce": IndustryBenchmark(
                industry="e-commerce",
                avg_score=78.5,
                percentile_25=65.0,
                percentile_50=78.0,
                percentile_75=87.0,
                percentile_90=92.0
            ),
            "saas": IndustryBenchmark(
                industry="saas",
                avg_score=82.3,
                percentile_25=72.0,
                percentile_50=82.0,
                percentile_75=89.0,
                percentile_90=94.0
            ),
            "healthcare": IndustryBenchmark(
                industry="healthcare",
                avg_score=88.7,
                percentile_25=80.0,
                percentile_50=89.0,
                percentile_75=94.0,
                percentile_90=97.0
            ),
            "financial": IndustryBenchmark(
                industry="financial",
                avg_score=90.2,
                percentile_25=84.0,
                percentile_50=90.0,
                percentile_75=95.0,
                percentile_90=98.0
            )
        }
        
        if industry and industry in benchmarks:
            return {
                "success": True,
                "data": {
                    "benchmark": benchmarks[industry].dict(),
                    "industry": industry
                }
            }
        
        return {
            "success": True,
            "data": {
                "benchmarks": {k: v.dict() for k, v in benchmarks.items()},
                "industries": list(benchmarks.keys())
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_health_alerts(
    user_id: str = Depends(get_current_user),
    limit: int = 20,
    unread_only: bool = False
):
    """
    Get health score alerts and notifications
    
    **Premium Feature**: Real-time alerts for score changes
    """
    try:
        # TODO: Query from database
        # Mock alerts
        alerts = [
            {
                "alert_id": str(uuid4()),
                "alert_type": "score_drop",
                "message": "Health score dropped from 85 to 72",
                "current_score": 72,
                "previous_score": 85,
                "severity": "high",
                "triggered_at": (datetime.now() - timedelta(hours=i)).isoformat(),
                "read": False if i < 3 else True
            }
            for i in range(limit)
        ]
        
        if unread_only:
            alerts = [a for a in alerts if not a["read"]]
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "unread_count": len([a for a in alerts if not a["read"]]),
                "total": len(alerts)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
