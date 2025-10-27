"""
Real-Time Cost Tracking
Budget alerts, anomaly detection, and cost attribution
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cost-tracking", tags=["cost-tracking"])


# Models
class TimeRange(str, Enum):
    LAST_24H = "24h"
    LAST_7D = "7d"
    LAST_30D = "30d"
    LAST_90D = "90d"
    CUSTOM = "custom"


class CostCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    BACKUP = "backup"
    NETWORK = "network"
    SUPPORT = "support"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CostDataPoint(BaseModel):
    """Single cost data point"""
    timestamp: datetime
    total_cost: float
    breakdown: Dict[CostCategory, float]


class BudgetAlert(BaseModel):
    """Budget alert configuration"""
    alert_id: str
    name: str
    budget_amount: float
    current_spend: float
    threshold_percentage: int = Field(ge=0, le=100)
    alert_triggered: bool
    severity: AlertSeverity
    notification_emails: List[str]


class CostAnomaly(BaseModel):
    """Detected cost anomaly"""
    anomaly_id: str
    detected_at: datetime
    category: CostCategory
    expected_cost: float
    actual_cost: float
    deviation_percentage: float
    confidence: float = Field(ge=0, le=100)
    possible_causes: List[str]


class CostAttribution(BaseModel):
    """Cost breakdown by dimension"""
    dimension: str  # "environment", "project", "team", etc.
    allocations: Dict[str, float]
    total: float


class CostTrackingDashboard(BaseModel):
    """Complete cost tracking dashboard"""
    time_range: TimeRange
    start_date: datetime
    end_date: datetime
    total_cost: float
    daily_average: float
    projected_monthly: float
    cost_trend: List[CostDataPoint]
    category_breakdown: Dict[CostCategory, float]
    budget_status: List[BudgetAlert]
    anomalies: List[CostAnomaly]
    attributions: List[CostAttribution]


class ForecastInput(BaseModel):
    """Input for cost forecasting"""
    historical_days: int = Field(default=30, ge=7, le=90)
    forecast_days: int = Field(default=30, ge=1, le=90)
    growth_factor: Optional[float] = None


class CostForecast(BaseModel):
    """Cost forecast response"""
    forecast_date: datetime
    forecasted_costs: List[CostDataPoint]
    confidence_interval_lower: List[float]
    confidence_interval_upper: List[float]
    projected_monthly_cost: float
    trend: str  # "increasing", "decreasing", "stable"


# Simulated cost data (in production, fetch from cloud provider billing APIs)
def generate_mock_cost_data(days: int = 30) -> List[CostDataPoint]:
    """Generate mock historical cost data"""
    data_points = []
    base_cost = 250.0
    
    for i in range(days):
        timestamp = datetime.utcnow() - timedelta(days=days-i)
        
        # Add some variance and trend
        variance = (hash(timestamp.day) % 20) - 10
        trend = i * 0.5
        total = base_cost + variance + trend
        
        breakdown = {
            CostCategory.COMPUTE: total * 0.6,
            CostCategory.STORAGE: total * 0.2,
            CostCategory.BACKUP: total * 0.1,
            CostCategory.NETWORK: total * 0.08,
            CostCategory.SUPPORT: total * 0.02
        }
        
        data_points.append(CostDataPoint(
            timestamp=timestamp,
            total_cost=round(total, 2),
            breakdown=breakdown
        ))
    
    return data_points


def detect_anomalies(cost_data: List[CostDataPoint]) -> List[CostAnomaly]:
    """Detect cost anomalies using statistical methods"""
    anomalies = []
    
    if len(cost_data) < 7:
        return anomalies
    
    # Calculate baseline (average of last 7 days)
    recent_costs = [dp.total_cost for dp in cost_data[-7:]]
    baseline = sum(recent_costs) / len(recent_costs)
    std_dev = (sum((x - baseline) ** 2 for x in recent_costs) / len(recent_costs)) ** 0.5
    
    # Check latest cost for anomaly
    latest = cost_data[-1]
    deviation = abs(latest.total_cost - baseline)
    deviation_pct = (deviation / baseline * 100) if baseline > 0 else 0
    
    # Anomaly if > 2 standard deviations from baseline
    if deviation > (2 * std_dev):
        # Find which category caused the anomaly
        for category in CostCategory:
            if category in latest.breakdown:
                category_cost = latest.breakdown[category]
                expected = baseline * 0.6 if category == CostCategory.COMPUTE else baseline * 0.2
                
                if abs(category_cost - expected) / expected > 0.3:  # 30% deviation
                    anomalies.append(CostAnomaly(
                        anomaly_id=f"anom-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        detected_at=latest.timestamp,
                        category=category,
                        expected_cost=round(expected, 2),
                        actual_cost=round(category_cost, 2),
                        deviation_percentage=round(deviation_pct, 2),
                        confidence=85.0,
                        possible_causes=[
                            "Unexpected traffic spike",
                            "New instance deployed",
                            "Storage growth",
                            "Configuration change"
                        ]
                    ))
    
    return anomalies


def calculate_budget_status() -> List[BudgetAlert]:
    """Calculate budget alert status"""
    return [
        BudgetAlert(
            alert_id="budget-prod-001",
            name="Production Environment Monthly Budget",
            budget_amount=10000.0,
            current_spend=8500.0,
            threshold_percentage=80,
            alert_triggered=True,
            severity=AlertSeverity.MEDIUM,
            notification_emails=["ops@schemasage.com"]
        ),
        BudgetAlert(
            alert_id="budget-dev-001",
            name="Development Environment Monthly Budget",
            budget_amount=2000.0,
            current_spend=1200.0,
            threshold_percentage=80,
            alert_triggered=False,
            severity=AlertSeverity.LOW,
            notification_emails=["dev@schemasage.com"]
        )
    ]


def calculate_cost_attribution() -> List[CostAttribution]:
    """Calculate cost attribution by dimensions"""
    return [
        CostAttribution(
            dimension="environment",
            allocations={
                "production": 6500.0,
                "staging": 2000.0,
                "development": 1500.0
            },
            total=10000.0
        ),
        CostAttribution(
            dimension="team",
            allocations={
                "platform": 4000.0,
                "backend": 3500.0,
                "frontend": 1500.0,
                "data": 1000.0
            },
            total=10000.0
        ),
        CostAttribution(
            dimension="project",
            allocations={
                "schemasage-core": 7000.0,
                "schemasage-analytics": 2000.0,
                "schemasage-ml": 1000.0
            },
            total=10000.0
        )
    ]


@router.get("/dashboard", response_model=CostTrackingDashboard)
async def get_cost_dashboard(
    time_range: TimeRange = TimeRange.LAST_30D,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get real-time cost tracking dashboard
    
    Provides:
    - Current spend and trends
    - Cost breakdown by category
    - Budget alerts
    - Anomaly detection
    - Cost attribution
    """
    try:
        # Determine date range
        if time_range == TimeRange.CUSTOM and start_date and end_date:
            days = (end_date - start_date).days
        elif time_range == TimeRange.LAST_24H:
            days = 1
        elif time_range == TimeRange.LAST_7D:
            days = 7
        elif time_range == TimeRange.LAST_90D:
            days = 90
        else:
            days = 30
        
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        # Generate cost data
        cost_data = generate_mock_cost_data(days)
        
        # Calculate totals
        total_cost = sum(dp.total_cost for dp in cost_data)
        daily_average = total_cost / len(cost_data)
        projected_monthly = daily_average * 30
        
        # Category breakdown (sum all categories)
        category_totals = {cat: 0.0 for cat in CostCategory}
        for dp in cost_data:
            for cat, amount in dp.breakdown.items():
                category_totals[cat] += amount
        
        # Detect anomalies
        anomalies = detect_anomalies(cost_data)
        
        # Get budget status
        budget_status = calculate_budget_status()
        
        # Get cost attribution
        attributions = calculate_cost_attribution()
        
        return CostTrackingDashboard(
            time_range=time_range,
            start_date=start,
            end_date=end,
            total_cost=round(total_cost, 2),
            daily_average=round(daily_average, 2),
            projected_monthly=round(projected_monthly, 2),
            cost_trend=cost_data,
            category_breakdown=category_totals,
            budget_status=budget_status,
            anomalies=anomalies,
            attributions=attributions
        )
    
    except Exception as e:
        logger.error(f"Dashboard retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")


@router.post("/forecast", response_model=CostForecast)
async def forecast_costs(input_data: ForecastInput):
    """
    Forecast future costs based on historical data
    
    Uses historical trends to project future spending
    with confidence intervals
    """
    try:
        # Get historical data
        historical_data = generate_mock_cost_data(input_data.historical_days)
        
        # Simple linear regression for forecast
        if len(historical_data) < 2:
            raise HTTPException(status_code=400, detail="Insufficient historical data")
        
        # Calculate trend
        costs = [dp.total_cost for dp in historical_data]
        avg_growth = (costs[-1] - costs[0]) / len(costs) if len(costs) > 0 else 0
        
        # Apply growth factor if provided
        if input_data.growth_factor:
            avg_growth *= input_data.growth_factor
        
        # Generate forecast
        last_cost = historical_data[-1].total_cost
        forecasted_costs = []
        lower_bounds = []
        upper_bounds = []
        
        for i in range(input_data.forecast_days):
            forecast_date = datetime.utcnow() + timedelta(days=i+1)
            forecasted_cost = last_cost + (avg_growth * (i + 1))
            
            # Add confidence intervals (±15%)
            lower_bound = forecasted_cost * 0.85
            upper_bound = forecasted_cost * 1.15
            
            breakdown = {
                CostCategory.COMPUTE: forecasted_cost * 0.6,
                CostCategory.STORAGE: forecasted_cost * 0.2,
                CostCategory.BACKUP: forecasted_cost * 0.1,
                CostCategory.NETWORK: forecasted_cost * 0.08,
                CostCategory.SUPPORT: forecasted_cost * 0.02
            }
            
            forecasted_costs.append(CostDataPoint(
                timestamp=forecast_date,
                total_cost=round(forecasted_cost, 2),
                breakdown=breakdown
            ))
            lower_bounds.append(round(lower_bound, 2))
            upper_bounds.append(round(upper_bound, 2))
        
        projected_monthly = forecasted_costs[-1].total_cost if len(forecasted_costs) >= 30 else sum(
            dp.total_cost for dp in forecasted_costs) / len(forecasted_costs) * 30
        
        trend = "increasing" if avg_growth > 1 else "decreasing" if avg_growth < -1 else "stable"
        
        return CostForecast(
            forecast_date=datetime.utcnow(),
            forecasted_costs=forecasted_costs,
            confidence_interval_lower=lower_bounds,
            confidence_interval_upper=upper_bounds,
            projected_monthly_cost=round(projected_monthly, 2),
            trend=trend
        )
    
    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")


@router.post("/alerts")
async def create_budget_alert(alert: BudgetAlert):
    """Create a new budget alert"""
    try:
        logger.info(f"Creating budget alert: {alert.name}")
        return {"alert_id": alert.alert_id, "status": "created", "alert": alert}
    except Exception as e:
        logger.error(f"Alert creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/{alert_id}")
async def get_budget_alert(alert_id: str):
    """Get specific budget alert details"""
    return {
        "alert_id": alert_id,
        "status": "active",
        "last_triggered": datetime.utcnow() - timedelta(hours=6)
    }


@router.delete("/alerts/{alert_id}")
async def delete_budget_alert(alert_id: str):
    """Delete a budget alert"""
    return {"alert_id": alert_id, "status": "deleted"}


@router.get("/export")
async def export_cost_report(
    time_range: TimeRange = TimeRange.LAST_30D,
    format: str = "csv"
):
    """
    Export cost report in various formats (CSV, JSON, PDF)
    """
    try:
        cost_data = generate_mock_cost_data(30 if time_range == TimeRange.LAST_30D else 7)
        
        if format == "json":
            return {"data": [dp.dict() for dp in cost_data]}
        else:
            # Return CSV data structure
            return {
                "format": "csv",
                "headers": ["Date", "Total Cost", "Compute", "Storage", "Backup", "Network"],
                "rows": [[
                    dp.timestamp.isoformat(),
                    dp.total_cost,
                    dp.breakdown.get(CostCategory.COMPUTE, 0),
                    dp.breakdown.get(CostCategory.STORAGE, 0),
                    dp.breakdown.get(CostCategory.BACKUP, 0),
                    dp.breakdown.get(CostCategory.NETWORK, 0)
                ] for dp in cost_data]
            }
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
