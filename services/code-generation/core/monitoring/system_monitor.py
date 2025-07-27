"""
System monitoring and health checks
"""
import asyncio
import logging
import psutil
import platform
import time
from typing import Dict, List, Any, Callable
from datetime import datetime

from .base import SystemMetrics, ApplicationMetrics, HealthCheck, MonitoringStatus

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor system-level metrics and health"""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.monitoring_enabled = True
        self._boot_time = psutil.boot_time()
    
    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_func
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024 ** 3)
            disk_free_gb = disk.free / (1024 ** 3)
            
            # Network metrics
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            # Load average (Unix-like systems)
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                # Windows doesn't have load average
                load_average = [0.0, 0.0, 0.0]
            
            # System uptime
            uptime_seconds = time.time() - self._boot_time
            
            # Process count
            process_count = len(psutil.pids())
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                load_average=load_average,
                uptime_seconds=uptime_seconds,
                process_count=process_count
            )
        
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise
    
    async def run_health_checks(self) -> List[HealthCheck]:
        """Run all registered health checks"""
        results = []
        
        for name, check_func in self.health_checks.items():
            start_time = time.time()
            
            try:
                # Run health check
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Parse result
                if isinstance(result, dict):
                    status = MonitoringStatus(result.get('status', 'unknown'))
                    message = result.get('message', 'Health check completed')
                    details = result.get('details', {})
                elif isinstance(result, bool):
                    status = MonitoringStatus.HEALTHY if result else MonitoringStatus.CRITICAL
                    message = "Health check passed" if result else "Health check failed"
                    details = {}
                else:
                    status = MonitoringStatus.UNKNOWN
                    message = str(result)
                    details = {}
                
                health_check = HealthCheck(
                    component=name,
                    status=status,
                    message=message,
                    duration_ms=duration_ms,
                    details=details
                )
                
                results.append(health_check)
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                health_check = HealthCheck(
                    component=name,
                    status=MonitoringStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    duration_ms=duration_ms,
                    details={'error': str(e), 'traceback': str(e.__traceback__)}
                )
                
                results.append(health_check)
                logger.error(f"Health check {name} failed: {e}")
        
        return results
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get general system information"""
        try:
            return {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'hostname': platform.node(),
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total_gb': psutil.virtual_memory().total / (1024 ** 3),
                'disk_total_gb': psutil.disk_usage('/').total / (1024 ** 3),
                'boot_time': datetime.fromtimestamp(self._boot_time).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    async def check_resource_thresholds(self, metrics: SystemMetrics) -> List[Dict[str, Any]]:
        """Check if system metrics exceed thresholds"""
        warnings = []
        
        # CPU threshold
        if metrics.cpu_percent > 80:
            warnings.append({
                'type': 'cpu',
                'severity': 'warning' if metrics.cpu_percent < 90 else 'critical',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent,
                'threshold': 80
            })
        
        # Memory threshold
        if metrics.memory_percent > 80:
            warnings.append({
                'type': 'memory',
                'severity': 'warning' if metrics.memory_percent < 90 else 'critical',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent,
                'threshold': 80
            })
        
        # Disk threshold
        if metrics.disk_usage_percent > 80:
            warnings.append({
                'type': 'disk',
                'severity': 'warning' if metrics.disk_usage_percent < 90 else 'critical',
                'message': f'High disk usage: {metrics.disk_usage_percent:.1f}%',
                'value': metrics.disk_usage_percent,
                'threshold': 80
            })
        
        # Load average threshold (for Unix-like systems)
        if metrics.load_average and metrics.load_average[0] > psutil.cpu_count():
            warnings.append({
                'type': 'load',
                'severity': 'warning',
                'message': f'High load average: {metrics.load_average[0]:.2f}',
                'value': metrics.load_average[0],
                'threshold': psutil.cpu_count()
            })
        
        return warnings


class ApplicationMonitor:
    """Monitor application-level metrics"""
    
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
        self.active_connections = 0
        self.schemas_processed = 0
        self.code_generations = 0
        self.active_workflows = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.database_connections = 0
        self.queue_size = 0
    
    def track_request(self, success: bool = True, response_time_ms: float = 0):
        """Track an API request"""
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        if response_time_ms > 0:
            self.response_times.append(response_time_ms)
            # Keep only last 1000 response times
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
    
    def track_schema_processing(self):
        """Track schema processing"""
        self.schemas_processed += 1
    
    def track_code_generation(self):
        """Track code generation"""
        self.code_generations += 1
    
    def track_cache_access(self, hit: bool):
        """Track cache access"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def set_active_connections(self, count: int):
        """Set current active connections"""
        self.active_connections = count
    
    def set_active_workflows(self, count: int):
        """Set current active workflows"""
        self.active_workflows = count
    
    def set_database_connections(self, count: int):
        """Set current database connections"""
        self.database_connections = count
    
    def set_queue_size(self, size: int):
        """Set current queue size"""
        self.queue_size = size
    
    def get_metrics(self) -> ApplicationMetrics:
        """Get current application metrics"""
        # Calculate error rate
        total_requests = max(self.request_count, 1)
        error_rate_percent = (self.error_count / total_requests) * 100
        
        # Calculate average response time
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )
        
        # Calculate cache hit rate
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            (self.cache_hits / total_cache_requests) * 100
            if total_cache_requests > 0 else 0
        )
        
        return ApplicationMetrics(
            active_connections=self.active_connections,
            total_requests=self.request_count,
            successful_requests=self.success_count,
            failed_requests=self.error_count,
            average_response_time_ms=avg_response_time,
            error_rate_percent=error_rate_percent,
            schemas_processed=self.schemas_processed,
            code_generations=self.code_generations,
            active_workflows=self.active_workflows,
            cache_hit_rate=cache_hit_rate,
            database_connections=self.database_connections,
            queue_size=self.queue_size
        )
    
    def reset_counters(self):
        """Reset all counters (for testing or periodic reset)"""
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.response_times.clear()
        self.schemas_processed = 0
        self.code_generations = 0
        self.cache_hits = 0
        self.cache_misses = 0
