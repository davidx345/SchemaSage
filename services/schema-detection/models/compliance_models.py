"""
Compliance models for Phase 2.1 features.
Includes models for encryption detection, access control auditing, and compliance reporting.
"""
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

# --- Enums ---

class ComplianceFramework(str, Enum):
    GDPR = "GDPR"
    CCPA = "CCPA"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS"
    SOC2 = "SOC2"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"

# --- Shared Models ---

class TableSchema(BaseModel):
    name: str
    columns: List[Dict[str, Any]]
    # Add other fields as necessary from the schema object

class DatabaseSchema(BaseModel):
    database_type: DatabaseType
    tables: List[TableSchema]

# --- Encryption Detection Models ---

class EncryptionDetectionRequest(BaseModel):
    schema_data: DatabaseSchema = Field(..., alias="schema")
    connection_string: str

class EncryptionIssue(BaseModel):
    table: str
    column: str
    data_type: str
    detected_pii_type: str
    sample_data: Optional[str] = None
    risk_level: Severity
    compliance_impact: List[ComplianceFramework]
    recommendation: str

class CostEstimate(BaseModel):
    min: float
    max: float
    recommended: float

class EncryptionSummary(BaseModel):
    total_issues: int
    critical_issues: int
    high_issues: int
    total_affected_records: int
    compliance_frameworks_at_risk: List[ComplianceFramework]
    estimated_fix_time_hours: float
    estimated_monthly_cost_increase: CostEstimate

class EncryptionDetectionData(BaseModel):
    issues: List[EncryptionIssue]
    summary: EncryptionSummary
    auto_fix_available: bool
    auto_fix_sql: List[str]

class EncryptionDetectionResponse(BaseModel):
    success: bool
    data: EncryptionDetectionData

# --- Access Control Auditor Models ---

class AccessControlRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    compliance_framework: ComplianceFramework

class UserAudit(BaseModel):
    username: str
    roles: List[str]
    last_login: Optional[datetime]
    password_last_changed: Optional[datetime]
    is_superuser: bool
    failed_login_attempts: int

class RoleAudit(BaseModel):
    role: str
    permissions: List[str]
    assigned_users: int
    risk_level: Severity
    recommendation: str

class AccessRecommendation(BaseModel):
    priority: Severity
    issue: str
    remediation: str
    compliance_impact: str

class AccessSummary(BaseModel):
    total_users: int
    critical_risk_users: int
    high_risk_users: int
    medium_risk_users: int
    low_risk_users: int
    total_issues: int
    compliance_score: int
    auto_fix_available: bool

class AccessControlData(BaseModel):
    users: List[UserAudit]
    role_matrix: List[RoleAudit]
    recommendations: List[AccessRecommendation]
    summary: AccessSummary
    auto_fix_sql: List[str]

class AccessControlResponse(BaseModel):
    success: bool
    data: AccessControlData

# --- Compliance Report Models ---

class ComplianceReportRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    frameworks: List[ComplianceFramework]
    report_type: str = "executive_summary"
    include_recommendations: bool = True

class ExecutiveSummary(BaseModel):
    status: str
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    compliant_controls: int
    total_controls_assessed: int
    estimated_remediation_time_hours: float
    estimated_cost: float

class FrameworkScore(BaseModel):
    score: int
    compliant_controls: int
    total_controls: int
    critical_gaps: int

class Finding(BaseModel):
    severity: Severity
    description: str
    affected_assets: List[str]
    remediation: str

class ComplianceControl(BaseModel):
    control_id: str
    status: str
    description: str
    remediation: str

class RemediationPhase(BaseModel):
    duration_days: int
    tasks: List[str]
    estimated_cost: float

class RemediationRoadmap(BaseModel):
    phase_1_critical: RemediationPhase
    phase_2_high: RemediationPhase

class ComplianceReportData(BaseModel):
    report_id: str
    generated_at: datetime
    database_name: str
    frameworks_assessed: List[ComplianceFramework]
    overall_compliance_score: int
    executive_summary: ExecutiveSummary
    framework_scores: Dict[str, FrameworkScore]
    findings_by_severity: List[Dict[str, Any]] # Simplified for flexibility
    compliance_controls: List[ComplianceControl]
    remediation_roadmap: RemediationRoadmap
    auto_fix_sql: List[str]
    report_download_url: str
    report_expires_at: datetime

class ComplianceReportResponse(BaseModel):
    success: bool
    data: ComplianceReportData
