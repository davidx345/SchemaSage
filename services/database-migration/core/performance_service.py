"""
Performance Optimization Service - Modularized
Phase 4: Query Analysis & Database Optimization
"""

# Import all performance services from modular structure
from .performance.query_analyzer import QueryAnalyzer
from .performance.index_optimizer import IndexOptimizer
from .performance.performance_monitor import PerformanceMonitor

# Export classes for backward compatibility
__all__ = [
    'QueryAnalyzer',
    'IndexOptimizer',
    'PerformanceMonitor'
]
