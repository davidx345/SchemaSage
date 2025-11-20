"""
Performance benchmark tool service.
Tests and compares query performance across databases.
"""
from typing import List, Tuple
from datetime import datetime
import random
import statistics

from models.benchmark_models import (
    DatabaseType, BenchmarkType, QueryComplexity, PerformanceRating,
    ConnectionConfig, QueryTest, QueryExecutionResult, QueryBenchmarkResult,
    ThroughputResult, ConcurrencyResult, ResourceUtilization,
    BenchmarkStatistics, BenchmarkSummary
)


class PerformanceBenchmark:
    """
    Service for benchmarking database performance.
    Simulates realistic performance testing across database systems.
    """
    
    def __init__(self):
        """Initialize the performance benchmark tool"""
        pass
        
    def run_benchmark(
        self,
        source_db_type: DatabaseType,
        target_db_type: DatabaseType,
        benchmark_type: BenchmarkType,
        queries: List[QueryTest],
        iterations: int = 10,
        concurrent_users: int = 1,
        warm_up_iterations: int = 3,
        timeout_seconds: int = 60
    ) -> Tuple[BenchmarkSummary, BenchmarkStatistics, List[QueryBenchmarkResult],
               ThroughputResult, ThroughputResult, ConcurrencyResult,
               ConcurrencyResult, ResourceUtilization, ResourceUtilization,
               List[str], List[str]]:
        """
        Run performance benchmarks comparing source and target databases.
        
        Args:
            source_db_type: Source database type
            target_db_type: Target database type
            benchmark_type: Type of benchmark to run
            queries: List of queries to test
            iterations: Number of iterations per query
            concurrent_users: Number of concurrent users
            warm_up_iterations: Number of warm-up runs
            timeout_seconds: Timeout per query
            
        Returns:
            Tuple of benchmark results
        """
        start_time = datetime.now()
        
        # Run benchmarks for each query
        query_results = []
        for query in queries:
            result = self._benchmark_query(
                query, source_db_type, target_db_type, iterations, warm_up_iterations
            )
            query_results.append(result)
            
        # Generate throughput metrics
        source_throughput = self._calculate_throughput(query_results, "source")
        target_throughput = self._calculate_throughput(query_results, "target")
        
        # Generate concurrency results
        source_concurrency = self._simulate_concurrency(
            queries, concurrent_users, source_db_type
        )
        target_concurrency = self._simulate_concurrency(
            queries, concurrent_users, target_db_type
        )
        
        # Generate resource utilization
        source_resources = self._measure_resources(source_db_type, query_results)
        target_resources = self._measure_resources(target_db_type, query_results)
        
        # Generate statistics
        end_time = datetime.now()
        stats = self._generate_statistics(query_results, start_time, end_time)
        
        # Generate summary
        summary = self._generate_summary(
            source_db_type, target_db_type, benchmark_type,
            query_results, start_time, end_time
        )
        
        # Generate warnings and recommendations
        warnings = self._generate_warnings(query_results, source_throughput, target_throughput)
        recommendations = self._generate_recommendations(
            query_results, source_resources, target_resources
        )
        
        return (summary, stats, query_results, source_throughput, target_throughput,
                source_concurrency, target_concurrency, source_resources,
                target_resources, warnings, recommendations)
                
    def _benchmark_query(
        self,
        query: QueryTest,
        source_db: DatabaseType,
        target_db: DatabaseType,
        iterations: int,
        warm_up: int
    ) -> QueryBenchmarkResult:
        """Benchmark a single query on both databases"""
        # Simulate query execution on source
        source_results = []
        for i in range(warm_up + iterations):
            exec_result = self._execute_query(query, source_db)
            if i >= warm_up:  # Skip warm-up iterations
                source_results.append(exec_result)
                
        # Simulate query execution on target
        target_results = []
        for i in range(warm_up + iterations):
            exec_result = self._execute_query(query, target_db)
            if i >= warm_up:
                target_results.append(exec_result)
                
        # Calculate statistics
        source_times = [r.execution_time_ms for r in source_results if r.success]
        target_times = [r.execution_time_ms for r in target_results if r.success]
        
        source_avg = statistics.mean(source_times) if source_times else 0
        target_avg = statistics.mean(target_times) if target_times else 0
        
        performance_ratio = target_avg / source_avg if source_avg > 0 else 1.0
        performance_diff = ((target_avg - source_avg) / source_avg * 100) if source_avg > 0 else 0
        
        return QueryBenchmarkResult(
            query_id=query.query_id,
            query_sql=query.sql,
            complexity=query.complexity,
            source_results=source_results,
            target_results=target_results,
            source_avg_time_ms=source_avg,
            target_avg_time_ms=target_avg,
            source_min_time_ms=min(source_times) if source_times else 0,
            target_min_time_ms=min(target_times) if target_times else 0,
            source_max_time_ms=max(source_times) if source_times else 0,
            target_max_time_ms=max(target_times) if target_times else 0,
            source_std_dev_ms=statistics.stdev(source_times) if len(source_times) > 1 else 0,
            target_std_dev_ms=statistics.stdev(target_times) if len(target_times) > 1 else 0,
            performance_ratio=performance_ratio,
            performance_difference_percent=performance_diff,
            source_rating=self._rate_performance(source_avg, query.complexity),
            target_rating=self._rate_performance(target_avg, query.complexity)
        )
        
    def _execute_query(self, query: QueryTest, db_type: DatabaseType) -> QueryExecutionResult:
        """Simulate query execution"""
        # Simulate execution time based on complexity and database
        base_time = {
            QueryComplexity.SIMPLE: 10,
            QueryComplexity.MODERATE: 50,
            QueryComplexity.COMPLEX: 200,
            QueryComplexity.VERY_COMPLEX: 1000
        }[query.complexity]
        
        # Add database-specific variance
        db_multiplier = {
            DatabaseType.POSTGRESQL: 1.0,
            DatabaseType.MYSQL: 1.1,
            DatabaseType.SQLSERVER: 1.15,
            DatabaseType.ORACLE: 0.95,
            DatabaseType.AURORA_POSTGRESQL: 0.85,
            DatabaseType.AURORA_MYSQL: 0.90
        }.get(db_type, 1.0)
        
        # Add random variance
        variance = random.uniform(0.8, 1.2)
        execution_time = base_time * db_multiplier * variance
        
        # Simulate occasional failures (1% chance)
        success = random.random() > 0.01
        
        return QueryExecutionResult(
            execution_time_ms=execution_time,
            rows_returned=query.expected_rows or random.randint(10, 1000),
            cpu_time_ms=execution_time * 0.7,
            io_reads=random.randint(100, 10000),
            io_writes=random.randint(0, 100),
            memory_used_kb=random.uniform(1024, 10240),
            success=success,
            error_message="Timeout" if not success else None
        )
        
    def _calculate_throughput(
        self,
        query_results: List[QueryBenchmarkResult],
        db_side: str
    ) -> ThroughputResult:
        """Calculate throughput metrics"""
        all_times = []
        for qr in query_results:
            times = [r.execution_time_ms for r in 
                    (qr.source_results if db_side == "source" else qr.target_results)
                    if r.success]
            all_times.extend(times)
            
        if not all_times:
            all_times = [100]
            
        avg_latency = statistics.mean(all_times)
        sorted_times = sorted(all_times)
        
        return ThroughputResult(
            transactions_per_second=1000.0 / avg_latency,
            queries_per_second=1000.0 / avg_latency,
            rows_per_second=random.uniform(5000, 15000),
            avg_latency_ms=avg_latency,
            p50_latency_ms=sorted_times[len(sorted_times) // 2],
            p95_latency_ms=sorted_times[int(len(sorted_times) * 0.95)],
            p99_latency_ms=sorted_times[int(len(sorted_times) * 0.99)],
            error_rate=random.uniform(0, 2)
        )
        
    def _simulate_concurrency(
        self,
        queries: List[QueryTest],
        concurrent_users: int,
        db_type: DatabaseType
    ) -> ConcurrencyResult:
        """Simulate concurrent load testing"""
        total_queries = len(queries) * concurrent_users * 10
        successful = int(total_queries * 0.98)
        failed = total_queries - successful
        
        avg_response = random.uniform(50, 200)
        
        throughput = ThroughputResult(
            transactions_per_second=1000.0 / avg_response * concurrent_users,
            queries_per_second=1000.0 / avg_response * concurrent_users,
            rows_per_second=random.uniform(5000, 15000) * concurrent_users,
            avg_latency_ms=avg_response,
            p50_latency_ms=avg_response * 0.8,
            p95_latency_ms=avg_response * 1.5,
            p99_latency_ms=avg_response * 2.0,
            error_rate=(failed / total_queries) * 100
        )
        
        return ConcurrencyResult(
            concurrent_users=concurrent_users,
            total_duration_seconds=60.0,
            total_queries=total_queries,
            successful_queries=successful,
            failed_queries=failed,
            avg_response_time_ms=avg_response,
            throughput=throughput
        )
        
    def _measure_resources(
        self,
        db_type: DatabaseType,
        query_results: List[QueryBenchmarkResult]
    ) -> ResourceUtilization:
        """Measure resource utilization"""
        return ResourceUtilization(
            avg_cpu_percent=random.uniform(40, 70),
            peak_cpu_percent=random.uniform(70, 95),
            avg_memory_mb=random.uniform(2048, 8192),
            peak_memory_mb=random.uniform(8192, 16384),
            avg_connections=random.randint(5, 15),
            peak_connections=random.randint(15, 30),
            total_io_mb=random.uniform(100, 1000)
        )
        
    def _rate_performance(self, exec_time_ms: float, complexity: QueryComplexity) -> PerformanceRating:
        """Rate query performance"""
        # Define thresholds based on complexity
        thresholds = {
            QueryComplexity.SIMPLE: [20, 50, 100, 200],
            QueryComplexity.MODERATE: [100, 200, 500, 1000],
            QueryComplexity.COMPLEX: [500, 1000, 2000, 5000],
            QueryComplexity.VERY_COMPLEX: [2000, 5000, 10000, 20000]
        }
        
        limits = thresholds[complexity]
        
        if exec_time_ms <= limits[0]:
            return PerformanceRating.EXCELLENT
        elif exec_time_ms <= limits[1]:
            return PerformanceRating.GOOD
        elif exec_time_ms <= limits[2]:
            return PerformanceRating.FAIR
        elif exec_time_ms <= limits[3]:
            return PerformanceRating.POOR
        else:
            return PerformanceRating.UNACCEPTABLE
            
    def _generate_statistics(
        self,
        query_results: List[QueryBenchmarkResult],
        start_time: datetime,
        end_time: datetime
    ) -> BenchmarkStatistics:
        """Generate benchmark statistics"""
        total_executions = sum(
            len(qr.source_results) + len(qr.target_results)
            for qr in query_results
        )
        
        successful = sum(
            sum(1 for r in qr.source_results if r.success) +
            sum(1 for r in qr.target_results if r.success)
            for qr in query_results
        )
        
        source_faster = sum(1 for qr in query_results if qr.source_avg_time_ms < qr.target_avg_time_ms)
        target_faster = sum(1 for qr in query_results if qr.target_avg_time_ms < qr.source_avg_time_ms)
        similar = len(query_results) - source_faster - target_faster
        
        return BenchmarkStatistics(
            total_queries_tested=len(query_results),
            total_executions=total_executions,
            successful_executions=successful,
            failed_executions=total_executions - successful,
            total_duration_seconds=(end_time - start_time).total_seconds(),
            source_faster_count=source_faster,
            target_faster_count=target_faster,
            similar_performance_count=similar
        )
        
    def _generate_summary(
        self,
        source_db: DatabaseType,
        target_db: DatabaseType,
        benchmark_type: BenchmarkType,
        query_results: List[QueryBenchmarkResult],
        start_time: datetime,
        end_time: datetime
    ) -> BenchmarkSummary:
        """Generate benchmark summary"""
        source_faster = sum(1 for qr in query_results if qr.source_avg_time_ms < qr.target_avg_time_ms)
        target_faster = sum(1 for qr in query_results if qr.target_avg_time_ms < qr.source_avg_time_ms)
        
        if source_faster > target_faster * 1.2:
            winner = "source"
            recommendation = f"{source_db.value} shows better performance for this workload"
        elif target_faster > source_faster * 1.2:
            winner = "target"
            recommendation = f"{target_db.value} shows better performance for this workload"
        else:
            winner = "similar"
            recommendation = "Both databases show similar performance characteristics"
            
        return BenchmarkSummary(
            benchmark_id=f"bench_{int(start_time.timestamp())}",
            start_time=start_time,
            end_time=end_time,
            source_db_type=source_db,
            target_db_type=target_db,
            benchmark_type=benchmark_type,
            overall_winner=winner,
            recommendation=recommendation
        )
        
    def _generate_warnings(
        self,
        query_results: List[QueryBenchmarkResult],
        source_throughput: ThroughputResult,
        target_throughput: ThroughputResult
    ) -> List[str]:
        """Generate warnings"""
        warnings = []
        
        # Check for high error rates
        if source_throughput.error_rate > 5:
            warnings.append(f"High error rate on source database: {source_throughput.error_rate:.1f}%")
            
        if target_throughput.error_rate > 5:
            warnings.append(f"High error rate on target database: {target_throughput.error_rate:.1f}%")
            
        # Check for poor ratings
        poor_queries = [qr for qr in query_results 
                       if qr.source_rating == PerformanceRating.UNACCEPTABLE 
                       or qr.target_rating == PerformanceRating.UNACCEPTABLE]
        if poor_queries:
            warnings.append(f"{len(poor_queries)} queries showed unacceptable performance")
            
        return warnings
        
    def _generate_recommendations(
        self,
        query_results: List[QueryBenchmarkResult],
        source_resources: ResourceUtilization,
        target_resources: ResourceUtilization
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        # Resource-based recommendations
        if source_resources.peak_cpu_percent > 90:
            recommendations.append("Source database CPU is near capacity - consider scaling up")
            
        if target_resources.peak_cpu_percent > 90:
            recommendations.append("Target database CPU is near capacity - consider scaling up")
            
        # Query optimization recommendations
        slow_queries = [qr for qr in query_results if qr.source_avg_time_ms > 1000 or qr.target_avg_time_ms > 1000]
        if slow_queries:
            recommendations.append(f"Optimize {len(slow_queries)} slow queries for better performance")
            
        recommendations.append("Run benchmarks during expected peak load for accurate capacity planning")
        
        return recommendations


def run_benchmark(
    source_db_type: DatabaseType,
    target_db_type: DatabaseType,
    benchmark_type: BenchmarkType,
    queries: List[QueryTest],
    iterations: int = 10,
    concurrent_users: int = 1,
    warm_up_iterations: int = 3,
    timeout_seconds: int = 60
) -> Tuple:
    """Run performance benchmarks"""
    benchmark = PerformanceBenchmark()
    return benchmark.run_benchmark(
        source_db_type, target_db_type, benchmark_type, queries,
        iterations, concurrent_users, warm_up_iterations, timeout_seconds
    )
