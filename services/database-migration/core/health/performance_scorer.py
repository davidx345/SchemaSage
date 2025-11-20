"""
Performance Scorer Core Logic.
Calculates weighted health scores across multiple categories.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models.health_models import (
    PerformanceScoreData, CategoryScore, PerformanceMetrics,
    HealthStatus, DatabaseType
)

class PerformanceScorer:
    """
    Calculates database performance scores using weighted categories.
    """
    
    def __init__(self):
        self.category_weights = {
            "indexing": 0.30,
            "query_patterns": 0.25,
            "schema_design": 0.20,
            "maintenance": 0.15,
            "resource_usage": 0.10
        }
    
    def calculate_score(self, db_type: DatabaseType, connection_string: str, include_recommendations: bool = True) -> PerformanceScoreData:
        """
        Calculates overall performance score with category breakdown.
        """
        # In production, this would query the database for real metrics
        # For now, we'll simulate the scoring logic
        
        metrics = self._gather_metrics()
        category_scores = self._score_categories(metrics, include_recommendations)
        overall_score = self._calculate_overall_score(category_scores)
        health_status = self._determine_health_status(overall_score)
        top_recommendations = self._get_top_recommendations(category_scores)
        
        return PerformanceScoreData(
            overall_score=overall_score,
            health_status=health_status,
            category_breakdown=category_scores,
            metrics=metrics,
            top_recommendations=top_recommendations,
            last_analyzed=datetime.now(),
            next_check_recommended=datetime.now() + timedelta(days=7)
        )
    
    def _gather_metrics(self) -> PerformanceMetrics:
        """Simulates gathering database metrics."""
        return PerformanceMetrics(
            total_queries=150000,
            slow_queries=450,
            avg_query_time_ms=12.5,
            cache_hit_ratio=0.92,
            connection_pool_usage=0.65,
            table_count=85,
            index_count=120,
            missing_indexes=8
        )
    
    def _score_categories(self, metrics: PerformanceMetrics, include_recommendations: bool) -> List[CategoryScore]:
        """Scores each performance category."""
        categories = []
        
        # Indexing Score
        index_ratio = metrics.index_count / max(metrics.table_count, 1)
        index_score = min(100, int(70 + (index_ratio * 10)))
        if metrics.missing_indexes > 0:
            index_score -= min(30, metrics.missing_indexes * 5)
        
        categories.append(CategoryScore(
            category="indexing",
            score=max(0, index_score),
            weight=self.category_weights["indexing"],
            issues=[
                f"{metrics.missing_indexes} missing indexes detected"
            ] if metrics.missing_indexes > 0 else [],
            recommendations=[
                "Add indexes on frequently queried columns",
                "Review and remove unused indexes"
            ] if include_recommendations else []
        ))
        
        # Query Patterns Score
        slow_query_ratio = metrics.slow_queries / max(metrics.total_queries, 1)
        query_score = int(100 - (slow_query_ratio * 10000))
        query_score = max(0, min(100, query_score))
        
        categories.append(CategoryScore(
            category="query_patterns",
            score=query_score,
            weight=self.category_weights["query_patterns"],
            issues=[
                f"{metrics.slow_queries} slow queries detected",
                f"Average query time: {metrics.avg_query_time_ms}ms"
            ],
            recommendations=[
                "Optimize slow queries using EXPLAIN ANALYZE",
                "Implement query result caching",
                "Review N+1 query patterns"
            ] if include_recommendations else []
        ))
        
        # Schema Design Score
        tables_per_index = metrics.index_count / max(metrics.table_count, 1)
        schema_score = 75
        if tables_per_index < 1.2:
            schema_score -= 15
        elif tables_per_index > 2.5:
            schema_score -= 10
        
        categories.append(CategoryScore(
            category="schema_design",
            score=max(0, schema_score),
            weight=self.category_weights["schema_design"],
            issues=[
                "Some tables lack proper normalization"
            ],
            recommendations=[
                "Review foreign key relationships",
                "Consider partitioning large tables",
                "Normalize denormalized structures"
            ] if include_recommendations else []
        ))
        
        # Maintenance Score
        maintenance_score = 80  # Base score
        
        categories.append(CategoryScore(
            category="maintenance",
            score=maintenance_score,
            weight=self.category_weights["maintenance"],
            issues=[],
            recommendations=[
                "Schedule regular VACUUM operations",
                "Update table statistics regularly",
                "Monitor bloat in indexes"
            ] if include_recommendations else []
        ))
        
        # Resource Usage Score
        cache_score = int(metrics.cache_hit_ratio * 100)
        pool_penalty = max(0, int((metrics.connection_pool_usage - 0.8) * 50))
        resource_score = max(0, cache_score - pool_penalty)
        
        categories.append(CategoryScore(
            category="resource_usage",
            score=resource_score,
            weight=self.category_weights["resource_usage"],
            issues=[
                "Connection pool usage high" if metrics.connection_pool_usage > 0.8 else ""
            ],
            recommendations=[
                "Increase connection pool size",
                "Implement connection pooling if not present",
                "Monitor memory usage patterns"
            ] if include_recommendations and metrics.connection_pool_usage > 0.8 else []
        ))
        
        return categories
    
    def _calculate_overall_score(self, category_scores: List[CategoryScore]) -> int:
        """Calculates weighted overall score."""
        weighted_sum = sum(cat.score * cat.weight for cat in category_scores)
        return int(weighted_sum)
    
    def _determine_health_status(self, score: int) -> HealthStatus:
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
    
    def _get_top_recommendations(self, category_scores: List[CategoryScore]) -> List[str]:
        """Extracts top 5 recommendations based on lowest scores."""
        sorted_categories = sorted(category_scores, key=lambda x: x.score)
        recommendations = []
        
        for cat in sorted_categories:
            recommendations.extend(cat.recommendations[:2])
            if len(recommendations) >= 5:
                break
        
        return recommendations[:5]
