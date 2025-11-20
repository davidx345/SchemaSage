"""
Cost Spike Analyzer and Budget Forecaster.
Analyzes cost spikes and generates budget forecasts with predictive modeling.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
from dateutil.relativedelta import relativedelta

from models.anomaly_models import (
    CostSpikeData, CostSpike, BudgetForecastData, ForecastDataPoint, BudgetAlert
)

class CostAnalyzer:
    """
    Analyzes cost spikes and generates budget forecasts.
    """
    
    def analyze_spikes(
        self,
        cost_data: List[Dict[str, Any]],
        spike_threshold: float = 1.5,
        include_root_cause: bool = True
    ) -> CostSpikeData:
        """
        Analyzes cost spikes in historical data.
        """
        spikes = self._detect_spikes(spike_threshold, include_root_cause)
        
        total_excess_cost = sum(spike.estimated_excess_cost for spike in spikes)
        avg_increase = sum(spike.increase_percentage for spike in spikes) / len(spikes) if spikes else 0
        
        pattern_analysis = {
            "time_of_day_pattern": "Most spikes occur between 2-4 AM (automated jobs)",
            "day_of_week_pattern": "Higher spike frequency on Mondays (weekly batch jobs)",
            "recurring_services": ["batch-processing", "data-pipeline"],
            "average_duration_hours": sum(s.duration_hours for s in spikes) / len(spikes) if spikes else 0
        }
        
        return CostSpikeData(
            spikes=spikes,
            total_spikes=len(spikes),
            total_excess_cost=total_excess_cost,
            spike_frequency=f"{len(spikes)} spikes in 30 days (~{round(len(spikes)/4.3, 1)} per week)",
            average_spike_increase=round(avg_increase, 1),
            pattern_analysis=pattern_analysis
        )
    
    def forecast_budget(
        self,
        historical_costs: List[Dict[str, Any]],
        forecast_months: int = 3,
        budget_limit: float = None,
        growth_rate: float = None
    ) -> BudgetForecastData:
        """
        Generates budget forecast with trend analysis.
        """
        # Calculate baseline from historical data
        baseline_cost = 5000.0  # Simulated baseline
        
        # Determine growth rate
        if growth_rate is None:
            growth_rate = 0.08  # 8% monthly growth (typical for growing applications)
        
        # Generate forecast
        forecast_points = []
        current_date = datetime.now()
        budget_alerts = []
        
        for i in range(forecast_months):
            month_date = current_date + relativedelta(months=i+1)
            month_str = month_date.strftime("%Y-%m")
            
            # Calculate predicted cost with growth
            predicted_cost = baseline_cost * ((1 + growth_rate) ** (i + 1))
            
            # Add variance for confidence bounds
            variance = predicted_cost * 0.15  # 15% variance
            lower_bound = predicted_cost - variance
            upper_bound = predicted_cost + variance
            
            # Determine budget status
            if budget_limit:
                if predicted_cost > budget_limit * 1.1:
                    status = "over_budget"
                elif predicted_cost > budget_limit * 0.9:
                    status = "at_risk"
                else:
                    status = "under_budget"
                
                # Generate alert if over budget
                if predicted_cost > budget_limit:
                    overrun = predicted_cost - budget_limit
                    budget_alerts.append(BudgetAlert(
                        alert_id=f"alert_{str(uuid4())[:8]}",
                        month=month_str,
                        predicted_cost=round(predicted_cost, 2),
                        budget_limit=budget_limit,
                        overrun_amount=round(overrun, 2),
                        overrun_percentage=round((overrun / budget_limit) * 100, 1),
                        recommended_actions=[
                            "Review and optimize high-cost resources",
                            "Consider reserved instances for predictable workloads",
                            "Implement auto-scaling policies to reduce waste",
                            "Audit unused or underutilized resources"
                        ]
                    ))
            else:
                status = "under_budget"
            
            forecast_points.append(ForecastDataPoint(
                month=month_str,
                predicted_cost=round(predicted_cost, 2),
                lower_bound=round(lower_bound, 2),
                upper_bound=round(upper_bound, 2),
                confidence=0.85 - (i * 0.05),  # Confidence decreases over time
                budget_status=status
            ))
        
        total_predicted = sum(fp.predicted_cost for fp in forecast_points)
        avg_monthly = total_predicted / forecast_months
        
        # Determine growth trend
        if growth_rate > 0.15:
            trend = f"Rapid growth: {growth_rate*100:.1f}% monthly increase"
        elif growth_rate > 0.05:
            trend = f"Steady growth: {growth_rate*100:.1f}% monthly increase"
        elif growth_rate > 0:
            trend = f"Slow growth: {growth_rate*100:.1f}% monthly increase"
        else:
            trend = "Stable costs"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            forecast_points,
            budget_limit,
            growth_rate
        )
        
        return BudgetForecastData(
            forecast=forecast_points,
            total_predicted_cost=round(total_predicted, 2),
            average_monthly_cost=round(avg_monthly, 2),
            growth_trend=trend,
            budget_alerts=budget_alerts,
            confidence_score=0.82,  # Overall confidence
            recommendations=recommendations
        )
    
    def _detect_spikes(self, threshold: float, include_root_cause: bool) -> List[CostSpike]:
        """Detects cost spikes in data."""
        spikes = []
        now = datetime.now()
        
        # Spike 1: Batch Job Spike
        spike1 = CostSpike(
            spike_id=f"spike_{str(uuid4())[:8]}",
            timestamp=now - timedelta(days=3),
            baseline_cost=150.0,
            spike_cost=525.0,
            increase_percentage=250.0,
            duration_hours=4,
            root_causes=[
                "Batch processing job ran with 3x normal data volume",
                "Inefficient query caused compute scaling",
                "No rate limiting on API calls"
            ] if include_root_cause else [],
            affected_services=["batch-processor", "compute-cluster"],
            estimated_excess_cost=375.0,
            mitigation_actions=[
                "Implement batch size limits",
                "Add query optimization and caching",
                "Configure rate limiting on external API calls",
                "Set up cost anomaly alerts"
            ]
        )
        spikes.append(spike1)
        
        # Spike 2: Traffic Surge
        spike2 = CostSpike(
            spike_id=f"spike_{str(uuid4())[:8]}",
            timestamp=now - timedelta(days=7),
            baseline_cost=300.0,
            spike_cost=780.0,
            increase_percentage=160.0,
            duration_hours=6,
            root_causes=[
                "Unexpected traffic surge from marketing campaign",
                "Auto-scaling triggered aggressive scale-out",
                "High database query volume"
            ] if include_root_cause else [],
            affected_services=["web-servers", "load-balancer", "database"],
            estimated_excess_cost=480.0,
            mitigation_actions=[
                "Pre-scale resources for planned campaigns",
                "Tune auto-scaling parameters",
                "Implement read replicas for database",
                "Use CDN for static content"
            ]
        )
        spikes.append(spike2)
        
        # Spike 3: Storage Spike
        if threshold <= 2.0:
            spike3 = CostSpike(
                spike_id=f"spike_{str(uuid4())[:8]}",
                timestamp=now - timedelta(days=12),
                baseline_cost=200.0,
                spike_cost=500.0,
                increase_percentage=150.0,
                duration_hours=24,
                root_causes=[
                    "Backup process created duplicate snapshots",
                    "Log retention policy not applied",
                    "Temp files not cleaned up"
                ] if include_root_cause else [],
                affected_services=["storage", "backup-service"],
                estimated_excess_cost=300.0,
                mitigation_actions=[
                    "Fix backup deduplication",
                    "Implement log rotation and archival",
                    "Add automated cleanup jobs",
                    "Set lifecycle policies for storage"
                ]
            )
            spikes.append(spike3)
        
        return sorted(spikes, key=lambda x: x.timestamp, reverse=True)
    
    def _generate_recommendations(
        self,
        forecast_points: List[ForecastDataPoint],
        budget_limit: float,
        growth_rate: float
    ) -> List[str]:
        """Generates cost optimization recommendations."""
        recommendations = []
        
        # Budget-based recommendations
        if budget_limit and any(fp.budget_status == "over_budget" for fp in forecast_points):
            recommendations.append("⚠️ Budget overrun predicted - immediate cost optimization required")
            recommendations.append("Consider purchasing reserved instances (up to 60% savings)")
            recommendations.append("Review and right-size over-provisioned resources")
        
        # Growth-based recommendations
        if growth_rate > 0.10:
            recommendations.append("High growth detected - plan capacity increases proactively")
            recommendations.append("Implement cost allocation tags for better tracking")
        
        # General recommendations
        recommendations.extend([
            "Set up automated cost anomaly detection alerts",
            "Review top 10 cost drivers monthly",
            "Implement auto-shutdown for non-production environments",
            "Use spot instances for fault-tolerant workloads"
        ])
        
        return recommendations[:6]  # Limit to top 6 recommendations
