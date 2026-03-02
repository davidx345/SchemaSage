"""
Comprehensive test suite for Schema Debt Tracker feature.
Tests antipattern detection, technical debt calculation, and ROI-based prioritization.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from main import app
from models.debt_models import (
    AntipatternDetectionRequest, TechnicalDebtRequest, PrioritizationRequest,
    DatabaseType, AntipatternType, Severity, Priority
)
from core.debt import AntipatternDetector, ROICalculator

client = TestClient(app)

# ===== ANTIPATTERN DETECTOR TESTS =====

class TestAntipatternDetector:
    """Test antipattern detection core logic."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = AntipatternDetector()
    
    def test_detect_missing_indexes(self):
        """Test detection of missing indexes."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            "public",
            True
        )
        
        assert result is not None
        assert len(result.antipatterns) > 0
        
        # Check for missing index antipatterns
        missing_indexes = [a for a in result.antipatterns if a.antipattern_type == AntipatternType.MISSING_INDEX]
        assert len(missing_indexes) > 0
        assert missing_indexes[0].severity in [Severity.HIGH, Severity.MEDIUM]
        assert missing_indexes[0].auto_fix_sql is not None
    
    def test_detect_no_foreign_keys(self):
        """Test detection of missing foreign keys."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        no_fk_antipatterns = [a for a in result.antipatterns if a.antipattern_type == AntipatternType.NO_FOREIGN_KEY]
        assert len(no_fk_antipatterns) > 0
        assert no_fk_antipatterns[0].severity == Severity.CRITICAL
        assert "FOREIGN KEY" in no_fk_antipatterns[0].auto_fix_sql
    
    def test_detect_denormalization(self):
        """Test detection of denormalization issues."""
        result = self.detector.detect(
            DatabaseType.MYSQL,
            "mysql://localhost/test"
        )
        
        denorm_antipatterns = [a for a in result.antipatterns if a.antipattern_type == AntipatternType.DENORMALIZATION]
        assert len(denorm_antipatterns) > 0
        assert denorm_antipatterns[0].severity in [Severity.MEDIUM, Severity.LOW]
    
    def test_detect_poor_naming(self):
        """Test detection of poor naming conventions."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        naming_antipatterns = [a for a in result.antipatterns if a.antipattern_type == AntipatternType.POOR_NAMING]
        assert len(naming_antipatterns) > 0
        assert naming_antipatterns[0].severity == Severity.LOW
        assert naming_antipatterns[0].auto_fix_sql is not None
    
    def test_detect_no_primary_key(self):
        """Test detection of missing primary keys."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        no_pk_antipatterns = [a for a in result.antipatterns if a.antipattern_type == AntipatternType.NO_PRIMARY_KEY]
        assert len(no_pk_antipatterns) > 0
        assert no_pk_antipatterns[0].severity == Severity.CRITICAL
    
    def test_detect_wide_tables(self):
        """Test detection of excessively wide tables."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        wide_table_antipatterns = [a for a in result.antipatterns if a.antipattern_type == AntipatternType.WIDE_TABLES]
        assert len(wide_table_antipatterns) > 0
        assert wide_table_antipatterns[0].severity in [Severity.MEDIUM, Severity.LOW]
    
    def test_technical_debt_calculation(self):
        """Test technical debt hours and cost calculation."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        assert result.total_debt_hours > 0
        assert result.total_debt_cost > 0
        assert result.total_debt_cost == result.total_debt_hours * 75.0  # Default hourly rate
    
    def test_recommendations_included(self):
        """Test that recommendations are included when requested."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            include_recommendations=True
        )
        
        for antipattern in result.antipatterns:
            assert antipattern.recommendation is not None
            assert len(antipattern.recommendation) > 0
    
    def test_recommendations_excluded(self):
        """Test that recommendations can be excluded."""
        result = self.detector.detect(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            include_recommendations=False
        )
        
        for antipattern in result.antipatterns:
            assert antipattern.recommendation is None or antipattern.recommendation == ""
    
    def test_mysql_detection(self):
        """Test antipattern detection for MySQL databases."""
        result = self.detector.detect(
            DatabaseType.MYSQL,
            "mysql://localhost/test"
        )
        
        assert result is not None
        assert len(result.antipatterns) > 0
        assert result.total_debt_hours > 0


# ===== ROI CALCULATOR TESTS =====

class TestROICalculator:
    """Test technical debt calculation and prioritization."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = ROICalculator()
    
    def test_calculate_debt_basic(self):
        """Test basic technical debt calculation."""
        result = self.calculator.calculate_debt(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        assert result.total_debt_hours > 0
        assert result.total_debt_cost > 0
        assert len(result.debt_items) > 0
        assert len(result.debt_by_category) > 0
    
    def test_calculate_debt_with_custom_rate(self):
        """Test debt calculation with custom hourly rate."""
        custom_rate = 100.0
        result = self.calculator.calculate_debt(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            hourly_rate=custom_rate
        )
        
        # Verify cost calculations use custom rate
        for item in result.debt_items:
            assert item.cost == item.effort_hours * custom_rate
    
    def test_calculate_debt_with_team_size(self):
        """Test debt calculation considers team size."""
        result = self.calculator.calculate_debt(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            team_size=10
        )
        
        assert "team_capacity_impact_weeks" in result.roi_metrics
        assert result.roi_metrics["team_capacity_impact_weeks"] > 0
    
    def test_debt_categorization(self):
        """Test debt items are properly categorized."""
        result = self.calculator.calculate_debt(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        # Verify categories exist
        categories = {cat.category for cat in result.debt_by_category}
        assert "performance" in categories
        assert "data_integrity" in categories
        assert "security" in categories
        
        # Verify category totals
        total_hours = sum(cat.total_hours for cat in result.debt_by_category)
        assert total_hours == result.total_debt_hours
    
    def test_debt_timeline(self):
        """Test debt timeline generation."""
        result = self.calculator.calculate_debt(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        timeline = result.debt_timeline
        assert timeline.immediate["hours"] >= 0
        assert timeline.short_term["hours"] >= 0
        assert timeline.medium_term["hours"] >= 0
        assert timeline.long_term["hours"] >= 0
        
        # Sum should equal total debt
        total_timeline = (
            timeline.immediate["hours"] +
            timeline.short_term["hours"] +
            timeline.medium_term["hours"] +
            timeline.long_term["hours"]
        )
        assert abs(total_timeline - result.total_debt_hours) < 0.01
    
    def test_roi_metrics(self):
        """Test ROI metrics calculation."""
        result = self.calculator.calculate_debt(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        metrics = result.roi_metrics
        assert "total_investment" in metrics
        assert "estimated_annual_savings" in metrics
        assert "payback_period_months" in metrics
        assert metrics["total_investment"] > 0
        assert metrics["estimated_annual_savings"] > 0
        assert metrics["payback_period_months"] > 0
    
    def test_interest_rate(self):
        """Test technical debt interest rate calculation."""
        result = self.calculator.calculate_debt(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        assert result.interest_rate > 0
        assert result.interest_rate < 1.0  # Should be less than 100%
    
    def test_prioritize_basic(self):
        """Test basic prioritization."""
        result = self.calculator.prioritize(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        assert len(result.prioritized_items) > 0
        assert len(result.sprint_recommendations) > 0
        assert result.roi_analysis is not None
    
    def test_prioritize_by_business_priorities(self):
        """Test prioritization respects business priorities."""
        result = self.calculator.prioritize(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            business_priorities=["security", "performance"]
        )
        
        # Higher priority items should appear first
        priorities = [item.priority for item in result.prioritized_items]
        assert Priority.P0_URGENT in priorities or Priority.P1_HIGH in priorities
        
        # Verify sorting
        for i in range(len(priorities) - 1):
            assert priorities[i].value <= priorities[i + 1].value
    
    def test_sprint_recommendations(self):
        """Test sprint planning recommendations."""
        hours_per_sprint = 80
        result = self.calculator.prioritize(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            available_hours_per_sprint=hours_per_sprint
        )
        
        for sprint in result.sprint_recommendations:
            assert sprint.total_hours <= hours_per_sprint * 1.2  # Allow 20% buffer
            assert len(sprint.items) > 0
            assert sprint.sprint_number > 0
            assert sprint.total_cost_savings >= 0
    
    def test_quick_wins_identification(self):
        """Test identification of quick wins."""
        result = self.calculator.prioritize(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        for quick_win in result.quick_wins:
            assert quick_win.roi_score > 500  # High ROI
            assert quick_win.effort_hours <= 12  # Low effort
    
    def test_critical_path(self):
        """Test critical path identification."""
        result = self.calculator.prioritize(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        assert len(result.critical_path) > 0
        
        # Verify all critical path items are P0
        p0_items = [item for item in result.prioritized_items if item.priority == Priority.P0_URGENT]
        assert len(result.critical_path) == len(p0_items)
    
    def test_deferred_items(self):
        """Test deferred items identification."""
        result = self.calculator.prioritize(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        for deferred in result.deferred_items:
            assert deferred.priority == Priority.P3_LOW
    
    def test_roi_analysis(self):
        """Test 3-year ROI analysis."""
        result = self.calculator.prioritize(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        roi = result.roi_analysis
        assert roi.total_investment > 0
        assert roi.expected_savings_year_1 > 0
        assert roi.expected_savings_year_2 > roi.expected_savings_year_1  # Should grow
        assert roi.expected_savings_year_3 > roi.expected_savings_year_2
        assert roi.payback_period_months > 0
        assert roi.roi_percentage != 0


# ===== API ENDPOINT TESTS =====

class TestDebtTrackerAPI:
    """Test debt tracker API endpoints."""
    
    def test_detect_antipatterns_endpoint(self):
        """Test /api/debt/detect-antipatterns endpoint."""
        request_data = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "schema_name": "public",
            "include_recommendations": True
        }
        
        response = client.post("/api/debt/detect-antipatterns", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "antipatterns" in data["data"]
        assert len(data["data"]["antipatterns"]) > 0
    
    def test_detect_antipatterns_without_recommendations(self):
        """Test antipattern detection without recommendations."""
        request_data = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "include_recommendations": False
        }
        
        response = client.post("/api/debt/detect-antipatterns", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_calculate_debt_endpoint(self):
        """Test /api/debt/calculate-debt endpoint."""
        request_data = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "team_size": 5,
            "hourly_rate": 75.0
        }
        
        response = client.post("/api/debt/calculate-debt", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total_debt_hours"] > 0
        assert data["data"]["total_debt_cost"] > 0
        assert len(data["data"]["debt_items"]) > 0
    
    def test_calculate_debt_with_schema(self):
        """Test debt calculation with specific schema."""
        request_data = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "schema_name": "public"
        }
        
        response = client.post("/api/debt/calculate-debt", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_prioritize_endpoint(self):
        """Test /api/debt/prioritize endpoint."""
        request_data = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "business_priorities": ["performance", "security", "reliability"],
            "available_hours_per_sprint": 80
        }
        
        response = client.post("/api/debt/prioritize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]["prioritized_items"]) > 0
        assert len(data["data"]["sprint_recommendations"]) > 0
        assert "roi_analysis" in data["data"]
    
    def test_prioritize_default_priorities(self):
        """Test prioritization with default business priorities."""
        request_data = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test"
        }
        
        response = client.post("/api/debt/prioritize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_invalid_database_type(self):
        """Test error handling for invalid database type."""
        request_data = {
            "database_type": "invalid_db",
            "connection_string": "invalid://localhost/test"
        }
        
        response = client.post("/api/debt/detect-antipatterns", json=request_data)
        
        # Should return 422 for validation error
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test error handling for missing required fields."""
        request_data = {
            "database_type": "postgresql"
            # Missing connection_string
        }
        
        response = client.post("/api/debt/calculate-debt", json=request_data)
        
        assert response.status_code == 422


# ===== INTEGRATION TESTS =====

class TestDebtTrackerIntegration:
    """Integration tests for debt tracker workflows."""
    
    def test_full_workflow_detect_calculate_prioritize(self):
        """Test complete workflow: detect → calculate → prioritize."""
        # Step 1: Detect antipatterns
        detect_request = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "include_recommendations": True
        }
        detect_response = client.post("/api/debt/detect-antipatterns", json=detect_request)
        assert detect_response.status_code == 200
        
        # Step 2: Calculate debt
        calc_request = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "team_size": 5,
            "hourly_rate": 75.0
        }
        calc_response = client.post("/api/debt/calculate-debt", json=calc_request)
        assert calc_response.status_code == 200
        calc_data = calc_response.json()["data"]
        assert calc_data["total_debt_hours"] > 0
        
        # Step 3: Prioritize fixes
        prioritize_request = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test",
            "business_priorities": ["security", "performance"],
            "available_hours_per_sprint": 80
        }
        prioritize_response = client.post("/api/debt/prioritize", json=prioritize_request)
        assert prioritize_response.status_code == 200
        prioritize_data = prioritize_response.json()["data"]
        
        # Verify workflow consistency
        assert len(prioritize_data["prioritized_items"]) > 0
        assert len(prioritize_data["sprint_recommendations"]) > 0
        assert prioritize_data["roi_analysis"]["total_investment"] > 0
    
    def test_consistent_debt_calculation(self):
        """Test that debt calculations are consistent across calls."""
        request_data = {
            "database_type": "postgresql",
            "connection_string": "postgresql://localhost/test"
        }
        
        response1 = client.post("/api/debt/calculate-debt", json=request_data)
        response2 = client.post("/api/debt/calculate-debt", json=request_data)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Results should be consistent (simulated data)
        data1 = response1.json()["data"]
        data2 = response2.json()["data"]
        assert data1["total_debt_hours"] == data2["total_debt_hours"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
