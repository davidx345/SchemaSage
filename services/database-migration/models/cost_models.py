"""
Cost Analysis Models - Week 1 Priority 1
Pydantic models for cost comparison endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class PerformanceRequirements(BaseModel):
    """Performance requirements for database instance"""
    qps: int = Field(..., description="Queries per second", gt=0)
    connections: int = Field(..., description="Max concurrent connections", gt=0)
    iops: int = Field(..., description="I/O operations per second", gt=0)

    @validator('qps', 'connections', 'iops')
    def validate_positive(cls, v):
        """Ensure all performance metrics are positive"""
        if v <= 0:
            raise ValueError("Performance metrics must be positive integers")
        return v


class CostComparisonRequest(BaseModel):
    """Request for cost comparison across cloud providers"""
    database_type: DatabaseType = Field(..., description="Type of database")
    storage_gb: int = Field(..., description="Storage size in GB", gt=0, le=100000)
    region: str = Field(..., description="Cloud region (e.g., us-east-1)")
    performance_requirements: PerformanceRequirements

    @validator('storage_gb')
    def validate_storage(cls, v):
        """Validate storage is reasonable"""
        if v <= 0:
            raise ValueError("Storage must be positive")
        if v > 100000:
            raise ValueError("Storage exceeds maximum limit of 100TB")
        return v


class CostBreakdown(BaseModel):
    """Cost breakdown by category"""
    instance: float = Field(..., description="Instance/compute cost")
    storage: float = Field(..., description="Storage cost")
    backup: float = Field(..., description="Backup cost")
    network: float = Field(..., description="Network transfer cost")
    iops: float = Field(..., description="IOPS cost")


class InstanceSpecs(BaseModel):
    """Cloud instance specifications"""
    cpu_cores: int = Field(..., description="Number of CPU cores")
    memory_gb: float = Field(..., description="Memory in GB")
    storage_type: str = Field(..., description="Storage type (e.g., gp3, pd-ssd)")
    iops: int = Field(..., description="Provisioned IOPS")


class ProviderCostEstimate(BaseModel):
    """Cost estimate for a single cloud provider"""
    provider: CloudProvider
    instance_type: str = Field(..., description="Instance type name")
    monthly_cost: float = Field(..., description="Total monthly cost in USD")
    breakdown: CostBreakdown
    specs: InstanceSpecs


class CostComparisonResponse(BaseModel):
    """Response with cost comparison across providers"""
    success: bool = True
    data: Dict = Field(..., description="Cost comparison data")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "providers": [
                        {
                            "provider": "aws",
                            "instance_type": "db.t3.large",
                            "monthly_cost": 127.44,
                            "breakdown": {
                                "instance": 72.96,
                                "storage": 10.00,
                                "backup": 15.00,
                                "network": 5.00,
                                "iops": 24.48
                            },
                            "specs": {
                                "cpu_cores": 2,
                                "memory_gb": 8,
                                "storage_type": "gp3",
                                "iops": 3000
                            }
                        }
                    ],
                    "recommendation": "aws",
                    "savings": {
                        "vs_gcp": 16.08,
                        "vs_azure": 29.45
                    }
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: Dict = Field(..., description="Error details")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "INVALID_REGION",
                    "message": "Invalid region specified",
                    "details": {
                        "field": "region",
                        "issue": "Region must be valid cloud provider region"
                    }
                }
            }
        }
