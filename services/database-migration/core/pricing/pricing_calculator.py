"""
Unified Pricing Calculator
Calculates and compares costs across AWS, GCP, and Azure
"""
from typing import Dict, List
import logging
from .aws_pricing import AWSPricing
from .gcp_pricing import GCPPricing
from .azure_pricing import AzurePricing

logger = logging.getLogger(__name__)


class PricingCalculator:
    """
    Unified pricing calculator for multi-cloud cost comparison
    """
    
    # Region mapping between providers
    REGION_MAPPING = {
        "us-east-1": {"aws": "us-east-1", "gcp": "us-east1", "azure": "eastus"},
        "us-west-2": {"aws": "us-west-2", "gcp": "us-west2", "azure": "westus2"},
        "eu-west-1": {"aws": "eu-west-1", "gcp": "europe-west1", "azure": "northeurope"},
        "ap-southeast-1": {"aws": "ap-southeast-1", "gcp": "asia-southeast1", "azure": "southeastasia"}
    }
    
    # Storage type mapping
    STORAGE_TYPE_MAPPING = {
        "aws": "gp3",
        "gcp": "pd-ssd",
        "azure": "Premium_LRS"
    }
    
    @classmethod
    def calculate_provider_cost(
        cls,
        provider: str,
        database_type: str,
        storage_gb: int,
        region: str,
        qps: int,
        connections: int,
        iops: int
    ) -> Dict:
        """
        Calculate cost for a specific provider
        
        Args:
            provider: Cloud provider (aws, gcp, azure)
            database_type: Type of database
            storage_gb: Storage size in GB
            region: Region (unified format like us-east-1)
            qps: Queries per second
            connections: Max concurrent connections
            iops: Required IOPS
            
        Returns:
            Dict with cost breakdown and instance details
        """
        # Map region to provider-specific format
        provider_region = cls.REGION_MAPPING.get(region, {}).get(provider, region)
        
        # Get appropriate pricing class
        if provider == "aws":
            pricing_class = AWSPricing
        elif provider == "gcp":
            pricing_class = GCPPricing
        elif provider == "azure":
            pricing_class = AzurePricing
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Estimate required resources
        resources = pricing_class.estimate_required_resources(qps, connections)
        cpu_cores = resources["cpu_cores"]
        memory_gb = resources["memory_gb"]
        
        # Match instance type
        instance_type = pricing_class.match_instance_by_requirements(
            cpu_cores, memory_gb, iops
        )
        
        # Get instance specs
        specs = pricing_class.get_instance_specs(instance_type)
        if not specs:
            logger.error(f"No specs found for {provider} instance {instance_type}")
            specs = {"cpu_cores": cpu_cores, "memory_gb": memory_gb, "max_iops": iops}
        
        # Calculate costs
        instance_cost = pricing_class.get_instance_cost(instance_type, provider_region)
        storage_type = cls.STORAGE_TYPE_MAPPING.get(provider, "gp3")
        storage_cost = pricing_class.get_storage_cost(storage_gb, storage_type)
        backup_cost = pricing_class.get_backup_cost(storage_gb)
        network_cost = pricing_class.get_network_cost()
        iops_cost = pricing_class.get_iops_cost(iops, storage_type)
        
        total_cost = instance_cost + storage_cost + backup_cost + network_cost + iops_cost
        
        return {
            "provider": provider,
            "instance_type": instance_type,
            "monthly_cost": round(total_cost, 2),
            "breakdown": {
                "instance": round(instance_cost, 2),
                "storage": round(storage_cost, 2),
                "backup": round(backup_cost, 2),
                "network": round(network_cost, 2),
                "iops": round(iops_cost, 2)
            },
            "specs": {
                "cpu_cores": specs["cpu_cores"],
                "memory_gb": specs["memory_gb"],
                "storage_type": storage_type,
                "iops": specs.get("max_iops", iops)
            }
        }
    
    @classmethod
    def compare_all_providers(
        cls,
        database_type: str,
        storage_gb: int,
        region: str,
        qps: int,
        connections: int,
        iops: int
    ) -> Dict:
        """
        Compare costs across all cloud providers
        
        Returns:
            Dict with providers list, recommendation, and savings
        """
        providers_data = []
        
        # Calculate for each provider
        for provider in ["aws", "gcp", "azure"]:
            try:
                provider_data = cls.calculate_provider_cost(
                    provider, database_type, storage_gb, region, qps, connections, iops
                )
                providers_data.append(provider_data)
            except Exception as e:
                logger.error(f"Error calculating {provider} costs: {e}")
                continue
        
        if not providers_data:
            raise ValueError("Could not calculate costs for any provider")
        
        # Sort by cost (cheapest first)
        providers_data.sort(key=lambda x: x["monthly_cost"])
        
        # Determine recommendation (cheapest)
        recommendation = providers_data[0]["provider"]
        cheapest_cost = providers_data[0]["monthly_cost"]
        
        # Calculate savings vs other providers
        savings = {}
        for provider_data in providers_data[1:]:
            provider_name = provider_data["provider"]
            saving = provider_data["monthly_cost"] - cheapest_cost
            savings[f"vs_{provider_name}"] = round(saving, 2)
        
        return {
            "providers": providers_data,
            "recommendation": recommendation,
            "savings": savings
        }
