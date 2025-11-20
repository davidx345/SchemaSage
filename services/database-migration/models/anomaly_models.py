"""
Cost Anomaly Detection Models.
Pydantic models for anomaly detection, spike analysis, and budget forecasting.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class AnomalyType(str, Enum):
    """Types of cost anomalies."""
    SPIKE = "spike"
    GRADUAL_INCREASE = "gradual_increase"
    UNUSUAL_PATTERN = "unusual_pattern"
    BUDGET_OVERRUN = "budget_overrun"
    RESOURCE_WASTE = "resource_waste"

class Severity(str, Enum):
    """Anomaly severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ResourceType(str, Enum):
    """Cloud resource types."""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    OTHER = "other"

# ===== REQUEST MODELS =====

class AnomalyDetectionRequest(BaseModel):
    """Request for detecting cost anomalies."""
    cost_data: List[Dict[str, Any]] = Field(
        description="Historical cost data with timestamps and amounts"
    )
    resource_type: Optional[ResourceType] = Field(
        default=None,
        description="Filter by specific resource type"
    )
    sensitivity: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Detection sensitivity (1=low, 5=high). Higher values detect more anomalies."
    )
    lookback_days: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Number of days to analyze"
    )

class CostSpikeRequest(BaseModel):
    """Request for analyzing cost spikes."""
    cost_data: List[Dict[str, Any]] = Field(
        description="Cost data with timestamps"
    )
    spike_threshold: float = Field(
        default=1.5,
        ge=1.0,
        le=10.0,
        description="Multiplier for spike detection (e.g., 1.5 = 50% increase)"
    )
    include_root_cause: bool = Field(
        default=True,
        description="Include root cause analysis"
    )

class BudgetForecastRequest(BaseModel):
    """Request for budget forecasting."""
    historical_costs: List[Dict[str, Any]] = Field(
        description="Historical cost data for forecasting"
    )
    forecast_months: int = Field(
        default=3,
        ge=1,
        le=12,
        description="Number of months to forecast"
    )
    budget_limit: Optional[float] = Field(
        default=None,
        description="Monthly budget limit for alerts"
    )
    growth_rate: Optional[float] = Field(
        default=None,
        description="Expected monthly growth rate (0.1 = 10%)"
    )

# ===== RESPONSE MODELS =====

class Anomaly(BaseModel):
    """Individual cost anomaly."""
    anomaly_id: str = Field(description="Unique anomaly identifier")
    anomaly_type: AnomalyType = Field(description="Type of anomaly")
    severity: Severity = Field(description="Severity level")
    timestamp: datetime = Field(description="When anomaly occurred")
    expected_cost: float = Field(description="Expected cost based on baseline")
    actual_cost: float = Field(description="Actual cost observed")
    deviation_percentage: float = Field(description="Percentage deviation from expected")
    affected_resources: List[str] = Field(description="Resources involved in anomaly")
    description: str = Field(description="Human-readable description")
    recommendation: Optional[str] = Field(default=None, description="Remediation recommendation")
    estimated_waste: Optional[float] = Field(default=None, description="Estimated wasted cost")

class AnomalyDetectionData(BaseModel):
    """Anomaly detection results."""
    anomalies: List[Anomaly] = Field(description="Detected anomalies")
    total_anomalies: int = Field(description="Total number of anomalies found")
    critical_count: int = Field(description="Number of critical anomalies")
    high_count: int = Field(description="Number of high severity anomalies")
    total_wasted_cost: float = Field(description="Total estimated wasted cost")
    detection_summary: Dict[str, Any] = Field(description="Summary statistics")

class AnomalyDetectionResponse(BaseModel):
    """Response from anomaly detection."""
    success: bool
    data: Optional[AnomalyDetectionData] = None
    error: Optional[str] = None

class CostSpike(BaseModel):
    """Individual cost spike event."""
    spike_id: str = Field(description="Unique spike identifier")
    timestamp: datetime = Field(description="When spike occurred")
    baseline_cost: float = Field(description="Normal baseline cost")
    spike_cost: float = Field(description="Cost during spike")
    increase_percentage: float = Field(description="Percentage increase")
    duration_hours: int = Field(description="Duration of spike in hours")
    root_causes: List[str] = Field(description="Identified root causes")
    affected_services: List[str] = Field(description="Services affected")
    estimated_excess_cost: float = Field(description="Excess cost due to spike")
    mitigation_actions: List[str] = Field(description="Recommended mitigation actions")

class CostSpikeData(BaseModel):
    """Cost spike analysis results."""
    spikes: List[CostSpike] = Field(description="Detected cost spikes")
    total_spikes: int = Field(description="Total number of spikes")
    total_excess_cost: float = Field(description="Total excess cost from spikes")
    spike_frequency: str = Field(description="Frequency of spikes (e.g., '2 per week')")
    average_spike_increase: float = Field(description="Average spike increase percentage")
    pattern_analysis: Dict[str, Any] = Field(description="Spike pattern analysis")

class CostSpikeResponse(BaseModel):
    """Response from cost spike analysis."""
    success: bool
    data: Optional[CostSpikeData] = None
    error: Optional[str] = None

class ForecastDataPoint(BaseModel):
    """Individual forecast data point."""
    month: str = Field(description="Month (YYYY-MM format)")
    predicted_cost: float = Field(description="Predicted cost")
    lower_bound: float = Field(description="Lower confidence bound")
    upper_bound: float = Field(description="Upper confidence bound")
    confidence: float = Field(ge=0.0, le=1.0, description="Prediction confidence (0-1)")
    budget_status: str = Field(description="Status: 'under_budget', 'at_risk', 'over_budget'")

class BudgetAlert(BaseModel):
    """Budget alert."""
    alert_id: str = Field(description="Alert identifier")
    month: str = Field(description="Month of concern")
    predicted_cost: float = Field(description="Predicted cost")
    budget_limit: float = Field(description="Budget limit")
    overrun_amount: float = Field(description="Amount over budget")
    overrun_percentage: float = Field(description="Percentage over budget")
    recommended_actions: List[str] = Field(description="Cost reduction recommendations")

class BudgetForecastData(BaseModel):
    """Budget forecast results."""
    forecast: List[ForecastDataPoint] = Field(description="Monthly forecast data")
    total_predicted_cost: float = Field(description="Total predicted cost for period")
    average_monthly_cost: float = Field(description="Average monthly cost")
    growth_trend: str = Field(description="Growth trend description")
    budget_alerts: List[BudgetAlert] = Field(description="Budget overrun alerts")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall forecast confidence")
    recommendations: List[str] = Field(description="Cost optimization recommendations")

class BudgetForecastResponse(BaseModel):
    """Response from budget forecasting."""
    success: bool
    data: Optional[BudgetForecastData] = None
    error: Optional[str] = None
