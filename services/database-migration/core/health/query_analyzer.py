"""
Slow Query Analyzer Core Logic.
Identifies and optimizes slow database queries.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
from models.health_models import (
    SlowQueryData, SlowQuery, QueryStatistics, ImpactAnalysis,
    QueryOptimization, ExecutionPlan, QueryIssueType, DatabaseType
)

class QueryAnalyzer:
    """
    Analyzes slow queries and generates optimization recommendations.
    """
    
    def analyze_queries(
        self, 
        db_type: DatabaseType, 
        connection_string: str, 
        threshold_ms: int = 1000, 
        limit: int = 50,
        include_explain: bool = True
    ) -> SlowQueryData:
        """
        Identifies slow queries and provides optimization recommendations.
        """
        # In production, this would query pg_stat_statements or similar
        slow_queries = self._identify_slow_queries(threshold_ms, limit, include_explain)
        statistics = self._calculate_statistics(slow_queries)
        impact_analysis = self._analyze_impact(slow_queries)
        top_optimizations = self._get_top_optimizations(slow_queries)
        auto_fix_sql = self._generate_auto_fix_sql(slow_queries)
        
        return SlowQueryData(
            slow_queries=slow_queries,
            statistics=statistics,
            impact_analysis=impact_analysis,
            top_optimizations=top_optimizations,
            auto_fix_available=len(auto_fix_sql) > 0,
            auto_fix_sql=auto_fix_sql
        )
    
    def _identify_slow_queries(self, threshold_ms: int, limit: int, include_explain: bool) -> List[SlowQuery]:
        """Simulates identifying slow queries from database."""
        # Sample slow queries with realistic patterns
        sample_queries = [
            {
                "query": "SELECT * FROM users WHERE email LIKE '%@example.com'",
                "time": 2500,
                "count": 1500,
                "tables": ["users"],
                "issue": QueryIssueType.FULL_TABLE_SCAN
            },
            {
                "query": "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id WHERE u.created_at > '2024-01-01'",
                "time": 1800,
                "count": 850,
                "tables": ["users", "orders"],
                "issue": QueryIssueType.MISSING_INDEX
            },
            {
                "query": "SELECT COUNT(*) FROM products WHERE category_id IN (SELECT id FROM categories WHERE active = true)",
                "time": 3200,
                "count": 200,
                "tables": ["products", "categories"],
                "issue": QueryIssueType.SUBOPTIMAL_QUERY
            },
            {
                "query": "SELECT * FROM order_items WHERE order_id = ?",
                "time": 1200,
                "count": 5000,
                "tables": ["order_items"],
                "issue": QueryIssueType.N_PLUS_ONE
            },
            {
                "query": "SELECT a.*, b.*, c.* FROM table_a a LEFT JOIN table_b b ON a.id = b.a_id LEFT JOIN table_c c ON b.id = c.b_id",
                "time": 4500,
                "count": 120,
                "tables": ["table_a", "table_b", "table_c"],
                "issue": QueryIssueType.INEFFICIENT_JOIN
            }
        ]
        
        slow_queries = []
        for i, sq in enumerate(sample_queries[:limit]):
            optimizations = self._generate_optimizations(sq["query"], sq["issue"], sq["tables"])
            execution_plan = self._generate_execution_plan(sq["tables"]) if include_explain else None
            
            slow_queries.append(SlowQuery(
                query_id=f"q_{str(uuid4())[:8]}",
                query_text=sq["query"],
                execution_time_ms=sq["time"],
                execution_count=sq["count"],
                avg_time_ms=sq["time"],
                max_time_ms=sq["time"] * 1.5,
                last_executed=datetime.now() - timedelta(hours=i),
                tables_accessed=sq["tables"],
                execution_plan=execution_plan,
                optimizations=optimizations,
                cost_estimate=self._estimate_cost(sq["time"], sq["count"])
            ))
        
        return slow_queries
    
    def _generate_execution_plan(self, tables: List[str]) -> ExecutionPlan:
        """Simulates EXPLAIN output."""
        return ExecutionPlan(
            operation="Seq Scan" if len(tables) == 1 else "Hash Join",
            cost=1500.50,
            rows=10000,
            details={
                "filter": "WHERE clause active",
                "join_type": "nested_loop" if len(tables) > 1 else None,
                "index_used": False
            }
        )
    
    def _generate_optimizations(self, query: str, issue_type: QueryIssueType, tables: List[str]) -> List[QueryOptimization]:
        """Generates optimization recommendations based on query analysis."""
        optimizations = []
        
        if issue_type == QueryIssueType.MISSING_INDEX:
            optimizations.append(QueryOptimization(
                issue_type=issue_type,
                severity="high",
                description=f"Missing index on {tables[0]} causing slow lookups",
                suggested_fix=f"Add index on frequently queried columns in {tables[0]}",
                estimated_improvement="60-80% faster",
                sql_fix=f"CREATE INDEX idx_{tables[0]}_lookup ON {tables[0]} (user_id, created_at);"
            ))
        
        elif issue_type == QueryIssueType.FULL_TABLE_SCAN:
            optimizations.append(QueryOptimization(
                issue_type=issue_type,
                severity="critical",
                description="LIKE with leading wildcard forces full table scan",
                suggested_fix="Use full-text search or trigram index for pattern matching",
                estimated_improvement="90% faster",
                sql_fix=f"CREATE INDEX idx_{tables[0]}_email_trgm ON {tables[0]} USING gin (email gin_trgm_ops);"
            ))
        
        elif issue_type == QueryIssueType.SUBOPTIMAL_QUERY:
            optimizations.append(QueryOptimization(
                issue_type=issue_type,
                severity="medium",
                description="Subquery in WHERE clause evaluated multiple times",
                suggested_fix="Convert subquery to JOIN or use CTE",
                estimated_improvement="50-70% faster",
                sql_fix="SELECT COUNT(*) FROM products p JOIN categories c ON p.category_id = c.id WHERE c.active = true;"
            ))
        
        elif issue_type == QueryIssueType.N_PLUS_ONE:
            optimizations.append(QueryOptimization(
                issue_type=issue_type,
                severity="high",
                description="N+1 query pattern detected - fetching related records in loop",
                suggested_fix="Use JOIN or batch loading to fetch all data in single query",
                estimated_improvement="95% fewer queries",
                sql_fix="SELECT o.*, oi.* FROM orders o LEFT JOIN order_items oi ON o.id = oi.order_id WHERE o.id IN (?, ?, ...);"
            ))
        
        elif issue_type == QueryIssueType.INEFFICIENT_JOIN:
            optimizations.append(QueryOptimization(
                issue_type=issue_type,
                severity="high",
                description="Multiple LEFT JOINs creating Cartesian product",
                suggested_fix="Add indexes on join columns and filter early",
                estimated_improvement="70% faster",
                sql_fix=f"CREATE INDEX idx_{tables[1]}_a_id ON {tables[1]} (a_id); CREATE INDEX idx_{tables[2]}_b_id ON {tables[2]} (b_id);"
            ))
        
        return optimizations
    
    def _estimate_cost(self, avg_time_ms: float, execution_count: int) -> float:
        """Estimates cost impact of slow query."""
        # Simple cost model: time * count * cost_per_ms
        cost_per_ms = 0.0001  # $0.0001 per ms of compute
        return round(avg_time_ms * execution_count * cost_per_ms, 2)
    
    def _calculate_statistics(self, slow_queries: List[SlowQuery]) -> QueryStatistics:
        """Calculates aggregate statistics."""
        total_time = sum(sq.execution_time_ms * sq.execution_count for sq in slow_queries)
        total_count = sum(sq.execution_count for sq in slow_queries)
        avg_time = total_time / total_count if total_count > 0 else 0
        optimization_count = sum(len(sq.optimizations) for sq in slow_queries)
        
        return QueryStatistics(
            total_slow_queries=len(slow_queries),
            total_execution_time_ms=total_time,
            avg_execution_time_ms=round(avg_time, 2),
            queries_analyzed=len(slow_queries),
            optimization_opportunities=optimization_count
        )
    
    def _analyze_impact(self, slow_queries: List[SlowQuery]) -> ImpactAnalysis:
        """Analyzes business impact of slow queries."""
        current_cost = sum(sq.cost_estimate for sq in slow_queries)
        
        # Estimate 60% average improvement
        potential_savings = current_cost * 0.6
        
        return ImpactAnalysis(
            current_cost_per_day=round(current_cost, 2),
            potential_savings_per_day=round(potential_savings, 2),
            affected_users=15000,  # Simulated
            business_impact="High - User experience degraded by slow page loads"
        )
    
    def _get_top_optimizations(self, slow_queries: List[SlowQuery]) -> List[QueryOptimization]:
        """Extracts top optimization opportunities."""
        all_optimizations = []
        for sq in slow_queries:
            for opt in sq.optimizations:
                all_optimizations.append(opt)
        
        # Sort by severity and estimated improvement
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_opts = sorted(all_optimizations, key=lambda x: severity_order.get(x.severity, 3))
        
        return sorted_opts[:10]
    
    def _generate_auto_fix_sql(self, slow_queries: List[SlowQuery]) -> List[str]:
        """Generates SQL statements to fix issues."""
        sql_statements = ["-- Auto-generated query optimizations", ""]
        
        for sq in slow_queries:
            for opt in sq.optimizations:
                if opt.sql_fix:
                    sql_statements.append(f"-- {opt.description}")
                    sql_statements.append(opt.sql_fix)
                    sql_statements.append("")
        
        return sql_statements
