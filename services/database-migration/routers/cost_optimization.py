"""
Cost Optimization Engine
Comprehensive cost analysis and optimization recommendations across cloud providers
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cost-optimization", tags=["cost-optimization"])


# Models
class OptimizationCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    BACKUP = "backup"
    LICENSING = "licensing"


class CostOptimizationInput(BaseModel):
    """Input for cost optimization analysis"""
    cloud_provider: str = Field(..., description="aws, azure, or gcp")
    current_config: Dict[str, Any] = Field(..., description="Current infrastructure configuration")
    usage_patterns: Optional[Dict[str, Any]] = Field(None, description="Historical usage patterns")
    business_requirements: Optional[Dict[str, Any]] = Field(None, description="SLA and compliance requirements")


class CostSavingOpportunity(BaseModel):
    """Individual cost saving opportunity"""
    category: OptimizationCategory
    title: str
    description: str
    current_monthly_cost: float
    optimized_monthly_cost: float
    monthly_savings: float
    annual_savings: float
    implementation_effort: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"
    confidence: float = Field(ge=0, le=100)
    action_items: List[str]


class ReservedInstanceRecommendation(BaseModel):
    """Reserved instance/savings plan recommendation"""
    instance_type: str
    current_on_demand_cost: float
    reserved_cost_1year: float
    reserved_cost_3year: float
    savings_1year: float
    savings_3year: float
    utilization_requirement: float
    recommendation: str


class CostOptimizationResponse(BaseModel):
    """Complete cost optimization analysis"""
    analysis_timestamp: datetime
    cloud_provider: str
    current_monthly_cost: float
    optimized_monthly_cost: float
    total_monthly_savings: float
    total_annual_savings: float
    savings_percentage: float
    opportunities: List[CostSavingOpportunity]
    reserved_instance_recommendations: List[ReservedInstanceRecommendation]
    quick_wins: List[str]
    long_term_strategies: List[str]


# Pricing data (simplified - integrate with cloud provider APIs in production)
PRICING_DATABASE = {
    'aws': {
        'compute': {
            'db.t3.micro': 0.017,
            'db.t3.small': 0.034,
            'db.t3.medium': 0.068,
            'db.t3.large': 0.136,
            'db.m5.large': 0.192,
            'db.m5.xlarge': 0.384,
            'db.r5.large': 0.240,
            'db.r5.xlarge': 0.480,
        },
        'storage_gp3': 0.08,
        'storage_gp2': 0.115,
        'storage_io1': 0.125,
        'backup': 0.095,
        'data_transfer': 0.09,
    },
    'azure': {
        'compute': {
            'Basic_B1s': 0.0152,
            'Basic_B2s': 0.0608,
            'Standard_D2s_v3': 0.096,
            'Standard_D4s_v3': 0.192,
            'Standard_D8s_v3': 0.384,
        },
        'storage_standard': 0.05,
        'storage_premium': 0.15,
        'backup': 0.10,
        'data_transfer': 0.087,
    },
    'gcp': {
        'compute': {
            'db-n1-standard-1': 0.0475,
            'db-n1-standard-2': 0.095,
            'db-n1-standard-4': 0.19,
            'db-n1-standard-8': 0.38,
        },
        'storage_ssd': 0.17,
        'storage_standard': 0.09,
        'backup': 0.08,
        'data_transfer': 0.12,
    }
}


def calculate_current_costs(cloud_provider: str, config: Dict[str, Any]) -> Dict[str, float]:
    """Calculate current infrastructure costs"""
    costs = {
        'compute': 0.0,
        'storage': 0.0,
        'backup': 0.0,
        'network': 0.0,
        'total': 0.0
    }
    
    pricing = PRICING_DATABASE.get(cloud_provider, {})
    
    # Compute costs
    instance_type = config.get('instance_type')
    if instance_type and 'compute' in pricing:
        hourly_cost = pricing['compute'].get(instance_type, 0.2)
        costs['compute'] = hourly_cost * 730  # hours per month
    
    # Storage costs
    storage_gb = config.get('storage_gb', 100)
    storage_type = config.get('storage_type', 'gp3')
    
    if cloud_provider == 'aws':
        storage_rate = pricing.get(f'storage_{storage_type}', 0.08)
    elif cloud_provider == 'azure':
        storage_rate = pricing.get('storage_standard', 0.05)
    else:
        storage_rate = pricing.get('storage_standard', 0.09)
    
    costs['storage'] = storage_gb * storage_rate
    
    # Backup costs
    if config.get('backup_enabled', True):
        backup_gb = storage_gb * 1.2  # Assume 20% overhead
        costs['backup'] = backup_gb * pricing.get('backup', 0.095)
    
    # Network costs
    data_transfer_gb = config.get('data_transfer_gb_per_month', 100)
    costs['network'] = data_transfer_gb * pricing.get('data_transfer', 0.09)
    
    costs['total'] = sum(v for k, v in costs.items() if k != 'total')
    
    return costs


def identify_compute_optimizations(cloud_provider: str, config: Dict[str, Any], usage_patterns: Optional[Dict[str, Any]]) -> List[CostSavingOpportunity]:
    """Identify compute cost optimization opportunities"""
    opportunities = []
    
    current_instance = config.get('instance_type')
    if not current_instance:
        return opportunities
    
    # Check for over-provisioning
    if usage_patterns:
        cpu_utilization = usage_patterns.get('avg_cpu_utilization', 70)
        memory_utilization = usage_patterns.get('avg_memory_utilization', 70)
        
        if cpu_utilization < 30 and memory_utilization < 30:
            # Significant over-provisioning
            current_cost = PRICING_DATABASE[cloud_provider]['compute'].get(current_instance, 0.2) * 730
            
            # Recommend smaller instance
            if cloud_provider == 'aws':
                if 'xlarge' in current_instance:
                    recommended = current_instance.replace('xlarge', 'large')
                elif 'large' in current_instance:
                    recommended = current_instance.replace('large', 'medium')
                else:
                    recommended = current_instance
                
                optimized_cost = PRICING_DATABASE[cloud_provider]['compute'].get(recommended, 0.1) * 730
                savings = current_cost - optimized_cost
                
                if savings > 0:
                    opportunities.append(CostSavingOpportunity(
                        category=OptimizationCategory.COMPUTE,
                        title='Downsize over-provisioned instance',
                        description=f'CPU and memory utilization <30%. Downsize from {current_instance} to {recommended}',
                        current_monthly_cost=current_cost,
                        optimized_monthly_cost=optimized_cost,
                        monthly_savings=savings,
                        annual_savings=savings * 12,
                        implementation_effort='low',
                        risk_level='low',
                        confidence=90.0,
                        action_items=[
                            f'Test application on {recommended} instance',
                            'Schedule downtime for instance resize',
                            'Monitor performance post-migration'
                        ]
                    ))
    
    # Check for reserved instance opportunities
    if config.get('payment_model') == 'on-demand':
        current_cost = PRICING_DATABASE[cloud_provider]['compute'].get(current_instance, 0.2) * 730
        reserved_savings = current_cost * 0.3  # 30% savings estimate
        
        opportunities.append(CostSavingOpportunity(
            category=OptimizationCategory.COMPUTE,
            title='Switch to Reserved Instances',
            description='Save up to 30-60% by committing to 1-year or 3-year reserved instances',
            current_monthly_cost=current_cost,
            optimized_monthly_cost=current_cost * 0.7,
            monthly_savings=reserved_savings,
            annual_savings=reserved_savings * 12,
            implementation_effort='low',
            risk_level='low',
            confidence=95.0,
            action_items=[
                'Analyze usage patterns for consistency',
                'Purchase reserved instances',
                'Set up auto-renewal alerts'
            ]
        ))
    
    return opportunities


def identify_storage_optimizations(cloud_provider: str, config: Dict[str, Any]) -> List[CostSavingOpportunity]:
    """Identify storage cost optimization opportunities"""
    opportunities = []
    
    storage_gb = config.get('storage_gb', 100)
    storage_type = config.get('storage_type', 'gp3')
    
    # Check for storage type optimization
    if cloud_provider == 'aws' and storage_type == 'gp2':
        current_cost = storage_gb * PRICING_DATABASE['aws']['storage_gp2']
        optimized_cost = storage_gb * PRICING_DATABASE['aws']['storage_gp3']
        savings = current_cost - optimized_cost
        
        opportunities.append(CostSavingOpportunity(
            category=OptimizationCategory.STORAGE,
            title='Migrate from gp2 to gp3 storage',
            description='gp3 provides better performance at lower cost',
            current_monthly_cost=current_cost,
            optimized_monthly_cost=optimized_cost,
            monthly_savings=savings,
            annual_savings=savings * 12,
            implementation_effort='low',
            risk_level='low',
            confidence=100.0,
            action_items=[
                'Modify storage type to gp3',
                'No downtime required',
                'Monitor performance metrics'
            ]
        ))
    
    # Check for over-provisioned storage
    if config.get('storage_utilization_percent'):
        utilization = config['storage_utilization_percent']
        if utilization < 50:
            current_cost = storage_gb * 0.08  # Average storage cost
            optimized_gb = int(storage_gb * 0.6)  # Right-size to 60%
            optimized_cost = optimized_gb * 0.08
            savings = current_cost - optimized_cost
            
            opportunities.append(CostSavingOpportunity(
                category=OptimizationCategory.STORAGE,
                title='Right-size over-provisioned storage',
                description=f'Storage utilization is {utilization}%. Reduce from {storage_gb}GB to {optimized_gb}GB',
                current_monthly_cost=current_cost,
                optimized_monthly_cost=optimized_cost,
                monthly_savings=savings,
                annual_savings=savings * 12,
                implementation_effort='low',
                risk_level='medium',
                confidence=80.0,
                action_items=[
                    'Backup database before resizing',
                    'Reduce storage allocation',
                    'Monitor storage usage trends'
                ]
            ))
    
    return opportunities


def identify_backup_optimizations(config: Dict[str, Any]) -> List[CostSavingOpportunity]:
    """Identify backup cost optimization opportunities"""
    opportunities = []
    
    if config.get('backup_retention_days', 7) > 7:
        # Suggest moving older backups to cheaper storage
        storage_gb = config.get('storage_gb', 100)
        retention_days = config['backup_retention_days']
        
        # Calculate current backup storage cost
        total_backup_gb = storage_gb * retention_days
        current_cost = total_backup_gb * 0.095
        
        # Optimize by moving backups >7 days to glacier
        standard_backup_gb = storage_gb * 7
        archive_backup_gb = storage_gb * (retention_days - 7)
        optimized_cost = (standard_backup_gb * 0.095) + (archive_backup_gb * 0.004)
        savings = current_cost - optimized_cost
        
        if savings > 5:  # Only recommend if savings > $5/month
            opportunities.append(CostSavingOpportunity(
                category=OptimizationCategory.BACKUP,
                title='Optimize backup storage with tiering',
                description=f'Move backups older than 7 days to archive storage',
                current_monthly_cost=current_cost,
                optimized_monthly_cost=optimized_cost,
                monthly_savings=savings,
                annual_savings=savings * 12,
                implementation_effort='low',
                risk_level='low',
                confidence=95.0,
                action_items=[
                    'Configure backup lifecycle policy',
                    'Transition backups >7 days to glacier/archive',
                    'Test backup restoration from archive'
                ]
            ))
    
    return opportunities


def generate_reserved_instance_recommendations(cloud_provider: str, current_instance: str, current_cost: float) -> List[ReservedInstanceRecommendation]:
    """Generate reserved instance recommendations"""
    recommendations = []
    
    if current_instance:
        # 1-year reserved
        reserved_1yr_cost = current_cost * 0.7  # 30% savings
        savings_1yr = current_cost - reserved_1yr_cost
        
        # 3-year reserved
        reserved_3yr_cost = current_cost * 0.5  # 50% savings
        savings_3yr = current_cost - reserved_3yr_cost
        
        recommendations.append(ReservedInstanceRecommendation(
            instance_type=current_instance,
            current_on_demand_cost=current_cost,
            reserved_cost_1year=reserved_1yr_cost,
            reserved_cost_3year=reserved_3yr_cost,
            savings_1year=savings_1yr,
            savings_3year=savings_3yr,
            utilization_requirement=75.0,
            recommendation='Recommended if utilization stays consistent above 75%'
        ))
    
    return recommendations


@router.post("/analyze", response_model=CostOptimizationResponse)
async def analyze_cost_optimization(input_data: CostOptimizationInput):
    """
    Comprehensive cost optimization analysis
    
    Analyzes current infrastructure configuration and provides actionable
    cost optimization recommendations across compute, storage, backup, and network.
    """
    try:
        # Calculate current costs
        current_costs = calculate_current_costs(input_data.cloud_provider, input_data.current_config)
        
        # Identify optimization opportunities
        opportunities = []
        
        # Compute optimizations
        compute_ops = identify_compute_optimizations(
            input_data.cloud_provider,
            input_data.current_config,
            input_data.usage_patterns
        )
        opportunities.extend(compute_ops)
        
        # Storage optimizations
        storage_ops = identify_storage_optimizations(
            input_data.cloud_provider,
            input_data.current_config
        )
        opportunities.extend(storage_ops)
        
        # Backup optimizations
        backup_ops = identify_backup_optimizations(input_data.current_config)
        opportunities.extend(backup_ops)
        
        # Calculate total savings
        total_monthly_savings = sum(opp.monthly_savings for opp in opportunities)
        total_annual_savings = total_monthly_savings * 12
        optimized_monthly_cost = current_costs['total'] - total_monthly_savings
        savings_percentage = (total_monthly_savings / current_costs['total'] * 100) if current_costs['total'] > 0 else 0
        
        # Generate reserved instance recommendations
        ri_recommendations = generate_reserved_instance_recommendations(
            input_data.cloud_provider,
            input_data.current_config.get('instance_type'),
            current_costs['compute']
        )
        
        # Quick wins (low effort, high savings)
        quick_wins = [
            opp.title for opp in opportunities 
            if opp.implementation_effort == 'low' and opp.monthly_savings > 20
        ]
        
        # Long-term strategies
        long_term_strategies = [
            'Implement auto-scaling to match demand',
            'Use spot instances for non-critical workloads',
            'Implement comprehensive monitoring and alerting',
            'Review and optimize monthly'
        ]
        
        return CostOptimizationResponse(
            analysis_timestamp=datetime.utcnow(),
            cloud_provider=input_data.cloud_provider,
            current_monthly_cost=current_costs['total'],
            optimized_monthly_cost=max(0, optimized_monthly_cost),
            total_monthly_savings=total_monthly_savings,
            total_annual_savings=total_annual_savings,
            savings_percentage=round(savings_percentage, 2),
            opportunities=opportunities,
            reserved_instance_recommendations=ri_recommendations,
            quick_wins=quick_wins,
            long_term_strategies=long_term_strategies
        )
    
    except Exception as e:
        logger.error(f'Cost optimization analysis failed: {e}')
        raise HTTPException(status_code=500, detail=f'Analysis failed: {str(e)}')


@router.get("/pricing-estimate")
async def get_pricing_estimate(
    cloud_provider: str,
    instance_type: str,
    storage_gb: int,
    region: str = 'us-east-1'
):
    """Get cost estimate for specific configuration"""
    try:
        pricing = PRICING_DATABASE.get(cloud_provider, {})
        
        # Compute cost
        compute_hourly = pricing.get('compute', {}).get(instance_type, 0.2)
        compute_monthly = compute_hourly * 730
        
        # Storage cost
        storage_monthly = storage_gb * 0.08  # Average
        
        # Total
        total_monthly = compute_monthly + storage_monthly
        
        return {
            'cloud_provider': cloud_provider,
            'instance_type': instance_type,
            'storage_gb': storage_gb,
            'region': region,
            'breakdown': {
                'compute_monthly': round(compute_monthly, 2),
                'storage_monthly': round(storage_monthly, 2),
                'total_monthly': round(total_monthly, 2),
                'total_annual': round(total_monthly * 12, 2)
            }
        }
    
    except Exception as e:
        logger.error(f'Pricing estimate failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
