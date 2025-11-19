"""
Azure Pricing Data and Calculator
Hardcoded pricing data for MVP
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AzurePricing:
    """Azure Database for PostgreSQL pricing"""
    
    # Azure Database pricing per hour by region
    INSTANCE_PRICING = {
        "eastus": {
            "Standard_B1ms": 0.0209,
            "Standard_B2s": 0.0836,
            "Standard_D2s_v3": 0.192,
            "Standard_D4s_v3": 0.384,
            "Standard_D8s_v3": 0.768,
            "Standard_D16s_v3": 1.536,
            "Standard_E2s_v3": 0.252,
            "Standard_E4s_v3": 0.504,
            "Standard_E8s_v3": 1.008
        },
        "westus2": {
            "Standard_B1ms": 0.0209,
            "Standard_B2s": 0.0836,
            "Standard_D2s_v3": 0.192,
            "Standard_D4s_v3": 0.384,
            "Standard_D8s_v3": 0.768,
            "Standard_D16s_v3": 1.536,
            "Standard_E2s_v3": 0.252,
            "Standard_E4s_v3": 0.504,
            "Standard_E8s_v3": 1.008
        },
        "northeurope": {
            "Standard_B1ms": 0.0230,
            "Standard_B2s": 0.0920,
            "Standard_D2s_v3": 0.211,
            "Standard_D4s_v3": 0.422,
            "Standard_D8s_v3": 0.845,
            "Standard_D16s_v3": 1.690,
            "Standard_E2s_v3": 0.277,
            "Standard_E4s_v3": 0.554,
            "Standard_E8s_v3": 1.109
        },
        "southeastasia": {
            "Standard_B1ms": 0.0251,
            "Standard_B2s": 0.1004,
            "Standard_D2s_v3": 0.230,
            "Standard_D4s_v3": 0.461,
            "Standard_D8s_v3": 0.922,
            "Standard_D16s_v3": 1.843,
            "Standard_E2s_v3": 0.302,
            "Standard_E4s_v3": 0.605,
            "Standard_E8s_v3": 1.210
        }
    }
    
    # Instance specifications
    INSTANCE_SPECS = {
        "Standard_B1ms": {"cpu_cores": 1, "memory_gb": 2, "max_iops": 640},
        "Standard_B2s": {"cpu_cores": 2, "memory_gb": 4, "max_iops": 1280},
        "Standard_D2s_v3": {"cpu_cores": 2, "memory_gb": 8, "max_iops": 3200},
        "Standard_D4s_v3": {"cpu_cores": 4, "memory_gb": 16, "max_iops": 6400},
        "Standard_D8s_v3": {"cpu_cores": 8, "memory_gb": 32, "max_iops": 12800},
        "Standard_D16s_v3": {"cpu_cores": 16, "memory_gb": 64, "max_iops": 25600},
        "Standard_E2s_v3": {"cpu_cores": 2, "memory_gb": 16, "max_iops": 3200},
        "Standard_E4s_v3": {"cpu_cores": 4, "memory_gb": 32, "max_iops": 6400},
        "Standard_E8s_v3": {"cpu_cores": 8, "memory_gb": 64, "max_iops": 12800}
    }
    
    # Storage pricing per GB-month
    STORAGE_PRICING = {
        "Premium_LRS": 0.150,
        "Standard_LRS": 0.045
    }
    
    # Backup storage pricing
    BACKUP_PRICING = 0.095
    
    # Network egress pricing per GB
    NETWORK_EGRESS = {
        "first_5gb": 0.00,
        "next_10tb": 0.087,
        "over_10tb": 0.083
    }
    
    @classmethod
    def get_instance_cost(cls, instance_type: str, region: str = "eastus") -> float:
        """Get monthly instance cost"""
        hourly_rate = cls.INSTANCE_PRICING.get(region, cls.INSTANCE_PRICING["eastus"]).get(instance_type, 0)
        return hourly_rate * 730
    
    @classmethod
    def get_storage_cost(cls, storage_gb: int, storage_type: str = "Premium_LRS") -> float:
        """Calculate monthly storage cost"""
        rate = cls.STORAGE_PRICING.get(storage_type, cls.STORAGE_PRICING["Premium_LRS"])
        return storage_gb * rate
    
    @classmethod
    def get_backup_cost(cls, storage_gb: int) -> float:
        """Calculate monthly backup cost"""
        return storage_gb * cls.BACKUP_PRICING * 2.2
    
    @classmethod
    def get_iops_cost(cls, iops: int, storage_type: str = "Premium_LRS") -> float:
        """Calculate IOPS cost"""
        if storage_type == "Premium_LRS":
            return 0.0
        else:
            return iops * 0.05
    
    @classmethod
    def get_network_cost(cls, data_transfer_gb: float = 0) -> float:
        """Calculate monthly network egress cost"""
        if data_transfer_gb <= 0:
            return 6.5
        
        cost = 0.0
        remaining = data_transfer_gb
        
        if remaining <= 5:
            return 0.0
        remaining -= 5
        
        billable = min(remaining, 10240)
        cost += billable * cls.NETWORK_EGRESS["next_10tb"]
        remaining -= billable
        
        if remaining > 0:
            cost += remaining * cls.NETWORK_EGRESS["over_10tb"]
        
        return cost
    
    @classmethod
    def get_instance_specs(cls, instance_type: str) -> Optional[Dict]:
        """Get instance specifications"""
        return cls.INSTANCE_SPECS.get(instance_type)
    
    @classmethod
    def match_instance_by_requirements(cls, cpu_cores: int, memory_gb: float, iops: int) -> str:
        """Find the best matching instance type"""
        best_match = None
        best_score = float('inf')
        
        for instance_type, specs in cls.INSTANCE_SPECS.items():
            if specs["cpu_cores"] < cpu_cores:
                continue
            if specs["memory_gb"] < memory_gb:
                continue
            if specs["max_iops"] < iops:
                continue
            
            cpu_waste = specs["cpu_cores"] - cpu_cores
            memory_waste = specs["memory_gb"] - memory_gb
            iops_waste = specs["max_iops"] - iops
            
            score = (cpu_waste * 2) + (memory_waste * 0.5) + (iops_waste * 0.001)
            
            if score < best_score:
                best_score = score
                best_match = instance_type
        
        if best_match is None:
            logger.warning(f"No Azure instance matches requirements")
            return "Standard_E8s_v3"
        
        return best_match
    
    @classmethod
    def estimate_required_resources(cls, qps: int, connections: int) -> Dict:
        """Estimate required resources"""
        cpu_cores = max(2, int(qps / 1000) + 1)
        memory_gb = max(4, (connections * 10) / 1024)
        return {"cpu_cores": cpu_cores, "memory_gb": memory_gb}
