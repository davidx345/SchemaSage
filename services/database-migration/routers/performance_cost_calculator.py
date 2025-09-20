"""
Performance Cost Calculator Router
Calculates infrastructure costs and provides optimization recommendations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json
import uuid

router = APIRouter(prefix="/performance", tags=["performance"])

# Models
class InfrastructureConfig(BaseModel):
    provider: str = Field(..., description="aws, azure, gcp")
    instance_type: str
    storage_gb: int
    region: str
    backup_enabled: bool = True
    high_availability: bool = False

class ExpectedLoad(BaseModel):
    reads_per_second: int
    writes_per_second: int
    concurrent_connections: int
    data_growth_rate_gb_per_month: Optional[int] = 10
    peak_load_multiplier: Optional[float] = 2.0

class CostAnalysisRequest(BaseModel):
    schema: Dict[str, Any]
    current_infrastructure: InfrastructureConfig
    expected_load: ExpectedLoad

class CostBreakdown(BaseModel):
    compute: float
    storage: float
    data_transfer: float
    backup: float = 0
    high_availability: float = 0

class OptimizationRecommendation(BaseModel):
    type: str
    description: str
    savings: float
    performance_improvement: Optional[str] = None
    cost_impact: Optional[float] = None
    implementation_effort: str

class ScalingProjection(BaseModel):
    load_multiplier: float
    cost_increase: float
    recommended_changes: List[str]

class CostAnalysisResponse(BaseModel):
    current_cost: Dict[str, Any]
    optimized_cost: Dict[str, Any]
    scaling_projections: List[ScalingProjection]

# Pricing data (simplified - in production, use real pricing APIs)
PRICING_DATA = {
    "aws": {
        "compute": {
            "db.t3.micro": {"hourly": 0.017, "cpu": 2, "ram_gb": 1},
            "db.t3.small": {"hourly": 0.034, "cpu": 2, "ram_gb": 2},
            "db.t3.medium": {"hourly": 0.068, "cpu": 2, "ram_gb": 4},
            "db.t3.large": {"hourly": 0.136, "cpu": 2, "ram_gb": 8},
            "db.r5.large": {"hourly": 0.240, "cpu": 2, "ram_gb": 16},
            "db.r5.xlarge": {"hourly": 0.480, "cpu": 4, "ram_gb": 32},
            "db.m5.large": {"hourly": 0.192, "cpu": 2, "ram_gb": 8},
            "db.m5.xlarge": {"hourly": 0.384, "cpu": 4, "ram_gb": 16}
        },
        "storage": {
            "gp2": 0.115,  # per GB per month
            "gp3": 0.08,   # per GB per month
            "io1": 0.125,  # per GB per month
            "io2": 0.125   # per GB per month
        },
        "data_transfer": 0.09,  # per GB
        "backup_storage": 0.095  # per GB per month
    },
    "azure": {
        "compute": {
            "Basic_B1s": {"hourly": 0.0152, "cpu": 1, "ram_gb": 1},
            "Basic_B2s": {"hourly": 0.0608, "cpu": 2, "ram_gb": 4},
            "Standard_S1": {"hourly": 0.0456, "cpu": 1, "ram_gb": 2},
            "Standard_S2": {"hourly": 0.0912, "cpu": 2, "ram_gb": 4},
            "Standard_S3": {"hourly": 0.1824, "cpu": 4, "ram_gb": 8}
        },
        "storage": {
            "standard": 0.05,  # per GB per month
            "premium": 0.15    # per GB per month
        },
        "data_transfer": 0.087,  # per GB
        "backup_storage": 0.10   # per GB per month
    },
    "gcp": {
        "compute": {
            "db-n1-standard-1": {"hourly": 0.0475, "cpu": 1, "ram_gb": 3.75},
            "db-n1-standard-2": {"hourly": 0.095, "cpu": 2, "ram_gb": 7.5},
            "db-n1-standard-4": {"hourly": 0.19, "cpu": 4, "ram_gb": 15},
            "db-n1-highmem-2": {"hourly": 0.1184, "cpu": 2, "ram_gb": 13},
            "db-n1-highmem-4": {"hourly": 0.2368, "cpu": 4, "ram_gb": 26}
        },
        "storage": {
            "pd-standard": 0.04,  # per GB per month
            "pd-ssd": 0.17        # per GB per month
        },
        "data_transfer": 0.12,   # per GB
        "backup_storage": 0.08   # per GB per month
    }
}

def calculate_schema_complexity(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate schema complexity metrics"""
    tables = schema.get("tables", {})
    total_tables = len(tables)
    total_columns = sum(len(table.get("columns", {})) for table in tables.values())
    
    # Count relationships
    relationships = 0
    indexes = 0
    
    for table in tables.values():
        for column in table.get("columns", {}).values():
            if column.get("foreign_key"):
                relationships += 1
            if column.get("indexed", False):
                indexes += 1
    
    complexity_score = (total_tables * 0.3 + total_columns * 0.1 + relationships * 0.4 + indexes * 0.2)
    
    return {
        "total_tables": total_tables,
        "total_columns": total_columns,
        "relationships": relationships,
        "indexes": indexes,
        "complexity_score": round(complexity_score, 2)
    }

def estimate_storage_requirements(schema: Dict[str, Any], expected_load: ExpectedLoad) -> Dict[str, Any]:
    """Estimate storage requirements based on schema and load"""
    tables = schema.get("tables", {})
    
    # Rough estimates based on column types and expected records
    estimated_data_size_gb = 0
    estimated_index_size_gb = 0
    
    for table_name, table in tables.items():
        columns = table.get("columns", {})
        
        # Estimate records per table based on load patterns
        if "user" in table_name.lower() or "customer" in table_name.lower():
            estimated_records = expected_load.concurrent_connections * 100
        elif "transaction" in table_name.lower() or "order" in table_name.lower():
            estimated_records = expected_load.writes_per_second * 86400 * 30  # Monthly
        else:
            estimated_records = expected_load.reads_per_second * 1000  # Reference data
        
        # Calculate size per record
        bytes_per_record = 0
        for column_name, column in columns.items():
            col_type = column.get("type", "").lower()
            if "varchar" in col_type or "text" in col_type:
                bytes_per_record += 50  # Average string size
            elif "int" in col_type:
                bytes_per_record += 8
            elif "decimal" in col_type or "float" in col_type:
                bytes_per_record += 8
            elif "uuid" in col_type:
                bytes_per_record += 16
            elif "timestamp" in col_type or "date" in col_type:
                bytes_per_record += 8
            else:
                bytes_per_record += 20  # Default
        
        table_size_gb = (estimated_records * bytes_per_record) / (1024**3)
        estimated_data_size_gb += table_size_gb
        
        # Estimate index size (roughly 30% of data size)
        estimated_index_size_gb += table_size_gb * 0.3
    
    total_storage_gb = estimated_data_size_gb + estimated_index_size_gb
    
    return {
        "data_size_gb": round(estimated_data_size_gb, 2),
        "index_size_gb": round(estimated_index_size_gb, 2),
        "total_storage_gb": round(total_storage_gb, 2),
        "growth_per_month_gb": expected_load.data_growth_rate_gb_per_month or 10
    }

def calculate_current_cost(config: InfrastructureConfig, storage_estimate: Dict[str, Any]) -> CostBreakdown:
    """Calculate current infrastructure cost"""
    provider = config.provider.lower()
    pricing = PRICING_DATA.get(provider, PRICING_DATA["aws"])
    
    # Compute cost
    instance_pricing = pricing["compute"].get(config.instance_type, pricing["compute"]["db.t3.large"])
    monthly_compute = instance_pricing["hourly"] * 24 * 30
    
    # Storage cost
    storage_type = "gp3" if provider == "aws" else "standard"
    storage_price_per_gb = pricing["storage"].get(storage_type, 0.1)
    monthly_storage = config.storage_gb * storage_price_per_gb
    
    # Data transfer (estimated)
    monthly_data_transfer = storage_estimate["total_storage_gb"] * 0.1  # 10% of data transferred monthly
    data_transfer_cost = monthly_data_transfer * pricing["data_transfer"]
    
    # Backup cost
    backup_cost = 0
    if config.backup_enabled:
        backup_cost = config.storage_gb * pricing.get("backup_storage", 0.1)
    
    # High availability cost (roughly 2x compute cost)
    ha_cost = 0
    if config.high_availability:
        ha_cost = monthly_compute
    
    return CostBreakdown(
        compute=round(monthly_compute, 2),
        storage=round(monthly_storage, 2),
        data_transfer=round(data_transfer_cost, 2),
        backup=round(backup_cost, 2),
        high_availability=round(ha_cost, 2)
    )

def generate_optimization_recommendations(
    config: InfrastructureConfig,
    expected_load: ExpectedLoad,
    schema_complexity: Dict[str, Any],
    current_cost: CostBreakdown
) -> List[OptimizationRecommendation]:
    """Generate cost optimization recommendations"""
    recommendations = []
    
    provider = config.provider.lower()
    pricing = PRICING_DATA.get(provider, PRICING_DATA["aws"])
    
    # Instance optimization
    current_instance = pricing["compute"].get(config.instance_type, {"cpu": 2, "ram_gb": 8, "hourly": 0.136})
    
    # Check if we can use a more cost-effective instance
    if expected_load.concurrent_connections < 50 and current_instance["ram_gb"] > 8:
        if provider == "aws":
            recommended_instance = "db.t3.medium"
            savings = (current_instance["hourly"] - pricing["compute"][recommended_instance]["hourly"]) * 24 * 30
            recommendations.append(OptimizationRecommendation(
                type="instance_optimization",
                description=f"Switch to {recommended_instance} for better price/performance ratio",
                savings=round(savings, 2),
                performance_improvement="Adequate for current load",
                implementation_effort="1-2 hours"
            ))
    
    # Storage optimization
    if provider == "aws" and config.storage_gb > 1000:
        gp3_savings = config.storage_gb * (pricing["storage"]["gp2"] - pricing["storage"]["gp3"])
        recommendations.append(OptimizationRecommendation(
            type="storage_optimization",
            description="Switch from GP2 to GP3 storage for better price/performance",
            savings=round(gp3_savings, 2),
            performance_improvement="Better IOPS baseline",
            implementation_effort="2-3 hours"
        ))
    
    # Index optimization
    if schema_complexity["indexes"] < schema_complexity["total_columns"] * 0.3:
        recommendations.append(OptimizationRecommendation(
            type="index_optimization",
            description="Add composite indexes to improve query performance",
            savings=-15.50,  # Negative because it increases cost but improves performance
            performance_improvement="40% faster queries",
            cost_impact=-15.50,
            implementation_effort="4-6 hours"
        ))
    
    # Connection pooling
    if expected_load.concurrent_connections > 100:
        recommendations.append(OptimizationRecommendation(
            type="connection_optimization",
            description="Implement connection pooling to reduce resource usage",
            savings=current_cost.compute * 0.15,
            performance_improvement="Better resource utilization",
            implementation_effort="2-3 days"
        ))
    
    # Read replicas for high read workload
    if expected_load.reads_per_second > expected_load.writes_per_second * 5:
        replica_cost = current_cost.compute * 0.5  # Read replica costs
        savings = current_cost.compute * 0.2  # Savings from reduced load on primary
        net_cost = replica_cost - savings
        recommendations.append(OptimizationRecommendation(
            type="scaling_optimization",
            description="Add read replicas to handle read-heavy workload",
            savings=-net_cost,
            performance_improvement="Reduced latency for read queries",
            cost_impact=net_cost,
            implementation_effort="1-2 days"
        ))
    
    return recommendations

def generate_scaling_projections(
    current_cost: CostBreakdown,
    expected_load: ExpectedLoad
) -> List[ScalingProjection]:
    """Generate scaling cost projections"""
    projections = []
    
    # 2x load scaling
    projections.append(ScalingProjection(
        load_multiplier=2.0,
        cost_increase=1.7,  # Cost doesn't scale linearly
        recommended_changes=[
            "Enable read replicas",
            "Implement connection pooling",
            "Add caching layer"
        ]
    ))
    
    # 5x load scaling
    projections.append(ScalingProjection(
        load_multiplier=5.0,
        cost_increase=3.5,
        recommended_changes=[
            "Implement database sharding",
            "Add multiple read replicas",
            "Consider microservices architecture",
            "Implement comprehensive caching"
        ]
    ))
    
    # 10x load scaling
    projections.append(ScalingProjection(
        load_multiplier=10.0,
        cost_increase=6.0,
        recommended_changes=[
            "Multi-region deployment",
            "Database clustering",
            "CDN for static content",
            "Advanced monitoring and auto-scaling"
        ]
    ))
    
    return projections

@router.post("/cost-analysis")
async def analyze_infrastructure_costs(request: CostAnalysisRequest):
    """Calculate infrastructure costs and optimization recommendations"""
    try:
        # Analyze schema complexity
        schema_complexity = calculate_schema_complexity(request.schema)
        
        # Estimate storage requirements
        storage_estimate = estimate_storage_requirements(request.schema, request.expected_load)
        
        # Calculate current costs
        current_cost = calculate_current_cost(request.current_infrastructure, storage_estimate)
        current_monthly_total = (
            current_cost.compute + current_cost.storage + current_cost.data_transfer + 
            current_cost.backup + current_cost.high_availability
        )
        
        # Generate optimization recommendations
        recommendations = generate_optimization_recommendations(
            request.current_infrastructure,
            request.expected_load,
            schema_complexity,
            current_cost
        )
        
        # Calculate optimized cost
        total_savings = sum(rec.savings for rec in recommendations if rec.savings > 0)
        optimized_monthly_total = current_monthly_total - total_savings
        savings_percentage = (total_savings / current_monthly_total) * 100 if current_monthly_total > 0 else 0
        
        # Generate scaling projections
        scaling_projections = generate_scaling_projections(current_cost, request.expected_load)
        
        response_data = {
            "current_cost": {
                "monthly_estimate": round(current_monthly_total, 2),
                "breakdown": {
                    "compute": current_cost.compute,
                    "storage": current_cost.storage,
                    "data_transfer": current_cost.data_transfer,
                    "backup": current_cost.backup,
                    "high_availability": current_cost.high_availability
                },
                "storage_analysis": storage_estimate,
                "schema_complexity": schema_complexity
            },
            "optimized_cost": {
                "monthly_estimate": round(max(optimized_monthly_total, 0), 2),
                "savings": round(total_savings, 2),
                "savings_percentage": round(savings_percentage, 2),
                "recommendations": [rec.dict() for rec in recommendations]
            },
            "scaling_projections": [proj.dict() for proj in scaling_projections]
        }
        
        return {
            "success": True,
            "data": response_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze costs: {str(e)}")

@router.get("/pricing-info")
async def get_pricing_information(provider: Optional[str] = None):
    """Get current pricing information for cloud providers"""
    try:
        if provider:
            provider_pricing = PRICING_DATA.get(provider.lower())
            if not provider_pricing:
                raise HTTPException(status_code=404, detail="Provider not found")
            return {
                "success": True,
                "data": {
                    "provider": provider.lower(),
                    "pricing": provider_pricing,
                    "last_updated": "2025-09-20"
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "all_providers": PRICING_DATA,
                    "supported_providers": list(PRICING_DATA.keys()),
                    "last_updated": "2025-09-20"
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing info: {str(e)}")

@router.post("/estimate-migration-cost")
async def estimate_migration_cost(
    source_config: InfrastructureConfig,
    target_config: InfrastructureConfig,
    schema: Dict[str, Any]
):
    """Estimate cost of migrating between cloud providers"""
    try:
        # Calculate storage requirements
        mock_load = ExpectedLoad(
            reads_per_second=100,
            writes_per_second=50,
            concurrent_connections=50
        )
        storage_estimate = estimate_storage_requirements(schema, mock_load)
        
        # Calculate costs for both configurations
        source_cost = calculate_current_cost(source_config, storage_estimate)
        target_cost = calculate_current_cost(target_config, storage_estimate)
        
        source_monthly = source_cost.compute + source_cost.storage + source_cost.data_transfer
        target_monthly = target_cost.compute + target_cost.storage + target_cost.data_transfer
        
        # Estimate migration costs
        data_transfer_cost = storage_estimate["total_storage_gb"] * 0.15  # Migration data transfer
        downtime_hours = 4  # Estimated downtime
        migration_effort_cost = 2000  # Professional services estimate
        
        total_migration_cost = data_transfer_cost + migration_effort_cost
        monthly_savings = source_monthly - target_monthly
        payback_months = total_migration_cost / abs(monthly_savings) if monthly_savings != 0 else float('inf')
        
        return {
            "success": True,
            "data": {
                "source_monthly_cost": round(source_monthly, 2),
                "target_monthly_cost": round(target_monthly, 2),
                "monthly_savings": round(monthly_savings, 2),
                "migration_cost": round(total_migration_cost, 2),
                "data_transfer_cost": round(data_transfer_cost, 2),
                "estimated_downtime_hours": downtime_hours,
                "payback_period_months": round(payback_months, 1) if payback_months != float('inf') else None,
                "yearly_savings": round(monthly_savings * 12, 2),
                "recommendation": "Migrate" if monthly_savings > 100 and payback_months < 12 else "Consider alternatives"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to estimate migration cost: {str(e)}")

@router.get("/optimization-templates")
async def get_optimization_templates():
    """Get pre-built optimization templates for common scenarios"""
    try:
        templates = [
            {
                "name": "Cost-Optimized OLTP",
                "description": "Optimized for transactional workloads with cost focus",
                "use_case": "E-commerce, SaaS applications",
                "recommendations": [
                    "Use burstable instances (T3/T4g)",
                    "Enable GP3 storage",
                    "Implement connection pooling",
                    "Use read replicas for reporting"
                ],
                "estimated_savings": "25-40%"
            },
            {
                "name": "Performance-Optimized Analytics",
                "description": "Optimized for analytical workloads",
                "use_case": "Data warehousing, business intelligence",
                "recommendations": [
                    "Use memory-optimized instances",
                    "Implement columnar storage",
                    "Add specialized indexes",
                    "Use caching for frequent queries"
                ],
                "estimated_savings": "15-30%"
            },
            {
                "name": "High-Availability Setup",
                "description": "Balanced cost and availability",
                "use_case": "Mission-critical applications",
                "recommendations": [
                    "Multi-AZ deployment",
                    "Automated backups",
                    "Read replicas in different regions",
                    "Monitoring and alerting"
                ],
                "estimated_savings": "10-20%"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "templates": templates
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization templates: {str(e)}")
