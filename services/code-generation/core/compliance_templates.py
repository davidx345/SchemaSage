"""
Universal Compliance Templates for Code Generation
Industry-specific templates for healthcare, education, financial, and government sectors
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class IndustryTemplate(Enum):
    """Industry-specific template types"""
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCIAL = "financial"
    GOVERNMENT = "government"
    SAAS = "saas"
    MANUFACTURING = "manufacturing"
    NONPROFIT = "nonprofit"


class DataRecordType(Enum):
    """Universal data record types"""
    PATIENT_RECORDS = "patient_records"
    STUDENT_RECORDS = "student_records"
    CUSTOMER_DATA = "customer_data"
    FINANCIAL_DATA = "financial_data"
    EMPLOYEE_DATA = "employee_data"
    TRANSACTION_DATA = "transaction_data"
    AUDIT_DATA = "audit_data"
    COMPLIANCE_DATA = "compliance_data"


@dataclass
class ComplianceTemplate:
    """Universal compliance template"""
    template_id: str
    name: str
    industry: IndustryTemplate
    record_type: DataRecordType
    applicable_frameworks: List[str]
    schema_template: Dict[str, Any]
    security_controls: List[str]
    audit_requirements: List[str]
    access_controls: List[str]
    encryption_requirements: List[str]
    retention_policies: Dict[str, Any]


class UniversalComplianceTemplates:
    """Universal compliance template generator for all industries"""
    
    def __init__(self):
        self.templates = self._load_universal_templates()
        
    def _load_universal_templates(self) -> Dict[str, ComplianceTemplate]:
        """Load all universal compliance templates"""
        templates = {}
        
        # Healthcare Templates (HIPAA Compliant)
        templates["healthcare_patient_records"] = ComplianceTemplate(
            template_id="healthcare_patient_records",
            name="HIPAA-Compliant Patient Records",
            industry=IndustryTemplate.HEALTHCARE,
            record_type=DataRecordType.PATIENT_RECORDS,
            applicable_frameworks=["hipaa", "gdpr", "soc2"],
            schema_template={
                "patients": {
                    "patient_id": {"type": "varchar(50)", "primary_key": True, "encrypted": True},
                    "medical_record_number": {"type": "varchar(20)", "unique": True, "encrypted": True},
                    "first_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "last_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "date_of_birth": {"type": "date", "encrypted": True, "pii": True},
                    "ssn": {"type": "varchar(11)", "encrypted": True, "sensitive": True},
                    "phone_number": {"type": "varchar(15)", "encrypted": True, "pii": True},
                    "email": {"type": "varchar(255)", "encrypted": True, "pii": True},
                    "emergency_contact": {"type": "varchar(255)", "encrypted": True},
                    "insurance_number": {"type": "varchar(50)", "encrypted": True, "sensitive": True},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "updated_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"},
                    "consent_date": {"type": "timestamp", "required": True},
                    "consent_type": {"type": "enum('treatment','disclosure','research')", "required": True},
                    "last_accessed": {"type": "timestamp"},
                    "access_count": {"type": "integer", "default": 0}
                },
                "medical_records": {
                    "record_id": {"type": "varchar(50)", "primary_key": True},
                    "patient_id": {"type": "varchar(50)", "foreign_key": "patients.patient_id"},
                    "diagnosis_code": {"type": "varchar(20)", "encrypted": True},
                    "treatment_notes": {"type": "text", "encrypted": True, "sensitive": True},
                    "medication": {"type": "text", "encrypted": True},
                    "provider_id": {"type": "varchar(50)", "required": True},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "minimum_necessary_flag": {"type": "boolean", "default": False}
                },
                "audit_log": {
                    "log_id": {"type": "varchar(50)", "primary_key": True},
                    "patient_id": {"type": "varchar(50)", "foreign_key": "patients.patient_id"},
                    "user_id": {"type": "varchar(50)", "required": True},
                    "action": {"type": "enum('view','edit','create','delete')", "required": True},
                    "timestamp": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "ip_address": {"type": "varchar(45)", "required": True},
                    "session_id": {"type": "varchar(100)", "required": True},
                    "reason_for_access": {"type": "text", "required": True}
                }
            },
            security_controls=[
                "Field-level encryption for all PHI",
                "Role-based access control (RBAC)",
                "Comprehensive audit logging",
                "Session management",
                "Data backup encryption",
                "Breach detection monitoring"
            ],
            audit_requirements=[
                "Log all PHI access attempts",
                "Record minimum necessary justification",
                "Track consent management",
                "Monitor unusual access patterns",
                "Generate HIPAA compliance reports"
            ],
            access_controls=[
                "Healthcare provider role verification",
                "Patient consent verification",
                "Minimum necessary access principle",
                "Emergency access procedures",
                "Delegated access management"
            ],
            encryption_requirements=[
                "AES-256 encryption for PHI fields",
                "Encrypted database storage",
                "TLS 1.3 for data in transit",
                "Key rotation every 90 days",
                "HSM key management"
            ],
            retention_policies={
                "patient_records": "7 years after last treatment",
                "medical_records": "7 years after creation", 
                "audit_logs": "6 years minimum",
                "consent_records": "Indefinite or until withdrawal"
            }
        )
        
        # Education Templates (FERPA Compliant)
        templates["education_student_records"] = ComplianceTemplate(
            template_id="education_student_records",
            name="FERPA-Compliant Student Records",
            industry=IndustryTemplate.EDUCATION,
            record_type=DataRecordType.STUDENT_RECORDS,
            applicable_frameworks=["ferpa", "gdpr", "ccpa"],
            schema_template={
                "students": {
                    "student_id": {"type": "varchar(50)", "primary_key": True, "encrypted": True},
                    "student_number": {"type": "varchar(20)", "unique": True, "encrypted": True},
                    "first_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "last_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "date_of_birth": {"type": "date", "encrypted": True, "pii": True},
                    "ssn": {"type": "varchar(11)", "encrypted": True, "sensitive": True},
                    "parent_email": {"type": "varchar(255)", "encrypted": True, "pii": True},
                    "student_email": {"type": "varchar(255)", "encrypted": True, "pii": True},
                    "home_address": {"type": "text", "encrypted": True, "pii": True},
                    "phone_number": {"type": "varchar(15)", "encrypted": True, "pii": True},
                    "emergency_contact": {"type": "text", "encrypted": True},
                    "enrollment_date": {"type": "date", "required": True},
                    "graduation_date": {"type": "date"},
                    "directory_opt_out": {"type": "boolean", "default": False},
                    "ferpa_consent_date": {"type": "timestamp"},
                    "parental_consent": {"type": "boolean", "default": False},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "updated_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"}
                },
                "academic_records": {
                    "record_id": {"type": "varchar(50)", "primary_key": True},
                    "student_id": {"type": "varchar(50)", "foreign_key": "students.student_id"},
                    "course_id": {"type": "varchar(50)", "required": True},
                    "semester": {"type": "varchar(20)", "required": True},
                    "grade": {"type": "varchar(5)", "encrypted": True, "sensitive": True},
                    "gpa": {"type": "decimal(3,2)", "encrypted": True, "sensitive": True},
                    "credits": {"type": "integer", "required": True},
                    "instructor_id": {"type": "varchar(50)", "required": True},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "legitimate_interest_flag": {"type": "boolean", "default": False}
                },
                "directory_information": {
                    "directory_id": {"type": "varchar(50)", "primary_key": True},
                    "student_id": {"type": "varchar(50)", "foreign_key": "students.student_id"},
                    "name": {"type": "varchar(255)", "required": True},
                    "major": {"type": "varchar(100)"},
                    "year": {"type": "varchar(20)"},
                    "honors": {"type": "text"},
                    "public_visible": {"type": "boolean", "default": False},
                    "parent_visible": {"type": "boolean", "default": True}
                },
                "ferpa_audit_log": {
                    "log_id": {"type": "varchar(50)", "primary_key": True},
                    "student_id": {"type": "varchar(50)", "foreign_key": "students.student_id"},
                    "user_id": {"type": "varchar(50)", "required": True},
                    "action": {"type": "enum('view','edit','create','delete','disclose')", "required": True},
                    "record_type": {"type": "varchar(50)", "required": True},
                    "legitimate_interest": {"type": "text", "required": True},
                    "timestamp": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "ip_address": {"type": "varchar(45)"},
                    "disclosure_recipient": {"type": "varchar(255)"}
                }
            },
            security_controls=[
                "Student record encryption",
                "Parental access controls",
                "Directory information management",
                "Legitimate educational interest verification",
                "Consent tracking system"
            ],
            audit_requirements=[
                "Log all student record access",
                "Track directory information disclosures",
                "Record parental consent status",
                "Monitor legitimate interest usage",
                "Generate FERPA compliance reports"
            ],
            access_controls=[
                "Role-based access (teacher, admin, parent)",
                "Legitimate educational interest verification",
                "Parental access rights (under 18)",
                "Student consent (over 18)",
                "Directory opt-out enforcement"
            ],
            encryption_requirements=[
                "AES-256 for academic records",
                "Encrypted student identifiers",
                "TLS for data transmission",
                "Key management for multi-tenant access"
            ],
            retention_policies={
                "student_records": "5 years after graduation",
                "academic_records": "Permanent (transcript purposes)",
                "audit_logs": "3 years minimum",
                "consent_records": "Until student reaches 23 years old"
            }
        )
        
        # Financial Templates (SOX/PCI-DSS Compliant)
        templates["financial_customer_data"] = ComplianceTemplate(
            template_id="financial_customer_data",
            name="SOX/PCI-DSS Compliant Financial Data",
            industry=IndustryTemplate.FINANCIAL,
            record_type=DataRecordType.FINANCIAL_DATA,
            applicable_frameworks=["sox", "pci_dss", "gdpr", "soc2"],
            schema_template={
                "customers": {
                    "customer_id": {"type": "varchar(50)", "primary_key": True, "encrypted": True},
                    "account_number": {"type": "varchar(20)", "unique": True, "encrypted": True},
                    "first_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "last_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "ssn": {"type": "varchar(11)", "encrypted": True, "sensitive": True},
                    "date_of_birth": {"type": "date", "encrypted": True, "pii": True},
                    "email": {"type": "varchar(255)", "encrypted": True, "pii": True},
                    "phone": {"type": "varchar(15)", "encrypted": True, "pii": True},
                    "address": {"type": "text", "encrypted": True, "pii": True},
                    "kyc_status": {"type": "enum('pending','verified','failed')", "required": True},
                    "risk_rating": {"type": "enum('low','medium','high')", "required": True},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "updated_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"},
                    "gdpr_consent": {"type": "boolean", "default": False},
                    "data_retention_date": {"type": "date"}
                },
                "payment_cards": {
                    "card_id": {"type": "varchar(50)", "primary_key": True},
                    "customer_id": {"type": "varchar(50)", "foreign_key": "customers.customer_id"},
                    "card_number_hash": {"type": "varchar(64)", "indexed": True},
                    "card_number_encrypted": {"type": "varchar(255)", "encrypted": True, "sensitive": True},
                    "expiry_date": {"type": "varchar(7)", "encrypted": True},
                    "card_type": {"type": "enum('visa','mastercard','amex','discover')"},
                    "last_four": {"type": "varchar(4)", "required": True},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "pci_compliance_flag": {"type": "boolean", "default": True}
                },
                "transactions": {
                    "transaction_id": {"type": "varchar(50)", "primary_key": True},
                    "customer_id": {"type": "varchar(50)", "foreign_key": "customers.customer_id"},
                    "card_id": {"type": "varchar(50)", "foreign_key": "payment_cards.card_id"},
                    "amount": {"type": "decimal(15,2)", "required": True, "encrypted": True},
                    "currency": {"type": "varchar(3)", "required": True},
                    "transaction_type": {"type": "enum('purchase','refund','chargeback')", "required": True},
                    "merchant_id": {"type": "varchar(50)", "required": True},
                    "authorization_code": {"type": "varchar(20)", "encrypted": True},
                    "transaction_date": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "settlement_date": {"type": "date"},
                    "fraud_score": {"type": "decimal(5,2)"},
                    "sox_control_flag": {"type": "boolean", "default": True}
                },
                "financial_audit_log": {
                    "log_id": {"type": "varchar(50)", "primary_key": True},
                    "table_name": {"type": "varchar(50)", "required": True},
                    "record_id": {"type": "varchar(50)", "required": True},
                    "user_id": {"type": "varchar(50)", "required": True},
                    "action": {"type": "enum('create','read','update','delete')", "required": True},
                    "before_values": {"type": "json", "encrypted": True},
                    "after_values": {"type": "json", "encrypted": True},
                    "timestamp": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "ip_address": {"type": "varchar(45)", "required": True},
                    "user_agent": {"type": "text"},
                    "session_id": {"type": "varchar(100)", "required": True},
                    "sox_relevant": {"type": "boolean", "default": True}
                }
            },
            security_controls=[
                "PCI DSS Level 1 compliance",
                "SOX internal controls",
                "Cardholder data encryption",
                "Network segmentation",
                "Regular penetration testing",
                "Fraud detection monitoring"
            ],
            audit_requirements=[
                "Complete transaction audit trail",
                "SOX compliance monitoring", 
                "PCI DSS audit logging",
                "Financial reporting integrity",
                "Segregation of duties tracking"
            ],
            access_controls=[
                "Segregation of duties enforcement",
                "Dual approval for high-value transactions",
                "Role-based access with SOX controls",
                "PCI DSS access restrictions",
                "Customer consent verification"
            ],
            encryption_requirements=[
                "AES-256 for cardholder data",
                "Strong cryptographic keys",
                "Secure key management",
                "Point-to-point encryption",
                "Database-level encryption"
            ],
            retention_policies={
                "customer_data": "7 years after account closure",
                "transaction_data": "7 years minimum",
                "audit_logs": "7 years for SOX compliance",
                "payment_card_data": "Delete after authorization unless stored for recurring transactions"
            }
        )
        
        # Government Templates (FISMA/FedRAMP Compliant)
        templates["government_contractor_data"] = ComplianceTemplate(
            template_id="government_contractor_data",
            name="FISMA/FedRAMP Compliant Government Data",
            industry=IndustryTemplate.GOVERNMENT,
            record_type=DataRecordType.COMPLIANCE_DATA,
            applicable_frameworks=["fisma", "nist", "itar", "fedramp"],
            schema_template={
                "personnel": {
                    "person_id": {"type": "varchar(50)", "primary_key": True, "encrypted": True},
                    "employee_number": {"type": "varchar(20)", "unique": True, "encrypted": True},
                    "first_name": {"type": "varchar(100)", "encrypted": True, "classified": True},
                    "last_name": {"type": "varchar(100)", "encrypted": True, "classified": True},
                    "ssn": {"type": "varchar(11)", "encrypted": True, "sensitive": True},
                    "security_clearance": {"type": "enum('unclassified','confidential','secret','top_secret')", "required": True},
                    "clearance_expiry": {"type": "date", "required": True},
                    "citizenship": {"type": "varchar(50)", "required": True},
                    "birth_country": {"type": "varchar(50)", "encrypted": True, "sensitive": True},
                    "position": {"type": "varchar(100)", "required": True},
                    "facility_access": {"type": "json", "encrypted": True},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "updated_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"},
                    "background_check_date": {"type": "date", "required": True},
                    "training_completion": {"type": "json"}
                },
                "classified_data": {
                    "data_id": {"type": "varchar(50)", "primary_key": True},
                    "classification": {"type": "enum('unclassified','cui','confidential','secret','top_secret')", "required": True},
                    "data_content": {"type": "text", "encrypted": True, "sensitive": True},
                    "owner_agency": {"type": "varchar(100)", "required": True},
                    "creation_date": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "declassification_date": {"type": "date"},
                    "access_control_list": {"type": "json", "required": True},
                    "export_controlled": {"type": "boolean", "default": False},
                    "itar_category": {"type": "varchar(20)"},
                    "handling_restrictions": {"type": "text", "required": True}
                },
                "system_access": {
                    "access_id": {"type": "varchar(50)", "primary_key": True},
                    "person_id": {"type": "varchar(50)", "foreign_key": "personnel.person_id"},
                    "system_name": {"type": "varchar(100)", "required": True},
                    "access_level": {"type": "enum('read','write','admin')", "required": True},
                    "granted_date": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "expiry_date": {"type": "date", "required": True},
                    "justification": {"type": "text", "required": True},
                    "approver_id": {"type": "varchar(50)", "required": True},
                    "continuous_monitoring": {"type": "boolean", "default": True}
                },
                "security_audit_log": {
                    "log_id": {"type": "varchar(50)", "primary_key": True},
                    "person_id": {"type": "varchar(50)", "foreign_key": "personnel.person_id"},
                    "system_name": {"type": "varchar(100)", "required": True},
                    "event_type": {"type": "enum('login','logout','access','modify','export')", "required": True},
                    "classification_level": {"type": "varchar(20)", "required": True},
                    "timestamp": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "ip_address": {"type": "varchar(45)", "required": True},
                    "location": {"type": "varchar(100)"},
                    "success": {"type": "boolean", "required": True},
                    "risk_score": {"type": "integer", "default": 0},
                    "requires_investigation": {"type": "boolean", "default": False}
                }
            },
            security_controls=[
                "Multi-factor authentication",
                "Continuous monitoring",
                "Security categorization",
                "Boundary protection",
                "Personnel security",
                "Export control monitoring"
            ],
            audit_requirements=[
                "Complete security event logging",
                "Continuous monitoring reporting",
                "Security control assessments",
                "Incident response tracking",
                "Compliance status reporting"
            ],
            access_controls=[
                "Security clearance verification",
                "Need-to-know enforcement",
                "Continuous authorization",
                "Export control screening",
                "Insider threat monitoring"
            ],
            encryption_requirements=[
                "FIPS 140-2 validated encryption",
                "NSA Suite B algorithms",
                "Key management infrastructure",
                "Classified data encryption",
                "Secure communications"
            ],
            retention_policies={
                "personnel_records": "75 years after separation",
                "classified_data": "Per classification guide",
                "audit_logs": "Minimum 3 years, up to 25 years for incidents",
                "access_records": "3 years after access termination"
            }
        )
        
        # SaaS Templates (SOC 2 Compliant)
        templates["saas_customer_data"] = ComplianceTemplate(
            template_id="saas_customer_data", 
            name="SOC 2 Compliant SaaS Customer Data",
            industry=IndustryTemplate.SAAS,
            record_type=DataRecordType.CUSTOMER_DATA,
            applicable_frameworks=["soc2", "gdpr", "ccpa", "iso_27001"],
            schema_template={
                "customers": {
                    "customer_id": {"type": "varchar(50)", "primary_key": True, "encrypted": True},
                    "tenant_id": {"type": "varchar(50)", "required": True, "indexed": True},
                    "company_name": {"type": "varchar(255)", "required": True},
                    "contact_email": {"type": "varchar(255)", "encrypted": True, "pii": True},
                    "billing_email": {"type": "varchar(255)", "encrypted": True, "pii": True},
                    "subscription_tier": {"type": "enum('free','pro','enterprise')", "required": True},
                    "data_region": {"type": "varchar(50)", "required": True},
                    "gdpr_applicable": {"type": "boolean", "default": False},
                    "ccpa_applicable": {"type": "boolean", "default": False},
                    "data_processing_agreement": {"type": "boolean", "default": False},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "updated_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"},
                    "retention_period": {"type": "integer", "default": 2555}
                },
                "user_data": {
                    "user_id": {"type": "varchar(50)", "primary_key": True},
                    "customer_id": {"type": "varchar(50)", "foreign_key": "customers.customer_id"},
                    "tenant_id": {"type": "varchar(50)", "required": True},
                    "email": {"type": "varchar(255)", "encrypted": True, "pii": True},
                    "first_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "last_name": {"type": "varchar(100)", "encrypted": True, "pii": True},
                    "phone": {"type": "varchar(15)", "encrypted": True, "pii": True},
                    "role": {"type": "varchar(50)", "required": True},
                    "last_login": {"type": "timestamp"},
                    "login_count": {"type": "integer", "default": 0},
                    "consent_marketing": {"type": "boolean", "default": False},
                    "consent_analytics": {"type": "boolean", "default": False},
                    "data_export_requested": {"type": "boolean", "default": False},
                    "data_deletion_requested": {"type": "boolean", "default": False}
                },
                "application_data": {
                    "data_id": {"type": "varchar(50)", "primary_key": True},
                    "customer_id": {"type": "varchar(50)", "foreign_key": "customers.customer_id"},
                    "tenant_id": {"type": "varchar(50)", "required": True},
                    "data_type": {"type": "varchar(100)", "required": True},
                    "data_content": {"type": "json", "encrypted": True},
                    "sensitivity_level": {"type": "enum('public','internal','confidential','restricted')", "required": True},
                    "processing_purpose": {"type": "text", "required": True},
                    "legal_basis": {"type": "enum('consent','contract','legal_obligation','vital_interests','public_task','legitimate_interests')"},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "retention_date": {"type": "date", "required": True}
                },
                "soc2_audit_log": {
                    "log_id": {"type": "varchar(50)", "primary_key": True},
                    "customer_id": {"type": "varchar(50)", "foreign_key": "customers.customer_id"},
                    "tenant_id": {"type": "varchar(50)", "required": True},
                    "user_id": {"type": "varchar(50)"},
                    "event_type": {"type": "varchar(100)", "required": True},
                    "resource_accessed": {"type": "varchar(255)", "required": True},
                    "action": {"type": "varchar(50)", "required": True},
                    "timestamp": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"},
                    "ip_address": {"type": "varchar(45)", "required": True},
                    "user_agent": {"type": "text"},
                    "session_id": {"type": "varchar(100)"},
                    "success": {"type": "boolean", "required": True},
                    "error_code": {"type": "varchar(50)"},
                    "soc2_category": {"type": "enum('security','availability','processing_integrity','confidentiality','privacy')", "required": True}
                }
            },
            security_controls=[
                "Multi-tenant data isolation",
                "Encryption at rest and in transit",
                "Access control and authentication",
                "Regular security assessments",
                "Incident response procedures",
                "Change management controls"
            ],
            audit_requirements=[
                "SOC 2 Type II audit trail",
                "Customer data access logging",
                "System availability monitoring",
                "Data processing integrity checks",
                "Privacy compliance tracking"
            ],
            access_controls=[
                "Role-based access control",
                "Multi-factor authentication",
                "Customer data segregation",
                "Admin access monitoring",
                "API access controls"
            ],
            encryption_requirements=[
                "AES-256 for customer data",
                "TLS 1.3 for data in transit",
                "Key management service",
                "Encrypted backups",
                "Secure key rotation"
            ],
            retention_policies={
                "customer_data": "As specified in customer agreement",
                "user_data": "30 days after account deletion",
                "application_data": "Per data processing agreement",
                "audit_logs": "7 years for SOC 2 compliance"
            }
        )
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[ComplianceTemplate]:
        """Get a specific compliance template"""
        return self.templates.get(template_id)
    
    def get_templates_by_industry(self, industry: IndustryTemplate) -> List[ComplianceTemplate]:
        """Get all templates for a specific industry"""
        return [template for template in self.templates.values() if template.industry == industry]
    
    def get_templates_by_framework(self, framework: str) -> List[ComplianceTemplate]:
        """Get all templates that support a specific framework"""
        return [template for template in self.templates.values() if framework in template.applicable_frameworks]
    
    def generate_sql_from_template(self, template_id: str, database_type: str = "mysql") -> str:
        """Generate SQL DDL from compliance template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        sql_statements = []
        
        # Add header comment
        sql_statements.append(f"-- {template.name}")
        sql_statements.append(f"-- Industry: {template.industry.value}")
        sql_statements.append(f"-- Compliance Frameworks: {', '.join(template.applicable_frameworks)}")
        sql_statements.append("-- Generated by SchemaSage Universal Compliance Platform")
        sql_statements.append("")
        
        # Generate table creation statements
        for table_name, columns in template.schema_template.items():
            sql_statements.append(f"CREATE TABLE {table_name} (")
            
            column_definitions = []
            for column_name, column_config in columns.items():
                column_def = f"    {column_name} {column_config['type']}"
                
                if column_config.get('primary_key'):
                    column_def += " PRIMARY KEY"
                elif column_config.get('unique'):
                    column_def += " UNIQUE"
                
                if column_config.get('required'):
                    column_def += " NOT NULL"
                
                if 'default' in column_config:
                    if database_type == "mysql" and column_config['default'] == "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP":
                        column_def += f" DEFAULT {column_config['default']}"
                    else:
                        column_def += f" DEFAULT {column_config['default']}"
                
                # Add compliance comments
                comments = []
                if column_config.get('encrypted'):
                    comments.append("ENCRYPTED")
                if column_config.get('pii'):
                    comments.append("PII")
                if column_config.get('sensitive'):
                    comments.append("SENSITIVE")
                if column_config.get('classified'):
                    comments.append("CLASSIFIED")
                
                if comments:
                    column_def += f" COMMENT '{', '.join(comments)}'"
                
                column_definitions.append(column_def)
            
            # Add foreign key constraints
            for column_name, column_config in columns.items():
                if 'foreign_key' in column_config:
                    fk_def = f"    FOREIGN KEY ({column_name}) REFERENCES {column_config['foreign_key']}"
                    column_definitions.append(fk_def)
            
            sql_statements.append(",\n".join(column_definitions))
            sql_statements.append(");")
            sql_statements.append("")
        
        # Add security control comments
        sql_statements.append("-- REQUIRED SECURITY CONTROLS:")
        for control in template.security_controls:
            sql_statements.append(f"-- - {control}")
        sql_statements.append("")
        
        # Add audit requirements
        sql_statements.append("-- AUDIT REQUIREMENTS:")
        for requirement in template.audit_requirements:
            sql_statements.append(f"-- - {requirement}")
        sql_statements.append("")
        
        # Add retention policy info
        sql_statements.append("-- DATA RETENTION POLICIES:")
        for data_type, policy in template.retention_policies.items():
            sql_statements.append(f"-- - {data_type}: {policy}")
        
        return "\n".join(sql_statements)
    
    def get_all_templates(self) -> Dict[str, ComplianceTemplate]:
        """Get all available templates"""
        return self.templates
    
    def get_template_summary(self) -> Dict[str, Any]:
        """Get summary of all available templates"""
        summary = {
            "total_templates": len(self.templates),
            "by_industry": {},
            "by_framework": {},
            "by_record_type": {}
        }
        
        for template in self.templates.values():
            # Count by industry
            industry = template.industry.value
            summary["by_industry"][industry] = summary["by_industry"].get(industry, 0) + 1
            
            # Count by framework
            for framework in template.applicable_frameworks:
                summary["by_framework"][framework] = summary["by_framework"].get(framework, 0) + 1
            
            # Count by record type
            record_type = template.record_type.value
            summary["by_record_type"][record_type] = summary["by_record_type"].get(record_type, 0) + 1
        
        return summary
