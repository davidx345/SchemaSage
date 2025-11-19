"""
GCP Pricing Data and Calculator
Hardcoded pricing data for MVP
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class GCPPricing:
    """GCP Cloud SQL pricing"""
    
    # Cloud SQL instance pricing per hour by region (PostgreSQL)
    INSTANCE_PRICING = {
        "us-east1": {
            "db-f1-micro": 0.0150,
            "db-g1-small": 0.0500,
            "db-n1-standard-1": 0.0950,
            "db-n1-standard-2": 0.1900,
            "db-n1-standard-4": 0.3800,
            "db-n1-standard-8": 0.7600,
            "db-n1-highmem-2": 0.2500,
            "db-n1-highmem-4": 0.5000,
            "db-n1-highmem-8": 1.0000,
        },
        "us-west2": {
            "db-f1-micro": 0.0150,
            "db-g1-small": 0.0500,
            "db-n1-standard-1": 0.0950,
            "db-n1-standard-2": 0.1900,
            "db-n1-standard-4": 0.3800,
            "db-n1-standard-8": 0.7600,
            "db-n1-highmem-2": 0.2500,
            "db-n1-highmem-4": 0.5000,
            "db-n1-highmem-8": 1.0000,
        },
        "europe-west1": {
            "db-f1-micro": 0.0165,
            "db-g1-small": 0.0550,
            "db-n1-standard-1": 0.1045,
            "db-n1-standard-2": 0.2090,
            "db-n1-standard-4": 0.4180,
            "db-n1-standard-8": 0.8360,
            "db-n1-highmem-2": 0.2750,
            "db-n1-highmem-4": 0.5500,
            "db-n1-highmem-8": 1.1000,
        },
        "asia-southeast1": {
            "db-f1-micro": 0.0180,
            "db-g1-small": 0.0600,
            "db-n1-standard-1": 0.1140,
            "db-n1-standard-2": 0.2280,
            "db-n1-standard-4": 0.4560,
            "db-n1-standard-8": 0.9120,
            "db-n1-highmem-2": 0.3000,
            "db-n1-highmem-4": 0.6000,
            "db-n1-highmem-8": 1.2000,
        }
    }
    
    # Instance specifications
    INSTANCE_SPECS = {
        "db-f1-micro": {"cpu_cores": 1, "memory_gb": 0.6, "max_iops": 2000},
        "db-g1-small": {"cpu_cores": 1, "memory_gb": 1.7, "max_iops": 2000},
        "db-n1-standard-1": {"cpu_cores": 1, "memory_gb": 3.75, "max_iops": 2500},
        "db-n1-standard-2": {"cpu_cores": 2, "memory_gb": 7.5, "max_iops": 3000},
        "db-n1-standard-4": {"cpu_cores": 4, "memory_gb": 15, "max_iops": 3000},
        "db-n1-standard-8": {"cpu_cores": 8, "memory_gb": 30, "max_iops": 3000},
        "db-n1-highmem-2": {"cpu_cores": 2, "memory_gb": 13, "max_iops": 3000},
        "db-n1-highmem-4": {"cpu_cores": 4, "memory_gb": 26, "max_iops": 3000},
        "db-n1-highmem-8": {"cpu_cores": 8, "memory_gb": 52, "max_iops": 3000},
    }
    
    # Storage pricing per GB-month (SSD)
    STORAGE_PRICING = {
        "pd-ssd": 0.170,  # SSD persistent disk
        "pd-standard": 0.040,  # Standard persistent disk
    }
    
    # Backup storage pricing per GB-month
    BACKUP_PRICING = 0.080
    
    # Network egress pricing per GB
    NETWORK_EGRESS = {
        "first_1tb": 0.12,
        "next_9tb": 0.11,
        "over_10tb": 0.08
    }
    
    @classmethod
    def get_instance_cost(cls, instance_type: str, region: str = "us-east1") -> float:
        """Get monthly instance cost"""
        hourly_rate = cls.INSTANCE_PRICING.get(region, cls.INSTANCE_PRICING["us-east1"]).get(instance_type, 0)
        return hourly_rate * 730
    
    @classmethod
    def get_storage_cost(cls, storage_gb: int, storage_type: str = "pd-ssd") -> float:
        """Calculate monthly storage cost"""
        rate = cls.STORAGE_PRICING.get(storage_type, cls.STORAGE_PRICING["pd-ssd"])
        return storage_gb * rate
    
    @classmethod
    def get_backup_cost(cls, storage_gb: int) -> float:
        """Calculate monthly backup cost"""
        return storage_gb * cls.BACKUP_PRICING * 2  # GCP charges for automated + manual
    
    @classmethod
    def get_iops_cost(cls, iops: int, storage_type: str = "pd-ssd") -> float:
        """GCP includes IOPS in storage cost, but charge extra for high IOPS"""
        if iops > 3000 and storage_type == "pd-ssd":
            extra_iops = iops - 3000
            return extra_iops * 0.065  # Per IOPS-month
        return 0.0
    
    @classmethod
    def get_network_cost(cls, data_transfer_gb: float = 0) -> float:
        """Calculate monthly network egress cost"""
        if data_transfer_gb <= 0:
            return 8.0  # Base estimate
        
        cost = 0.0
        remaining = data_transfer_gb
        
        # First 1 TB free, then first 1 TB billed
        if remaining > 1024:
            remaining -= 1024
            billable = min(remaining, 1024)
            cost += billable * cls.NETWORK_EGRESS["first_1tb"]
            remaining -= billable
        
        # Next 9 TB
        if remaining > 0:
            billable = min(remaining, 9216)
            cost += billable * cls.NETWORK_EGRESS["next_9tb"]
            remaining -= billable
        
        # Over 10 TB
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
            logger.warning(f"No GCP instance matches requirements")
            return "db-n1-highmem-8"
        
        return best_match
    
    @classmethod
    def estimate_required_resources(cls, qps: int, connections: int) -> Dict:
        """Estimate required resources"""
        cpu_cores = max(2, int(qps / 1000) + 1)
        memory_gb = max(4, (connections * 10) / 1024)
        return {"cpu_cores": cpu_cores, "memory_gb": memory_gb}
