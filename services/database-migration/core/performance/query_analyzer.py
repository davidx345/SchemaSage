"""
Query Analyzer Module
Advanced SQL query analysis and optimization.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.performance import QueryAnalysis
from ...core.database import DatabaseManager
from ...utils.logging import get_logger
from ...utils.exceptions import PerformanceAnalysisError

logger = get_logger(__name__)

class QueryAnalyzer:
    """Advanced SQL query analysis and optimization."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    async def analyze_query_performance(
        self,
        connection_id: str,
        query: str,
        workspace_id: str,
        session: AsyncSession
    ) -> QueryAnalysis:
        """Perform comprehensive query performance analysis."""
        
        connection = await self.db_manager.get_connection(connection_id)
        
        analysis = QueryAnalysis(
            workspace_id=workspace_id,
            connection_id=connection_id,
            original_query=query
        )
        
        try:
            # Parse and analyze query structure
            analysis = await self._parse_query_structure(query, analysis)
            
            # Get execution plan
            execution_plan = await self._get_execution_plan(connection, query)
            analysis.execution_plan = execution_plan
            
            # Analyze performance metrics
            performance_metrics = await self._analyze_performance_metrics(connection, query)
            analysis.execution_time_ms = performance_metrics.get('execution_time_ms', 0)
            analysis.cpu_cost = performance_metrics.get('cpu_cost', 0)
            analysis.io_cost = performance_metrics.get('io_cost', 0)
            analysis.memory_usage_mb = performance_metrics.get('memory_usage_mb', 0)
            
            # Identify bottlenecks
            analysis.bottlenecks = await self._identify_bottlenecks(execution_plan, performance_metrics)
            
            # Generate optimization suggestions
            analysis.optimization_suggestions = await self._generate_optimization_suggestions(analysis)
            
            # Calculate complexity score
            analysis.complexity_score = self._calculate_complexity_score(analysis)
            
            # Generate optimized query
            analysis.optimized_query = await self._generate_optimized_query(analysis)
            
            analysis.analyzed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            raise PerformanceAnalysisError(f"Query analysis failed: {e}")
        
        return analysis
    
    async def _parse_query_structure(self, query: str, analysis: QueryAnalysis) -> QueryAnalysis:
        """Parse and analyze SQL query structure."""
        
        query_upper = query.upper().strip()
        
        # Determine query type
        if query_upper.startswith('SELECT'):
            analysis.query_type = "SELECT"
        elif query_upper.startswith('INSERT'):
            analysis.query_type = "INSERT"
        elif query_upper.startswith('UPDATE'):
            analysis.query_type = "UPDATE"
        elif query_upper.startswith('DELETE'):
            analysis.query_type = "DELETE"
        else:
            analysis.query_type = "OTHER"
        
        # Extract tables
        analysis.tables_accessed = self._extract_tables_from_query(query)
        
        # Extract columns
        analysis.columns_accessed = self._extract_columns_from_query(query)
        
        # Analyze joins
        analysis.join_operations = self._analyze_joins(query)
        
        # Check for subqueries
        analysis.has_subqueries = 'SELECT' in query_upper[query_upper.find('FROM'):] if 'FROM' in query_upper else False
        
        # Check for aggregations
        aggregation_functions = ['SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'GROUP BY']
        analysis.has_aggregations = any(func in query_upper for func in aggregation_functions)
        
        # Estimate rows processed (simplified)
        analysis.estimated_rows_processed = 1000  # Default estimate
        
        return analysis
    
    def _extract_tables_from_query(self, query: str) -> List[str]:
        """Extract table names from SQL query."""
        tables = []
        
        # Simple regex patterns for table extraction
        patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            tables.extend(matches)
        
        return list(set(tables))
    
    def _extract_columns_from_query(self, query: str) -> List[str]:
        """Extract column names from SQL query."""
        columns = []
        
        # Extract SELECT columns
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_part = select_match.group(1)
            if '*' not in select_part:
                # Parse individual columns (simplified)
                column_parts = select_part.split(',')
                for part in column_parts:
                    column = part.strip().split()[-1]  # Get last word (column alias or name)
                    if column and not column.upper() in ['AS', 'FROM']:
                        columns.append(column)
        
        # Extract WHERE columns
        where_pattern = r'WHERE\s+.*?(\w+)\s*[=<>!]'
        where_matches = re.findall(where_pattern, query, re.IGNORECASE)
        columns.extend(where_matches)
        
        return list(set(columns))
    
    def _analyze_joins(self, query: str) -> List[Dict[str, Any]]:
        """Analyze JOIN operations in query."""
        joins = []
        
        join_patterns = [
            (r'INNER\s+JOIN\s+(\w+)\s+ON\s+(.*?)(?=\s+(?:INNER|LEFT|RIGHT|OUTER|WHERE|GROUP|ORDER|$))', 'INNER'),
            (r'LEFT\s+(?:OUTER\s+)?JOIN\s+(\w+)\s+ON\s+(.*?)(?=\s+(?:INNER|LEFT|RIGHT|OUTER|WHERE|GROUP|ORDER|$))', 'LEFT'),
            (r'RIGHT\s+(?:OUTER\s+)?JOIN\s+(\w+)\s+ON\s+(.*?)(?=\s+(?:INNER|LEFT|RIGHT|OUTER|WHERE|GROUP|ORDER|$))', 'RIGHT'),
            (r'FULL\s+(?:OUTER\s+)?JOIN\s+(\w+)\s+ON\s+(.*?)(?=\s+(?:INNER|LEFT|RIGHT|OUTER|WHERE|GROUP|ORDER|$))', 'FULL')
        ]
        
        for pattern, join_type in join_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE | re.DOTALL)
            for match in matches:
                joins.append({
                    'type': join_type,
                    'table': match[0],
                    'condition': match[1].strip()
                })
        
        return joins
    
    async def _get_execution_plan(self, connection: Any, query: str) -> Dict[str, Any]:
        """Get query execution plan."""
        
        try:
            # Try EXPLAIN (format varies by database)
            explain_query = f"EXPLAIN (FORMAT JSON) {query}"
            
            async with connection.execute(text(explain_query)) as result:
                plan_result = await result.fetchone()
                
                if plan_result:
                    return json.loads(plan_result[0])
                
        except Exception as e:
            logger.warning(f"Could not get execution plan: {e}")
            
            # Fallback to basic EXPLAIN
            try:
                async with connection.execute(text(f"EXPLAIN {query}")) as result:
                    rows = await result.fetchall()
                    return {"plan_text": [str(row) for row in rows]}
            except Exception as e2:
                logger.warning(f"Basic EXPLAIN also failed: {e2}")
        
        return {"error": "Could not retrieve execution plan"}
    
    async def _analyze_performance_metrics(self, connection: Any, query: str) -> Dict[str, Any]:
        """Analyze query performance metrics."""
        
        metrics = {}
        
        try:
            # Measure actual execution time
            start_time = datetime.utcnow()
            
            async with connection.execute(text(query)) as result:
                # Fetch one row to ensure query executes
                await result.fetchone()
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            metrics['execution_time_ms'] = execution_time
            metrics['cpu_cost'] = execution_time * 0.1  # Simplified estimate
            metrics['io_cost'] = execution_time * 0.05   # Simplified estimate
            metrics['memory_usage_mb'] = 10.0            # Default estimate
            
        except Exception as e:
            logger.warning(f"Could not measure performance metrics: {e}")
            metrics = {
                'execution_time_ms': 0,
                'cpu_cost': 0,
                'io_cost': 0,
                'memory_usage_mb': 0
            }
        
        return metrics
    
    async def _identify_bottlenecks(
        self, 
        execution_plan: Dict[str, Any], 
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify performance bottlenecks."""
        
        bottlenecks = []
        
        # High execution time
        if metrics.get('execution_time_ms', 0) > 1000:
            bottlenecks.append("High execution time detected")
        
        # Analyze execution plan for common issues
        plan_text = str(execution_plan).upper()
        
        if 'SEQ SCAN' in plan_text or 'TABLE SCAN' in plan_text:
            bottlenecks.append("Sequential table scan detected")
        
        if 'NESTED LOOP' in plan_text:
            bottlenecks.append("Nested loop join detected")
        
        if 'SORT' in plan_text and 'MEMORY' not in plan_text:
            bottlenecks.append("Disk-based sorting detected")
        
        if 'HASH' in plan_text and 'MEMORY' not in plan_text:
            bottlenecks.append("Disk-based hash operation detected")
        
        return bottlenecks
    
    async def _generate_optimization_suggestions(self, analysis: QueryAnalysis) -> List[str]:
        """Generate query optimization suggestions."""
        
        suggestions = []
        
        # Index suggestions
        if "Sequential table scan detected" in analysis.bottlenecks:
            suggestions.append("Consider adding indexes on frequently queried columns")
        
        # Join optimization
        if analysis.join_operations and "Nested loop join detected" in analysis.bottlenecks:
            suggestions.append("Consider optimizing join conditions and ensuring proper indexes exist")
        
        # Query structure suggestions
        if analysis.has_subqueries:
            suggestions.append("Consider rewriting subqueries as JOINs for better performance")
        
        if analysis.complexity_score > 0.8:
            suggestions.append("Consider breaking down complex query into simpler parts")
        
        # Column selection
        if 'SELECT *' in analysis.original_query.upper():
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        return suggestions
    
    def _calculate_complexity_score(self, analysis: QueryAnalysis) -> float:
        """Calculate query complexity score (0.0 to 1.0)."""
        
        complexity = 0.0
        
        # Base complexity based on query type
        if analysis.query_type == "SELECT":
            complexity += 0.1
        elif analysis.query_type in ["INSERT", "UPDATE", "DELETE"]:
            complexity += 0.2
        
        # Table count
        table_count = len(analysis.tables_accessed)
        complexity += min(table_count * 0.1, 0.3)
        
        # Join complexity
        join_count = len(analysis.join_operations)
        complexity += min(join_count * 0.15, 0.4)
        
        # Subqueries
        if analysis.has_subqueries:
            complexity += 0.2
        
        # Aggregations
        if analysis.has_aggregations:
            complexity += 0.1
        
        return min(complexity, 1.0)
    
    async def _generate_optimized_query(self, analysis: QueryAnalysis) -> Optional[str]:
        """Generate an optimized version of the query."""
        
        # For now, return basic optimization suggestions
        # In a full implementation, this would use AI or rule-based optimization
        
        optimized = analysis.original_query
        
        # Replace SELECT * with specific columns if possible
        if 'SELECT *' in optimized.upper() and analysis.columns_accessed:
            columns = ', '.join(analysis.columns_accessed[:10])  # Limit to first 10
            optimized = re.sub(r'SELECT\s+\*', f'SELECT {columns}', optimized, flags=re.IGNORECASE)
        
        return optimized if optimized != analysis.original_query else None
