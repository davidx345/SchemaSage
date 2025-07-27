"""
System resource monitoring and health tracking
"""

import time
import psutil
import logging
import threading
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Any

from .models import SystemSnapshot, SystemTrend, MetricType
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Monitors system resources and health metrics
    """
    
    def __init__(self, metrics_collector: MetricsCollector, collection_interval: int = 60):
        self.metrics_collector = metrics_collector
        self.collection_interval = collection_interval  # seconds
        
        # System snapshots storage
        self.system_snapshots: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        
        # Monitoring state
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Performance tracking
        self._last_network_counters = None
        self._network_speed_mbps = {"bytes_sent": 0.0, "bytes_recv": 0.0}
    
    def start_monitoring(self):
        """Start background system monitoring"""
        if self._monitoring_active:
            logger.warning("System monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self._monitor_thread.start()
        
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop background system monitoring"""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        logger.info("System monitoring stopped")
    
    def get_current_snapshot(self) -> SystemSnapshot:
        """Get current system resource snapshot"""
        try:
            # Get network I/O counters
            net_io = psutil.net_io_counters()
            network_io = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
            
            # Calculate disk usage for root filesystem
            try:
                disk_usage = psutil.disk_usage('/').percent
            except:
                # Windows fallback
                disk_usage = psutil.disk_usage('C:\\').percent
            
            snapshot = SystemSnapshot(
                timestamp=datetime.now(),
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                memory_used_mb=psutil.virtual_memory().used / 1024 / 1024,
                disk_usage_percent=disk_usage,
                network_io=network_io,
                process_count=len(psutil.pids())
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error collecting system snapshot: {e}")
            # Return empty snapshot
            return SystemSnapshot(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                network_io={},
                process_count=0
            )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        snapshot = self.get_current_snapshot()
        
        # Determine health status
        status = 'healthy'
        issues = []
        
        if snapshot.cpu_percent > 90:
            status = 'critical'
            issues.append(f"Critical CPU usage: {snapshot.cpu_percent:.1f}%")
        elif snapshot.cpu_percent > 80:
            status = 'warning' if status == 'healthy' else status
            issues.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")
        
        if snapshot.memory_percent > 90:
            status = 'critical'
            issues.append(f"Critical memory usage: {snapshot.memory_percent:.1f}%")
        elif snapshot.memory_percent > 80:
            status = 'warning' if status == 'healthy' else status
            issues.append(f"High memory usage: {snapshot.memory_percent:.1f}%")
        
        if snapshot.disk_usage_percent > 95:
            status = 'critical'
            issues.append(f"Critical disk usage: {snapshot.disk_usage_percent:.1f}%")
        elif snapshot.disk_usage_percent > 85:
            status = 'warning' if status == 'healthy' else status
            issues.append(f"High disk usage: {snapshot.disk_usage_percent:.1f}%")
        
        return {
            'timestamp': snapshot.timestamp.isoformat(),
            'status': status,
            'issues': issues,
            'metrics': {
                'cpu_percent': snapshot.cpu_percent,
                'memory_percent': snapshot.memory_percent,
                'memory_used_mb': snapshot.memory_used_mb,
                'disk_usage_percent': snapshot.disk_usage_percent,
                'process_count': snapshot.process_count,
                'network_speed_mbps': self._network_speed_mbps
            }
        }
    
    def get_system_trends(self, time_range: timedelta) -> Dict[str, SystemTrend]:
        """Get system resource trends over time range"""
        cutoff = datetime.now() - time_range
        recent_snapshots = [
            s for s in self.system_snapshots 
            if s.timestamp >= cutoff
        ]
        
        if len(recent_snapshots) < 2:
            return {}
        
        time_span_minutes = time_range.total_seconds() / 60
        
        trends = {}
        
        # CPU trend
        cpu_values = [s.cpu_percent for s in recent_snapshots]
        trends['cpu'] = SystemTrend.calculate_trend('cpu_percent', cpu_values, time_span_minutes)
        
        # Memory trend
        memory_values = [s.memory_percent for s in recent_snapshots]
        trends['memory'] = SystemTrend.calculate_trend('memory_percent', memory_values, time_span_minutes)
        
        # Disk trend
        disk_values = [s.disk_usage_percent for s in recent_snapshots]
        trends['disk'] = SystemTrend.calculate_trend('disk_usage_percent', disk_values, time_span_minutes)
        
        # Process count trend
        process_values = [float(s.process_count) for s in recent_snapshots]
        trends['processes'] = SystemTrend.calculate_trend('process_count', process_values, time_span_minutes)
        
        return trends
    
    def get_resource_utilization_history(self, hours: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Get historical resource utilization"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [
            s for s in self.system_snapshots 
            if s.timestamp >= cutoff
        ]
        
        return {
            'cpu': [
                {'timestamp': s.timestamp.isoformat(), 'value': s.cpu_percent}
                for s in recent_snapshots
            ],
            'memory': [
                {'timestamp': s.timestamp.isoformat(), 'value': s.memory_percent}
                for s in recent_snapshots
            ],
            'disk': [
                {'timestamp': s.timestamp.isoformat(), 'value': s.disk_usage_percent}
                for s in recent_snapshots
            ],
            'processes': [
                {'timestamp': s.timestamp.isoformat(), 'value': s.process_count}
                for s in recent_snapshots
            ]
        }
    
    def get_process_information(self) -> List[Dict[str, Any]]:
        """Get information about running processes"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
                try:
                    proc_info = proc.info
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent'],
                        'create_time': proc_info['create_time']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error getting process information: {e}")
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
        
        # Return top 20 processes
        return processes[:20]
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'active_connections': net_connections,
                'speed_mbps': self._network_speed_mbps
            }
        except Exception as e:
            logger.error(f"Error getting network statistics: {e}")
            return {}
    
    def get_disk_statistics(self) -> Dict[str, Any]:
        """Get disk I/O statistics"""
        try:
            disk_io = psutil.disk_io_counters()
            
            return {
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count,
                'read_time': disk_io.read_time,
                'write_time': disk_io.write_time
            }
        except Exception as e:
            logger.error(f"Error getting disk statistics: {e}")
            return {}
    
    def _monitor_system(self):
        """Background system monitoring loop"""
        logger.info("Starting system monitoring loop")
        
        while self._monitoring_active:
            try:
                # Collect system snapshot
                snapshot = self.get_current_snapshot()
                self.system_snapshots.append(snapshot)
                
                # Calculate network speed
                self._calculate_network_speed(snapshot)
                
                # Record metrics
                self.metrics_collector.record_metric(
                    MetricType.CPU_USAGE, 
                    snapshot.cpu_percent,
                    context={'source': 'system_monitor'}
                )
                
                self.metrics_collector.record_metric(
                    MetricType.MEMORY_USAGE, 
                    snapshot.memory_percent,
                    context={'source': 'system_monitor'}
                )
                
                # Log health status if concerning
                if snapshot.cpu_percent > 80 or snapshot.memory_percent > 80:
                    logger.warning(
                        f"High resource usage - CPU: {snapshot.cpu_percent:.1f}%, "
                        f"Memory: {snapshot.memory_percent:.1f}%"
                    )
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                time.sleep(self.collection_interval)
        
        logger.info("System monitoring loop stopped")
    
    def _calculate_network_speed(self, current_snapshot: SystemSnapshot):
        """Calculate network speed in Mbps"""
        if self._last_network_counters is None:
            self._last_network_counters = {
                'bytes_sent': current_snapshot.network_io.get('bytes_sent', 0),
                'bytes_recv': current_snapshot.network_io.get('bytes_recv', 0),
                'timestamp': current_snapshot.timestamp
            }
            return
        
        # Calculate time difference
        time_diff = (current_snapshot.timestamp - self._last_network_counters['timestamp']).total_seconds()
        
        if time_diff > 0:
            # Calculate bytes per second
            sent_bps = (current_snapshot.network_io.get('bytes_sent', 0) - 
                       self._last_network_counters['bytes_sent']) / time_diff
            recv_bps = (current_snapshot.network_io.get('bytes_recv', 0) - 
                       self._last_network_counters['bytes_recv']) / time_diff
            
            # Convert to Mbps
            self._network_speed_mbps = {
                'bytes_sent': sent_bps * 8 / 1_000_000,  # Convert to Mbps
                'bytes_recv': recv_bps * 8 / 1_000_000
            }
        
        # Update last counters
        self._last_network_counters = {
            'bytes_sent': current_snapshot.network_io.get('bytes_sent', 0),
            'bytes_recv': current_snapshot.network_io.get('bytes_recv', 0),
            'timestamp': current_snapshot.timestamp
        }


class ResourceAlertMonitor:
    """
    Monitors system resources and generates alerts for thresholds
    """
    
    def __init__(self, system_monitor: SystemMonitor):
        self.system_monitor = system_monitor
        
        # Alert thresholds
        self.cpu_warning_threshold = 80.0
        self.cpu_critical_threshold = 90.0
        self.memory_warning_threshold = 80.0
        self.memory_critical_threshold = 90.0
        self.disk_warning_threshold = 85.0
        self.disk_critical_threshold = 95.0
        
        # Alert state tracking
        self._last_alerts = {}
        self._alert_cooldown = timedelta(minutes=5)
    
    def check_resource_alerts(self) -> List[Dict[str, Any]]:
        """Check for resource threshold violations"""
        alerts = []
        snapshot = self.system_monitor.get_current_snapshot()
        now = datetime.now()
        
        # Check CPU alerts
        cpu_alert = self._check_threshold_alert(
            'cpu', snapshot.cpu_percent,
            self.cpu_warning_threshold, self.cpu_critical_threshold
        )
        if cpu_alert and self._should_send_alert('cpu', now):
            alerts.append(cpu_alert)
            self._last_alerts['cpu'] = now
        
        # Check Memory alerts
        memory_alert = self._check_threshold_alert(
            'memory', snapshot.memory_percent,
            self.memory_warning_threshold, self.memory_critical_threshold
        )
        if memory_alert and self._should_send_alert('memory', now):
            alerts.append(memory_alert)
            self._last_alerts['memory'] = now
        
        # Check Disk alerts
        disk_alert = self._check_threshold_alert(
            'disk', snapshot.disk_usage_percent,
            self.disk_warning_threshold, self.disk_critical_threshold
        )
        if disk_alert and self._should_send_alert('disk', now):
            alerts.append(disk_alert)
            self._last_alerts['disk'] = now
        
        return alerts
    
    def _check_threshold_alert(self, resource: str, value: float, warning: float, critical: float) -> Optional[Dict[str, Any]]:
        """Check if value exceeds thresholds"""
        if value >= critical:
            return {
                'resource': resource,
                'level': 'critical',
                'value': value,
                'threshold': critical,
                'message': f"Critical {resource} usage: {value:.1f}% >= {critical}%"
            }
        elif value >= warning:
            return {
                'resource': resource,
                'level': 'warning', 
                'value': value,
                'threshold': warning,
                'message': f"High {resource} usage: {value:.1f}% >= {warning}%"
            }
        
        return None
    
    def _should_send_alert(self, resource: str, now: datetime) -> bool:
        """Check if alert should be sent based on cooldown"""
        last_alert = self._last_alerts.get(resource)
        
        if last_alert is None:
            return True
        
        return (now - last_alert) >= self._alert_cooldown
