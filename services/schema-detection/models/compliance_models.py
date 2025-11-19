"""
Compliance Models - Week 1 Priority 1
Pydantic models for PII detection and compliance endpoints
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


class PIIType(str, Enum):
    """Types of PII data"""
    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number"
    SOCIAL_SECURITY_NUMBER = "social_security_number"
    CREDIT_CARD = "credit_card_number"
    IP_ADDRESS = "ip_address"
    PHYSICAL_ADDRESS = "physical_address"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FULL_NAME = "full_name"
    DATE_OF_BIRTH = "date_of_birth"
    DRIVERS_LICENSE = "drivers_license"


class ComplianceFramework(str, Enum):
    """Compliance frameworks"""
    GDPR = "GDPR"
    CCPA = "CCPA"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS"
    SOC2 = "SOC2"


class Severity(str, Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ColumnInfo(BaseModel):
    """Column information for PII detection"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")


class TableInfo(BaseModel):
    """Table information for PII detection"""
    name: str = Field(..., description="Table name")
    columns: List[ColumnInfo] = Field(..., description="List of columns")


class SchemaInfo(BaseModel):
    """Schema information for PII detection"""
    database_type: DatabaseType
    tables: List[TableInfo] = Field(..., description="List of tables to scan")
    
    @validator('tables')
    def validate_tables(cls, v):
        """Ensure at least one table provided"""
        if not v:
            raise ValueError("At least one table must be provided")
        return v


class PIIDetectionRequest(BaseModel):
    """Request for PII detection"""
    schema: SchemaInfo = Field(..., description="Database schema to scan")
    
    class Config:
        schema_extra = {
            "example": {
                "schema": {
                    "database_type": "postgresql",
                    "tables": [
                        {
                            "name": "users",
                            "columns": [
                                {"name": "id", "type": "integer"},
                                {"name": "email", "type": "varchar"},
                                {"name": "phone", "type": "varchar"},
                                {"name": "ssn", "type": "varchar"}
                            ]
                        }
                    ]
                }
            }
        }


class PIIField(BaseModel):
    """Detected PII field"""
    table: str = Field(..., description="Table name")
    column: str = Field(..., description="Column name")
    pii_type: PIIType = Field(..., description="Type of PII detected")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    severity: Severity = Field(..., description="Severity level")
    affected_records: int = Field(default=0, description="Estimated affected records")
    compliance_frameworks: List[ComplianceFramework] = Field(
        ..., description="Relevant compliance frameworks"
    )
    recommendations: List[str] = Field(..., description="Compliance recommendations")


class PIISummary(BaseModel):
    """Summary of PII detection results"""
    total_pii_fields: int = Field(..., description="Total PII fields found")
    total_affected_records: int = Field(..., description="Total records with PII")
    compliance_risk: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Overall compliance risk level"
    )
    frameworks_affected: List[ComplianceFramework] = Field(
        ..., description="Compliance frameworks that apply"
    )


class PIIDetectionResponse(BaseModel):
    """Response with PII detection results"""
    success: bool = True
    data: Dict = Field(..., description="PII detection data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "pii_fields": [
                        {
                            "table": "users",
                            "column": "email",
                            "pii_type": "email_address",
                            "confidence": 0.99,
                            "severity": "high",
                            "affected_records": 125847,
                            "compliance_frameworks": ["GDPR", "CCPA"],
                            "recommendations": [
                                "Enable encryption at rest",
                                "Add data retention policy"
                            ]
                        }
                    ],
                    "summary": {
                        "total_pii_fields": 3,
                        "total_affected_records": 125847,
                        "compliance_risk": "high",
                        "frameworks_affected": ["GDPR", "CCPA", "HIPAA"]
                    }
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: Dict = Field(..., description="Error details")
