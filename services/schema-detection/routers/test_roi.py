"""
ROI Dashboard Tests - Phase 3.6
40+ comprehensive test cases covering all 6 endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from main import app

client = TestClient(app)

# Test data constants
ORG_ID = "test-org-123"
START_DATE = "2024-05-01"
END_DATE = "2024-11-30"


class TestCalculateValue:
    """Test suite for POST /api/roi/calculate-value (10 tests)"""
    
    def test_calculate_value_basic(self):
        """Test basic ROI calculation with required fields"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {
                "start_date": START_DATE,
                "end_date": END_DATE
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "calculation_id" in data["data"]
        assert "total_value" in data["data"]
        assert "roi_metrics" in data["data"]
        assert "value_categories" in data["data"]
    
    def test_calculate_value_with_options(self):
        """Test ROI calculation with analysis options"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {
                "start_date": START_DATE,
                "end_date": END_DATE
            },
            "analysis_options": {
                "include_projections": True,
                "confidence_level": "high",
                "currency": "USD"
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["time_period"]["duration_months"] == 7
    
    def test_cost_savings_category(self):
        """Test cost savings breakdown is present"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        categories = response.json()["data"]["value_categories"]
        assert "cost_savings" in categories
        cost_savings = categories["cost_savings"]
        assert cost_savings["total_value"] == 795000
        assert cost_savings["monthly_average"] > 0
        assert cost_savings["percentage_of_total"] == 20
        assert "breakdown" in cost_savings
        assert "infrastructure_optimization" in cost_savings["breakdown"]
    
    def test_time_savings_category(self):
        """Test time savings breakdown includes key areas"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        categories = response.json()["data"]["value_categories"]
        time_savings = categories["time_savings"]
        assert time_savings["total_value"] == 1170000
        assert time_savings["percentage_of_total"] == 29
        assert "automated_schema_design" in time_savings["breakdown"]
        assert "migration_planning" in time_savings["breakdown"]
        assert "incident_response" in time_savings["breakdown"]
    
    def test_risk_reduction_category(self):
        """Test risk reduction has compliance and security metrics"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        categories = response.json()["data"]["value_categories"]
        risk_reduction = categories["risk_reduction"]
        assert risk_reduction["total_value"] == 1450000
        assert risk_reduction["percentage_of_total"] == 36
        assert "compliance_fines_avoided" in risk_reduction["breakdown"]
        assert "data_breach_prevention" in risk_reduction["breakdown"]
    
    def test_productivity_gains_category(self):
        """Test productivity gains category breakdown"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        categories = response.json()["data"]["value_categories"]
        productivity = categories["productivity_gain"]
        assert productivity["total_value"] == 585000
        assert productivity["percentage_of_total"] == 15
        assert "developer_efficiency" in productivity["breakdown"]
    
    def test_roi_metrics_structure(self):
        """Test ROI metrics contain all required financial indicators"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        metrics = response.json()["data"]["roi_metrics"]
        assert "total_investment" in metrics
        assert "roi_percentage" in metrics
        assert metrics["roi_percentage"] == 3903
        assert "roi_ratio" in metrics
        assert metrics["roi_ratio"] == 40.03
        assert "payback_period_months" in metrics
        assert metrics["payback_period_months"] == 1
        assert "npv" in metrics
        assert "irr" in metrics
    
    def test_key_achievements_present(self):
        """Test key achievements with baseline/current/impact"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        achievements = response.json()["data"]["key_achievements"]
        assert len(achievements) == 5
        first = achievements[0]
        assert "achievement" in first
        assert "baseline" in first
        assert "current" in first
        assert "impact_value" in first
        assert "confidence_level" in first
    
    def test_adoption_metrics(self):
        """Test adoption metrics contain user satisfaction data"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        adoption = response.json()["data"]["adoption_metrics"]
        assert adoption["total_users"] == 30
        assert adoption["active_users"] == 25
        assert adoption["adoption_rate"] == 83
        assert adoption["satisfaction_score"] == 4.7
        assert adoption["nps_score"] == 62
    
    def test_methodology_confidence(self):
        """Test confidence breakdown by methodology type"""
        response = client.post("/api/roi/calculate-value", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE}
        })
        confidence = response.json()["data"]["methodology_confidence"]
        assert confidence["high_confidence_percentage"] == 83
        assert confidence["medium_confidence_percentage"] == 14
        assert confidence["low_confidence_percentage"] == 3
        assert "explanation" in confidence


class TestTimeSeries:
    """Test suite for GET /api/roi/time-series (8 tests)"""
    
    def test_time_series_basic(self):
        """Test basic time series request"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "time_series" in data["data"]
        assert len(data["data"]["time_series"]) == 7  # 7 months
    
    def test_time_series_monthly_values(self):
        """Test monthly value progression"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}"
        )
        time_series = response.json()["data"]["time_series"]
        first_month = time_series[0]
        last_month = time_series[-1]
        assert first_month["monthly_value"] == 185000
        assert last_month["monthly_value"] == 670000
        assert last_month["monthly_value"] > first_month["monthly_value"]
    
    def test_time_series_cumulative_growth(self):
        """Test cumulative value tracking"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}"
        )
        time_series = response.json()["data"]["time_series"]
        cumulative_values = [point["cumulative_value"] for point in time_series]
        # Cumulative should always increase
        assert all(cumulative_values[i] <= cumulative_values[i+1] for i in range(len(cumulative_values)-1))
        assert cumulative_values[-1] == 3345000
    
    def test_time_series_roi_progression(self):
        """Test ROI percentage growth over time"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}"
        )
        time_series = response.json()["data"]["time_series"]
        first_roi = time_series[0]["roi_percentage"]
        last_roi = time_series[-1]["roi_percentage"]
        assert first_roi == 85
        assert last_roi == 3245
        assert last_roi > first_roi
    
    def test_time_series_feature_adoption(self):
        """Test active features and adoption rate tracking"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}"
        )
        time_series = response.json()["data"]["time_series"]
        first_month = time_series[0]
        last_month = time_series[-1]
        assert first_month["active_features"] == 3
        assert last_month["active_features"] == 12
        assert first_month["adoption_rate"] == 40
        assert last_month["adoption_rate"] == 92
    
    def test_growth_metrics(self):
        """Test growth metrics calculation"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}"
        )
        growth = response.json()["data"]["growth_metrics"]
        assert growth["month_over_month_growth"] == 14.2
        assert growth["total_growth_percentage"] == 262
        assert growth["average_monthly_value"] == 478000
        assert "peak_month" in growth
        assert "lowest_month" in growth
    
    def test_projections(self):
        """Test future projections with confidence intervals"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}"
        )
        projections = response.json()["data"]["projections"]["next_3_months"]
        assert len(projections) == 3
        first_projection = projections[0]
        assert first_projection["period"] == "2024-12"
        assert first_projection["projected_value"] == 750000
        assert "confidence_interval" in first_projection
        assert "upper_bound" in first_projection["confidence_interval"]
        assert "lower_bound" in first_projection["confidence_interval"]
    
    def test_quarterly_granularity(self):
        """Test quarterly granularity option"""
        response = client.get(
            f"/api/roi/time-series?organization_id={ORG_ID}&start_date={START_DATE}&end_date={END_DATE}&granularity=quarterly"
        )
        assert response.status_code == 200
        # Should have fewer data points than monthly
        time_series = response.json()["data"]["time_series"]
        assert len(time_series) < 7


class TestFeatureAnalysis:
    """Test suite for GET /api/roi/by-feature (8 tests)"""
    
    def test_feature_analysis_basic(self):
        """Test basic feature analysis request"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "features" in data["data"]
        assert len(data["data"]["features"]) == 8
    
    def test_feature_ranking(self):
        """Test features are ranked by value contribution"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}")
        features = response.json()["data"]["features"]
        # Top feature should be PII Detection
        assert features[0]["feature_id"] == "FEAT-001"
        assert features[0]["name"] == "PII Detection & Anonymization"
        assert features[0]["percentage_of_total"] == 32.5
        # Features should be in descending value order
        percentages = [f["percentage_of_total"] for f in features]
        assert percentages == sorted(percentages, reverse=True)
    
    def test_pii_detection_metrics(self):
        """Test PII Detection feature metrics"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}")
        pii_feature = response.json()["data"]["features"][0]
        assert pii_feature["value_delivered"] == 1300000
        assert pii_feature["roi_percentage"] == 3426
        assert pii_feature["adoption_rate"] == 95
        assert pii_feature["user_satisfaction"] == 4.8
        # Check usage metrics
        usage = pii_feature["usage_metrics"]
        assert usage["total_scans"] == 247
        assert usage["pii_fields_detected"] == 4453
    
    def test_migration_planner_metrics(self):
        """Test Migration Planner has highest adoption"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}")
        features = response.json()["data"]["features"]
        migration = next(f for f in features if f["feature_id"] == "FEAT-002")
        assert migration["adoption_rate"] == 100
        assert migration["user_satisfaction"] == 4.9  # Highest satisfaction
        assert migration["usage_metrics"]["successful_migrations"] == 47
        assert migration["usage_metrics"]["failed_migrations"] == 0
    
    def test_feature_value_breakdown(self):
        """Test feature value breakdown by category"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}")
        pii_feature = response.json()["data"]["features"][0]
        breakdown = pii_feature["value_breakdown"]
        assert "cost_savings" in breakdown
        assert "time_savings" in breakdown
        assert "risk_reduction" in breakdown
        # Risk reduction should be highest for PII Detection
        assert breakdown["risk_reduction"] > breakdown["cost_savings"]
    
    def test_feature_satisfaction_scores(self):
        """Test all features have satisfaction scores"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}")
        features = response.json()["data"]["features"]
        for feature in features:
            assert "user_satisfaction" in feature
            assert 1.0 <= feature["user_satisfaction"] <= 5.0
            assert "adoption_rate" in feature
            assert 0 <= feature["adoption_rate"] <= 100
    
    def test_feature_analysis_summary(self):
        """Test summary statistics"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}")
        summary = response.json()["data"]["summary"]
        assert summary["total_value"] == 4003000
        assert summary["total_features"] == 8
        assert summary["average_roi_percentage"] == 1568
        assert summary["highest_roi_feature"] == "PII Detection & Anonymization"
        assert summary["most_adopted_feature"] == "Cross-Cloud Migration Planner"
        assert summary["highest_satisfaction_feature"] == "Cross-Cloud Migration Planner"
    
    def test_custom_time_period(self):
        """Test custom time period parameter"""
        response = client.get(f"/api/roi/by-feature?organization_id={ORG_ID}&time_period_months=12")
        assert response.status_code == 200
        data = response.json()
        # Should still return all 8 features
        assert len(data["data"]["features"]) == 8


class TestCompetitiveAnalysis:
    """Test suite for POST /api/roi/competitive-analysis (8 tests)"""
    
    def test_competitive_analysis_all_competitors(self):
        """Test analysis against all competitors"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["collibra", "onetrust", "erwin", "manual"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "schemasage_metrics" in data["data"]
        assert len(data["data"]["alternatives"]) == 4
    
    def test_schemasage_metrics(self):
        """Test SchemaSage baseline metrics"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["collibra"]
        })
        metrics = response.json()["data"]["schemasage_metrics"]
        assert metrics["annual_cost"] == 100000
        assert metrics["implementation_months"] == 1.5
        assert metrics["value_delivered"] == 4000000
        assert metrics["roi_percentage"] == 3903
        assert metrics["features_count"] == 12
        assert metrics["satisfaction_score"] == 4.7
    
    def test_collibra_comparison(self):
        """Test comparison against Collibra"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["collibra"]
        })
        alternatives = response.json()["data"]["alternatives"]
        collibra = alternatives[0]
        assert collibra["name"] == "Collibra Data Governance"
        assert collibra["annual_cost"] == 250000
        assert collibra["implementation_months"] == 12
        # Cost comparison
        cost_comp = collibra["cost_comparison"]
        assert cost_comp["annual_savings"] == 150000
        assert cost_comp["savings_percentage"] == 60
        # Advantages
        assert len(collibra["schemasage_advantages"]) >= 5
        assert any("10x faster" in adv for adv in collibra["schemasage_advantages"])
    
    def test_onetrust_comparison(self):
        """Test comparison against OneTrust"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["onetrust"]
        })
        onetrust = response.json()["data"]["alternatives"][0]
        assert onetrust["name"] == "OneTrust DataDiscovery"
        assert onetrust["annual_cost"] == 180000
        cost_comp = onetrust["cost_comparison"]
        assert cost_comp["savings_percentage"] == 44
        assert any("15x higher ROI" in adv for adv in onetrust["schemasage_advantages"])
    
    def test_erwin_comparison(self):
        """Test comparison against Erwin"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["erwin"]
        })
        erwin = response.json()["data"]["alternatives"][0]
        assert erwin["name"] == "Erwin Data Modeler Enterprise"
        assert erwin["annual_cost"] == 95000
        # Erwin is cheaper but less features
        assert erwin["features_count"] == 1
        assert any("20x higher ROI" in adv for adv in erwin["schemasage_advantages"])
        assert any("cloud-native" in adv.lower() for adv in erwin["schemasage_advantages"])
    
    def test_manual_comparison(self):
        """Test comparison against manual processes"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["manual"]
        })
        manual = response.json()["data"]["alternatives"][0]
        assert manual["name"] == "Manual Schema Design Process"
        assert manual["annual_cost"] == 0
        time_comp = manual["time_comparison"]
        assert time_comp["hours_saved_per_year"] == 1950
        assert time_comp["efficiency_gain_percentage"] == 81
        assert any("95% error reduction" in adv for adv in manual["schemasage_advantages"])
    
    def test_feature_comparison(self):
        """Test feature comparison lists"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["collibra"]
        })
        collibra = response.json()["data"]["alternatives"][0]
        feature_comp = collibra["feature_comparison"]
        assert "schemasage_has_but_alternative_lacks" in feature_comp
        assert "alternative_has_but_schemasage_lacks" in feature_comp
        # SchemaSage should have AI features Collibra lacks
        assert len(feature_comp["schemasage_has_but_alternative_lacks"]) >= 3
    
    def test_competitive_summary(self):
        """Test competitive summary statistics"""
        response = client.post("/api/roi/competitive-analysis", json={
            "organization_id": ORG_ID,
            "alternatives": ["collibra", "onetrust", "erwin"]
        })
        summary = response.json()["data"]["competitive_summary"]
        assert "average_competitor_cost" in summary
        assert "average_savings" in summary
        assert "roi_advantage_percentage" in summary
        assert summary["roi_advantage_percentage"] == 1652
        assert "key_advantages" in summary
        assert len(summary["key_advantages"]) >= 3


class TestExportGeneration:
    """Test suite for export endpoints (6 tests)"""
    
    def test_export_pdf_generation(self):
        """Test PDF export request"""
        response = client.post("/api/roi/export-summary", json={
            "organization_id": ORG_ID,
            "time_period": {
                "start_date": START_DATE,
                "end_date": END_DATE
            },
            "export_options": {
                "format": "pdf",
                "include_charts": True,
                "sections": ["executive_summary", "value_breakdown", "feature_analysis"]
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "export_id" in data["data"]
        assert data["data"]["status"] == "processing"
        assert data["data"]["format"] == "pdf"
        assert data["data"]["estimated_completion_seconds"] == 15
    
    def test_export_excel_generation(self):
        """Test Excel export request"""
        response = client.post("/api/roi/export-summary", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE},
            "export_options": {
                "format": "excel",
                "include_charts": False
            }
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["format"] == "excel"
        assert data["status"] == "processing"
    
    def test_export_with_branding(self):
        """Test export with custom branding"""
        response = client.post("/api/roi/export-summary", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE},
            "export_options": {"format": "pdf"},
            "branding": {
                "company_name": "Test Corp",
                "logo_url": "https://example.com/logo.png",
                "primary_color": "#0066CC"
            }
        })
        assert response.status_code == 200
        assert response.json()["data"]["page_count_estimate"] == 18
    
    def test_export_status_completed(self):
        """Test export status check after completion"""
        # First generate export
        create_response = client.post("/api/roi/export-summary", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE},
            "export_options": {"format": "pdf"}
        })
        export_id = create_response.json()["data"]["export_id"]
        
        # Check status
        status_response = client.get(f"/api/roi/export-summary/{export_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()["data"]
        assert status_data["status"] == "completed"
        assert "download_url" in status_data
        assert "expiry_timestamp" in status_data
        assert status_data["file_size_bytes"] == 4567890
        assert status_data["page_count"] == 17
    
    def test_export_sections_generated(self):
        """Test sections_generated array in status"""
        create_response = client.post("/api/roi/export-summary", json={
            "organization_id": ORG_ID,
            "time_period": {"start_date": START_DATE, "end_date": END_DATE},
            "export_options": {"format": "pdf"}
        })
        export_id = create_response.json()["data"]["export_id"]
        
        status_response = client.get(f"/api/roi/export-summary/{export_id}/status")
        sections = status_response.json()["data"]["sections_generated"]
        assert len(sections) == 6
        # Check executive summary section
        exec_summary = next(s for s in sections if s["section_name"] == "executive_summary")
        assert exec_summary["pages"] == 2
        assert exec_summary["charts_count"] == 3
    
    def test_export_not_found(self):
        """Test export status for non-existent ID"""
        response = client.get("/api/roi/export-summary/nonexistent-id/status")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
