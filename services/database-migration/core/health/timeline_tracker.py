"""
Health Timeline Tracker Core Logic.
Tracks performance trends over time with anomaly detection and forecasting.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from models.health_models import (
    HealthTimelineData, DataPoint, Anomaly, Forecast,
    TrendAnalysis, TrendDirection, HealthStatus, DatabaseType
)

class TimelineTracker:
    """
    Tracks database health metrics over time.
    """
    
    def track_timeline(self, db_type: DatabaseType, connection_string: str, days: int = 30, include_forecast: bool = True) -> HealthTimelineData:
        """
        Generates health timeline with trend analysis and forecasting.
        """
        timeline = self._generate_timeline_data(days)
        trend_analysis = self._analyze_trend(timeline)
        anomalies = self._detect_anomalies(timeline)
        forecast = self._forecast_health(timeline, days=7) if include_forecast else None
        period_summary = self._generate_summary(timeline, trend_analysis)
        
        return HealthTimelineData(
            timeline=timeline,
            trend_analysis=trend_analysis,
            anomalies=anomalies,
            forecast=forecast,
            period_summary=period_summary
        )
    
    def _generate_timeline_data(self, days: int) -> List[DataPoint]:
        """Simulates historical health data."""
        timeline = []
        base_score = 75
        
        for i in range(days):
            # Simulate score variation with slight downward trend
            variation = random.randint(-5, 5)
            trend_impact = -0.2 * i  # Slight decline over time
            score = int(max(40, min(100, base_score + variation + trend_impact)))
            
            timestamp = datetime.now() - timedelta(days=days - i)
            
            timeline.append(DataPoint(
                timestamp=timestamp,
                score=score,
                health_status=self._score_to_status(score),
                key_metrics={
                    "avg_query_time": 10 + random.uniform(0, 5),
                    "cache_hit_ratio": 0.85 + random.uniform(0, 0.10),
                    "connection_count": 50 + random.randint(-10, 20),
                    "slow_queries": random.randint(10, 50)
                }
            ))
        
        return timeline
    
    def _score_to_status(self, score: int) -> HealthStatus:
        """Maps score to health status."""
        if score >= 90:
            return HealthStatus.EXCELLENT
        elif score >= 75:
            return HealthStatus.GOOD
        elif score >= 60:
            return HealthStatus.FAIR
        elif score >= 40:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL
    
    def _analyze_trend(self, timeline: List[DataPoint]) -> TrendAnalysis:
        """Analyzes health trend."""
        if len(timeline) < 2:
            return TrendAnalysis(
                direction=TrendDirection.STABLE,
                change_percentage=0.0,
                velocity=0.0,
                volatility=0.0
            )
        
        scores = [dp.score for dp in timeline]
        first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        change_percentage = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        velocity = (scores[-1] - scores[0]) / len(scores)
        
        # Calculate volatility (standard deviation)
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        volatility = variance ** 0.5
        
        # Determine direction
        if change_percentage > 5:
            direction = TrendDirection.IMPROVING
        elif change_percentage < -5:
            direction = TrendDirection.DECLINING
        else:
            direction = TrendDirection.STABLE
        
        return TrendAnalysis(
            direction=direction,
            change_percentage=round(change_percentage, 2),
            velocity=round(velocity, 2),
            volatility=round(volatility, 2)
        )
    
    def _detect_anomalies(self, timeline: List[DataPoint]) -> List[Anomaly]:
        """Detects significant deviations in health scores."""
        anomalies = []
        
        if len(timeline) < 7:
            return anomalies
        
        scores = [dp.score for dp in timeline]
        mean = sum(scores) / len(scores)
        std_dev = (sum((x - mean) ** 2 for x in scores) / len(scores)) ** 0.5
        
        for dp in timeline:
            deviation = abs(dp.score - mean)
            if deviation > 2 * std_dev:  # 2 standard deviations
                anomalies.append(Anomaly(
                    timestamp=dp.timestamp,
                    severity="high" if deviation > 3 * std_dev else "medium",
                    description=f"Unusual health score: {dp.score} (expected ~{int(mean)})",
                    impact_score=int(deviation),
                    potential_cause="Sudden increase in slow queries" if dp.score < mean else "Performance optimization applied"
                ))
        
        return anomalies[:10]  # Limit to top 10 anomalies
    
    def _forecast_health(self, timeline: List[DataPoint], days: int = 7) -> List[Forecast]:
        """Simple linear forecast of health scores."""
        if len(timeline) < 7:
            return []
        
        scores = [dp.score for dp in timeline]
        
        # Simple linear regression
        n = len(scores)
        x_mean = n / 2
        y_mean = sum(scores) / n
        
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        forecasts = []
        last_timestamp = timeline[-1].timestamp
        
        for i in range(1, days + 1):
            predicted_score = int(slope * (n + i) + intercept)
            predicted_score = max(0, min(100, predicted_score))
            
            # Confidence decreases with distance
            confidence = max(0.5, 1 - (i * 0.05))
            
            forecasts.append(Forecast(
                timestamp=last_timestamp + timedelta(days=i),
                predicted_score=predicted_score,
                confidence=round(confidence, 2),
                prediction_range={
                    "min": max(0, predicted_score - 10),
                    "max": min(100, predicted_score + 10)
                }
            ))
        
        return forecasts
    
    def _generate_summary(self, timeline: List[DataPoint], trend: TrendAnalysis) -> Dict[str, Any]:
        """Generates period summary statistics."""
        scores = [dp.score for dp in timeline]
        
        return {
            "period_days": len(timeline),
            "avg_score": round(sum(scores) / len(scores), 2),
            "min_score": min(scores),
            "max_score": max(scores),
            "score_range": max(scores) - min(scores),
            "trend_direction": trend.direction.value,
            "days_above_75": sum(1 for s in scores if s >= 75),
            "days_below_60": sum(1 for s in scores if s < 60)
        }
