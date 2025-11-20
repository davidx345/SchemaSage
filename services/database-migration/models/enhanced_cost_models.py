"""
Models for enhanced migration cost calculator endpoint.
Provides comprehensive cost analysis for cloud migrations.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CloudProvider(str, Enum):
    """Cloud provider options"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ORACLE_CLOUD = "oracle_cloud"
    IBM_CLOUD = "ibm_cloud"


class DatabaseService(str, Enum):
    """Managed database service options"""
    RDS = "rds"
    AURORA = "aurora"
    AZURE_SQL = "azure_sql"
    AZURE_POSTGRESQL = "azure_postgresql"
    CLOUD_SQL = "cloud_sql"
    CLOUD_SPANNER = "cloud_spanner"


class MigrationComplexity(str, Enum):
    """Migration complexity level"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class CostCategory(str, Enum):
    """Category of cost"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    LICENSING = "licensing"
    SUPPORT = "support"
    BACKUP = "backup"
    DATA_TRANSFER = "data_transfer"
    MIGRATION_TOOLS = "migration_tools"


class DatabaseConfig(BaseModel):
    """Database configuration for cost estimation"""
    engine: str = Field(..., description="Database engine (postgres, mysql, sqlserver, etc)")
    version: str = Field(..., description="Database version")
    storage_size_gb: float = Field(..., ge=0.1, description="Storage size in GB")
    memory_gb: int = Field(..., ge=1, le=1024, description="Memory in GB")
    vcpus: int = Field(..., ge=1, le=256, description="Number of vCPUs")
    iops: Optional[int] = Field(None, ge=0, description="IOPS requirement")
    high_availability: bool = Field(default=False, description="High availability required")
    read_replicas: int = Field(default=0, ge=0, le=15, description="Number of read replicas")


class WorkloadProfile(BaseModel):
    """Workload profile for cost estimation"""
    daily_active_users: int = Field(..., ge=1, description="Daily active users")
    queries_per_second: float = Field(..., ge=0.0, description="Average queries per second")
    peak_queries_per_second: float = Field(..., ge=0.0, description="Peak queries per second")
    data_growth_percent_yearly: float = Field(..., ge=0.0, le=1000.0, description="Annual data growth rate")
    backup_retention_days: int = Field(default=7, ge=1, le=365, description="Backup retention in days")
    estimated_data_transfer_gb_monthly: float = Field(..., ge=0.0, description="Monthly data transfer in GB")


class EnhancedCostRequest(BaseModel):
    """Request for enhanced migration cost calculation"""
    source_database: DatabaseConfig = Field(..., description="Source database configuration")
    target_cloud_provider: CloudProvider = Field(..., description="Target cloud provider")
    target_service: DatabaseService = Field(..., description="Target managed database service")
    workload_profile: WorkloadProfile = Field(..., description="Workload profile")
    migration_complexity: MigrationComplexity = Field(..., description="Migration complexity")
    region: str = Field(..., description="Target cloud region")
    commitment_term_months: int = Field(default=0, ge=0, le=36, description="Commitment term (0=on-demand)")
    include_migration_costs: bool = Field(default=True, description="Include one-time migration costs")
    include_support_costs: bool = Field(default=True, description="Include support costs")


class CostBreakdown(BaseModel):
    """Breakdown of costs by category"""
    category: CostCategory = Field(..., description="Cost category")
    monthly_cost: float = Field(..., ge=0.0, description="Monthly cost in USD")
    annual_cost: float = Field(..., ge=0.0, description="Annual cost in USD")
    percentage_of_total: float = Field(..., ge=0.0, le=100.0, description="Percentage of total cost")
    details: str = Field(..., description="Detailed breakdown")


class ResourceCost(BaseModel):
    """Cost for a specific resource"""
    resource_type: str = Field(..., description="Type of resource")
    resource_name: str = Field(..., description="Name of the resource")
    quantity: float = Field(..., ge=0.0, description="Quantity of resource")
    unit: str = Field(..., description="Unit of measurement")
    unit_price: float = Field(..., ge=0.0, description="Price per unit")
    monthly_cost: float = Field(..., ge=0.0, description="Monthly cost")
    annual_cost: float = Field(..., ge=0.0, description="Annual cost")


class MigrationCost(BaseModel):
    """One-time migration costs"""
    migration_tool_license: float = Field(..., ge=0.0, description="Migration tool licensing cost")
    data_transfer: float = Field(..., ge=0.0, description="Data transfer cost")
    downtime_cost: float = Field(..., ge=0.0, description="Estimated downtime cost")
    professional_services: float = Field(..., ge=0.0, description="Professional services cost")
    testing_validation: float = Field(..., ge=0.0, description="Testing and validation cost")
    total: float = Field(..., ge=0.0, description="Total migration cost")


class CostComparison(BaseModel):
    """Comparison with current costs"""
    current_monthly_cost: float = Field(..., ge=0.0, description="Current monthly cost")
    target_monthly_cost: float = Field(..., ge=0.0, description="Target monthly cost")
    monthly_savings: float = Field(..., description="Monthly savings (negative if increase)")
    annual_savings: float = Field(..., description="Annual savings (negative if increase)")
    savings_percent: float = Field(..., description="Savings percentage")
    break_even_months: Optional[int] = Field(None, ge=0, description="Months to break even")


class CostOptimizationOpportunity(BaseModel):
    """Opportunity for cost optimization"""
    opportunity_type: str = Field(..., description="Type of optimization")
    description: str = Field(..., description="Description of the opportunity")
    potential_monthly_savings: float = Field(..., ge=0.0, description="Potential monthly savings")
    potential_annual_savings: float = Field(..., ge=0.0, description="Potential annual savings")
    implementation_complexity: str = Field(..., description="Complexity of implementation")
    recommendation: str = Field(..., description="Specific recommendation")


class PricingTier(BaseModel):
    """Alternative pricing tier option"""
    tier_name: str = Field(..., description="Name of the pricing tier")
    instance_type: str = Field(..., description="Instance type/SKU")
    vcpus: int = Field(..., ge=1, description="Number of vCPUs")
    memory_gb: int = Field(..., ge=1, description="Memory in GB")
    monthly_cost: float = Field(..., ge=0.0, description="Monthly cost")
    annual_cost: float = Field(..., ge=0.0, description="Annual cost")
    suitable_for: str = Field(..., description="Workload suitability")


class CostForecast(BaseModel):
    """Cost forecast over time"""
    year: int = Field(..., ge=1, le=5, description="Year number")
    monthly_cost: float = Field(..., ge=0.0, description="Projected monthly cost")
    annual_cost: float = Field(..., ge=0.0, description="Projected annual cost")
    storage_gb: float = Field(..., ge=0.0, description="Projected storage size")
    assumptions: str = Field(..., description="Forecast assumptions")


class CostStatistics(BaseModel):
    """Statistical summary of costs"""
    total_monthly_cost: float = Field(..., ge=0.0, description="Total monthly cost")
    total_annual_cost: float = Field(..., ge=0.0, description="Total annual cost")
    cost_per_user_monthly: float = Field(..., ge=0.0, description="Cost per user per month")
    cost_per_gb_monthly: float = Field(..., ge=0.0, description="Cost per GB per month")
    cost_per_query: float = Field(..., ge=0.0, description="Cost per million queries")


class EnhancedCostSummary(BaseModel):
    """Summary of enhanced cost calculation"""
    calculation_id: str = Field(..., description="Unique calculation identifier")
    calculation_timestamp: str = Field(..., description="When calculation was performed")
    target_provider: CloudProvider = Field(..., description="Target cloud provider")
    target_service: DatabaseService = Field(..., description="Target database service")
    recommended_tier: str = Field(..., description="Recommended pricing tier")
    total_cost_of_ownership_year1: float = Field(..., ge=0.0, description="Year 1 TCO including migration")
    total_cost_of_ownership_year3: float = Field(..., ge=0.0, description="3-year TCO")
    recommendation: str = Field(..., description="Overall cost recommendation")


class EnhancedCostResponse(BaseModel):
    """Response from enhanced cost calculator"""
    summary: EnhancedCostSummary = Field(..., description="Cost calculation summary")
    statistics: CostStatistics = Field(..., description="Cost statistics")
    cost_breakdown: List[CostBreakdown] = Field(..., description="Detailed cost breakdown by category")
    resource_costs: List[ResourceCost] = Field(..., description="Individual resource costs")
    migration_costs: MigrationCost = Field(..., description="One-time migration costs")
    comparison: Optional[CostComparison] = Field(None, description="Comparison with current costs")
    optimization_opportunities: List[CostOptimizationOpportunity] = Field(
        default_factory=list,
        description="Cost optimization opportunities"
    )
    alternative_tiers: List[PricingTier] = Field(default_factory=list, description="Alternative pricing options")
    cost_forecast: List[CostForecast] = Field(default_factory=list, description="5-year cost forecast")
    recommendations: List[str] = Field(default_factory=list, description="Cost optimization recommendations")
    warnings: List[str] = Field(default_factory=list, description="Warnings and considerations")
