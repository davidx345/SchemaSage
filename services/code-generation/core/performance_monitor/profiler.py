"""
Performance profiling utilities
"""

import cProfile
import pstats
import time
import logging
from io import StringIO
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import functools
import threading

from .models import ProfileResult

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """
    Detailed performance profiler for code analysis
    """
    
    def __init__(self, max_profiles: int = 50):
        self.profiles: Dict[str, ProfileResult] = {}
        self.max_profiles = max_profiles
        self._lock = threading.Lock()
    
    @contextmanager
    def profile(self, profile_name: str, **context):
        """
        Context manager for detailed profiling
        
        Args:
            profile_name: Name for the profile
            **context: Additional context data
            
        Yields:
            Profile name
        """
        profiler = cProfile.Profile()
        start_time = time.time()
        
        try:
            profiler.enable()
            yield profile_name
        finally:
            profiler.disable()
            end_time = time.time()
            
            # Generate profile report
            self._save_profile_result(profiler, profile_name, end_time - start_time, context)
    
    def profile_function(self, profile_name: Optional[str] = None, **context):
        """
        Decorator to profile function execution
        
        Args:
            profile_name: Custom profile name
            **context: Additional context data
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            name = profile_name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile(name, **context):
                    return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def get_profile_report(self, profile_name: str) -> Optional[ProfileResult]:
        """
        Get detailed profile report
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Profile result or None if not found
        """
        with self._lock:
            return self.profiles.get(profile_name)
    
    def list_profiles(self) -> List[str]:
        """
        List available profiles
        
        Returns:
            List of profile names
        """
        with self._lock:
            return list(self.profiles.keys())
    
    def get_profiles_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of all profiles
        
        Returns:
            Dictionary of profile summaries
        """
        with self._lock:
            summary = {}
            for name, profile in self.profiles.items():
                summary[name] = {
                    'timestamp': profile.timestamp,
                    'total_time': profile.total_time,
                    'stats_summary': profile.stats_summary
                }
            return summary
    
    def clear_profiles(self, older_than_hours: Optional[int] = None):
        """
        Clear profile data
        
        Args:
            older_than_hours: Only clear profiles older than this many hours
        """
        with self._lock:
            if older_than_hours is None:
                self.profiles.clear()
                logger.info("Cleared all profiles")
            else:
                cutoff = datetime.now().timestamp() - (older_than_hours * 3600)
                profiles_to_remove = []
                
                for name, profile in self.profiles.items():
                    profile_time = datetime.fromisoformat(profile.timestamp).timestamp()
                    if profile_time < cutoff:
                        profiles_to_remove.append(name)
                
                for name in profiles_to_remove:
                    del self.profiles[name]
                
                logger.info(f"Cleared {len(profiles_to_remove)} profiles older than {older_than_hours} hours")
    
    def _save_profile_result(self, profiler: cProfile.Profile, name: str, total_time: float, context: Dict[str, Any]):
        """Save profiling results"""
        try:
            # Generate profile output
            s = StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            # Extract statistics summary
            stats_summary = self._extract_stats_summary(ps)
            
            # Create profile result
            profile_result = ProfileResult(
                profile_name=name,
                timestamp=datetime.now().isoformat(),
                total_time=total_time,
                profile_output=s.getvalue(),
                stats_summary=stats_summary
            )
            
            with self._lock:
                self.profiles[name] = profile_result
                
                # Limit number of stored profiles
                if len(self.profiles) > self.max_profiles:
                    # Remove oldest profile
                    oldest_name = min(self.profiles.keys(), 
                                    key=lambda k: self.profiles[k].timestamp)
                    del self.profiles[oldest_name]
            
            logger.info(f"Saved profile '{name}' with {total_time:.3f}s total time")
            
        except Exception as e:
            logger.error(f"Error saving profile result: {e}")
    
    def _extract_stats_summary(self, stats: pstats.Stats) -> Dict[str, Any]:
        """Extract summary from pstats"""
        try:
            # Get basic statistics
            summary = {
                'total_calls': getattr(stats, 'total_calls', 0),
                'primitive_calls': getattr(stats, 'prim_calls', 0),
                'total_time': getattr(stats, 'total_tt', 0.0),
            }
            
            # Get top functions by cumulative time
            stats.sort_stats('cumulative')
            
            # Extract function statistics
            if hasattr(stats, 'stats') and stats.stats:
                func_stats = []
                for (filename, line, func_name), (cc, nc, tt, ct, callers) in list(stats.stats.items())[:10]:
                    func_stats.append({
                        'function': f"{filename}:{line}({func_name})",
                        'calls': cc,
                        'total_time': tt,
                        'cumulative_time': ct,
                        'per_call': tt / cc if cc > 0 else 0
                    })
                
                summary['top_functions'] = func_stats
            
            return summary
            
        except Exception as e:
            logger.error(f"Error extracting stats summary: {e}")
            return {
                'total_calls': 0,
                'primitive_calls': 0,
                'total_time': 0.0,
                'top_functions': []
            }


class LineProfiler:
    """
    Line-by-line performance profiler
    """
    
    def __init__(self):
        self.line_profiles: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def profile_lines(self, profile_name: str, target_function: Callable):
        """
        Profile function line by line
        
        Args:
            profile_name: Name for the profile
            target_function: Function to profile
            
        Yields:
            Profile name
        """
        try:
            # Try to use line_profiler if available
            from line_profiler import LineProfiler as LP
            
            profiler = LP()
            profiler.add_function(target_function)
            profiler.enable()
            
            try:
                yield profile_name
            finally:
                profiler.disable()
                
                # Get results
                s = StringIO()
                profiler.print_stats(stream=s)
                
                # Save results
                with self._lock:
                    self.line_profiles[profile_name] = {
                        'timestamp': datetime.now().isoformat(),
                        'function': f"{target_function.__module__}.{target_function.__name__}",
                        'profile_output': s.getvalue()
                    }
                
        except ImportError:
            logger.warning("line_profiler not available, skipping line profiling")
            yield profile_name
        except Exception as e:
            logger.error(f"Error in line profiling: {e}")
            yield profile_name
    
    def get_line_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get line profile results"""
        with self._lock:
            return self.line_profiles.get(profile_name)
    
    def list_line_profiles(self) -> List[str]:
        """List available line profiles"""
        with self._lock:
            return list(self.line_profiles.keys())


class MemoryProfiler:
    """
    Memory usage profiler
    """
    
    def __init__(self):
        self.memory_profiles: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def profile_memory(self, profile_name: str):
        """
        Profile memory usage
        
        Args:
            profile_name: Name for the profile
            
        Yields:
            Profile name
        """
        try:
            import psutil
            import gc
            
            # Get initial memory
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            gc.collect()  # Force garbage collection
            
            start_time = time.time()
            
            try:
                yield profile_name
            finally:
                end_time = time.time()
                gc.collect()  # Force garbage collection
                
                # Get final memory
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = final_memory - initial_memory
                
                # Save results
                with self._lock:
                    self.memory_profiles[profile_name] = {
                        'timestamp': datetime.now().isoformat(),
                        'duration': end_time - start_time,
                        'initial_memory_mb': initial_memory,
                        'final_memory_mb': final_memory,
                        'memory_delta_mb': memory_delta,
                        'peak_memory_mb': process.memory_info().peak_wset / 1024 / 1024 if hasattr(process.memory_info(), 'peak_wset') else None
                    }
                
                logger.info(f"Memory profile '{profile_name}': {memory_delta:+.2f} MB delta")
                
        except Exception as e:
            logger.error(f"Error in memory profiling: {e}")
            yield profile_name
    
    def get_memory_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get memory profile results"""
        with self._lock:
            return self.memory_profiles.get(profile_name)
    
    def list_memory_profiles(self) -> List[str]:
        """List available memory profiles"""
        with self._lock:
            return list(self.memory_profiles.keys())


class CombinedProfiler:
    """
    Combined profiler that runs multiple profiling types
    """
    
    def __init__(self):
        self.performance_profiler = PerformanceProfiler()
        self.line_profiler = LineProfiler()
        self.memory_profiler = MemoryProfiler()
    
    @contextmanager
    def profile_all(
        self,
        profile_name: str,
        target_function: Optional[Callable] = None,
        include_lines: bool = False,
        include_memory: bool = True
    ):
        """
        Run all available profilers
        
        Args:
            profile_name: Name for the profile
            target_function: Function for line profiling
            include_lines: Whether to include line profiling
            include_memory: Whether to include memory profiling
            
        Yields:
            Profile name
        """
        contexts = []
        
        # Performance profiling
        perf_context = self.performance_profiler.profile(f"{profile_name}_performance")
        contexts.append(perf_context)
        
        # Memory profiling
        if include_memory:
            memory_context = self.memory_profiler.profile_memory(f"{profile_name}_memory")
            contexts.append(memory_context)
        
        # Line profiling
        if include_lines and target_function:
            line_context = self.line_profiler.profile_lines(f"{profile_name}_lines", target_function)
            contexts.append(line_context)
        
        # Enter all contexts
        entered_contexts = []
        try:
            for context in contexts:
                entered_contexts.append(context.__enter__())
            
            yield profile_name
            
        except Exception as e:
            # Exit contexts in reverse order with exception info
            for context in reversed(contexts):
                try:
                    context.__exit__(type(e), e, e.__traceback__)
                except:
                    pass
            raise
        else:
            # Exit contexts in reverse order
            for context in reversed(contexts):
                try:
                    context.__exit__(None, None, None)
                except:
                    pass
    
    def get_combined_report(self, profile_name: str) -> Dict[str, Any]:
        """Get combined profiling report"""
        report = {
            'profile_name': profile_name,
            'timestamp': datetime.now().isoformat(),
            'performance': None,
            'memory': None,
            'lines': None
        }
        
        # Get performance profile
        perf_profile = self.performance_profiler.get_profile_report(f"{profile_name}_performance")
        if perf_profile:
            report['performance'] = perf_profile.to_dict()
        
        # Get memory profile
        memory_profile = self.memory_profiler.get_memory_profile(f"{profile_name}_memory")
        if memory_profile:
            report['memory'] = memory_profile
        
        # Get line profile
        line_profile = self.line_profiler.get_line_profile(f"{profile_name}_lines")
        if line_profile:
            report['lines'] = line_profile
        
        return report


# Convenience decorators
def profile_performance(profile_name: Optional[str] = None, **context):
    """Decorator for performance profiling"""
    profiler = PerformanceProfiler()
    return profiler.profile_function(profile_name, **context)


def profile_memory(profile_name: Optional[str] = None):
    """Decorator for memory profiling"""
    def decorator(func: Callable) -> Callable:
        profiler = MemoryProfiler()
        name = profile_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with profiler.profile_memory(name):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
