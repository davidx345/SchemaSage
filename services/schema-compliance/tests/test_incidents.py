"""
Comprehensive tests for Phase 3.5 - Database Incident Timeline
40+ test cases covering all 5 endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)


# ===== Event Correlation Tests (10+ test cases) =====

class TestEventCorrelation:
    """Test incident-event correlation endpoint"""
    
    def test_correlate_events_success(self):
        """Test successful event correlation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["deployments", "migrations", "config_changes", "traffic_spikes"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        correlation_data = data["data"]
        assert "incident" in correlation_data
        assert correlation_data["incident"]["incident_id"] == "INC-2024-11-24-001"
    
    def test_correlate_events_deployment(self):
        """Test deployment event correlation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["deployments"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        correlation_data = data["data"]
        
        assert "correlated_events" in correlation_data
        events = correlation_data["correlated_events"]
        
        deployment_events = [e for e in events if e["event_type"] == "deployment"]
        if deployment_events:
            event = deployment_events[0]
            assert event["correlation_score"] >= 0
            assert event["correlation_score"] <= 100
            assert "time_before_incident" in event
    
    def test_correlate_events_migration(self):
        """Test migration event correlation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["migrations"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        correlation_data = data["data"]
        
        events = correlation_data["correlated_events"]
        migration_events = [e for e in events if e["event_type"] == "migration"]
        
        if migration_events:
            assert migration_events[0]["correlation_score"] >= 0
    
    def test_correlate_events_traffic_spike(self):
        """Test traffic spike correlation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["traffic_spikes"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        correlation_data = data["data"]
        
        events = correlation_data["correlated_events"]
        traffic_events = [e for e in events if e["event_type"] == "traffic_spike"]
        
        if traffic_events:
            event = traffic_events[0]
            assert "impact_likelihood" in event
            assert event["impact_likelihood"] in ["very_high", "high", "medium", "low"]
    
    def test_correlate_events_config_change(self):
        """Test config change correlation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["config_changes"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        correlation_data = data["data"]
        
        events = correlation_data["correlated_events"]
        config_events = [e for e in events if e["event_type"] == "config_change"]
        
        if config_events:
            assert "event_metadata" in config_events[0]
    
    def test_correlate_events_causality_analysis(self):
        """Test causality analysis with primary cause"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["deployments", "migrations"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        correlation_data = data["data"]
        
        assert "causality_analysis" in correlation_data
        causality = correlation_data["causality_analysis"]
        
        assert "primary_cause" in causality
        primary = causality["primary_cause"]
        assert "event_type" in primary
        assert "confidence" in primary
        assert primary["confidence"] >= 0 and primary["confidence"] <= 100
    
    def test_correlate_events_contributing_factors(self):
        """Test contributing factors identification"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["deployments", "traffic_spikes"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        correlation_data = data["data"]
        
        causality = correlation_data["causality_analysis"]
        assert "contributing_factors" in causality
        
        factors = causality["contributing_factors"]
        assert isinstance(factors, list)
        
        if factors:
            factor = factors[0]
            assert "factor" in factor
            assert "explanation" in factor
    
    def test_correlate_events_time_window(self):
        """Test different time windows"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 6,  # 6-hour window
            "event_sources": ["deployments"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_correlate_events_correlation_score(self):
        """Test correlation score range"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["deployments", "migrations", "config_changes"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        events = data["data"]["correlated_events"]
        
        # All correlation scores should be 0-100
        for event in events:
            assert event["correlation_score"] >= 0
            assert event["correlation_score"] <= 100
    
    def test_correlate_events_incident_metrics(self):
        """Test incident metrics at time of incident"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "time_window_hours": 24,
            "event_sources": ["deployments"]
        }
        
        response = client.post("/api/incidents/correlate-events", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        incident = data["data"]["incident"]
        
        assert "metrics_at_time" in incident
        metrics = incident["metrics_at_time"]
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "connection_count" in metrics


# ===== Root Cause Analysis Tests (10+ test cases) =====

class TestRootCauseAnalysis:
    """Test ML-powered root cause analysis endpoint"""
    
    def test_analyze_root_cause_success(self):
        """Test successful root cause analysis"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "standard",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        rca_data = data["data"]
        assert "incident_id" in rca_data
        assert rca_data["incident_id"] == "INC-2024-11-24-001"
    
    def test_analyze_root_cause_quick_depth(self):
        """Test quick analysis depth"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "quick",
            "include_historical_patterns": False
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_analyze_root_cause_comprehensive_depth(self):
        """Test comprehensive analysis depth with Five Whys"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "comprehensive",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rca_data = data["data"]
        
        # Comprehensive should include Five Whys
        assert "five_whys" in rca_data
        five_whys = rca_data["five_whys"]
        
        assert "why1" in five_whys
        assert "root_cause" in five_whys
    
    def test_analyze_root_cause_confidence_scoring(self):
        """Test confidence scoring for root causes"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "standard",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rca_data = data["data"]
        
        assert "root_causes" in rca_data
        root_causes = rca_data["root_causes"]
        assert len(root_causes) > 0
        
        for cause in root_causes:
            assert "confidence" in cause
            assert cause["confidence"] >= 0 and cause["confidence"] <= 100
    
    def test_analyze_root_cause_evidence_collection(self):
        """Test evidence collection"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "standard",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        root_causes = data["data"]["root_causes"]
        
        for cause in root_causes:
            assert "evidence" in cause
            evidence = cause["evidence"]
            assert isinstance(evidence, list)
            assert len(evidence) > 0
    
    def test_analyze_root_cause_affected_components(self):
        """Test affected components identification"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "standard",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        root_causes = data["data"]["root_causes"]
        
        for cause in root_causes:
            assert "affected_components" in cause
            components = cause["affected_components"]
            assert isinstance(components, list)
    
    def test_analyze_root_cause_pattern_matching(self):
        """Test historical pattern matching"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "standard",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rca_data = data["data"]
        
        assert "pattern_matches" in rca_data
        patterns = rca_data["pattern_matches"]
        
        if patterns:
            pattern = patterns[0]
            assert "pattern_name" in pattern
            assert "similarity_score" in pattern
            assert "historical_occurrences" in pattern
    
    def test_analyze_root_cause_query_performance(self):
        """Test query performance root cause"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "standard",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        root_causes = data["data"]["root_causes"]
        
        query_causes = [c for c in root_causes if c["cause"] == "query_performance"]
        if query_causes:
            cause = query_causes[0]
            assert "typical_symptoms" in cause
    
    def test_analyze_root_cause_mitigation_urgency(self):
        """Test mitigation urgency assessment"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "standard",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        root_causes = data["data"]["root_causes"]
        
        for cause in root_causes:
            assert "mitigation_urgency" in cause
            urgency = cause["mitigation_urgency"]
            assert urgency in ["immediate", "high", "medium", "low"]
    
    def test_analyze_root_cause_five_whys_structure(self):
        """Test Five Whys analysis structure"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "analysis_depth": "comprehensive",
            "include_historical_patterns": True
        }
        
        response = client.post("/api/incidents/analyze-root-cause", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        five_whys = data["data"]["five_whys"]
        
        assert "why1" in five_whys
        assert "why2" in five_whys
        assert "why3" in five_whys
        assert "why4" in five_whys
        assert "why5" in five_whys
        assert "root_cause" in five_whys


# ===== Similar Incidents Tests (8+ test cases) =====

class TestSimilarIncidents:
    """Test similar incident search endpoint"""
    
    def test_find_similar_incidents_success(self):
        """Test successful similar incident search"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        similar_data = data["data"]
        assert "incident_id" in similar_data
        assert similar_data["incident_id"] == incident_id
    
    def test_find_similar_incidents_similarity_scoring(self):
        """Test similarity scoring"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        similar_data = data["data"]
        
        assert "similar_incidents" in similar_data
        similar = similar_data["similar_incidents"]
        
        for incident in similar:
            assert "similarity_score" in incident
            assert incident["similarity_score"] >= 0
            assert incident["similarity_score"] <= 100
    
    def test_find_similar_incidents_resolution_details(self):
        """Test resolution details"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        similar = data["data"]["similar_incidents"]
        
        if similar:
            incident = similar[0]
            assert "resolution" in incident
            resolution = incident["resolution"]
            assert "summary" in resolution
            assert "time_to_resolve" in resolution
    
    def test_find_similar_incidents_lessons_learned(self):
        """Test lessons learned"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        similar = data["data"]["similar_incidents"]
        
        if similar:
            incident = similar[0]
            assert "lessons_learned" in incident
            lessons = incident["lessons_learned"]
            assert isinstance(lessons, list)
    
    def test_find_similar_incidents_recurrence_pattern(self):
        """Test recurrence pattern analysis"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        similar_data = data["data"]
        
        assert "recurrence_pattern" in similar_data
        pattern = similar_data["recurrence_pattern"]
        
        assert "pattern_name" in pattern
        assert "occurrences" in pattern
        assert "frequency" in pattern
    
    def test_find_similar_incidents_trend_analysis(self):
        """Test trend analysis (increasing/decreasing)"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        pattern = data["data"]["recurrence_pattern"]
        
        assert "trend" in pattern
        trend = pattern["trend"]
        assert trend in ["increasing", "stable", "decreasing"]
    
    def test_find_similar_incidents_prevention_measures(self):
        """Test prevention measures"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        pattern = data["data"]["recurrence_pattern"]
        
        assert "prevention_measures" in pattern
        measures = pattern["prevention_measures"]
        assert isinstance(measures, list)
    
    def test_find_similar_incidents_ordered_by_similarity(self):
        """Test results ordered by similarity score"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/similar/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        similar = data["data"]["similar_incidents"]
        
        if len(similar) > 1:
            # Should be ordered by similarity descending
            scores = [inc["similarity_score"] for inc in similar]
            assert scores == sorted(scores, reverse=True)


# ===== Fix Generation Tests (8+ test cases) =====

class TestFixGeneration:
    """Test fix recommendation generation endpoint"""
    
    def test_generate_fix_success(self):
        """Test successful fix generation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {
                "include_immediate": True,
                "include_short_term": True,
                "include_long_term": True,
                "risk_tolerance": "moderate"
            }
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        fix_data = data["data"]
        assert "incident_id" in fix_data
        assert fix_data["incident_id"] == "INC-2024-11-24-001"
    
    def test_generate_fix_immediate_fixes(self):
        """Test immediate fix generation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {"include_immediate": True}
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        fix_data = data["data"]
        
        assert "recommendations" in fix_data
        recommendations = fix_data["recommendations"]
        
        immediate = [r for r in recommendations if r["fix_type"] == "immediate"]
        assert len(immediate) > 0
        
        imm_fix = immediate[0]
        assert "sql_commands" in imm_fix
        assert "estimated_time" in imm_fix
    
    def test_generate_fix_short_term_fixes(self):
        """Test short-term fix generation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {"include_short_term": True}
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["data"]["recommendations"]
        
        short_term = [r for r in recommendations if r["fix_type"] == "short_term"]
        if short_term:
            fix = short_term[0]
            assert "description" in fix
            assert "estimated_time" in fix
    
    def test_generate_fix_long_term_fixes(self):
        """Test long-term fix generation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {"include_long_term": True}
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["data"]["recommendations"]
        
        long_term = [r for r in recommendations if r["fix_type"] == "long_term"]
        if long_term:
            fix = long_term[0]
            assert "description" in fix
            assert "impact_analysis" in fix
    
    def test_generate_fix_sql_commands(self):
        """Test SQL command generation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {"include_immediate": True}
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["data"]["recommendations"]
        
        for rec in recommendations:
            if "sql_commands" in rec:
                commands = rec["sql_commands"]
                assert isinstance(commands, list)
                
                if commands:
                    assert isinstance(commands[0], str)
    
    def test_generate_fix_rollback_plans(self):
        """Test rollback plan generation"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {"include_immediate": True}
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["data"]["recommendations"]
        
        for rec in recommendations:
            if "rollback_plan" in rec:
                rollback = rec["rollback_plan"]
                assert "steps" in rollback
    
    def test_generate_fix_automated_detection(self):
        """Test automated fix detection"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {}
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        fix_data = data["data"]
        
        assert "automated_fix" in fix_data
        automated = fix_data["automated_fix"]
        
        if automated:
            assert "can_automate" in automated
            assert "estimated_duration" in automated
            assert "risk_level" in automated
    
    def test_generate_fix_risk_assessment(self):
        """Test risk assessment for fixes"""
        request_data = {
            "incident_id": "INC-2024-11-24-001",
            "fix_preferences": {}
        }
        
        response = client.post("/api/incidents/generate-fix", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        recommendations = data["data"]["recommendations"]
        
        for rec in recommendations:
            assert "risk_level" in rec
            risk = rec["risk_level"]
            assert risk in ["safe", "moderate", "high"]


# ===== Prevention Checklist Tests (6+ test cases) =====

class TestPreventionChecklist:
    """Test prevention checklist generation endpoint"""
    
    def test_get_prevention_checklist_success(self):
        """Test successful checklist generation"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/prevention-checklist/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        checklist_data = data["data"]
        assert "incident_id" in checklist_data
        assert checklist_data["incident_id"] == incident_id
    
    def test_get_prevention_checklist_categories(self):
        """Test checklist categories"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/prevention-checklist/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        checklist_data = data["data"]
        
        assert "checklist" in checklist_data
        checklist = checklist_data["checklist"]
        
        categories = {item["category"] for item in checklist}
        assert "Testing" in categories or "Monitoring" in categories
    
    def test_get_prevention_checklist_priority_levels(self):
        """Test priority levels"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/prevention-checklist/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        checklist = data["data"]["checklist"]
        
        for item in checklist:
            assert "priority" in item
            priority = item["priority"]
            assert priority in ["high", "medium", "low"]
    
    def test_get_prevention_checklist_effort_estimation(self):
        """Test effort estimation"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/prevention-checklist/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        checklist = data["data"]["checklist"]
        
        for item in checklist:
            assert "effort_hours" in item
            assert item["effort_hours"] > 0
    
    def test_get_prevention_checklist_summary(self):
        """Test checklist summary"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/prevention-checklist/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        checklist_data = data["data"]
        
        assert "summary" in checklist_data
        summary = checklist_data["summary"]
        
        assert "total_items" in summary
        assert "implemented_count" in summary
        assert "not_implemented_count" in summary
        assert "total_effort_hours" in summary
    
    def test_get_prevention_checklist_quick_wins(self):
        """Test quick wins identification"""
        incident_id = "INC-2024-11-24-001"
        
        response = client.get(f"/api/incidents/prevention-checklist/{incident_id}")
        assert response.status_code == 200
        
        data = response.json()
        checklist_data = data["data"]
        
        assert "quick_wins" in checklist_data
        quick_wins = checklist_data["quick_wins"]
        
        # Quick wins should have low effort, high impact
        for win in quick_wins:
            assert "task" in win
            assert "effort_hours" in win
            assert win["effort_hours"] <= 8  # Low effort (< 1 day)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
