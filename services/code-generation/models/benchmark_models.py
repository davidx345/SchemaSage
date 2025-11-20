"""
Models for performance benchmark tool endpoint.
Tests and compares query performance across databases.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types for benchmarking"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    MARIADB = "mariadb"
    AURORA_POSTGRESQL = "aurora_postgresql"
    AURORA_MYSQL = "aurora_mysql"


class BenchmarkType(str, Enum):
    """Type of benchmark test"""
    QUERY_PERFORMANCE = "query_performance"
    WRITE_THROUGHPUT = "write_throughput"
    READ_THROUGHPUT = "read_throughput"
    TRANSACTION_PERFORMANCE = "transaction_performance"
    CONCURRENT_LOAD = "concurrent_load"
    MIXED_WORKLOAD = "mixed_workload"


class QueryComplexity(str, Enum):
    """Complexity level of queries"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class PerformanceRating(str, Enum):
    """Performance rating classification"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class ConnectionConfig(BaseModel):
    """Database connection configuration"""
    host: str = Field(..., description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    ssl_enabled: bool = Field(default=True, description="Whether SSL is enabled")


class QueryTest(BaseModel):
    """Individual query test specification"""
    query_id: str = Field(..., description="Unique identifier for the query")
    sql: str = Field(..., description="SQL query to test")
    complexity: QueryComplexity = Field(..., description="Query complexity level")
    expected_rows: Optional[int] = Field(None, ge=0, description="Expected number of result rows")
    description: Optional[str] = Field(None, description="Description of what query tests")


class BenchmarkRequest(BaseModel):
    """Request to run performance benchmarks"""
    source_db_type: DatabaseType = Field(..., description="Source database type")
    target_db_type: DatabaseType = Field(..., description="Target database type")
    source_connection: ConnectionConfig = Field(..., description="Source database connection")
    target_connection: ConnectionConfig = Field(..., description="Target database connection")
    benchmark_type: BenchmarkType = Field(..., description="Type of benchmark to run")
    queries: List[QueryTest] = Field(..., min_length=1, description="List of queries to test")
    iterations: int = Field(default=10, ge=1, le=1000, description="Number of iterations per query")
    concurrent_users: int = Field(default=1, ge=1, le=100, description="Number of concurrent users to simulate")
    warm_up_iterations: int = Field(default=3, ge=0, le=10, description="Number of warm-up iterations")
    timeout_seconds: int = Field(default=60, ge=1, le=600, description="Timeout per query in seconds")


class QueryExecutionResult(BaseModel):
    """Result of a single query execution"""
    execution_time_ms: float = Field(..., ge=0.0, description="Execution time in milliseconds")
    rows_returned: int = Field(..., ge=0, description="Number of rows returned")
    cpu_time_ms: Optional[float] = Field(None, ge=0.0, description="CPU time in milliseconds")
    io_reads: Optional[int] = Field(None, ge=0, description="Number of IO reads")
    io_writes: Optional[int] = Field(None, ge=0, description="Number of IO writes")
    memory_used_kb: Optional[float] = Field(None, ge=0.0, description="Memory used in KB")
    success: bool = Field(..., description="Whether execution was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class QueryBenchmarkResult(BaseModel):
    """Benchmark results for a single query"""
    query_id: str = Field(..., description="Query identifier")
    query_sql: str = Field(..., description="SQL query tested")
    complexity: QueryComplexity = Field(..., description="Query complexity")
    source_results: List[QueryExecutionResult] = Field(..., description="Results from source database")
    target_results: List[QueryExecutionResult] = Field(..., description="Results from target database")
    source_avg_time_ms: float = Field(..., ge=0.0, description="Average execution time on source")
    target_avg_time_ms: float = Field(..., ge=0.0, description="Average execution time on target")
    source_min_time_ms: float = Field(..., ge=0.0, description="Minimum execution time on source")
    target_min_time_ms: float = Field(..., ge=0.0, description="Minimum execution time on target")
    source_max_time_ms: float = Field(..., ge=0.0, description="Maximum execution time on source")
    target_max_time_ms: float = Field(..., ge=0.0, description="Maximum execution time on target")
    source_std_dev_ms: float = Field(..., ge=0.0, description="Standard deviation on source")
    target_std_dev_ms: float = Field(..., ge=0.0, description="Standard deviation on target")
    performance_ratio: float = Field(..., description="Target/Source performance ratio (lower is better)")
    performance_difference_percent: float = Field(..., description="Performance difference percentage")
    source_rating: PerformanceRating = Field(..., description="Performance rating for source")
    target_rating: PerformanceRating = Field(..., description="Performance rating for target")


class ThroughputResult(BaseModel):
    """Throughput measurement result"""
    transactions_per_second: float = Field(..., ge=0.0, description="Transactions per second")
    queries_per_second: float = Field(..., ge=0.0, description="Queries per second")
    rows_per_second: float = Field(..., ge=0.0, description="Rows processed per second")
    avg_latency_ms: float = Field(..., ge=0.0, description="Average latency in milliseconds")
    p50_latency_ms: float = Field(..., ge=0.0, description="50th percentile latency")
    p95_latency_ms: float = Field(..., ge=0.0, description="95th percentile latency")
    p99_latency_ms: float = Field(..., ge=0.0, description="99th percentile latency")
    error_rate: float = Field(..., ge=0.0, le=100.0, description="Error rate percentage")


class ConcurrencyResult(BaseModel):
    """Results from concurrent load testing"""
    concurrent_users: int = Field(..., ge=1, description="Number of concurrent users")
    total_duration_seconds: float = Field(..., ge=0.0, description="Total test duration")
    total_queries: int = Field(..., ge=0, description="Total queries executed")
    successful_queries: int = Field(..., ge=0, description="Number of successful queries")
    failed_queries: int = Field(..., ge=0, description="Number of failed queries")
    avg_response_time_ms: float = Field(..., ge=0.0, description="Average response time")
    throughput: ThroughputResult = Field(..., description="Throughput metrics")


class ResourceUtilization(BaseModel):
    """Resource utilization during benchmark"""
    avg_cpu_percent: float = Field(..., ge=0.0, le=100.0, description="Average CPU usage")
    peak_cpu_percent: float = Field(..., ge=0.0, le=100.0, description="Peak CPU usage")
    avg_memory_mb: float = Field(..., ge=0.0, description="Average memory usage in MB")
    peak_memory_mb: float = Field(..., ge=0.0, description="Peak memory usage in MB")
    avg_connections: int = Field(..., ge=0, description="Average active connections")
    peak_connections: int = Field(..., ge=0, description="Peak active connections")
    total_io_mb: float = Field(..., ge=0.0, description="Total IO in MB")


class BenchmarkStatistics(BaseModel):
    """Statistical summary of benchmark results"""
    total_queries_tested: int = Field(..., ge=0, description="Total number of queries tested")
    total_executions: int = Field(..., ge=0, description="Total query executions")
    successful_executions: int = Field(..., ge=0, description="Successful executions")
    failed_executions: int = Field(..., ge=0, description="Failed executions")
    total_duration_seconds: float = Field(..., ge=0.0, description="Total benchmark duration")
    source_faster_count: int = Field(..., ge=0, description="Queries faster on source")
    target_faster_count: int = Field(..., ge=0, description="Queries faster on target")
    similar_performance_count: int = Field(..., ge=0, description="Queries with similar performance")


class BenchmarkSummary(BaseModel):
    """Summary of benchmark results"""
    benchmark_id: str = Field(..., description="Unique benchmark identifier")
    start_time: datetime = Field(..., description="Benchmark start time")
    end_time: datetime = Field(..., description="Benchmark end time")
    source_db_type: DatabaseType = Field(..., description="Source database type")
    target_db_type: DatabaseType = Field(..., description="Target database type")
    benchmark_type: BenchmarkType = Field(..., description="Type of benchmark")
    overall_winner: str = Field(..., description="Overall better performer (source/target/similar)")
    recommendation: str = Field(..., description="Performance-based recommendation")


class BenchmarkResponse(BaseModel):
    """Response from performance benchmark endpoint"""
    summary: BenchmarkSummary = Field(..., description="Benchmark summary")
    statistics: BenchmarkStatistics = Field(..., description="Statistical summary")
    query_results: List[QueryBenchmarkResult] = Field(..., description="Individual query results")
    source_throughput: Optional[ThroughputResult] = Field(None, description="Source throughput metrics")
    target_throughput: Optional[ThroughputResult] = Field(None, description="Target throughput metrics")
    source_concurrency: Optional[ConcurrencyResult] = Field(None, description="Source concurrency results")
    target_concurrency: Optional[ConcurrencyResult] = Field(None, description="Target concurrency results")
    source_resources: ResourceUtilization = Field(..., description="Source resource utilization")
    target_resources: ResourceUtilization = Field(..., description="Target resource utilization")
    warnings: List[str] = Field(default_factory=list, description="Warnings or anomalies detected")
    recommendations: List[str] = Field(default_factory=list, description="Performance recommendations")
