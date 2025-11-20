"""
Unit tests for Health Benchmark Phase 2.2 features.
Tests performance scorer, timeline tracker, and slow query analyzer.
"""
import pytest
from datetime import datetime, timedelta
from models.health_models import (
    DatabaseType, HealthStatus, TrendDirection, QueryIssueType,
    PerformanceScoreRequest, HealthTimelineRequest, SlowQueryRequest
)
from core.health import PerformanceScorer, TimelineTracker, QueryAnalyzer


class TestPerformanceScorer:
    """Tests for PerformanceScorer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scorer = PerformanceScorer()
    
    def test_category_weights_sum_to_one(self):
        """Test that category weights sum to 1.0"""
        total_weight = sum(self.scorer.category_weights.values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_calculate_score_returns_valid_data(self):
        """Test score calculation returns complete data"""
        result = self.scorer.calculate_score(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            include_recommendations=True
        )
        
        assert result.overall_score >= 0
        assert result.overall_score <= 100
        assert result.health_status is not None
        assert len(result.category_breakdown) == 5
        assert result.metrics is not None
        assert len(result.top_recommendations) <= 5
    
    def test_health_status_mapping(self):
        """Test score to health status mapping"""
        assert self.scorer._determine_health_status(95) == HealthStatus.EXCELLENT
        assert self.scorer._determine_health_status(80) == HealthStatus.GOOD
        assert self.scorer._determine_health_status(65) == HealthStatus.FAIR
        assert self.scorer._determine_health_status(45) == HealthStatus.POOR
        assert self.scorer._determine_health_status(30) == HealthStatus.CRITICAL
    
    def test_category_scores_structure(self):
        """Test category score data structure"""
        metrics = self.scorer._gather_metrics()
        categories = self.scorer._score_categories(metrics, True)
        
        for cat in categories:
            assert 0 <= cat.score <= 100
            assert 0 <= cat.weight <= 1
            assert isinstance(cat.issues, list)
            assert isinstance(cat.recommendations, list)
    
    def test_overall_score_calculation(self):
        """Test weighted overall score calculation"""
        # Create mock category scores
        from models.health_models import CategoryScore
        
        categories = [
            CategoryScore(category="test1", score=80, weight=0.5, issues=[], recommendations=[]),
            CategoryScore(category="test2", score=60, weight=0.5, issues=[], recommendations=[])
        ]
        
        overall = self.scorer._calculate_overall_score(categories)
        assert overall == 70  # (80*0.5 + 60*0.5)
    
    def test_recommendations_without_flag(self):
        """Test recommendations are excluded when flag is False"""
        metrics = self.scorer._gather_metrics()
        categories = self.scorer._score_categories(metrics, False)
        
        for cat in categories:
            assert len(cat.recommendations) == 0
    
    def test_next_check_recommended(self):
        """Test next check recommendation is in the future"""
        result = self.scorer.calculate_score(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        assert result.next_check_recommended > result.last_analyzed


class TestTimelineTracker:
    """Tests for TimelineTracker"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tracker = TimelineTracker()
    
    def test_track_timeline_returns_complete_data(self):
        """Test timeline tracking returns all components"""
        result = self.tracker.track_timeline(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            days=30,
            include_forecast=True
        )
        
        assert len(result.timeline) == 30
        assert result.trend_analysis is not None
        assert isinstance(result.anomalies, list)
        assert result.forecast is not None
        assert len(result.forecast) <= 7
        assert result.period_summary is not None
    
    def test_timeline_data_points_structure(self):
        """Test data point structure"""
        timeline = self.tracker._generate_timeline_data(10)
        
        for dp in timeline:
            assert 0 <= dp.score <= 100
            assert dp.health_status is not None
            assert isinstance(dp.key_metrics, dict)
            assert dp.timestamp is not None
    
    def test_trend_analysis_direction(self):
        """Test trend direction detection"""
        from models.health_models import DataPoint
        
        # Create improving trend
        improving = [
            DataPoint(timestamp=datetime.now(), score=60, health_status=HealthStatus.FAIR, key_metrics={}),
            DataPoint(timestamp=datetime.now(), score=70, health_status=HealthStatus.GOOD, key_metrics={}),
            DataPoint(timestamp=datetime.now(), score=80, health_status=HealthStatus.GOOD, key_metrics={})
        ]
        
        trend = self.tracker._analyze_trend(improving)
        assert trend.direction == TrendDirection.IMPROVING
    
    def test_anomaly_detection(self):
        """Test anomaly detection logic"""
        timeline = self.tracker._generate_timeline_data(30)
        anomalies = self.tracker._detect_anomalies(timeline)
        
        for anomaly in anomalies:
            assert anomaly.severity in ["low", "medium", "high", "critical"]
            assert anomaly.impact_score >= 0
            assert anomaly.potential_cause is not None
    
    def test_forecast_confidence_decreases(self):
        """Test forecast confidence decreases with distance"""
        timeline = self.tracker._generate_timeline_data(30)
        forecasts = self.tracker._forecast_health(timeline, days=7)
        
        if len(forecasts) > 1:
            assert forecasts[0].confidence >= forecasts[-1].confidence
    
    def test_period_summary_statistics(self):
        """Test period summary calculations"""
        timeline = self.tracker._generate_timeline_data(30)
        from models.health_models import TrendAnalysis, TrendDirection
        
        trend = TrendAnalysis(
            direction=TrendDirection.STABLE,
            change_percentage=0.0,
            velocity=0.0,
            volatility=5.0
        )
        
        summary = self.tracker._generate_summary(timeline, trend)
        
        assert summary["period_days"] == 30
        assert "avg_score" in summary
        assert "min_score" in summary
        assert "max_score" in summary
    
    def test_timeline_without_forecast(self):
        """Test timeline generation without forecast"""
        result = self.tracker.track_timeline(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            days=15,
            include_forecast=False
        )
        
        assert result.forecast is None


class TestQueryAnalyzer:
    """Tests for QueryAnalyzer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = QueryAnalyzer()
    
    def test_analyze_queries_returns_complete_data(self):
        """Test query analysis returns all components"""
        result = self.analyzer.analyze_queries(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            threshold_ms=1000,
            limit=50,
            include_explain=True
        )
        
        assert isinstance(result.slow_queries, list)
        assert result.statistics is not None
        assert result.impact_analysis is not None
        assert isinstance(result.top_optimizations, list)
        assert isinstance(result.auto_fix_sql, list)
    
    def test_slow_query_structure(self):
        """Test slow query data structure"""
        queries = self.analyzer._identify_slow_queries(1000, 5, True)
        
        for query in queries:
            assert query.query_id is not None
            assert query.execution_time_ms > 0
            assert query.execution_count > 0
            assert len(query.tables_accessed) > 0
            assert len(query.optimizations) > 0
    
    def test_optimization_recommendations(self):
        """Test optimization generation"""
        opt = self.analyzer._generate_optimizations(
            "SELECT * FROM users WHERE email LIKE '%@test.com'",
            QueryIssueType.FULL_TABLE_SCAN,
            ["users"]
        )
        
        assert len(opt) > 0
        assert opt[0].issue_type == QueryIssueType.FULL_TABLE_SCAN
        assert opt[0].severity in ["low", "medium", "high", "critical"]
        assert opt[0].sql_fix is not None
    
    def test_cost_estimation(self):
        """Test query cost estimation"""
        cost = self.analyzer._estimate_cost(2000, 1000)
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_statistics_calculation(self):
        """Test aggregate statistics"""
        queries = self.analyzer._identify_slow_queries(1000, 10, True)
        stats = self.analyzer._calculate_statistics(queries)
        
        assert stats.total_slow_queries == len(queries)
        assert stats.total_execution_time_ms > 0
        assert stats.avg_execution_time_ms > 0
        assert stats.optimization_opportunities > 0
    
    def test_impact_analysis(self):
        """Test business impact analysis"""
        queries = self.analyzer._identify_slow_queries(1000, 10, True)
        impact = self.analyzer._analyze_impact(queries)
        
        assert impact.current_cost_per_day >= 0
        assert impact.potential_savings_per_day >= 0
        assert impact.affected_users >= 0
        assert impact.business_impact is not None
    
    def test_auto_fix_sql_generation(self):
        """Test auto-fix SQL generation"""
        queries = self.analyzer._identify_slow_queries(1000, 5, True)
        sql = self.analyzer._generate_auto_fix_sql(queries)
        
        assert len(sql) > 0
        assert any("CREATE INDEX" in line for line in sql)
    
    def test_execution_plan_included(self):
        """Test execution plan is included when requested"""
        queries = self.analyzer._identify_slow_queries(1000, 1, True)
        assert queries[0].execution_plan is not None
        assert queries[0].execution_plan.operation is not None
    
    def test_execution_plan_excluded(self):
        """Test execution plan is excluded when not requested"""
        queries = self.analyzer._identify_slow_queries(1000, 1, False)
        assert queries[0].execution_plan is None
    
    def test_top_optimizations_sorted_by_severity(self):
        """Test top optimizations are sorted by severity"""
        queries = self.analyzer._identify_slow_queries(1000, 10, True)
        top_opts = self.analyzer._get_top_optimizations(queries)
        
        # Should prioritize critical and high severity
        if len(top_opts) > 1:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            first_severity = severity_order.get(top_opts[0].severity, 3)
            last_severity = severity_order.get(top_opts[-1].severity, 3)
            assert first_severity <= last_severity


class TestIntegration:
    """Integration tests combining multiple components"""
    
    def test_full_health_benchmark_workflow(self):
        """Test complete health benchmark workflow"""
        scorer = PerformanceScorer()
        tracker = TimelineTracker()
        analyzer = QueryAnalyzer()
        
        # Get performance score
        score_result = scorer.calculate_score(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        # Get timeline
        timeline_result = tracker.track_timeline(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            days=30
        )
        
        # Analyze slow queries
        query_result = analyzer.analyze_queries(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test"
        )
        
        # Assertions
        assert score_result.overall_score >= 0
        assert len(timeline_result.timeline) == 30
        assert len(query_result.slow_queries) > 0
        assert query_result.auto_fix_available is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
