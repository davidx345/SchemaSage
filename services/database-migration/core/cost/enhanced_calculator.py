"""
Enhanced migration cost calculator.
Calculates detailed migration costs with TCO analysis and forecasts.
"""
from typing import List, Tuple, Dict
from datetime import datetime

from models.enhanced_cost_models import (
    CloudProvider, DatabaseService, MigrationComplexity, CostCategory,
    DatabaseConfig, WorkloadProfile, CostBreakdown, ResourceCost,
    MigrationCost, CostComparison, CostOptimizationOpportunity,
    PricingTier, CostForecast, CostStatistics, EnhancedCostSummary
)


class EnhancedCostCalculator:
    """
    Calculator for detailed migration costs with TCO analysis.
    """
    
    def __init__(self):
        """Initialize the cost calculator"""
        # Base pricing per cloud provider (simplified)
        self.pricing = {
            CloudProvider.AWS: {
                "compute_per_vcpu_monthly": 50.0,
                "storage_per_gb_monthly": 0.115,
                "memory_per_gb_monthly": 10.0,
                "iops_per_unit_monthly": 0.065,
                "data_transfer_per_gb": 0.09
            },
            CloudProvider.AZURE: {
                "compute_per_vcpu_monthly": 48.0,
                "storage_per_gb_monthly": 0.12,
                "memory_per_gb_monthly": 9.5,
                "iops_per_unit_monthly": 0.07,
                "data_transfer_per_gb": 0.087
            },
            CloudProvider.GCP: {
                "compute_per_vcpu_monthly": 45.0,
                "storage_per_gb_monthly": 0.10,
                "memory_per_gb_monthly": 9.0,
                "iops_per_unit_monthly": 0.06,
                "data_transfer_per_gb": 0.08
            }
        }
        
    def calculate_migration_cost(
        self,
        source_db: DatabaseConfig,
        target_provider: CloudProvider,
        target_service: DatabaseService,
        target_db: DatabaseConfig,
        workload: WorkloadProfile,
        complexity: MigrationComplexity,
        region: str,
        commitment_months: int = 0
    ) -> Tuple[CostBreakdown, MigrationCost, CostComparison,
               List[CostOptimizationOpportunity], List[PricingTier],
               CostForecast, CostStatistics, EnhancedCostSummary, List[str]]:
        """
        Calculate comprehensive migration costs.
        """
        # Calculate ongoing costs
        cost_breakdown = self._calculate_ongoing_costs(
            target_db, target_provider, workload, region, commitment_months
        )
        
        # Calculate one-time migration costs
        migration_costs = self._calculate_migration_costs(
            source_db, target_db, complexity, workload
        )
        
        # Compare source vs target
        comparison = self._compare_costs(
            source_db, target_db, target_provider, cost_breakdown, migration_costs
        )
        
        # Identify optimization opportunities
        optimizations = self._identify_optimizations(
            target_db, workload, cost_breakdown, target_provider
        )
        
        # Generate alternative pricing tiers
        alternatives = self._generate_alternatives(
            target_db, target_provider, target_service
        )
        
        # Generate 5-year forecast
        forecast = self._generate_forecast(
            cost_breakdown, workload, migration_costs
        )
        
        # Calculate statistics
        statistics = self._calculate_statistics(
            cost_breakdown, workload, target_db
        )
        
        # Generate summary
        summary = self._generate_summary(
            cost_breakdown, migration_costs, forecast, comparison
        )
        
        # Generate warnings
        warnings = self._generate_warnings(
            cost_breakdown, comparison, workload
        )
        
        return (cost_breakdown, migration_costs, comparison, optimizations,
                alternatives, forecast, statistics, summary, warnings)
                
    def _calculate_ongoing_costs(
        self,
        db: DatabaseConfig,
        provider: CloudProvider,
        workload: WorkloadProfile,
        region: str,
        commitment: int
    ) -> CostBreakdown:
        """Calculate ongoing monthly costs"""
        pricing = self.pricing.get(provider, self.pricing[CloudProvider.AWS])
        
        # Compute costs
        compute_monthly = db.vcpus * pricing["compute_per_vcpu_monthly"]
        compute_annual = compute_monthly * 12
        
        # Storage costs
        storage_monthly = db.storage_size_gb * pricing["storage_per_gb_monthly"]
        storage_annual = storage_monthly * 12
        
        # Memory costs
        memory_monthly = db.memory_gb * pricing["memory_per_gb_monthly"]
        memory_annual = memory_monthly * 12
        
        # IOPS costs
        iops_monthly = db.iops * pricing["iops_per_unit_monthly"]
        iops_annual = iops_monthly * 12
        
        # Network/data transfer
        network_monthly = workload.estimated_data_transfer_gb_monthly * pricing["data_transfer_per_gb"]
        network_annual = network_monthly * 12
        
        # Backup costs (10% of storage)
        backup_monthly = storage_monthly * 0.10
        backup_annual = backup_monthly * 12
        
        # Licensing (for commercial databases)
        license_monthly = 0.0
        if "sqlserver" in db.engine.lower() or "oracle" in db.engine.lower():
            license_monthly = compute_monthly * 0.5
        license_annual = license_monthly * 12
        
        # Support costs (5% of total)
        base_total = (compute_monthly + storage_monthly + memory_monthly +
                     iops_monthly + network_monthly + backup_monthly + license_monthly)
        support_monthly = base_total * 0.05
        support_annual = support_monthly * 12
        
        # Apply commitment discount
        discount_multiplier = 1.0
        if commitment >= 36:
            discount_multiplier = 0.72  # 28% discount
        elif commitment >= 12:
            discount_multiplier = 0.85  # 15% discount
            
        # Calculate total
        total_monthly = base_total + support_monthly
        total_annual = total_monthly * 12
        
        # Apply discount
        total_monthly *= discount_multiplier
        total_annual *= discount_multiplier
        
        # Calculate percentages
        categories = {
            CostCategory.COMPUTE: compute_monthly * discount_multiplier,
            CostCategory.STORAGE: storage_monthly * discount_multiplier,
            CostCategory.NETWORK: network_monthly * discount_multiplier,
            CostCategory.LICENSING: license_monthly * discount_multiplier,
            CostCategory.SUPPORT: support_monthly * discount_multiplier,
            CostCategory.BACKUP: backup_monthly * discount_multiplier
        }
        
        costs = {}
        for category, monthly in categories.items():
            percentage = (monthly / total_monthly * 100) if total_monthly > 0 else 0
            costs[category] = ResourceCost(
                monthly_cost=round(monthly, 2),
                annual_cost=round(monthly * 12, 2),
                percentage_of_total=round(percentage, 1)
            )
            
        return CostBreakdown(costs=costs)
        
    def _calculate_migration_costs(
        self,
        source: DatabaseConfig,
        target: DatabaseConfig,
        complexity: MigrationComplexity,
        workload: WorkloadProfile
    ) -> MigrationCost:
        """Calculate one-time migration costs"""
        # Base migration cost by complexity
        complexity_multipliers = {
            MigrationComplexity.LOW: 5000,
            MigrationComplexity.MEDIUM: 15000,
            MigrationComplexity.HIGH: 35000,
            MigrationComplexity.VERY_HIGH: 75000
        }
        base_cost = complexity_multipliers.get(complexity, 15000)
        
        # Tool licensing (for commercial migration tools)
        tool_license = base_cost * 0.1
        
        # Data transfer costs (one-time)
        data_transfer = source.storage_size_gb * 0.05
        
        # Estimated downtime cost (based on workload)
        downtime_hours = 4 if complexity == MigrationComplexity.LOW else 24
        hourly_cost = workload.daily_active_users * 10  # $10 per user-hour
        downtime_cost = downtime_hours * hourly_cost
        
        # Professional services
        professional_services = base_cost * 0.8
        
        # Testing and validation
        testing = base_cost * 0.3
        
        total = tool_license + data_transfer + downtime_cost + professional_services + testing
        
        return MigrationCost(
            migration_tool_license=round(tool_license, 2),
            data_transfer_cost=round(data_transfer, 2),
            estimated_downtime_cost=round(downtime_cost, 2),
            professional_services=round(professional_services, 2),
            testing_and_validation=round(testing, 2),
            total_one_time_cost=round(total, 2)
        )
        
    def _compare_costs(
        self,
        source: DatabaseConfig,
        target: DatabaseConfig,
        provider: CloudProvider,
        breakdown: CostBreakdown,
        migration: MigrationCost
    ) -> CostComparison:
        """Compare source vs target costs"""
        # Estimate current monthly cost (simplified)
        current_monthly = source.storage_size_gb * 0.15 + source.memory_gb * 12 + source.vcpus * 60
        
        # Target monthly cost
        target_monthly = sum(cost.monthly_cost for cost in breakdown.costs.values())
        
        # Calculate savings
        monthly_savings = current_monthly - target_monthly
        annual_savings = monthly_savings * 12
        
        # Calculate break-even
        if monthly_savings > 0:
            break_even = migration.total_one_time_cost / monthly_savings
        else:
            break_even = 999  # Never breaks even
            
        # ROI calculation
        first_year_savings = annual_savings - migration.total_one_time_cost
        roi = (first_year_savings / migration.total_one_time_cost * 100) if migration.total_one_time_cost > 0 else 0
        
        return CostComparison(
            current_monthly_cost=round(current_monthly, 2),
            target_monthly_cost=round(target_monthly, 2),
            monthly_savings=round(monthly_savings, 2),
            annual_savings=round(annual_savings, 2),
            break_even_months=round(break_even, 1),
            roi_percent=round(roi, 1)
        )
        
    def _identify_optimizations(
        self,
        db: DatabaseConfig,
        workload: WorkloadProfile,
        breakdown: CostBreakdown,
        provider: CloudProvider
    ) -> List[CostOptimizationOpportunity]:
        """Identify cost optimization opportunities"""
        opportunities = []
        
        # Check for over-provisioning
        if workload.queries_per_second < 100 and db.vcpus > 4:
            savings = db.vcpus * 25  # $25 per vCPU monthly
            opportunities.append(CostOptimizationOpportunity(
                opportunity_type="Right-sizing",
                description="Database appears over-provisioned for current workload",
                potential_monthly_savings=round(savings, 2),
                implementation_complexity="Low",
                recommendation="Reduce vCPUs from current allocation"
            ))
            
        # Check for reserved instance opportunity
        opportunities.append(CostOptimizationOpportunity(
            opportunity_type="Reserved Instances",
            description="Commit to 1-3 year term for significant discounts",
            potential_monthly_savings=round(sum(c.monthly_cost for c in breakdown.costs.values()) * 0.25, 2),
            implementation_complexity="Low",
            recommendation="Purchase 1-year or 3-year reserved capacity"
        ))
        
        # Check storage optimization
        if db.storage_size_gb > 1000:
            opportunities.append(CostOptimizationOpportunity(
                opportunity_type="Storage Optimization",
                description="Implement data archival for older records",
                potential_monthly_savings=round(db.storage_size_gb * 0.10 * 0.3, 2),
                implementation_complexity="Medium",
                recommendation="Archive data older than 2 years to cheaper storage"
            ))
            
        return opportunities
        
    def _generate_alternatives(
        self,
        db: DatabaseConfig,
        provider: CloudProvider,
        service: DatabaseService
    ) -> List[PricingTier]:
        """Generate alternative pricing tiers"""
        alternatives = []
        
        # Current tier
        current_monthly = db.vcpus * 50 + db.memory_gb * 10 + db.storage_size_gb * 0.12
        
        # Lower tier
        alternatives.append(PricingTier(
            tier_name="Basic",
            vcpus=max(2, db.vcpus // 2),
            memory_gb=max(4, db.memory_gb // 2),
            storage_gb=db.storage_size_gb,
            monthly_cost=round(current_monthly * 0.5, 2),
            recommended_for="Development/Testing workloads"
        ))
        
        # Current tier
        alternatives.append(PricingTier(
            tier_name="Standard",
            vcpus=db.vcpus,
            memory_gb=db.memory_gb,
            storage_gb=db.storage_size_gb,
            monthly_cost=round(current_monthly, 2),
            recommended_for="Production workloads (current configuration)"
        ))
        
        # Higher tier
        alternatives.append(PricingTier(
            tier_name="Premium",
            vcpus=db.vcpus * 2,
            memory_gb=db.memory_gb * 2,
            storage_gb=db.storage_size_gb,
            monthly_cost=round(current_monthly * 2, 2),
            recommended_for="High-performance production workloads"
        ))
        
        return alternatives
        
    def _generate_forecast(
        self,
        breakdown: CostBreakdown,
        workload: WorkloadProfile,
        migration: MigrationCost
    ) -> CostForecast:
        """Generate 5-year cost forecast"""
        base_monthly = sum(cost.monthly_cost for cost in breakdown.costs.values())
        
        # Apply growth rate
        growth_rate = workload.data_growth_percent_yearly / 100
        
        years = []
        for year in range(1, 6):
            # Calculate growth multiplier
            multiplier = (1 + growth_rate) ** year
            projected_monthly = base_monthly * multiplier
            projected_annual = projected_monthly * 12
            
            # Add migration cost in year 1
            total = projected_annual
            if year == 1:
                total += migration.total_one_time_cost
                
            years.append({
                "year": year,
                "projected_monthly_cost": round(projected_monthly, 2),
                "projected_annual_cost": round(projected_annual, 2),
                "cumulative_cost": round(total, 2)
            })
            
        return CostForecast(forecast_years=years)
        
    def _calculate_statistics(
        self,
        breakdown: CostBreakdown,
        workload: WorkloadProfile,
        db: DatabaseConfig
    ) -> CostStatistics:
        """Calculate cost statistics"""
        total_monthly = sum(cost.monthly_cost for cost in breakdown.costs.values())
        
        cost_per_user = total_monthly / max(1, workload.daily_active_users)
        cost_per_gb = total_monthly / max(1, db.storage_size_gb)
        cost_per_query = (total_monthly / max(1, workload.queries_per_second)) / (30 * 24 * 3600)
        
        return CostStatistics(
            cost_per_user_monthly=round(cost_per_user, 2),
            cost_per_gb_monthly=round(cost_per_gb, 2),
            cost_per_transaction=round(cost_per_query * 1000, 4)
        )
        
    def _generate_summary(
        self,
        breakdown: CostBreakdown,
        migration: MigrationCost,
        forecast: CostForecast,
        comparison: CostComparison
    ) -> EnhancedCostSummary:
        """Generate cost summary"""
        monthly_total = sum(cost.monthly_cost for cost in breakdown.costs.values())
        
        year1_total = monthly_total * 12 + migration.total_one_time_cost
        year3_total = sum(y["cumulative_cost"] for y in forecast.forecast_years[:3])
        
        return EnhancedCostSummary(
            total_cost_of_ownership_year1=round(year1_total, 2),
            total_cost_of_ownership_year3=round(year3_total, 2),
            recommended_action="Proceed with migration" if comparison.roi_percent > 20 else "Evaluate alternatives"
        )
        
    def _generate_warnings(
        self,
        breakdown: CostBreakdown,
        comparison: CostComparison,
        workload: WorkloadProfile
    ) -> List[str]:
        """Generate cost warnings"""
        warnings = []
        
        monthly_total = sum(cost.monthly_cost for cost in breakdown.costs.values())
        
        if monthly_total > 10000:
            warnings.append(f"High monthly cost (${monthly_total:,.2f}) - review optimization opportunities")
            
        if comparison.break_even_months > 24:
            warnings.append(f"Long break-even period ({comparison.break_even_months:.1f} months) - consider alternatives")
            
        if workload.data_growth_percent_yearly > 50:
            warnings.append(f"High growth rate ({workload.data_growth_percent_yearly}% yearly) will significantly increase future costs")
            
        return warnings


def calculate_enhanced_migration_cost(
    source_db: DatabaseConfig,
    target_provider: CloudProvider,
    target_service: DatabaseService,
    target_db: DatabaseConfig,
    workload: WorkloadProfile,
    complexity: MigrationComplexity,
    region: str,
    commitment_months: int = 0
) -> Tuple:
    """Calculate enhanced migration costs"""
    calculator = EnhancedCostCalculator()
    return calculator.calculate_migration_cost(
        source_db, target_provider, target_service, target_db,
        workload, complexity, region, commitment_months
    )
