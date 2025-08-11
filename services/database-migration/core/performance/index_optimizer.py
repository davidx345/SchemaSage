"""
Index Optimizer Module
Database index optimization and recommendation service.
"""
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.performance import IndexRecommendation
from ...core.database import DatabaseManager
from ...utils.logging import get_logger
from ...utils.exceptions import PerformanceAnalysisError

logger = get_logger(__name__)

class IndexOptimizer:
    """Database index optimization service."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def analyze_index_opportunities(
        self,
        connection_id: str,
        workspace_id: str,
        session: AsyncSession
    ) -> List[IndexRecommendation]:
        """Analyze and recommend index optimizations."""
        
        connection = await self.db_manager.get_connection(connection_id)
        recommendations = []
        
        try:
            # Get table statistics
            tables = await self._get_table_statistics(connection)
            
            # Analyze query patterns (simplified)
            query_patterns = await self._analyze_query_patterns(connection_id, session)
            
            # Generate index recommendations
            for table_name, stats in tables.items():
                table_recommendations = await self._recommend_indexes_for_table(
                    table_name, stats, query_patterns, workspace_id, connection_id
                )
                recommendations.extend(table_recommendations)
            
        except Exception as e:
            logger.error(f"Index analysis failed: {e}")
            raise PerformanceAnalysisError(f"Index analysis failed: {e}")
        
        return recommendations
    
    async def _get_table_statistics(self, connection: Any) -> Dict[str, Dict[str, Any]]:
        """Get table statistics for analysis."""
        
        tables = {}
        
        try:
            # Get table sizes and row counts (PostgreSQL example)
            stats_query = """
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_tuples,
                n_dead_tup as dead_tuples
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            """
            
            async with connection.execute(text(stats_query)) as result:
                rows = await result.fetchall()
                
                for row in rows:
                    table_name = f"{row[0]}.{row[1]}"
                    tables[table_name] = {
                        'inserts': row[2],
                        'updates': row[3],
                        'deletes': row[4],
                        'live_tuples': row[5],
                        'dead_tuples': row[6]
                    }
        
        except Exception as e:
            logger.warning(f"Could not get table statistics: {e}")
        
        return tables
    
    async def _analyze_query_patterns(
        self, 
        connection_id: str, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze historical query patterns."""
        
        # In a real implementation, this would analyze query logs
        # For now, return mock patterns
        return {
            'frequent_where_columns': ['id', 'created_at', 'user_id'],
            'frequent_join_columns': ['id', 'user_id', 'order_id'],
            'frequent_order_columns': ['created_at', 'updated_at']
        }
    
    async def _recommend_indexes_for_table(
        self,
        table_name: str,
        stats: Dict[str, Any],
        patterns: Dict[str, Any],
        workspace_id: str,
        connection_id: str
    ) -> List[IndexRecommendation]:
        """Generate index recommendations for a specific table."""
        
        recommendations = []
        
        # High-volume tables should have better indexing
        if stats.get('live_tuples', 0) > 10000:
            
            # Recommend indexes on frequently queried columns
            for column in patterns.get('frequent_where_columns', []):
                recommendation = IndexRecommendation(
                    workspace_id=workspace_id,
                    connection_id=connection_id,
                    table_name=table_name,
                    columns=[column],
                    index_type="btree",
                    estimated_benefit_score=0.8,
                    estimated_size_mb=stats.get('live_tuples', 0) * 0.001,  # Rough estimate
                    creation_sql=f"CREATE INDEX idx_{table_name}_{column} ON {table_name} ({column});",
                    impact_analysis={
                        'query_performance_improvement': '20-40%',
                        'storage_overhead': f"{stats.get('live_tuples', 0) * 0.001:.1f} MB",
                        'maintenance_overhead': 'Low'
                    }
                )
                recommendations.append(recommendation)
        
        return recommendations
