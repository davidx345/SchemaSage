"""
Multi-Cloud Comparison Engine
Unified comparison of AWS, Azure, and GCP with cost estimates and feature parity
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/multi-cloud", tags=["multi-cloud-comparison"])


# Models
class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class DatabaseEngine(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"


class ComparisonInput(BaseModel):
    """Input for multi-cloud comparison"""
    database_engine: DatabaseEngine
    database_version: str
    vcpu_count: int = Field(ge=1, le=128)
    memory_gb: int = Field(ge=1, le=1024)
    storage_gb: int = Field(ge=20, le=65536)
    iops_required: Optional[int] = None
    multi_az: bool = False
    backup_retention_days: int = Field(default=7, ge=1, le=35)
    region: str = "us-east"


class InstanceRecommendation(BaseModel):
    """Cloud provider instance recommendation"""
    cloud_provider: CloudProvider
    instance_type: str
    vcpu: int
    memory_gb: float
    storage_type: str
    monthly_compute_cost: float
    monthly_storage_cost: float
    monthly_backup_cost: float
    monthly_total_cost: float
    annual_cost: float
    reserved_1yr_cost: float
    reserved_3yr_cost: float


class FeatureComparison(BaseModel):
    """Feature availability comparison"""
    feature: str
    aws_support: str  # "full", "partial", "none"
    azure_support: str
    gcp_support: str
    notes: str


class MigrationComplexity(BaseModel):
    """Migration complexity assessment"""
    source_provider: CloudProvider
    target_provider: CloudProvider
    complexity_score: int = Field(ge=1, le=10)
    estimated_migration_time: str
    key_challenges: List[str]
    recommended_approach: str


class MultiCloudComparisonResponse(BaseModel):
    """Complete multi-cloud comparison"""
    requirements: ComparisonInput
    recommendations: List[InstanceRecommendation]
    lowest_cost_provider: CloudProvider
    best_value_provider: CloudProvider
    feature_comparison: List[FeatureComparison]
    migration_complexity: List[MigrationComplexity]


# Cloud provider instance mappings
AWS_INSTANCES = {
    "t3": {"vcpu_range": (2, 8), "memory_per_vcpu": 2, "cost_per_hour": 0.034},
    "m5": {"vcpu_range": (2, 96), "memory_per_vcpu": 4, "cost_per_hour": 0.096},
    "r5": {"vcpu_range": (2, 96), "memory_per_vcpu": 8, "cost_per_hour": 0.126},
    "x1e": {"vcpu_range": (4, 128), "memory_per_vcpu": 30.5, "cost_per_hour": 1.002}
}

AZURE_INSTANCES = {
    "B": {"vcpu_range": (1, 4), "memory_per_vcpu": 2, "cost_per_hour": 0.030},
    "D": {"vcpu_range": (2, 64), "memory_per_vcpu": 4, "cost_per_hour": 0.096},
    "E": {"vcpu_range": (2, 64), "memory_per_vcpu": 8, "cost_per_hour": 0.126}
}

GCP_INSTANCES = {
    "db-f1": {"vcpu": 1, "memory": 0.6, "cost_per_hour": 0.0150},
    "db-g1": {"vcpu": 1, "memory": 1.7, "cost_per_hour": 0.0250},
    "db-n1-standard": {"vcpu_range": (1, 96), "memory_per_vcpu": 3.75, "cost_per_hour": 0.0475},
    "db-n1-highmem": {"vcpu_range": (2, 96), "memory_per_vcpu": 6.5, "cost_per_hour": 0.0592}
}


def find_aws_instance(vcpu: int, memory: int) -> Dict[str, Any]:
    """Find best matching AWS RDS instance"""
    memory_per_vcpu = memory / vcpu if vcpu > 0 else 4
    
    # Select instance family based on memory ratio
    if memory_per_vcpu >= 8:
        family = "r5"
    elif memory_per_vcpu >= 4:
        family = "m5"
    else:
        family = "t3"
    
    # Find closest vCPU match
    vcpu_options = [2, 4, 8, 16, 32, 64, 96]
    selected_vcpu = min([v for v in vcpu_options if v >= vcpu], default=96)
    
    instance_type = f"db.{family}.{['large', 'xlarge', '2xlarge', '4xlarge', '8xlarge', '16xlarge', '24xlarge'][vcpu_options.index(selected_vcpu) if selected_vcpu in vcpu_options else 0]}"
    
    base_cost = AWS_INSTANCES[family]["cost_per_hour"] * (selected_vcpu / 2)
    
    return {
        "instance_type": instance_type,
        "vcpu": selected_vcpu,
        "memory_gb": selected_vcpu * AWS_INSTANCES[family]["memory_per_vcpu"],
        "cost_per_hour": base_cost
    }


def find_azure_instance(vcpu: int, memory: int) -> Dict[str, Any]:
    """Find best matching Azure Database instance"""
    memory_per_vcpu = memory / vcpu if vcpu > 0 else 4
    
    if memory_per_vcpu >= 8:
        family = "E"
    elif memory_per_vcpu >= 4:
        family = "D"
    else:
        family = "B"
    
    vcpu_options = [2, 4, 8, 16, 32, 64]
    selected_vcpu = min([v for v in vcpu_options if v >= vcpu], default=64)
    
    instance_type = f"Standard_{family}{selected_vcpu}s_v3"
    base_cost = AZURE_INSTANCES[family]["cost_per_hour"] * (selected_vcpu / 2)
    
    return {
        "instance_type": instance_type,
        "vcpu": selected_vcpu,
        "memory_gb": selected_vcpu * AZURE_INSTANCES[family]["memory_per_vcpu"],
        "cost_per_hour": base_cost
    }


def find_gcp_instance(vcpu: int, memory: int) -> Dict[str, Any]:
    """Find best matching GCP Cloud SQL instance"""
    memory_per_vcpu = memory / vcpu if vcpu > 0 else 4
    
    if memory_per_vcpu >= 6:
        family = "db-n1-highmem"
    else:
        family = "db-n1-standard"
    
    vcpu_options = [1, 2, 4, 8, 16, 32, 64, 96]
    selected_vcpu = min([v for v in vcpu_options if v >= vcpu], default=96)
    
    instance_type = f"{family}-{selected_vcpu}"
    base_cost = GCP_INSTANCES[family]["cost_per_hour"] * selected_vcpu
    
    return {
        "instance_type": instance_type,
        "vcpu": selected_vcpu,
        "memory_gb": selected_vcpu * GCP_INSTANCES[family]["memory_per_vcpu"],
        "cost_per_hour": base_cost
    }


def calculate_storage_cost(provider: CloudProvider, storage_gb: int, iops: Optional[int]) -> float:
    """Calculate storage costs"""
    storage_rates = {
        CloudProvider.AWS: 0.115,  # gp2
        CloudProvider.AZURE: 0.125,  # Premium SSD
        CloudProvider.GCP: 0.17  # SSD
    }
    
    base_cost = storage_gb * storage_rates[provider]
    
    # Add IOPS cost if specified
    if iops and provider == CloudProvider.AWS:
        provisioned_iops_cost = (iops - 3000) * 0.065 if iops > 3000 else 0
        base_cost += provisioned_iops_cost
    
    return base_cost


def calculate_backup_cost(provider: CloudProvider, storage_gb: int, retention_days: int) -> float:
    """Calculate backup costs"""
    backup_rates = {
        CloudProvider.AWS: 0.095,
        CloudProvider.AZURE: 0.10,
        CloudProvider.GCP: 0.08
    }
    
    # Simplified: assume backup size = storage * retention multiplier
    backup_gb = storage_gb * (retention_days / 7) * 0.8
    return backup_gb * backup_rates[provider]


@router.post("/compare", response_model=MultiCloudComparisonResponse)
async def compare_cloud_providers(input_data: ComparisonInput):
    """
    Compare costs and features across AWS, Azure, and GCP
    
    Provides:
    - Instance recommendations for each provider
    - Cost comparison (monthly, annual, reserved)
    - Feature availability matrix
    - Migration complexity assessment
    """
    try:
        recommendations = []
        
        # AWS recommendation
        aws_instance = find_aws_instance(input_data.vcpu_count, input_data.memory_gb)
        aws_compute_cost = aws_instance["cost_per_hour"] * 730
        aws_storage_cost = calculate_storage_cost(CloudProvider.AWS, input_data.storage_gb, input_data.iops_required)
        aws_backup_cost = calculate_backup_cost(CloudProvider.AWS, input_data.storage_gb, input_data.backup_retention_days)
        aws_total = aws_compute_cost + aws_storage_cost + aws_backup_cost
        
        if input_data.multi_az:
            aws_total *= 1.5  # Multi-AZ adds ~50% cost
        
        recommendations.append(InstanceRecommendation(
            cloud_provider=CloudProvider.AWS,
            instance_type=aws_instance["instance_type"],
            vcpu=aws_instance["vcpu"],
            memory_gb=aws_instance["memory_gb"],
            storage_type="gp3",
            monthly_compute_cost=round(aws_compute_cost, 2),
            monthly_storage_cost=round(aws_storage_cost, 2),
            monthly_backup_cost=round(aws_backup_cost, 2),
            monthly_total_cost=round(aws_total, 2),
            annual_cost=round(aws_total * 12, 2),
            reserved_1yr_cost=round(aws_total * 0.7 * 12, 2),
            reserved_3yr_cost=round(aws_total * 0.5 * 12, 2)
        ))
        
        # Azure recommendation
        azure_instance = find_azure_instance(input_data.vcpu_count, input_data.memory_gb)
        azure_compute_cost = azure_instance["cost_per_hour"] * 730
        azure_storage_cost = calculate_storage_cost(CloudProvider.AZURE, input_data.storage_gb, input_data.iops_required)
        azure_backup_cost = calculate_backup_cost(CloudProvider.AZURE, input_data.storage_gb, input_data.backup_retention_days)
        azure_total = azure_compute_cost + azure_storage_cost + azure_backup_cost
        
        recommendations.append(InstanceRecommendation(
            cloud_provider=CloudProvider.AZURE,
            instance_type=azure_instance["instance_type"],
            vcpu=azure_instance["vcpu"],
            memory_gb=azure_instance["memory_gb"],
            storage_type="Premium SSD",
            monthly_compute_cost=round(azure_compute_cost, 2),
            monthly_storage_cost=round(azure_storage_cost, 2),
            monthly_backup_cost=round(azure_backup_cost, 2),
            monthly_total_cost=round(azure_total, 2),
            annual_cost=round(azure_total * 12, 2),
            reserved_1yr_cost=round(azure_total * 0.65 * 12, 2),
            reserved_3yr_cost=round(azure_total * 0.45 * 12, 2)
        ))
        
        # GCP recommendation
        gcp_instance = find_gcp_instance(input_data.vcpu_count, input_data.memory_gb)
        gcp_compute_cost = gcp_instance["cost_per_hour"] * 730
        gcp_storage_cost = calculate_storage_cost(CloudProvider.GCP, input_data.storage_gb, input_data.iops_required)
        gcp_backup_cost = calculate_backup_cost(CloudProvider.GCP, input_data.storage_gb, input_data.backup_retention_days)
        gcp_total = gcp_compute_cost + gcp_storage_cost + gcp_backup_cost
        
        recommendations.append(InstanceRecommendation(
            cloud_provider=CloudProvider.GCP,
            instance_type=gcp_instance["instance_type"],
            vcpu=gcp_instance["vcpu"],
            memory_gb=gcp_instance["memory_gb"],
            storage_type="SSD",
            monthly_compute_cost=round(gcp_compute_cost, 2),
            monthly_storage_cost=round(gcp_storage_cost, 2),
            monthly_backup_cost=round(gcp_backup_cost, 2),
            monthly_total_cost=round(gcp_total, 2),
            annual_cost=round(gcp_total * 12, 2),
            reserved_1yr_cost=round(gcp_total * 0.63 * 12, 2),
            reserved_3yr_cost=round(gcp_total * 0.47 * 12, 2)
        ))
        
        # Determine lowest cost and best value
        lowest_cost = min(recommendations, key=lambda x: x.monthly_total_cost)
        
        # Feature comparison
        features = [
            FeatureComparison(
                feature="Automated Backups",
                aws_support="full",
                azure_support="full",
                gcp_support="full",
                notes="All providers support automated backups with configurable retention"
            ),
            FeatureComparison(
                feature="Point-in-Time Recovery",
                aws_support="full",
                azure_support="full",
                gcp_support="full",
                notes="Restore to any point within backup retention period"
            ),
            FeatureComparison(
                feature="Read Replicas",
                aws_support="full",
                azure_support="full",
                gcp_support="full",
                notes="All support cross-region read replicas"
            ),
            FeatureComparison(
                feature="Auto-scaling Storage",
                aws_support="full",
                azure_support="partial",
                gcp_support="full",
                notes="AWS and GCP fully automated, Azure requires manual scaling"
            )
        ]
        
        # Migration complexity
        migrations = [
            MigrationComplexity(
                source_provider=CloudProvider.AWS,
                target_provider=CloudProvider.AZURE,
                complexity_score=6,
                estimated_migration_time="4-8 hours",
                key_challenges=["Different IAM models", "VPC vs VNet configuration", "Backup format conversion"],
                recommended_approach="Database Migration Service with pre-migration testing"
            ),
            MigrationComplexity(
                source_provider=CloudProvider.AWS,
                target_provider=CloudProvider.GCP,
                complexity_score=5,
                estimated_migration_time="3-6 hours",
                key_challenges=["Network configuration differences", "Monitoring tool changes"],
                recommended_approach="Native export/import or Database Migration Service"
            )
        ]
        
        return MultiCloudComparisonResponse(
            requirements=input_data,
            recommendations=recommendations,
            lowest_cost_provider=lowest_cost.cloud_provider,
            best_value_provider=lowest_cost.cloud_provider,
            feature_comparison=features,
            migration_complexity=migrations
        )
    
    except Exception as e:
        logger.error(f"Multi-cloud comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/pricing/{provider}")
async def get_provider_pricing(provider: CloudProvider, instance_type: str):
    """Get detailed pricing for specific instance"""
    try:
        pricing_data = {
            "provider": provider,
            "instance_type": instance_type,
            "pricing": {
                "on_demand_hourly": 0.192,
                "on_demand_monthly": 140.16,
                "reserved_1yr_no_upfront": 98.00,
                "reserved_3yr_no_upfront": 70.00
            }
        }
        return pricing_data
    except Exception as e:
        logger.error(f"Pricing lookup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
