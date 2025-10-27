"""
Infrastructure Optimization Router
Provides RDS/Azure/GCP right-sizing recommendations based on schema analysis
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/infrastructure", tags=["infrastructure-optimization"])


# Models
class SchemaAnalysisInput(BaseModel):
    """Input for schema-based infrastructure analysis"""
    schema: Dict[str, Any] = Field(..., description="Database schema information")
    current_workload: Optional[Dict[str, Any]] = Field(None, description="Current workload metrics")
    cloud_provider: str = Field(..., description="Target cloud provider: aws, azure, gcp")
    region: str = Field(default="us-east-1", description="Target region")


class RightSizingRecommendation(BaseModel):
    """Instance right-sizing recommendation"""
    current_instance: Optional[str] = None
    recommended_instance: str
    reason: str
    estimated_monthly_savings: float
    performance_impact: str  # "improved", "maintained", "reduced"
    cpu_utilization_current: Optional[float] = None
    cpu_utilization_target: float
    memory_utilization_current: Optional[float] = None
    memory_utilization_target: float
    confidence_score: float = Field(ge=0, le=100)


class StorageOptimization(BaseModel):
    """Storage optimization recommendation"""
    current_storage_type: Optional[str] = None
    recommended_storage_type: str
    recommended_size_gb: int
    iops_required: int
    reason: str
    monthly_cost_savings: float


class PerformanceTuning(BaseModel):
    """Performance tuning suggestion"""
    category: str  # "indexing", "partitioning", "caching", "connection_pooling"
    suggestion: str
    expected_improvement: str
    implementation_complexity: str  # "low", "medium", "high"
    estimated_cost_impact: float


class InfrastructureOptimizationResponse(BaseModel):
    """Complete infrastructure optimization analysis"""
    analysis_timestamp: datetime
    cloud_provider: str
    region: str
    compute_recommendations: List[RightSizingRecommendation]
    storage_recommendations: List[StorageOptimization]
    performance_tuning: List[PerformanceTuning]
    total_estimated_monthly_savings: float
    implementation_priority: List[str]
    risk_assessment: Dict[str, Any]


# Helper functions
def analyze_schema_requirements(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze schema to determine compute and storage requirements"""
    total_tables = len(schema.get('tables', []))
    total_columns = sum(len(table.get('columns', [])) for table in schema.get('tables', []))
    estimated_row_count = sum(table.get('row_count', 1000) for table in schema.get('tables', []))
    
    # Calculate estimated data size
    avg_row_size = 200  # bytes, estimated
    estimated_data_gb = (estimated_row_count * avg_row_size) / (1024**3)
    
    # Determine complexity
    has_foreign_keys = any(table.get('foreign_keys') for table in schema.get('tables', []))
    has_indexes = any(table.get('indexes') for table in schema.get('tables', []))
    
    complexity_score = 0
    if total_tables > 50:
        complexity_score += 3
    elif total_tables > 20:
        complexity_score += 2
    elif total_tables > 10:
        complexity_score += 1
    
    if has_foreign_keys:
        complexity_score += 2
    if has_indexes:
        complexity_score += 1
    
    return {
        'total_tables': total_tables,
        'total_columns': total_columns,
        'estimated_row_count': estimated_row_count,
        'estimated_data_gb': estimated_data_gb,
        'complexity_score': complexity_score,
        'has_foreign_keys': has_foreign_keys,
        'has_indexes': has_indexes
    }


def calculate_compute_requirements(schema_analysis: Dict[str, Any], workload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate required compute resources"""
    complexity = schema_analysis['complexity_score']
    data_gb = schema_analysis['estimated_data_gb']
    
    # Base requirements
    required_vcpus = 2
    required_memory_gb = 4
    
    # Adjust based on complexity
    if complexity >= 5:
        required_vcpus = 8
        required_memory_gb = 32
    elif complexity >= 3:
        required_vcpus = 4
        required_memory_gb = 16
    
    # Adjust based on data size
    if data_gb > 500:
        required_memory_gb = max(required_memory_gb, 64)
        required_vcpus = max(required_vcpus, 8)
    elif data_gb > 100:
        required_memory_gb = max(required_memory_gb, 32)
        required_vcpus = max(required_vcpus, 4)
    
    # Adjust based on workload
    if workload:
        reads_per_sec = workload.get('reads_per_second', 0)
        writes_per_sec = workload.get('writes_per_second', 0)
        
        if reads_per_sec + writes_per_sec > 1000:
            required_vcpus = max(required_vcpus, 8)
            required_memory_gb = max(required_memory_gb, 32)
    
    return {
        'required_vcpus': required_vcpus,
        'required_memory_gb': required_memory_gb,
        'target_cpu_utilization': 70,
        'target_memory_utilization': 75
    }


def get_instance_recommendation(cloud_provider: str, compute_reqs: Dict[str, Any]) -> str:
    """Get instance type recommendation based on requirements"""
    required_vcpus = compute_reqs['required_vcpus']
    required_memory_gb = compute_reqs['required_memory_gb']
    
    if cloud_provider == 'aws':
        if required_vcpus <= 2 and required_memory_gb <= 8:
            return 'db.t3.large'
        elif required_vcpus <= 4 and required_memory_gb <= 16:
            return 'db.m5.xlarge'
        elif required_vcpus <= 4 and required_memory_gb <= 32:
            return 'db.r5.xlarge'
        elif required_vcpus <= 8 and required_memory_gb <= 64:
            return 'db.r5.2xlarge'
        else:
            return 'db.r5.4xlarge'
    
    elif cloud_provider == 'azure':
        if required_vcpus <= 2 and required_memory_gb <= 4:
            return 'Standard_D2s_v3'
        elif required_vcpus <= 4 and required_memory_gb <= 16:
            return 'Standard_D4s_v3'
        elif required_vcpus <= 8 and required_memory_gb <= 32:
            return 'Standard_D8s_v3'
        else:
            return 'Standard_D16s_v3'
    
    elif cloud_provider == 'gcp':
        if required_vcpus <= 2 and required_memory_gb <= 8:
            return 'db-n1-standard-2'
        elif required_vcpus <= 4 and required_memory_gb <= 16:
            return 'db-n1-standard-4'
        elif required_vcpus <= 8 and required_memory_gb <= 32:
            return 'db-n1-standard-8'
        else:
            return 'db-n1-standard-16'
    
    return 'db.m5.xlarge'  # default


def calculate_storage_requirements(schema_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate storage requirements"""
    data_gb = schema_analysis['estimated_data_gb']
    
    # Add 30% overhead for indexes, logs, and growth
    recommended_storage_gb = int(data_gb * 1.3)
    
    # Minimum 100GB
    recommended_storage_gb = max(recommended_storage_gb, 100)
    
    # Determine IOPS based on complexity
    if schema_analysis['complexity_score'] >= 5:
        required_iops = 10000
        storage_type = 'io2'
    elif schema_analysis['complexity_score'] >= 3:
        required_iops = 5000
        storage_type = 'gp3'
    else:
        required_iops = 3000
        storage_type = 'gp3'
    
    return {
        'recommended_storage_gb': recommended_storage_gb,
        'recommended_storage_type': storage_type,
        'required_iops': required_iops
    }


def generate_performance_tuning_suggestions(schema: Dict[str, Any], schema_analysis: Dict[str, Any]) -> List[PerformanceTuning]:
    """Generate performance tuning suggestions based on schema"""
    suggestions = []
    
    # Check for missing indexes
    tables_without_indexes = [
        table for table in schema.get('tables', [])
        if not table.get('indexes') and table.get('row_count', 0) > 10000
    ]
    
    if tables_without_indexes:
        suggestions.append(PerformanceTuning(
            category='indexing',
            suggestion=f'Add indexes to {len(tables_without_indexes)} large tables without indexes',
            expected_improvement='30-50% query performance improvement',
            implementation_complexity='low',
            estimated_cost_impact=0
        ))
    
    # Check for large tables that could benefit from partitioning
    large_tables = [
        table for table in schema.get('tables', [])
        if table.get('row_count', 0) > 1000000
    ]
    
    if large_tables:
        suggestions.append(PerformanceTuning(
            category='partitioning',
            suggestion=f'Consider partitioning {len(large_tables)} tables with >1M rows',
            expected_improvement='40-60% query performance for range queries',
            implementation_complexity='medium',
            estimated_cost_impact=0
        ))
    
    # Connection pooling recommendation
    if schema_analysis['total_tables'] > 20:
        suggestions.append(PerformanceTuning(
            category='connection_pooling',
            suggestion='Implement connection pooling to reduce connection overhead',
            expected_improvement='20-30% reduction in connection latency',
            implementation_complexity='low',
            estimated_cost_impact=0
        ))
    
    # Caching recommendation
    if schema_analysis['complexity_score'] >= 3:
        suggestions.append(PerformanceTuning(
            category='caching',
            suggestion='Implement query result caching for frequently accessed data',
            expected_improvement='50-70% reduction in read latency',
            implementation_complexity='medium',
            estimated_cost_impact=50  # Cost of cache service
        ))
    
    return suggestions


@router.post("/analyze-and-optimize", response_model=InfrastructureOptimizationResponse)
async def analyze_and_optimize_infrastructure(input_data: SchemaAnalysisInput):
    """
    Analyze database schema and provide comprehensive infrastructure optimization recommendations
    
    This endpoint analyzes your database schema and current workload to provide:
    - Right-sizing recommendations for compute instances
    - Storage optimization suggestions
    - Performance tuning recommendations
    - Cost savings estimates
    """
    try:
        # Analyze schema
        schema_analysis = analyze_schema_requirements(input_data.schema)
        
        # Calculate compute requirements
        compute_reqs = calculate_compute_requirements(schema_analysis, input_data.current_workload)
        
        # Get instance recommendation
        recommended_instance = get_instance_recommendation(input_data.cloud_provider, compute_reqs)
        
        # Calculate storage requirements
        storage_reqs = calculate_storage_requirements(schema_analysis)
        
        # Generate right-sizing recommendation
        compute_recommendations = [
            RightSizingRecommendation(
                current_instance=input_data.current_workload.get('current_instance') if input_data.current_workload else None,
                recommended_instance=recommended_instance,
                reason=f'Based on {schema_analysis["total_tables"]} tables, {schema_analysis["estimated_data_gb"]:.1f}GB data, complexity score {schema_analysis["complexity_score"]}',
                estimated_monthly_savings=200.0,  # Simplified calculation
                performance_impact='maintained',
                cpu_utilization_target=compute_reqs['target_cpu_utilization'],
                memory_utilization_target=compute_reqs['target_memory_utilization'],
                confidence_score=85.0
            )
        ]
        
        # Generate storage recommendations
        storage_recommendations = [
            StorageOptimization(
                current_storage_type=input_data.current_workload.get('storage_type') if input_data.current_workload else None,
                recommended_storage_type=storage_reqs['recommended_storage_type'],
                recommended_size_gb=storage_reqs['recommended_storage_gb'],
                iops_required=storage_reqs['required_iops'],
                reason=f'Optimized for {schema_analysis["estimated_data_gb"]:.1f}GB data with {schema_analysis["complexity_score"]} complexity',
                monthly_cost_savings=50.0
            )
        ]
        
        # Generate performance tuning suggestions
        performance_tuning = generate_performance_tuning_suggestions(input_data.schema, schema_analysis)
        
        # Calculate total savings
        total_savings = sum(rec.estimated_monthly_savings for rec in compute_recommendations) + \
                       sum(rec.monthly_cost_savings for rec in storage_recommendations)
        
        # Implementation priority
        implementation_priority = [
            'Right-size compute instance',
            'Optimize storage configuration',
            'Add missing indexes',
            'Implement connection pooling'
        ]
        
        # Risk assessment
        risk_assessment = {
            'downtime_required': False,
            'data_migration_needed': False,
            'rollback_complexity': 'low',
            'estimated_implementation_time_hours': 2
        }
        
        return InfrastructureOptimizationResponse(
            analysis_timestamp=datetime.utcnow(),
            cloud_provider=input_data.cloud_provider,
            region=input_data.region,
            compute_recommendations=compute_recommendations,
            storage_recommendations=storage_recommendations,
            performance_tuning=performance_tuning,
            total_estimated_monthly_savings=total_savings,
            implementation_priority=implementation_priority,
            risk_assessment=risk_assessment
        )
    
    except Exception as e:
        logger.error(f'Infrastructure optimization analysis failed: {e}')
        raise HTTPException(status_code=500, detail=f'Analysis failed: {str(e)}')


@router.post("/compare-instances")
async def compare_instance_types(
    cloud_provider: str,
    instance_types: List[str],
    workload_requirements: Dict[str, Any]
):
    """Compare different instance types for given workload requirements"""
    try:
        comparisons = []
        
        for instance_type in instance_types:
            # Simplified comparison - in production, use actual pricing APIs
            comparison = {
                'instance_type': instance_type,
                'monthly_cost': 150.0,  # Placeholder
                'vcpus': 4,
                'memory_gb': 16,
                'performance_score': 85,
                'suitability_score': 80,
                'pros': ['Good balance of cost and performance'],
                'cons': []
            }
            comparisons.append(comparison)
        
        return {
            'cloud_provider': cloud_provider,
            'comparisons': comparisons,
            'recommended': comparisons[0]['instance_type'] if comparisons else None
        }
    
    except Exception as e:
        logger.error(f'Instance comparison failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
