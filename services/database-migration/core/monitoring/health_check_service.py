"""
Health Check Service - Database health monitoring
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.monitoring import HealthCheck, HealthCheckResult
from ...core.database import DatabaseManager
from ...utils.logging import get_logger
from ...utils.exceptions import MonitoringError

logger = get_logger(__name__)

class HealthCheckService:
    """Database health check service."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def execute_health_checks(
        self,
        workspace_id: str,
        connection_id: Optional[str] = None,
        session: AsyncSession = None
    ) -> List[HealthCheckResult]:
        """Execute all health checks for a workspace or connection."""
        
        results = []
        
        try:
            # Load health checks
            health_checks = await self._load_health_checks(workspace_id, connection_id, session)
            
            # Execute each health check
            for check in health_checks:
                if check.is_enabled:
                    result = await self._execute_health_check(check)
                    results.append(result)
        
        except Exception as e:
            logger.error(f"Health check execution failed: {e}")
            raise MonitoringError(f"Health check execution failed: {e}")
        
        return results
    
    async def _load_health_checks(
        self,
        workspace_id: str,
        connection_id: Optional[str],
        session: AsyncSession
    ) -> List[HealthCheck]:
        """Load health checks from database."""
        
        # Return sample health checks
        return [
            HealthCheck(
                workspace_id=workspace_id,
                connection_id=connection_id,
                name="Database Connectivity",
                description="Check if database connection is working",
                check_type="connectivity",
                check_sql="SELECT 1",
                expected_result=1,
                timeout_seconds=30,
                interval_minutes=5,
                created_by="system"
            ),
            HealthCheck(
                workspace_id=workspace_id,
                connection_id=connection_id,
                name="Query Performance",
                description="Check average query performance",
                check_type="query_performance",
                check_sql="SELECT avg(mean_exec_time) FROM pg_stat_statements WHERE calls > 10",
                timeout_seconds=60,
                interval_minutes=10,
                created_by="system"
            ),
            HealthCheck(
                workspace_id=workspace_id,
                connection_id=connection_id,
                name="Data Freshness",
                description="Check if data is being updated recently",
                check_type="data_freshness",
                check_sql="SELECT COUNT(*) FROM user_activity WHERE created_at > NOW() - INTERVAL '1 hour'",
                timeout_seconds=30,
                interval_minutes=15,
                created_by="system"
            )
        ]
    
    async def _execute_health_check(self, check: HealthCheck) -> HealthCheckResult:
        """Execute a single health check."""
        
        start_time = datetime.utcnow()
        
        result = HealthCheckResult(
            health_check_id=check.health_check_id,
            executed_at=start_time
        )
        
        try:
            if check.check_type == "connectivity":
                success, response_time, value = await self._check_connectivity(check)
            elif check.check_type == "query_performance":
                success, response_time, value = await self._check_query_performance(check)
            elif check.check_type == "data_freshness":
                success, response_time, value = await self._check_data_freshness(check)
            elif check.check_type == "custom":
                success, response_time, value = await self._check_custom(check)
            else:
                success, response_time, value = False, 0.0, None
                result.error_message = f"Unknown health check type: {check.check_type}"
            
            result.success = success
            result.response_time_ms = response_time
            result.result_value = value
            
            # Determine status
            if success:
                if check.expected_result is not None:
                    if value == check.expected_result:
                        result.status = "healthy"
                    else:
                        result.status = "warning"
                else:
                    result.status = "healthy"
            else:
                result.status = "critical"
            
            # Update health check record
            check.last_run = start_time
            if success:
                check.last_success = start_time
                check.consecutive_failures = 0
            else:
                check.last_failure = start_time
                check.consecutive_failures += 1
        
        except Exception as e:
            result.success = False
            result.status = "error"
            result.error_message = str(e)
            logger.error(f"Health check {check.health_check_id} failed: {e}")
        
        # Calculate execution time
        end_time = datetime.utcnow()
        result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return result
    
    async def _check_connectivity(self, check: HealthCheck) -> Tuple[bool, float, Any]:
        """Check database connectivity."""
        
        start_time = datetime.utcnow()
        
        try:
            connection = await self.db_manager.get_connection(check.connection_id)
            
            async with connection.execute(text(check.check_sql or "SELECT 1")) as result:
                row = await result.fetchone()
                value = row[0] if row else None
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return True, response_time, value
        
        except Exception as e:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            return False, response_time, str(e)
    
    async def _check_query_performance(self, check: HealthCheck) -> Tuple[bool, float, Any]:
        """Check query performance metrics."""
        
        start_time = datetime.utcnow()
        
        try:
            connection = await self.db_manager.get_connection(check.connection_id)
            
            # Execute performance check query
            async with connection.execute(text(check.check_sql)) as result:
                row = await result.fetchone()
                avg_time = float(row[0]) if row and row[0] else 0.0
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Consider healthy if average query time is under 1 second
            success = avg_time < 1000.0
            
            return success, response_time, avg_time
        
        except Exception as e:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            return False, response_time, str(e)
    
    async def _check_data_freshness(self, check: HealthCheck) -> Tuple[bool, float, Any]:
        """Check data freshness."""
        
        start_time = datetime.utcnow()
        
        try:
            connection = await self.db_manager.get_connection(check.connection_id)
            
            async with connection.execute(text(check.check_sql)) as result:
                row = await result.fetchone()
                count = int(row[0]) if row and row[0] else 0
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Consider healthy if there's recent activity
            success = count > 0
            
            return success, response_time, count
        
        except Exception as e:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            return False, response_time, str(e)
    
    async def _check_custom(self, check: HealthCheck) -> Tuple[bool, float, Any]:
        """Execute custom health check."""
        
        start_time = datetime.utcnow()
        
        try:
            connection = await self.db_manager.get_connection(check.connection_id)
            
            async with connection.execute(text(check.check_sql)) as result:
                row = await result.fetchone()
                value = row[0] if row else None
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # For custom checks, assume success if no exception and value is returned
            success = value is not None
            
            return success, response_time, value
        
        except Exception as e:
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            return False, response_time, str(e)
