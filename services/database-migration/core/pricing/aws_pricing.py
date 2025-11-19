"""
AWS Pricing Data and Calculator
Hardcoded pricing data for MVP - can be replaced with AWS Price List API later
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AWSPricing:
    """AWS database instance and storage pricing"""
    
    # RDS Instance pricing per hour by region (PostgreSQL)
    INSTANCE_PRICING = {
        "us-east-1": {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.t3.medium": 0.068,
            "db.t3.large": 0.136,
            "db.t3.xlarge": 0.272,
            "db.t3.2xlarge": 0.544,
            "db.r5.large": 0.240,
            "db.r5.xlarge": 0.480,
            "db.r5.2xlarge": 0.960,
            "db.r5.4xlarge": 1.920,
        },
        "us-west-2": {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.t3.medium": 0.068,
            "db.t3.large": 0.136,
            "db.t3.xlarge": 0.272,
            "db.t3.2xlarge": 0.544,
            "db.r5.large": 0.240,
            "db.r5.xlarge": 0.480,
            "db.r5.2xlarge": 0.960,
            "db.r5.4xlarge": 1.920,
        },
        "eu-west-1": {
            "db.t3.micro": 0.019,
            "db.t3.small": 0.038,
            "db.t3.medium": 0.075,
            "db.t3.large": 0.150,
            "db.t3.xlarge": 0.300,
            "db.t3.2xlarge": 0.600,
            "db.r5.large": 0.264,
            "db.r5.xlarge": 0.528,
            "db.r5.2xlarge": 1.056,
            "db.r5.4xlarge": 2.112,
        },
        "ap-southeast-1": {
            "db.t3.micro": 0.020,
            "db.t3.small": 0.040,
            "db.t3.medium": 0.080,
            "db.t3.large": 0.162,
            "db.t3.xlarge": 0.324,
            "db.t3.2xlarge": 0.648,
            "db.r5.large": 0.288,
            "db.r5.xlarge": 0.576,
            "db.r5.2xlarge": 1.152,
            "db.r5.4xlarge": 2.304,
        }
    }
    
    # Instance specifications
    INSTANCE_SPECS = {
        "db.t3.micro": {"cpu_cores": 2, "memory_gb": 1, "network_gbps": 5, "max_iops": 2085},
        "db.t3.small": {"cpu_cores": 2, "memory_gb": 2, "network_gbps": 5, "max_iops": 2085},
        "db.t3.medium": {"cpu_cores": 2, "memory_gb": 4, "network_gbps": 5, "max_iops": 2085},
        "db.t3.large": {"cpu_cores": 2, "memory_gb": 8, "network_gbps": 5, "max_iops": 2780},
        "db.t3.xlarge": {"cpu_cores": 4, "memory_gb": 16, "network_gbps": 5, "max_iops": 2780},
        "db.t3.2xlarge": {"cpu_cores": 8, "memory_gb": 32, "network_gbps": 5, "max_iops": 2780},
        "db.r5.large": {"cpu_cores": 2, "memory_gb": 16, "network_gbps": 10, "max_iops": 3000},
        "db.r5.xlarge": {"cpu_cores": 4, "memory_gb": 32, "network_gbps": 10, "max_iops": 3000},
        "db.r5.2xlarge": {"cpu_cores": 8, "memory_gb": 64, "network_gbps": 10, "max_iops": 3000},
        "db.r5.4xlarge": {"cpu_cores": 16, "memory_gb": 128, "network_gbps": 10, "max_iops": 3000},
    }
    
    # Storage pricing per GB-month
    STORAGE_PRICING = {
        "gp3": 0.115,  # General Purpose SSD
        "gp2": 0.115,  # General Purpose SSD (legacy)
        "io1": 0.125,  # Provisioned IOPS SSD
        "io2": 0.125,  # Provisioned IOPS SSD
    }
    
    # Backup storage pricing per GB-month (same as storage for first backup)
    BACKUP_PRICING = 0.095
    
    # IOPS pricing for gp3 (first 3000 IOPS free, then $0.20 per provisioned IOPS-month)
    IOPS_PRICING = {
        "gp3": {"free_iops": 3000, "per_iops": 0.20},
        "io1": {"free_iops": 0, "per_iops": 0.10},
        "io2": {"free_iops": 0, "per_iops": 0.10},
    }
    
    # Data transfer pricing per GB
    DATA_TRANSFER_OUT = {
        "first_10tb": 0.09,
        "next_40tb": 0.085,
        "next_100tb": 0.07,
        "over_150tb": 0.05
    }
    
    # Cross-AZ data transfer
    CROSS_AZ_TRANSFER = 0.01  # per GB
    
    @classmethod
    def get_instance_cost(cls, instance_type: str, region: str = "us-east-1") -> float:
        """Get hourly instance cost, return monthly cost"""
        hourly_rate = cls.INSTANCE_PRICING.get(region, cls.INSTANCE_PRICING["us-east-1"]).get(instance_type, 0)
        return hourly_rate * 730  # 730 hours per month average
    
    @classmethod
    def get_storage_cost(cls, storage_gb: int, storage_type: str = "gp3") -> float:
        """Calculate monthly storage cost"""
        rate = cls.STORAGE_PRICING.get(storage_type, cls.STORAGE_PRICING["gp3"])
        return storage_gb * rate
    
    @classmethod
    def get_backup_cost(cls, storage_gb: int) -> float:
        """Calculate monthly backup cost (automated backups = 100% of storage)"""
        return storage_gb * cls.BACKUP_PRICING
    
    @classmethod
    def get_iops_cost(cls, iops: int, storage_type: str = "gp3") -> float:
        """Calculate monthly IOPS cost"""
        pricing = cls.IOPS_PRICING.get(storage_type, cls.IOPS_PRICING["gp3"])
        if iops <= pricing["free_iops"]:
            return 0.0
        billable_iops = iops - pricing["free_iops"]
        return billable_iops * pricing["per_iops"]
    
    @classmethod
    def get_network_cost(cls, data_transfer_gb: float = 0) -> float:
        """Calculate monthly data transfer cost"""
        if data_transfer_gb <= 0:
            return 5.0  # Base network cost estimate
        
        cost = 0.0
        remaining = data_transfer_gb
        
        # First 10 TB
        if remaining > 0:
            billable = min(remaining, 10240)
            cost += billable * cls.DATA_TRANSFER_OUT["first_10tb"]
            remaining -= billable
        
        # Next 40 TB
        if remaining > 0:
            billable = min(remaining, 40960)
            cost += billable * cls.DATA_TRANSFER_OUT["next_40tb"]
            remaining -= billable
        
        # Next 100 TB
        if remaining > 0:
            billable = min(remaining, 102400)
            cost += billable * cls.DATA_TRANSFER_OUT["next_100tb"]
            remaining -= billable
        
        # Over 150 TB
        if remaining > 0:
            cost += remaining * cls.DATA_TRANSFER_OUT["over_150tb"]
        
        return cost
    
    @classmethod
    def get_instance_specs(cls, instance_type: str) -> Optional[Dict]:
        """Get instance specifications"""
        return cls.INSTANCE_SPECS.get(instance_type)
    
    @classmethod
    def match_instance_by_requirements(cls, cpu_cores: int, memory_gb: float, iops: int) -> str:
        """Find the best matching instance type based on requirements"""
        best_match = None
        best_score = float('inf')
        
        for instance_type, specs in cls.INSTANCE_SPECS.items():
            # Instance must meet minimum requirements
            if specs["cpu_cores"] < cpu_cores:
                continue
            if specs["memory_gb"] < memory_gb:
                continue
            if specs["max_iops"] < iops:
                continue
            
            # Calculate "waste" score (lower is better)
            cpu_waste = specs["cpu_cores"] - cpu_cores
            memory_waste = specs["memory_gb"] - memory_gb
            iops_waste = specs["max_iops"] - iops
            
            # Weighted score (prioritize not over-provisioning)
            score = (cpu_waste * 2) + (memory_waste * 0.5) + (iops_waste * 0.001)
            
            if score < best_score:
                best_score = score
                best_match = instance_type
        
        # If no match found, return largest instance
        if best_match is None:
            logger.warning(f"No instance matches requirements: {cpu_cores} cores, {memory_gb} GB RAM, {iops} IOPS")
            return "db.r5.4xlarge"
        
        return best_match
    
    @classmethod
    def estimate_required_resources(cls, qps: int, connections: int) -> Dict:
        """Estimate CPU and memory requirements based on workload"""
        # Rule of thumb: 1 vCPU can handle ~1000 QPS for simple queries
        # Rule of thumb: Each connection needs ~10 MB RAM
        
        cpu_cores = max(2, int(qps / 1000) + 1)
        memory_gb = max(4, (connections * 10) / 1024)  # Convert MB to GB
        
        return {
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb
        }
