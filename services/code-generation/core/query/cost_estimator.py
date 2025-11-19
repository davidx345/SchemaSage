"""
Query Cost Estimator

Estimates execution cost for SQL queries based on parsed structure.
"""

import logging
from typing import Dict, List, Optional
from models.query_models import (
    CostBreakdown, ExecutionStats, OptimizationSuggestion,
    OptimizationCategory, CostSeverity, QueryType
)

logger = logging.getLogger(__name__)


class CostEstimator:
    """Estimate query execution costs"""
    
    # Base cost multipliers
    BASE_CPU_COST = 1.0
    BASE_IO_COST = 2.0
    BASE_MEMORY_COST = 0.5
    
    # Operation cost weights
    TABLE_SCAN_COST = 10.0
    INDEX_SCAN_COST = 2.0
    JOIN_COST = 5.0
    SUBQUERY_COST = 8.0
    AGGREGATION_COST = 3.0
    WHERE_CLAUSE_COST = 1.0
    
    def __init__(self):
        self.cpu_cost = 0.0
        self.io_cost = 0.0
        self.memory_cost = 0.0
        
    def estimate(
        self,
        parsed_query: Dict,
        schema_info: Optional[Dict] = None
    ) -> tuple[CostBreakdown, ExecutionStats]:
        """
        Estimate query execution cost
        
        Args:
            parsed_query: Parsed query metadata from SQLParser
            schema_info: Optional schema information (row counts, indexes)
            
        Returns:
            Tuple of (CostBreakdown, ExecutionStats)
        """
        # Reset costs
        self.cpu_cost = self.BASE_CPU_COST
        self.io_cost = self.BASE_IO_COST
        self.memory_cost = self.BASE_MEMORY_COST
        
        # Extract parsed data
        tables = parsed_query.get("tables", [])
        joins = parsed_query.get("joins", [])
        where_clauses = parsed_query.get("where_clauses", [])
        subqueries = parsed_query.get("subqueries", 0)
        aggregations = parsed_query.get("aggregations", [])
        
        # Estimate row counts
        estimated_rows = self._estimate_rows(tables, schema_info)
        
        # Calculate costs
        self._add_table_scan_costs(tables, estimated_rows)
        self._add_join_costs(joins, estimated_rows)
        self._add_where_costs(where_clauses)
        self._add_subquery_costs(subqueries)
        self._add_aggregation_costs(aggregations, estimated_rows)
        
        # Build cost breakdown
        total_cost = self.cpu_cost + self.io_cost + self.memory_cost
        cost_breakdown = CostBreakdown(
            cpu_cost=round(self.cpu_cost, 2),
            io_cost=round(self.io_cost, 2),
            memory_cost=round(self.memory_cost, 2),
            network_cost=0.0,
            total_cost=round(total_cost, 2),
            cost_unit="abstract_units"
        )
        
        # Build execution stats
        execution_stats = ExecutionStats(
            estimated_rows=estimated_rows,
            estimated_time_ms=self._estimate_time(total_cost),
            tables_accessed=tables,
            indexes_used=self._detect_indexes(where_clauses, schema_info),
            full_table_scans=len(tables) if not where_clauses else 0
        )
        
        return cost_breakdown, execution_stats
    
    def _estimate_rows(self, tables: List[str], schema_info: Optional[Dict]) -> int:
        """Estimate number of rows processed"""
        if not tables:
            return 0
        
        # Use schema info if available
        if schema_info and "row_counts" in schema_info:
            total_rows = 0
            for table in tables:
                total_rows += schema_info["row_counts"].get(table, 10000)
            return total_rows
        
        # Default estimate: 10k rows per table
        return len(tables) * 10000
    
    def _add_table_scan_costs(self, tables: List[str], estimated_rows: int):
        """Add costs for table scans"""
        num_tables = len(tables)
        
        # I/O cost for reading tables
        self.io_cost += num_tables * self.TABLE_SCAN_COST * (estimated_rows / 10000)
        
        # CPU cost for processing rows
        self.cpu_cost += num_tables * 2.0 * (estimated_rows / 10000)
    
    def _add_join_costs(self, joins: List[str], estimated_rows: int):
        """Add costs for JOIN operations"""
        num_joins = len(joins)
        
        if num_joins == 0:
            return
        
        # CPU cost for join operations
        join_factor = 1.5 ** num_joins  # Exponential growth
        self.cpu_cost += self.JOIN_COST * join_factor * (estimated_rows / 10000)
        
        # Memory cost for hash tables
        self.memory_cost += num_joins * 5.0
        
        # I/O cost if spilling to disk
        if num_joins > 2:
            self.io_cost += num_joins * 3.0
    
    def _add_where_costs(self, where_clauses: List[str]):
        """Add costs for WHERE clause filtering"""
        num_clauses = len(where_clauses)
        
        # CPU cost for condition evaluation
        self.cpu_cost += num_clauses * self.WHERE_CLAUSE_COST
    
    def _add_subquery_costs(self, subqueries: int):
        """Add costs for subqueries"""
        if subqueries == 0:
            return
        
        # Subqueries multiply costs
        multiplier = 1.5 ** subqueries
        self.cpu_cost *= multiplier
        self.io_cost *= multiplier
        self.memory_cost += subqueries * self.SUBQUERY_COST
    
    def _add_aggregation_costs(self, aggregations: List[str], estimated_rows: int):
        """Add costs for aggregation functions"""
        num_aggs = len(aggregations)
        
        if num_aggs == 0:
            return
        
        # CPU cost for aggregation
        self.cpu_cost += num_aggs * self.AGGREGATION_COST * (estimated_rows / 10000)
        
        # Memory cost for aggregation buffers
        self.memory_cost += num_aggs * 3.0
    
    def _detect_indexes(
        self,
        where_clauses: List[str],
        schema_info: Optional[Dict]
    ) -> List[str]:
        """Detect which indexes might be used"""
        indexes = []
        
        if schema_info and "indexes" in schema_info:
            # Check if WHERE clauses match indexed columns
            for clause in where_clauses:
                for index in schema_info["indexes"]:
                    if any(col in clause.lower() for col in index.get("columns", [])):
                        indexes.append(index.get("name", "unknown_index"))
        
        return indexes
    
    def _estimate_time(self, total_cost: float) -> float:
        """
        Estimate execution time in milliseconds
        
        Rough heuristic: 1 cost unit ≈ 10ms
        """
        return round(total_cost * 10.0, 2)


def estimate_query_cost(
    parsed_query: Dict,
    schema_info: Optional[Dict] = None
) -> tuple[CostBreakdown, ExecutionStats]:
    """
    Convenience function to estimate query cost
    
    Args:
        parsed_query: Parsed query metadata
        schema_info: Optional schema information
        
    Returns:
        Tuple of (CostBreakdown, ExecutionStats)
    """
    estimator = CostEstimator()
    return estimator.estimate(parsed_query, schema_info)


class OptimizationEngine:
    """Generate optimization suggestions based on query analysis"""
    
    @staticmethod
    def generate_suggestions(
        parsed_query: Dict,
        execution_stats: ExecutionStats,
        cost_breakdown: CostBreakdown
    ) -> List[OptimizationSuggestion]:
        """
        Generate optimization suggestions
        
        Args:
            parsed_query: Parsed query metadata
            execution_stats: Execution statistics
            cost_breakdown: Cost breakdown
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Check for full table scans
        if execution_stats.full_table_scans > 0:
            suggestions.append(OptimizationSuggestion(
                category=OptimizationCategory.INDEX,
                severity=CostSeverity.HIGH,
                title="Full table scan detected",
                description=f"Query performs {execution_stats.full_table_scans} full table scan(s) without using indexes",
                suggestion="Add indexes on columns used in WHERE clauses to avoid full table scans",
                potential_savings=60.0,
                sql_example="CREATE INDEX idx_column_name ON table_name(column_name);"
            ))
        
        # Check for multiple joins
        num_joins = len(parsed_query.get("joins", []))
        if num_joins > 3:
            suggestions.append(OptimizationSuggestion(
                category=OptimizationCategory.QUERY_REWRITE,
                severity=CostSeverity.MEDIUM,
                title="Complex join operation",
                description=f"Query contains {num_joins} JOIN operations which may be expensive",
                suggestion="Consider breaking down complex joins into smaller queries or using materialized views",
                potential_savings=30.0
            ))
        
        # Check for subqueries
        subqueries = parsed_query.get("subqueries", 0)
        if subqueries > 0:
            suggestions.append(OptimizationSuggestion(
                category=OptimizationCategory.QUERY_REWRITE,
                severity=CostSeverity.MEDIUM if subqueries == 1 else CostSeverity.HIGH,
                title="Subquery detected",
                description=f"Query contains {subqueries} subquery/subqueries which can be expensive",
                suggestion="Consider using JOINs instead of subqueries or using WITH (CTE) clauses",
                potential_savings=40.0,
                sql_example="WITH cte AS (SELECT ...) SELECT ... FROM cte JOIN ..."
            ))
        
        # Check for high I/O cost
        if cost_breakdown.io_cost > 50.0:
            suggestions.append(OptimizationSuggestion(
                category=OptimizationCategory.CACHING,
                severity=CostSeverity.HIGH,
                title="High I/O cost",
                description=f"Query has high I/O cost ({cost_breakdown.io_cost} units)",
                suggestion="Consider implementing query result caching or adding appropriate indexes",
                potential_savings=50.0
            ))
        
        # Check for high complexity
        complexity = parsed_query.get("complexity_score", 0)
        if complexity > 70:
            suggestions.append(OptimizationSuggestion(
                category=OptimizationCategory.QUERY_REWRITE,
                severity=CostSeverity.CRITICAL,
                title="High query complexity",
                description=f"Query complexity score is {complexity}/100",
                suggestion="Simplify query by breaking into smaller operations or using intermediate tables",
                potential_savings=45.0
            ))
        
        # Check for aggregations without GROUP BY optimization
        aggregations = parsed_query.get("aggregations", [])
        if len(aggregations) > 2:
            suggestions.append(OptimizationSuggestion(
                category=OptimizationCategory.SCHEMA_DESIGN,
                severity=CostSeverity.LOW,
                title="Multiple aggregations",
                description=f"Query uses {len(aggregations)} aggregation functions",
                suggestion="Consider pre-aggregating data in materialized views or summary tables",
                potential_savings=25.0
            ))
        
        return suggestions
