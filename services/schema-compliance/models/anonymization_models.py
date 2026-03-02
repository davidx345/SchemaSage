"""
Pydantic Models for Phase 3.3 - Production Data Anonymizer
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class PIIType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    DOB = "dob"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnonymizationStrategy(str, Enum):
    FAKE_DATA = "fake_data"
    MASKING = "masking"
    TOKENIZATION = "tokenization"
    HASHING = "hashing"
    REDACTION = "redaction"
    GENERALIZATION = "generalization"


class SubsettingStrategy(str, Enum):
    RANDOM_SAMPLING = "random_sampling"
    STRATIFIED_SAMPLING = "stratified_sampling"
    TIME_BASED = "time_based"
    CUSTOM_QUERY = "custom_query"


class ComplianceFramework(str, Enum):
    GDPR = "GDPR"
    CCPA = "CCPA"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS"
    SOX = "SOX"
    COPPA = "COPPA"


# ============================================================================
# PII DETECTION SCAN (3.3.1)
# ============================================================================

class ScanOptions(BaseModel):
    tables: Optional[List[str]] = Field(default=None, description="Specific tables to scan")
    confidence_threshold: int = Field(default=75, ge=0, le=100, description="Minimum confidence for PII detection")
    include_samples: bool = Field(default=True, description="Include sample values in results")
    max_sample_size: int = Field(default=3, ge=1, le=10, description="Number of sample values per field")


class PIIScanRequest(BaseModel):
    connection_string: str = Field(..., description="Database connection string")
    scan_options: ScanOptions = Field(default_factory=ScanOptions)


class PIIField(BaseModel):
    table: str
    column: str
    pii_type: PIIType
    confidence: int = Field(..., ge=0, le=100)
    sample_values: List[str]
    records_affected: int
    severity: Severity
    compliance_impact: List[str]


class PIIScanData(BaseModel):
    scan_id: str
    total_tables_scanned: int
    total_columns_scanned: int
    pii_fields_detected: int
    total_records_affected: int
    compliance_violations: List[str]
    scan_duration_seconds: int
    fields: List[PIIField]
    recommendations: List[str]


class PIIScanResponse(BaseModel):
    success: bool
    data: PIIScanData


# ============================================================================
# ANONYMIZATION RULES (3.3.2)
# ============================================================================

class AnonymizationOptions(BaseModel):
    maintain_domain: Optional[bool] = None
    preserve_uniqueness: Optional[bool] = None
    mask_pattern: Optional[str] = None
    preserve_last_n: Optional[int] = None
    token_format: Optional[str] = None
    reversible: Optional[bool] = None
    algorithm: Optional[str] = None
    salt: Optional[str] = None


class AnonymizationRule(BaseModel):
    table: str
    column: str
    strategy: AnonymizationStrategy
    options: Optional[AnonymizationOptions] = Field(default_factory=AnonymizationOptions)


class RuleCreateRequest(BaseModel):
    scan_id: str
    rules: List[AnonymizationRule]


class ExampleTransformation(BaseModel):
    before: str
    after: str


class RuleDetails(BaseModel):
    rule_id: str
    table: str
    column: str
    strategy: AnonymizationStrategy
    estimated_records: int
    reversible: bool
    maintains_format: bool
    performance_impact: str
    example_transformation: ExampleTransformation


class RuleSetData(BaseModel):
    rule_set_id: str
    total_rules: int
    estimated_processing_time: str
    rules: List[RuleDetails]
    validation_warnings: List[str]


class RuleCreateResponse(BaseModel):
    success: bool
    data: RuleSetData


# ============================================================================
# ANONYMIZATION EXECUTION (3.3.3)
# ============================================================================

class ExecutionOptions(BaseModel):
    dry_run: bool = Field(default=False)
    batch_size: int = Field(default=1000, ge=100, le=10000)
    verify_referential_integrity: bool = Field(default=True)
    create_backup: bool = Field(default=True)


class ApplyMaskingRequest(BaseModel):
    rule_set_id: str
    target_connection: str
    execution_options: ExecutionOptions = Field(default_factory=ExecutionOptions)


class ProgressInfo(BaseModel):
    percentage: float = Field(..., ge=0, le=100)
    current_rule: str
    records_processed: int
    total_records: int
    estimated_remaining: str


class PerformanceMetrics(BaseModel):
    records_per_second: int
    error_count: int
    warning_count: int


class ApplyMaskingData(BaseModel):
    execution_id: str
    status: str
    progress: ProgressInfo
    performance_metrics: PerformanceMetrics
    logs: List[str]


class ApplyMaskingResponse(BaseModel):
    success: bool
    data: ApplyMaskingData


class CompletedRule(BaseModel):
    rule_id: str
    table: str
    column: str
    records_anonymized: int
    duration_seconds: int
    status: str


# ============================================================================
# DATA SUBSETTING (3.3.4)
# ============================================================================

class SubsettingOptions(BaseModel):
    sample_percentage: int = Field(..., ge=1, le=100)
    preserve_referential_integrity: bool = Field(default=True)
    include_reference_tables: str = Field(default="full", description="full, partial, or none")
    anonymize_after_subset: bool = Field(default=True)


class SubsetCreateRequest(BaseModel):
    source_connection: str
    target_connection: str
    subsetting_strategy: SubsettingStrategy
    options: SubsettingOptions


class TableSubsetPlan(BaseModel):
    table: str
    original_records: int
    subset_records: int
    reduction_percentage: int
    subsetting_method: str
    foreign_key_dependencies: List[str]
    includes_full_graph: bool


class SubsettingPlan(BaseModel):
    estimated_duration: str
    source_size_gb: float
    target_size_gb: float
    reduction_percentage: int
    tables: List[TableSubsetPlan]
    total_records_to_copy: int
    estimated_copy_time: str
    estimated_anonymization_time: str


class SubsetData(BaseModel):
    subset_id: str
    subsetting_plan: SubsettingPlan


class SubsetCreateResponse(BaseModel):
    success: bool
    data: SubsetData


class SubsetProgress(BaseModel):
    percentage: float
    current_phase: str
    records_copied: int
    total_records: int
    estimated_remaining: str


class SubsetExecuteData(BaseModel):
    execution_id: str
    status: str
    progress: SubsetProgress


class SubsetExecuteResponse(BaseModel):
    success: bool
    data: SubsetExecuteData


# ============================================================================
# COMPLIANCE VALIDATION (3.3.5)
# ============================================================================

class ValidationOptions(BaseModel):
    run_pii_rescan: bool = Field(default=True)
    check_referential_integrity: bool = Field(default=True)
    verify_data_quality: bool = Field(default=True)


class ComplianceValidationRequest(BaseModel):
    execution_id: str
    compliance_frameworks: List[ComplianceFramework]
    validation_options: ValidationOptions = Field(default_factory=ValidationOptions)


class ComplianceCheck(BaseModel):
    requirement: str
    status: str
    evidence: str


class FrameworkValidation(BaseModel):
    framework: str
    status: str
    requirements_met: int
    requirements_total: int
    checks: List[ComplianceCheck]


class PIIRescanResults(BaseModel):
    pii_fields_detected: int
    confidence_level: float
    scan_coverage: str
    false_positive_rate: float


class ReferentialIntegrity(BaseModel):
    status: str
    foreign_key_violations: int
    orphaned_records: int
    checks_performed: int


class DataQuality(BaseModel):
    status: str
    null_percentage: float
    duplicate_records: int
    format_errors: int
    quality_score: float


class AuditLog(BaseModel):
    anonymization_timestamp: str
    anonymized_by: str
    rules_applied: int
    records_affected: int
    backup_snapshot_id: str


class ComplianceValidationData(BaseModel):
    validation_id: str
    overall_compliance_status: str
    frameworks: List[FrameworkValidation]
    pii_rescan_results: PIIRescanResults
    referential_integrity: ReferentialIntegrity
    data_quality: DataQuality
    audit_log: AuditLog


class ComplianceValidationResponse(BaseModel):
    success: bool
    data: ComplianceValidationData
