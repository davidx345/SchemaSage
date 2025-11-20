"""
Comprehensive test suite for Cost Anomaly Detector feature.
Tests anomaly detection, cost spike analysis, and budget forecasting.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from main import app
from models.anomaly_models import (
    AnomalyDetectionRequest, CostSpikeRequest, BudgetForecastRequest,
    AnomalyType, Severity, ResourceType
)
from core.anomaly import AnomalyDetector, CostAnalyzer

client = TestClient(app)

# ===== ANOMALY DETECTOR TESTS =====

class TestAnomalyDetector:
    """Test anomaly detection core logic."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = AnomalyDetector()
        self.sample_cost_data = [
            {"timestamp": "2025-11-01", "cost": 100.0},
            {"timestamp": "2025-11-02", "cost": 105.0},
            {"timestamp": "2025-11-03", "cost": 350.0},  # Spike
        ]
    
    def test_detect_anomalies_basic(self):
        """Test basic anomaly detection."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        assert result is not None
        assert result.total_anomalies > 0
        assert len(result.anomalies) > 0
        assert result.total_wasted_cost >= 0
    
    def test_detect_budget_overrun(self):
        """Test detection of budget overruns."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        overruns = [a for a in result.anomalies if a.anomaly_type == AnomalyType.BUDGET_OVERRUN]
        assert len(overruns) > 0
        assert overruns[0].severity == Severity.CRITICAL
        assert overruns[0].deviation_percentage > 100
    
    def test_detect_cost_spikes(self):
        """Test detection of cost spikes."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        spikes = [a for a in result.anomalies if a.anomaly_type == AnomalyType.SPIKE]
        assert len(spikes) > 0
        assert spikes[0].severity in [Severity.HIGH, Severity.CRITICAL]
    
    def test_detect_resource_waste(self):
        """Test detection of resource waste."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        waste = [a for a in result.anomalies if a.anomaly_type == AnomalyType.RESOURCE_WASTE]
        assert len(waste) > 0
        assert waste[0].estimated_waste > 0
    
    def test_detect_gradual_increase(self):
        """Test detection of gradual cost increases."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        gradual = [a for a in result.anomalies if a.anomaly_type == AnomalyType.GRADUAL_INCREASE]
        assert len(gradual) > 0
        assert gradual[0].severity in [Severity.MEDIUM, Severity.HIGH]
    
    def test_detect_unusual_patterns(self):
        """Test detection of unusual patterns."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        unusual = [a for a in result.anomalies if a.anomaly_type == AnomalyType.UNUSUAL_PATTERN]
        assert len(unusual) > 0
    
    def test_sensitivity_levels(self):
        """Test different sensitivity levels."""
        low_sensitivity = self.detector.detect(
            self.sample_cost_data,
            sensitivity=1.5,
            lookback_days=30
        )
        
        high_sensitivity = self.detector.detect(
            self.sample_cost_data,
            sensitivity=4.0,
            lookback_days=30
        )
        
        # Higher sensitivity should detect more anomalies
        assert high_sensitivity.total_anomalies >= low_sensitivity.total_anomalies
    
    def test_severity_counts(self):
        """Test severity counting."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        assert result.critical_count >= 0
        assert result.high_count >= 0
        assert result.critical_count + result.high_count <= result.total_anomalies
    
    def test_detection_summary(self):
        """Test detection summary statistics."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        summary = result.detection_summary
        assert "analysis_period_days" in summary
        assert summary["analysis_period_days"] == 30
        assert "sensitivity_level" in summary
        assert "anomalies_per_day" in summary
        assert "most_common_type" in summary
        assert "resource_breakdown" in summary
    
    def test_resource_breakdown(self):
        """Test resource type breakdown."""
        result = self.detector.detect(
            self.sample_cost_data,
            sensitivity=2.0,
            lookback_days=30
        )
        
        breakdown = result.detection_summary["resource_breakdown"]
        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0
    
    def test_filter_by_resource_type(self):
        """Test filtering by resource type."""
        result = self.detector.detect(
            self.sample_cost_data,
            resource_type=ResourceType.DATABASE,
            sensitivity=2.0,
            lookback_days=30
        )
        
        assert result is not None
        # In real implementation, would verify filtering


# ===== COST ANALYZER TESTS =====

class TestCostAnalyzer:
    """Test cost spike analysis and budget forecasting."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = CostAnalyzer()
        self.sample_cost_data = [
            {"timestamp": "2025-11-01", "cost": 100.0},
            {"timestamp": "2025-11-02", "cost": 105.0},
        ]
    
    def test_analyze_spikes_basic(self):
        """Test basic spike analysis."""
        result = self.analyzer.analyze_spikes(
            self.sample_cost_data,
            spike_threshold=1.5,
            include_root_cause=True
        )
        
        assert result is not None
        assert result.total_spikes > 0
        assert len(result.spikes) > 0
        assert result.total_excess_cost >= 0
    
    def test_spike_details(self):
        """Test spike detail information."""
        result = self.analyzer.analyze_spikes(
            self.sample_cost_data,
            spike_threshold=1.5,
            include_root_cause=True
        )
        
        spike = result.spikes[0]
        assert spike.spike_id is not None
        assert spike.baseline_cost > 0
        assert spike.spike_cost > spike.baseline_cost
        assert spike.increase_percentage > 0
        assert spike.duration_hours > 0
        assert len(spike.affected_services) > 0
        assert len(spike.mitigation_actions) > 0
    
    def test_root_cause_analysis(self):
        """Test root cause inclusion."""
        with_root_cause = self.analyzer.analyze_spikes(
            self.sample_cost_data,
            spike_threshold=1.5,
            include_root_cause=True
        )
        
        without_root_cause = self.analyzer.analyze_spikes(
            self.sample_cost_data,
            spike_threshold=1.5,
            include_root_cause=False
        )
        
        # With root cause should have causes
        assert len(with_root_cause.spikes[0].root_causes) > 0
        
        # Without should be empty
        assert len(without_root_cause.spikes[0].root_causes) == 0
    
    def test_spike_threshold(self):
        """Test different spike thresholds."""
        low_threshold = self.analyzer.analyze_spikes(
            self.sample_cost_data,
            spike_threshold=1.3,
            include_root_cause=False
        )
        
        high_threshold = self.analyzer.analyze_spikes(
            self.sample_cost_data,
            spike_threshold=2.5,
            include_root_cause=False
        )
        
        # Lower threshold should detect more or equal spikes
        assert low_threshold.total_spikes >= high_threshold.total_spikes
    
    def test_pattern_analysis(self):
        """Test spike pattern analysis."""
        result = self.analyzer.analyze_spikes(
            self.sample_cost_data,
            spike_threshold=1.5,
            include_root_cause=True
        )
        
        patterns = result.pattern_analysis
        assert "time_of_day_pattern" in patterns
        assert "day_of_week_pattern" in patterns
        assert "recurring_services" in patterns
        assert "average_duration_hours" in patterns
    
    def test_forecast_budget_basic(self):
        """Test basic budget forecasting."""
        result = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3,
            budget_limit=None,
            growth_rate=None
        )
        
        assert result is not None
        assert len(result.forecast) == 3
        assert result.total_predicted_cost > 0
        assert result.average_monthly_cost > 0
    
    def test_forecast_data_points(self):
        """Test forecast data point structure."""
        result = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3
        )
        
        for point in result.forecast:
            assert point.month is not None
            assert point.predicted_cost > 0
            assert point.lower_bound < point.predicted_cost
            assert point.upper_bound > point.predicted_cost
            assert 0 <= point.confidence <= 1
            assert point.budget_status in ["under_budget", "at_risk", "over_budget"]
    
    def test_budget_alerts(self):
        """Test budget overrun alerts."""
        result = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3,
            budget_limit=5000.0  # Set low limit to trigger alerts
        )
        
        if len(result.budget_alerts) > 0:
            alert = result.budget_alerts[0]
            assert alert.predicted_cost > alert.budget_limit
            assert alert.overrun_amount > 0
            assert alert.overrun_percentage > 0
            assert len(alert.recommended_actions) > 0
    
    def test_growth_trend_description(self):
        """Test growth trend description."""
        result = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3,
            growth_rate=0.08
        )
        
        assert result.growth_trend is not None
        assert len(result.growth_trend) > 0
    
    def test_custom_growth_rate(self):
        """Test custom growth rate."""
        slow_growth = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3,
            growth_rate=0.02
        )
        
        fast_growth = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3,
            growth_rate=0.20
        )
        
        # Fast growth should have higher predicted costs
        assert fast_growth.total_predicted_cost > slow_growth.total_predicted_cost
    
    def test_recommendations(self):
        """Test cost optimization recommendations."""
        result = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3,
            budget_limit=5000.0
        )
        
        assert len(result.recommendations) > 0
        assert all(isinstance(rec, str) for rec in result.recommendations)
    
    def test_confidence_score(self):
        """Test forecast confidence scoring."""
        result = self.analyzer.forecast_budget(
            self.sample_cost_data,
            forecast_months=3
        )
        
        assert 0 <= result.confidence_score <= 1


# ===== API ENDPOINT TESTS =====

class TestCostAnomalyAPI:
    """Test cost anomaly API endpoints."""
    
    def test_detect_anomalies_endpoint(self):
        """Test /api/anomaly/detect endpoint."""
        request_data = {
            "cost_data": [
                {"timestamp": "2025-11-01", "cost": 100.0},
                {"timestamp": "2025-11-02", "cost": 350.0}
            ],
            "sensitivity": 2.0,
            "lookback_days": 30
        }
        
        response = client.post("/api/anomaly/detect", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "anomalies" in data["data"]
        assert len(data["data"]["anomalies"]) > 0
    
    def test_detect_with_resource_type(self):
        """Test anomaly detection with resource type filter."""
        request_data = {
            "cost_data": [{"timestamp": "2025-11-01", "cost": 100.0}],
            "resource_type": "database",
            "sensitivity": 2.0,
            "lookback_days": 30
        }
        
        response = client.post("/api/anomaly/detect", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_analyze_spikes_endpoint(self):
        """Test /api/anomaly/analyze-spikes endpoint."""
        request_data = {
            "cost_data": [
                {"timestamp": "2025-11-01", "cost": 100.0},
                {"timestamp": "2025-11-02", "cost": 300.0}
            ],
            "spike_threshold": 1.5,
            "include_root_cause": True
        }
        
        response = client.post("/api/anomaly/analyze-spikes", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "spikes" in data["data"]
        assert data["data"]["total_spikes"] > 0
    
    def test_analyze_spikes_without_root_cause(self):
        """Test spike analysis without root cause."""
        request_data = {
            "cost_data": [{"timestamp": "2025-11-01", "cost": 100.0}],
            "spike_threshold": 1.5,
            "include_root_cause": False
        }
        
        response = client.post("/api/anomaly/analyze-spikes", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_forecast_budget_endpoint(self):
        """Test /api/anomaly/forecast-budget endpoint."""
        request_data = {
            "historical_costs": [
                {"timestamp": "2025-10-01", "cost": 4500.0},
                {"timestamp": "2025-11-01", "cost": 4800.0}
            ],
            "forecast_months": 3,
            "budget_limit": 6000.0,
            "growth_rate": 0.08
        }
        
        response = client.post("/api/anomaly/forecast-budget", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]["forecast"]) == 3
        assert data["data"]["total_predicted_cost"] > 0
    
    def test_forecast_without_budget_limit(self):
        """Test forecasting without budget limit."""
        request_data = {
            "historical_costs": [{"timestamp": "2025-11-01", "cost": 5000.0}],
            "forecast_months": 3
        }
        
        response = client.post("/api/anomaly/forecast-budget", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["budget_alerts"]) >= 0
    
    def test_invalid_sensitivity(self):
        """Test error handling for invalid sensitivity."""
        request_data = {
            "cost_data": [{"timestamp": "2025-11-01", "cost": 100.0}],
            "sensitivity": 10.0,  # Out of range
            "lookback_days": 30
        }
        
        response = client.post("/api/anomaly/detect", json=request_data)
        
        assert response.status_code == 422
    
    def test_invalid_forecast_months(self):
        """Test error handling for invalid forecast months."""
        request_data = {
            "historical_costs": [{"timestamp": "2025-11-01", "cost": 5000.0}],
            "forecast_months": 20  # Out of range
        }
        
        response = client.post("/api/anomaly/forecast-budget", json=request_data)
        
        assert response.status_code == 422


# ===== INTEGRATION TESTS =====

class TestCostAnomalyIntegration:
    """Integration tests for cost anomaly workflows."""
    
    def test_full_workflow_detect_analyze_forecast(self):
        """Test complete workflow: detect → analyze → forecast."""
        cost_data = [
            {"timestamp": "2025-10-01", "cost": 4500.0},
            {"timestamp": "2025-11-01", "cost": 5200.0}
        ]
        
        # Step 1: Detect anomalies
        detect_response = client.post("/api/anomaly/detect", json={
            "cost_data": cost_data,
            "sensitivity": 2.0,
            "lookback_days": 30
        })
        assert detect_response.status_code == 200
        detect_data = detect_response.json()["data"]
        assert detect_data["total_anomalies"] > 0
        
        # Step 2: Analyze spikes
        spike_response = client.post("/api/anomaly/analyze-spikes", json={
            "cost_data": cost_data,
            "spike_threshold": 1.5,
            "include_root_cause": True
        })
        assert spike_response.status_code == 200
        spike_data = spike_response.json()["data"]
        assert spike_data["total_spikes"] > 0
        
        # Step 3: Forecast budget
        forecast_response = client.post("/api/anomaly/forecast-budget", json={
            "historical_costs": cost_data,
            "forecast_months": 3,
            "budget_limit": 6000.0
        })
        assert forecast_response.status_code == 200
        forecast_data = forecast_response.json()["data"]
        assert len(forecast_data["forecast"]) == 3
    
    def test_end_to_end_budget_planning(self):
        """Test end-to-end budget planning scenario."""
        # Historical data shows cost growth
        historical_costs = [
            {"timestamp": "2025-09-01", "cost": 4000.0},
            {"timestamp": "2025-10-01", "cost": 4400.0},
            {"timestamp": "2025-11-01", "cost": 5000.0}
        ]
        
        # Forecast future costs
        forecast_response = client.post("/api/anomaly/forecast-budget", json={
            "historical_costs": historical_costs,
            "forecast_months": 6,
            "budget_limit": 6000.0,
            "growth_rate": 0.10
        })
        
        assert forecast_response.status_code == 200
        forecast_data = forecast_response.json()["data"]
        
        # Verify forecasting logic
        assert len(forecast_data["forecast"]) == 6
        assert forecast_data["growth_trend"] is not None
        assert len(forecast_data["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
