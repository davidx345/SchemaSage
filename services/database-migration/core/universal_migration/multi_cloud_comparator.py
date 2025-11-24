"""
Multi-Cloud Comparator Core Logic.
Compares database offerings across AWS, Azure, and GCP.
"""
from typing import List, Dict, Any
from models.universal_migration_models import (
    CloudComparisonData, CloudRecommendation, BestValue, CloudProvider
)


class MultiCloudComparator:
    """
    Compares database offerings across multiple cloud providers.
    """
    
    # Pricing data (simplified, per hour in USD)
    PRICING = {
        CloudProvider.AWS: {
            "postgresql": {"db.t3.medium": 0.068, "db.r5.large": 0.24, "db.r5.xlarge": 0.48},
            "mysql": {"db.t3.medium": 0.068, "db.r5.large": 0.24, "db.r5.xlarge": 0.48},
            "mongodb": {"M10": 0.08, "M20": 0.20, "M30": 0.54}
        },
        CloudProvider.AZURE: {
            "postgresql": {"B_Gen5_1": 0.055, "GP_Gen5_2": 0.228, "GP_Gen5_4": 0.456},
            "mysql": {"B_Gen5_1": 0.055, "GP_Gen5_2": 0.228, "GP_Gen5_4": 0.456},
            "mongodb": {"M10": 0.08, "M20": 0.20, "M30": 0.54}
        },
        CloudProvider.GCP: {
            "postgresql": {"db-n1-standard-1": 0.095, "db-n1-standard-2": 0.19, "db-n1-standard-4": 0.38},
            "mysql": {"db-n1-standard-1": 0.095, "db-n1-standard-2": 0.19, "db-n1-standard-4": 0.38},
            "mongodb": {"M10": 0.08, "M20": 0.20, "M30": 0.54}
        }
    }
    
    def compare_offerings(self, db_type: str, workload_size: str, required_features: List[str]) -> CloudComparisonData:
        """Compares database offerings across cloud providers."""
        recommendations = []
        
        # AWS Recommendation
        aws_rec = self._generate_aws_recommendation(db_type, workload_size, required_features)
        recommendations.append(aws_rec)
        
        # Azure Recommendation
        azure_rec = self._generate_azure_recommendation(db_type, workload_size, required_features)
        recommendations.append(azure_rec)
        
        # GCP Recommendation
        gcp_rec = self._generate_gcp_recommendation(db_type, workload_size, required_features)
        recommendations.append(gcp_rec)
        
        # Find best value
        best_rec = max(recommendations, key=lambda x: x.overall_score)
        best_value = BestValue(
            provider=best_rec.provider,
            reason=f"Best overall score ({best_rec.overall_score}/100) with optimal cost-performance ratio",
            estimated_savings_vs_others=self._calculate_savings(best_rec, recommendations)
        )
        
        return CloudComparisonData(
            recommendations=recommendations,
            best_value=best_value
        )
    
    def _generate_aws_recommendation(self, db_type: str, workload_size: str, required_features: List[str]) -> CloudRecommendation:
        """Generates AWS recommendation."""
        service_name = self._get_aws_service_name(db_type)
        instance_type = self._select_instance(workload_size, "aws")
        
        monthly_cost = self._calculate_monthly_cost(CloudProvider.AWS, db_type, instance_type)
        
        features = ["Auto-scaling", "Multi-AZ deployment", "Read replicas", "Automated backups", "Point-in-time recovery"]
        pros = ["Mature ecosystem", "Extensive global reach", "Deep integration with AWS services", "Comprehensive monitoring"]
        cons = ["Can be expensive at scale", "Complex pricing model", "Vendor lock-in concerns"]
        
        # Calculate scores
        cost_score = self._calculate_cost_score(monthly_cost, db_type, workload_size)
        performance_score = 85
        reliability_score = 92
        ease_of_use_score = 80
        
        overall_score = int((cost_score + performance_score + reliability_score + ease_of_use_score) / 4)
        
        return CloudRecommendation(
            provider=CloudProvider.AWS,
            service_name=service_name,
            instance_type=instance_type,
            estimated_monthly_cost=monthly_cost,
            supported_features=features,
            pros=pros,
            cons=cons,
            cost_score=cost_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            ease_of_use_score=ease_of_use_score,
            overall_score=overall_score
        )
    
    def _generate_azure_recommendation(self, db_type: str, workload_size: str, required_features: List[str]) -> CloudRecommendation:
        """Generates Azure recommendation."""
        service_name = self._get_azure_service_name(db_type)
        instance_type = self._select_instance(workload_size, "azure")
        
        monthly_cost = self._calculate_monthly_cost(CloudProvider.AZURE, db_type, instance_type)
        
        features = ["Hyperscale tier", "Intelligent performance", "Advanced threat protection", "Automated tuning", "Built-in HA"]
        pros = ["Competitive pricing", "Excellent hybrid cloud support", "Strong enterprise features", "Active Directory integration"]
        cons = ["Smaller global footprint than AWS", "Less mature ecosystem", "Occasional service limitations"]
        
        cost_score = self._calculate_cost_score(monthly_cost, db_type, workload_size)
        performance_score = 83
        reliability_score = 88
        ease_of_use_score = 85
        
        overall_score = int((cost_score + performance_score + reliability_score + ease_of_use_score) / 4)
        
        return CloudRecommendation(
            provider=CloudProvider.AZURE,
            service_name=service_name,
            instance_type=instance_type,
            estimated_monthly_cost=monthly_cost,
            supported_features=features,
            pros=pros,
            cons=cons,
            cost_score=cost_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            ease_of_use_score=ease_of_use_score,
            overall_score=overall_score
        )
    
    def _generate_gcp_recommendation(self, db_type: str, workload_size: str, required_features: List[str]) -> CloudRecommendation:
        """Generates GCP recommendation."""
        service_name = self._get_gcp_service_name(db_type)
        instance_type = self._select_instance(workload_size, "gcp")
        
        monthly_cost = self._calculate_monthly_cost(CloudProvider.GCP, db_type, instance_type)
        
        features = ["Automatic storage increase", "Query Insights", "High availability config", "Automated backups", "Cloud SQL Proxy"]
        pros = ["Strong data analytics integration", "Innovative features", "Good performance", "Competitive pricing for compute"]
        cons = ["Smaller market share", "Less third-party integrations", "Limited regional availability"]
        
        cost_score = self._calculate_cost_score(monthly_cost, db_type, workload_size)
        performance_score = 86
        reliability_score = 87
        ease_of_use_score = 82
        
        overall_score = int((cost_score + performance_score + reliability_score + ease_of_use_score) / 4)
        
        return CloudRecommendation(
            provider=CloudProvider.GCP,
            service_name=service_name,
            instance_type=instance_type,
            estimated_monthly_cost=monthly_cost,
            supported_features=features,
            pros=pros,
            cons=cons,
            cost_score=cost_score,
            performance_score=performance_score,
            reliability_score=reliability_score,
            ease_of_use_score=ease_of_use_score,
            overall_score=overall_score
        )
    
    def _get_aws_service_name(self, db_type: str) -> str:
        """Gets AWS service name for database type."""
        mapping = {
            "postgresql": "Amazon RDS for PostgreSQL",
            "mysql": "Amazon RDS for MySQL",
            "mongodb": "Amazon DocumentDB",
            "mssql": "Amazon RDS for SQL Server",
            "oracle": "Amazon RDS for Oracle"
        }
        return mapping.get(db_type.lower(), "Amazon RDS")
    
    def _get_azure_service_name(self, db_type: str) -> str:
        """Gets Azure service name for database type."""
        mapping = {
            "postgresql": "Azure Database for PostgreSQL",
            "mysql": "Azure Database for MySQL",
            "mongodb": "Azure Cosmos DB for MongoDB",
            "mssql": "Azure SQL Database"
        }
        return mapping.get(db_type.lower(), "Azure SQL Database")
    
    def _get_gcp_service_name(self, db_type: str) -> str:
        """Gets GCP service name for database type."""
        mapping = {
            "postgresql": "Cloud SQL for PostgreSQL",
            "mysql": "Cloud SQL for MySQL",
            "mongodb": "MongoDB Atlas on GCP",
            "mssql": "Cloud SQL for SQL Server"
        }
        return mapping.get(db_type.lower(), "Cloud SQL")
    
    def _select_instance(self, workload_size: str, provider: str) -> str:
        """Selects appropriate instance type based on workload size."""
        if provider == "aws":
            mapping = {"small": "db.t3.medium", "medium": "db.r5.large", "large": "db.r5.xlarge"}
        elif provider == "azure":
            mapping = {"small": "B_Gen5_1", "medium": "GP_Gen5_2", "large": "GP_Gen5_4"}
        else:  # gcp
            mapping = {"small": "db-n1-standard-1", "medium": "db-n1-standard-2", "large": "db-n1-standard-4"}
        return mapping.get(workload_size.lower(), mapping["medium"])
    
    def _calculate_monthly_cost(self, provider: CloudProvider, db_type: str, instance_type: str) -> float:
        """Calculates estimated monthly cost."""
        hourly_cost = self.PRICING.get(provider, {}).get(db_type.lower(), {}).get(instance_type, 0.10)
        hours_per_month = 730  # Average hours in a month
        storage_cost = 50  # Base storage cost
        return round((hourly_cost * hours_per_month) + storage_cost, 2)
    
    def _calculate_cost_score(self, monthly_cost: float, db_type: str, workload_size: str) -> int:
        """Calculates cost score (0-100, higher is better)."""
        # Lower cost = higher score
        if monthly_cost < 100:
            return 95
        elif monthly_cost < 200:
            return 85
        elif monthly_cost < 300:
            return 75
        elif monthly_cost < 500:
            return 65
        else:
            return 55
    
    def _calculate_savings(self, best_rec: CloudRecommendation, all_recs: List[CloudRecommendation]) -> str:
        """Calculates savings compared to other providers."""
        other_costs = [r.estimated_monthly_cost for r in all_recs if r.provider != best_rec.provider]
        if not other_costs:
            return "N/A"
        
        avg_other_cost = sum(other_costs) / len(other_costs)
        savings_pct = ((avg_other_cost - best_rec.estimated_monthly_cost) / avg_other_cost) * 100
        
        if savings_pct > 0:
            return f"~{int(savings_pct)}% savings (${avg_other_cost - best_rec.estimated_monthly_cost:.2f}/month)"
        else:
            return "Comparable pricing"
