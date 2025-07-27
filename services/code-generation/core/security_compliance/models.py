"""
Security and compliance data models
Defines data structures for security policies, classifications, and audit events
"""

from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid


class SecurityLevel(Enum):
    """Security levels for data classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    SOC2 = "soc2"
    CCPA = "ccpa"
    FERPA = "ferpa"
    FISMA = "fisma"
    NIST = "nist"


class EncryptionType(Enum):
    """Encryption algorithms and types"""
    NONE = "none"
    AES_128 = "aes_128"
    AES_256 = "aes_256"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    FERNET = "fernet"
    FIELD_LEVEL = "field_level"


class AccessControlType(Enum):
    """Access control mechanisms"""
    RBAC = "rbac"  # Role-Based Access Control
    ABAC = "abac"  # Attribute-Based Access Control
    MAC = "mac"    # Mandatory Access Control
    DAC = "dac"    # Discretionary Access Control


class AuditEventType(Enum):
    """Types of security audit events"""
    DATA_ACCESS = "data_access"
    SCHEMA_MODIFICATION = "schema_modification"
    PERMISSION_CHANGE = "permission_change"
    ENCRYPTION_CHANGE = "encryption_change"
    COMPLIANCE_VIOLATION = "compliance_violation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGE = "configuration_change"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityPolicy:
    """Security policy definition"""
    policy_id: str
    name: str
    description: str
    security_level: SecurityLevel
    encryption_required: bool
    access_controls: List[AccessControlType]
    compliance_frameworks: List[ComplianceFramework]
    data_retention_days: Optional[int] = None
    access_logging_required: bool = True
    anonymization_required: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'description': self.description,
            'security_level': self.security_level.value,
            'encryption_required': self.encryption_required,
            'access_controls': [ac.value for ac in self.access_controls],
            'compliance_frameworks': [cf.value for cf in self.compliance_frameworks],
            'data_retention_days': self.data_retention_days,
            'access_logging_required': self.access_logging_required,
            'anonymization_required': self.anonymization_required,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class DataClassification:
    """Data classification result"""
    classification_id: str
    target_type: str  # 'schema', 'table', 'column', 'relationship'
    target_name: str
    security_level: SecurityLevel
    compliance_requirements: List[ComplianceFramework]
    sensitive_data_types: List[str]
    encryption_recommendation: EncryptionType
    access_restrictions: List[str]
    data_lineage_tracking: bool
    retention_policy: Optional[Dict[str, Any]] = None
    anonymization_rules: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'classification_id': self.classification_id,
            'target_type': self.target_type,
            'target_name': self.target_name,
            'security_level': self.security_level.value,
            'compliance_requirements': [cr.value for cr in self.compliance_requirements],
            'sensitive_data_types': self.sensitive_data_types,
            'encryption_recommendation': self.encryption_recommendation.value,
            'access_restrictions': self.access_restrictions,
            'data_lineage_tracking': self.data_lineage_tracking,
            'retention_policy': self.retention_policy,
            'anonymization_rules': self.anonymization_rules,
            'risk_score': self.risk_score,
            'confidence_score': self.confidence_score,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class SecurityAuditEvent:
    """Security audit event"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: str
    session_id: str
    source_ip: str
    target_resource: str
    action_performed: str
    result: str  # 'success', 'failure', 'blocked'
    risk_level: RiskLevel
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_related: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'source_ip': self.source_ip,
            'target_resource': self.target_resource,
            'action_performed': self.action_performed,
            'result': self.result,
            'risk_level': self.risk_level.value,
            'details': self.details,
            'compliance_related': self.compliance_related
        }


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    violation_id: str
    framework: ComplianceFramework
    rule_id: str
    rule_description: str
    violation_type: str
    severity: RiskLevel
    affected_resources: List[str]
    description: str
    remediation_steps: List[str]
    discovered_at: datetime
    status: str = "open"  # open, investigating, resolved, false_positive
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'violation_id': self.violation_id,
            'framework': self.framework.value,
            'rule_id': self.rule_id,
            'rule_description': self.rule_description,
            'violation_type': self.violation_type,
            'severity': self.severity.value,
            'affected_resources': self.affected_resources,
            'description': self.description,
            'remediation_steps': self.remediation_steps,
            'discovered_at': self.discovered_at.isoformat(),
            'status': self.status,
            'assigned_to': self.assigned_to,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'metadata': self.metadata
        }


@dataclass
class ComplianceReport:
    """Compliance assessment report"""
    report_id: str
    schema_name: str
    framework: ComplianceFramework
    assessment_date: datetime
    overall_score: float
    compliance_status: str  # 'compliant', 'non_compliant', 'partial'
    violations: List[ComplianceViolation]
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    next_assessment_date: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'report_id': self.report_id,
            'schema_name': self.schema_name,
            'framework': self.framework.value,
            'assessment_date': self.assessment_date.isoformat(),
            'overall_score': self.overall_score,
            'compliance_status': self.compliance_status,
            'violations': [v.to_dict() for v in self.violations],
            'recommendations': self.recommendations,
            'risk_assessment': self.risk_assessment,
            'next_assessment_date': self.next_assessment_date.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class EncryptionConfiguration:
    """Encryption configuration for data elements"""
    config_id: str
    target_type: str  # 'table', 'column', 'field'
    target_name: str
    encryption_type: EncryptionType
    key_management: str  # 'internal', 'external', 'hsm'
    rotation_policy: Dict[str, Any]
    performance_impact: str  # 'low', 'medium', 'high'
    compliance_requirements: List[ComplianceFramework]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'config_id': self.config_id,
            'target_type': self.target_type,
            'target_name': self.target_name,
            'encryption_type': self.encryption_type.value,
            'key_management': self.key_management,
            'rotation_policy': self.rotation_policy,
            'performance_impact': self.performance_impact,
            'compliance_requirements': [cr.value for cr in self.compliance_requirements],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class AccessControlRule:
    """Access control rule definition"""
    rule_id: str
    name: str
    description: str
    target_type: str  # 'schema', 'table', 'column'
    target_pattern: str  # Pattern to match targets
    control_type: AccessControlType
    permissions: List[str]  # 'read', 'write', 'delete', 'admin'
    conditions: Dict[str, Any]  # Additional conditions
    priority: int = 100
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'target_type': self.target_type,
            'target_pattern': self.target_pattern,
            'control_type': self.control_type.value,
            'permissions': self.permissions,
            'conditions': self.conditions,
            'priority': self.priority,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class SecurityMetrics:
    """Security metrics and KPIs"""
    metric_id: str
    metric_name: str
    metric_value: float
    metric_unit: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    current_status: str = "normal"  # normal, warning, critical
    trend: str = "stable"  # improving, stable, degrading
    measurement_period: str = "daily"
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metric_id': self.metric_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'threshold_warning': self.threshold_warning,
            'threshold_critical': self.threshold_critical,
            'current_status': self.current_status,
            'trend': self.trend,
            'measurement_period': self.measurement_period,
            'last_updated': self.last_updated.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    threat_id: str
    threat_type: str
    severity: RiskLevel
    description: str
    indicators: List[str]
    affected_systems: List[str]
    mitigation_steps: List[str]
    source: str
    confidence_level: float
    first_seen: datetime
    last_seen: datetime
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'threat_id': self.threat_id,
            'threat_type': self.threat_type,
            'severity': self.severity.value,
            'description': self.description,
            'indicators': self.indicators,
            'affected_systems': self.affected_systems,
            'mitigation_steps': self.mitigation_steps,
            'source': self.source,
            'confidence_level': self.confidence_level,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'is_active': self.is_active,
            'metadata': self.metadata
        }


@dataclass
class SecurityIncident:
    """Security incident record"""
    incident_id: str
    title: str
    description: str
    severity: RiskLevel
    status: str  # open, investigating, contained, resolved, closed
    incident_type: str
    affected_assets: List[str]
    detected_at: datetime
    reported_by: str
    assigned_to: Optional[str] = None
    resolution_steps: List[str] = field(default_factory=list)
    lessons_learned: str = ""
    closed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'incident_id': self.incident_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'status': self.status,
            'incident_type': self.incident_type,
            'affected_assets': self.affected_assets,
            'detected_at': self.detected_at.isoformat(),
            'reported_by': self.reported_by,
            'assigned_to': self.assigned_to,
            'resolution_steps': self.resolution_steps,
            'lessons_learned': self.lessons_learned,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'metadata': self.metadata
        }
