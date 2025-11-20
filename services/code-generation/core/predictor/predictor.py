"""
Query performance predictor service.
Predicts query performance and provides optimization suggestions.
"""
from typing import List, Tuple
import re
import random

from models.predictor_models import (
    QueryType, DatabaseEngine, PerformancePrediction, OptimizationPriority,
    TableStatistics, QueryAnalysis, PerformanceMetrics, OptimizationSuggestion,
    IndexRecommendation, BottleneckAnalysis, ComparisonMetrics, PredictorSummary
)


class QueryPerformancePredictor:
    """
    Service for predicting query performance.
    Analyzes queries and provides optimization recommendations.
    """
    
    def __init__(self):
        """Initialize the performance predictor"""
        pass
        
    def predict_performance(
        self,
        sql_query: str,
        database_engine: DatabaseEngine,
        table_statistics: List[TableStatistics],
        query_type: QueryType = None,
        expected_result_rows: int = None,
        concurrent_queries: int = 1
    ) -> Tuple[QueryAnalysis, PerformanceMetrics, List[BottleneckAnalysis],
               List[OptimizationSuggestion], List[IndexRecommendation],
               ComparisonMetrics, PredictorSummary, List[str]]:
        """
        Predict query performance and generate recommendations.
        """
        # Analyze query structure
        query_analysis = self._analyze_query(sql_query, table_statistics, query_type)
        
        # Predict performance metrics
        performance_metrics = self._predict_metrics(
            query_analysis, table_statistics, database_engine, concurrent_queries
        )
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(query_analysis, performance_metrics, table_statistics)
        
        # Generate optimization suggestions
        suggestions = self._generate_suggestions(query_analysis, bottlenecks, database_engine)
        
        # Generate index recommendations
        index_recommendations = self._recommend_indexes(query_analysis, table_statistics)
        
        # Compare with similar queries
        comparison = self._compare_with_similar(performance_metrics, query_analysis)
        
        # Generate summary
        summary = self._generate_summary(
            performance_metrics, bottlenecks, suggestions, query_analysis
        )
        
        # Generate warnings
        warnings = self._generate_warnings(query_analysis, performance_metrics, concurrent_queries)
        
        return (query_analysis, performance_metrics, bottlenecks, suggestions,
                index_recommendations, comparison, summary, warnings)
                
    def _analyze_query(
        self,
        sql_query: str,
        table_stats: List[TableStatistics],
        query_type: QueryType = None
    ) -> QueryAnalysis:
        """Analyze the query structure"""
        sql_lower = sql_query.lower()
        
        # Detect query type
        if not query_type:
            if 'select' in sql_lower:
                query_type = QueryType.SELECT
            elif 'insert' in sql_lower:
                query_type = QueryType.INSERT
            elif 'update' in sql_lower:
                query_type = QueryType.UPDATE
            elif 'delete' in sql_lower:
                query_type = QueryType.DELETE
            else:
                query_type = QueryType.SELECT
                
        # Extract tables
        tables = [ts.table_name for ts in table_stats]
        
        # Count joins
        joins_count = sql_lower.count('join')
        
        # Check for subqueries
        has_subqueries = '(' in sql_query and 'select' in sql_lower.split('(')[1] if '(' in sql_query else False
        
        # Check for aggregations
        has_aggregations = any(agg in sql_lower for agg in ['sum(', 'count(', 'avg(', 'max(', 'min(', 'group by'])
        
        # Analyze WHERE clause
        where_complexity = "simple"
        if 'where' in sql_lower:
            where_clause = sql_lower.split('where')[1].split('order by')[0].split('group by')[0]
            condition_count = where_clause.count('and') + where_clause.count('or') + 1
            if condition_count > 5:
                where_complexity = "complex"
            elif condition_count > 2:
                where_complexity = "moderate"
                
        # Estimate rows scanned
        total_rows = sum(ts.row_count for ts in table_stats)
        if 'where' in sql_lower:
            estimated_rows_scanned = int(total_rows * 0.2)  # Assume 20% with WHERE
        else:
            estimated_rows_scanned = total_rows
            
        # Calculate selectivity
        selectivity = (estimated_rows_scanned / total_rows * 100) if total_rows > 0 else 100
        
        return QueryAnalysis(
            query_type=query_type,
            tables_involved=tables,
            joins_count=joins_count,
            has_subqueries=has_subqueries,
            has_aggregations=has_aggregations,
            where_clause_complexity=where_complexity,
            estimated_rows_scanned=estimated_rows_scanned,
            selectivity=round(selectivity, 2)
        )
        
    def _predict_metrics(
        self,
        analysis: QueryAnalysis,
        table_stats: List[TableStatistics],
        engine: DatabaseEngine,
        concurrent: int
    ) -> PerformanceMetrics:
        """Predict performance metrics"""
        # Base execution time calculation
        base_time = 10.0  # Base 10ms
        
        # Add time for row scanning
        base_time += analysis.estimated_rows_scanned * 0.001
        
        # Add time for joins
        base_time += analysis.joins_count * 50
        
        # Add time for subqueries
        if analysis.has_subqueries:
            base_time *= 2
            
        # Add time for aggregations
        if analysis.has_aggregations:
            base_time *= 1.5
            
        # Adjust for concurrency
        if concurrent > 10:
            base_time *= (1 + (concurrent - 10) * 0.05)
            
        # Engine-specific multiplier
        engine_multipliers = {
            DatabaseEngine.POSTGRESQL: 1.0,
            DatabaseEngine.MYSQL: 1.1,
            DatabaseEngine.SQLSERVER: 1.15,
            DatabaseEngine.ORACLE: 0.95,
            DatabaseEngine.MARIADB: 1.05
        }
        base_time *= engine_multipliers.get(engine, 1.0)
        
        # Calculate CPU and IO costs
        cpu_cost = base_time * 0.6
        io_cost = base_time * 0.4
        
        # Estimate memory
        memory_mb = min(1024, analysis.estimated_rows_scanned * 0.001)
        
        # Calculate confidence (higher for simpler queries)
        confidence = 95.0
        if analysis.has_subqueries:
            confidence -= 15
        if analysis.joins_count > 3:
            confidence -= 10
        if analysis.where_clause_complexity == "complex":
            confidence -= 10
        confidence = max(50, confidence)
        
        # Determine rating
        if base_time < 100:
            rating = PerformancePrediction.EXCELLENT
        elif base_time < 500:
            rating = PerformancePrediction.GOOD
        elif base_time < 2000:
            rating = PerformancePrediction.ACCEPTABLE
        elif base_time < 5000:
            rating = PerformancePrediction.SLOW
        else:
            rating = PerformancePrediction.VERY_SLOW
            
        return PerformanceMetrics(
            estimated_execution_time_ms=round(base_time, 2),
            estimated_cpu_cost=round(cpu_cost, 2),
            estimated_io_cost=round(io_cost, 2),
            estimated_memory_mb=round(memory_mb, 2),
            confidence_score=round(confidence, 2),
            performance_rating=rating
        )
        
    def _identify_bottlenecks(
        self,
        analysis: QueryAnalysis,
        metrics: PerformanceMetrics,
        table_stats: List[TableStatistics]
    ) -> List[BottleneckAnalysis]:
        """Identify query bottlenecks"""
        bottlenecks = []
        
        # Check for full table scan
        if analysis.selectivity > 50:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_type="Full Table Scan",
                severity="High",
                description=f"Query scans {analysis.selectivity:.1f}% of table rows",
                impact_on_performance="Significant - causes high I/O and CPU usage",
                resolution="Add indexes on columns used in WHERE clause"
            ))
            
        # Check for missing indexes on joins
        if analysis.joins_count > 0:
            for table in table_stats:
                if table.index_count == 0:
                    bottlenecks.append(BottleneckAnalysis(
                        bottleneck_type="Unindexed Join",
                        severity="Critical",
                        description=f"Table '{table.table_name}' has no indexes for join operations",
                        impact_on_performance="Critical - join performance will degrade significantly",
                        resolution=f"Create index on join columns in '{table.table_name}'"
                    ))
                    
        # Check for complex subqueries
        if analysis.has_subqueries:
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_type="Subquery Execution",
                severity="Medium",
                description="Query contains subqueries that may execute multiple times",
                impact_on_performance="Moderate - subqueries can multiply execution time",
                resolution="Consider rewriting as JOIN or using WITH clause (CTE)"
            ))
            
        return bottlenecks
        
    def _generate_suggestions(
        self,
        analysis: QueryAnalysis,
        bottlenecks: List[BottleneckAnalysis],
        engine: DatabaseEngine
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Suggest indexes for WHERE clause
        if analysis.where_clause_complexity != "simple":
            suggestions.append(OptimizationSuggestion(
                priority=OptimizationPriority.HIGH,
                category="Indexing",
                suggestion="Create indexes on columns used in WHERE clause conditions",
                expected_improvement="50-90% reduction in query time",
                implementation_complexity="Low - simple index creation",
                example="CREATE INDEX idx_column_name ON table_name(column_name);"
            ))
            
        # Suggest query rewrite for subqueries
        if analysis.has_subqueries:
            suggestions.append(OptimizationSuggestion(
                priority=OptimizationPriority.MEDIUM,
                category="Query Rewrite",
                suggestion="Replace correlated subqueries with JOINs or CTEs",
                expected_improvement="30-70% performance improvement",
                implementation_complexity="Medium - requires query rewrite",
                example="WITH subquery AS (...) SELECT ... FROM table JOIN subquery ..."
            ))
            
        # Suggest limiting result set
        if analysis.estimated_rows_scanned > 10000:
            suggestions.append(OptimizationSuggestion(
                priority=OptimizationPriority.MEDIUM,
                category="Result Set",
                suggestion="Use LIMIT clause to restrict result set size",
                expected_improvement="Proportional to reduction in rows returned",
                implementation_complexity="Low - add LIMIT clause",
                example="SELECT ... FROM table WHERE ... LIMIT 1000;"
            ))
            
        return suggestions
        
    def _recommend_indexes(
        self,
        analysis: QueryAnalysis,
        table_stats: List[TableStatistics]
    ) -> List[IndexRecommendation]:
        """Recommend indexes for query optimization"""
        recommendations = []
        
        # Recommend indexes for tables with few indexes
        for table in table_stats:
            if table.index_count < 2 and table.row_count > 1000:
                # Simulate column detection from query
                recommendations.append(IndexRecommendation(
                    table_name=table.table_name,
                    columns=["id", "created_at"],  # Common patterns
                    index_type="BTREE",
                    estimated_improvement_percent=min(80, 50 + (table.row_count / 10000)),
                    creation_sql=f"CREATE INDEX idx_{table.table_name}_lookup ON {table.table_name}(id, created_at);"
                ))
                
        return recommendations
        
    def _compare_with_similar(
        self,
        metrics: PerformanceMetrics,
        analysis: QueryAnalysis
    ) -> ComparisonMetrics:
        """Compare with similar queries"""
        # Simulate comparison with historical data
        similar_avg = metrics.estimated_execution_time_ms * random.uniform(0.8, 1.5)
        
        percentile = 50.0
        if metrics.estimated_execution_time_ms < similar_avg:
            percentile = 30.0
        elif metrics.estimated_execution_time_ms > similar_avg * 1.5:
            percentile = 80.0
            
        improvement = max(0, (metrics.estimated_execution_time_ms - similar_avg) / similar_avg * 100)
        
        return ComparisonMetrics(
            similar_query_avg_time_ms=round(similar_avg, 2),
            percentile_ranking=round(percentile, 2),
            improvement_potential_percent=round(improvement, 2)
        )
        
    def _generate_summary(
        self,
        metrics: PerformanceMetrics,
        bottlenecks: List[BottleneckAnalysis],
        suggestions: List[OptimizationSuggestion],
        analysis: QueryAnalysis
    ) -> PredictorSummary:
        """Generate prediction summary"""
        critical_count = sum(1 for b in bottlenecks if b.severity in ["Critical", "High"])
        
        if metrics.performance_rating in [PerformancePrediction.EXCELLENT, PerformancePrediction.GOOD]:
            assessment = "Query performance is good with current configuration"
            needs_opt = False
        else:
            assessment = f"Query performance is {metrics.performance_rating.value} and needs optimization"
            needs_opt = True
            
        est_hours = len(suggestions) * 0.5 + critical_count * 1.0
        
        return PredictorSummary(
            overall_assessment=assessment,
            needs_optimization=needs_opt,
            critical_issues_count=critical_count,
            estimated_optimization_time_hours=round(est_hours, 1)
        )
        
    def _generate_warnings(
        self,
        analysis: QueryAnalysis,
        metrics: PerformanceMetrics,
        concurrent: int
    ) -> List[str]:
        """Generate warnings"""
        warnings = []
        
        if analysis.selectivity > 80:
            warnings.append("Query will scan most of the table - consider adding more selective conditions")
            
        if concurrent > 50:
            warnings.append(f"High concurrency ({concurrent} queries) may cause resource contention")
            
        if metrics.estimated_memory_mb > 512:
            warnings.append(f"High memory usage ({metrics.estimated_memory_mb:.0f}MB) - monitor memory pressure")
            
        return warnings


def predict_query_performance(
    sql_query: str,
    database_engine: DatabaseEngine,
    table_statistics: List[TableStatistics],
    query_type: QueryType = None,
    expected_result_rows: int = None,
    concurrent_queries: int = 1
) -> Tuple:
    """Predict query performance"""
    predictor = QueryPerformancePredictor()
    return predictor.predict_performance(
        sql_query, database_engine, table_statistics,
        query_type, expected_result_rows, concurrent_queries
    )
