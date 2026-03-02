"""
Enhanced PII Detection Engine for Universal Compliance
Extends existing PII detection with multi-framework patterns for GDPR, SOC2, FERPA, HIPAA, etc.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class PIIFramework(Enum):
    """PII classification frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    FERPA = "ferpa"
    SOC2 = "soc2"
    CCPA = "ccpa"
    PCI_DSS = "pci_dss"
    FISMA = "fisma"
    ITAR = "itar"


class PIIType(Enum):
    """Universal PII type classifications"""
    DIRECT_IDENTIFIER = "direct_identifier"
    QUASI_IDENTIFIER = "quasi_identifier"
    SENSITIVE_PERSONAL = "sensitive_personal"
    BIOMETRIC = "biometric"
    FINANCIAL = "financial"
    HEALTH = "health"
    EDUCATION = "education"
    GOVERNMENT = "government"
    BEHAVIORAL = "behavioral"


@dataclass
class PIIPattern:
    """PII detection pattern"""
    pattern_id: str
    name: str
    regex_pattern: str
    applicable_frameworks: List[PIIFramework]
    pii_type: PIIType
    sensitivity_level: int  # 1-5, 5 being highest
    field_name_indicators: List[str]
    data_type_indicators: List[str]
    context_requirements: List[str] = field(default_factory=list)


@dataclass
class PIIDetectionResult:
    """PII detection result"""
    field_name: str
    detected_pii_types: List[PIIType]
    applicable_frameworks: List[PIIFramework]
    confidence_score: float  # 0-1
    sensitivity_level: int
    recommendations: List[str]
    compliance_notes: Dict[str, str]


class UniversalPIIDetector:
    """Universal PII detector supporting multiple compliance frameworks"""
    
    def __init__(self):
        self.pii_patterns = self._load_universal_pii_patterns()
        self.framework_requirements = self._load_framework_requirements()
        
    def _load_universal_pii_patterns(self) -> List[PIIPattern]:
        """Load comprehensive PII patterns for all frameworks"""
        return [
            # Direct Identifiers
            PIIPattern(
                pattern_id="SSN_001",
                name="Social Security Number",
                regex_pattern=r'\b\d{3}-?\d{2}-?\d{4}\b',
                applicable_frameworks=[PIIFramework.GDPR, PIIFramework.HIPAA, PIIFramework.SOC2, PIIFramework.CCPA],
                pii_type=PIIType.DIRECT_IDENTIFIER,
                sensitivity_level=5,
                field_name_indicators=["ssn", "social_security", "social_security_number", "social_sec"],
                data_type_indicators=["varchar", "char", "text", "string"]
            ),
            PIIPattern(
                pattern_id="EMAIL_001", 
                name="Email Address",
                regex_pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                applicable_frameworks=[PIIFramework.GDPR, PIIFramework.SOC2, PIIFramework.CCPA, PIIFramework.FERPA],
                pii_type=PIIType.DIRECT_IDENTIFIER,
                sensitivity_level=4,
                field_name_indicators=["email", "email_address", "e_mail", "email_addr", "contact_email"],
                data_type_indicators=["varchar", "text", "string"]
            ),
            PIIPattern(
                pattern_id="PHONE_001",
                name="Phone Number", 
                regex_pattern=r'\b(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                applicable_frameworks=[PIIFramework.GDPR, PIIFramework.SOC2, PIIFramework.CCPA, PIIFramework.HIPAA],
                pii_type=PIIType.DIRECT_IDENTIFIER,
                sensitivity_level=3,
                field_name_indicators=["phone", "phone_number", "telephone", "mobile", "cell_phone", "contact_number"],
                data_type_indicators=["varchar", "char", "text", "string"]
            ),
            
            # Health Information (HIPAA)
            PIIPattern(
                pattern_id="MRN_001",
                name="Medical Record Number",
                regex_pattern=r'\b(MRN|MR)[-\s]?\d{6,10}\b',
                applicable_frameworks=[PIIFramework.HIPAA, PIIFramework.GDPR],
                pii_type=PIIType.HEALTH,
                sensitivity_level=5,
                field_name_indicators=["medical_record", "mrn", "patient_id", "health_record", "medical_id"],
                data_type_indicators=["varchar", "bigint", "integer", "text"]
            ),
            PIIPattern(
                pattern_id="INSURANCE_001",
                name="Health Insurance Number",
                regex_pattern=r'\b[A-Z]{2,3}\d{6,12}\b',
                applicable_frameworks=[PIIFramework.HIPAA],
                pii_type=PIIType.HEALTH,
                sensitivity_level=5,
                field_name_indicators=["insurance_number", "policy_number", "member_id", "subscriber_id"],
                data_type_indicators=["varchar", "char", "text"]
            ),
            
            # Education Information (FERPA)
            PIIPattern(
                pattern_id="STUDENT_ID_001",
                name="Student ID Number",
                regex_pattern=r'\b(ST|STU)\d{6,10}\b',
                applicable_frameworks=[PIIFramework.FERPA, PIIFramework.GDPR],
                pii_type=PIIType.EDUCATION,
                sensitivity_level=4,
                field_name_indicators=["student_id", "student_number", "enrollment_id", "learner_id"],
                data_type_indicators=["varchar", "bigint", "integer"]
            ),
            PIIPattern(
                pattern_id="GRADE_001",
                name="Academic Grades",
                regex_pattern=r'\b[A-F][+-]?|[0-9]{1,3}\.?[0-9]?%?\b',
                applicable_frameworks=[PIIFramework.FERPA],
                pii_type=PIIType.EDUCATION,
                sensitivity_level=3,
                field_name_indicators=["grade", "score", "gpa", "mark", "result", "evaluation"],
                data_type_indicators=["decimal", "float", "varchar", "char"]
            ),
            
            # Financial Information (PCI-DSS, SOX)
            PIIPattern(
                pattern_id="CREDIT_CARD_001",
                name="Credit Card Number",
                regex_pattern=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                applicable_frameworks=[PIIFramework.PCI_DSS, PIIFramework.GDPR, PIIFramework.SOC2],
                pii_type=PIIType.FINANCIAL,
                sensitivity_level=5,
                field_name_indicators=["credit_card", "card_number", "payment_card", "cc_number"],
                data_type_indicators=["varchar", "char", "bigint", "encrypted"]
            ),
            PIIPattern(
                pattern_id="BANK_ACCOUNT_001",
                name="Bank Account Number",
                regex_pattern=r'\b\d{8,17}\b',
                applicable_frameworks=[PIIFramework.PCI_DSS, PIIFramework.SOC2, PIIFramework.GDPR],
                pii_type=PIIType.FINANCIAL,
                sensitivity_level=5,
                field_name_indicators=["account_number", "bank_account", "routing_number", "iban"],
                data_type_indicators=["varchar", "bigint", "char"]
            ),
            
            # Government/Security (FISMA, ITAR)
            PIIPattern(
                pattern_id="SECURITY_CLEARANCE_001",
                name="Security Clearance Level",
                regex_pattern=r'\b(SECRET|TOP SECRET|CONFIDENTIAL|UNCLASSIFIED)\b',
                applicable_frameworks=[PIIFramework.FISMA, PIIFramework.ITAR],
                pii_type=PIIType.GOVERNMENT,
                sensitivity_level=5,
                field_name_indicators=["clearance", "classification", "security_level", "access_level"],
                data_type_indicators=["varchar", "char", "enum"]
            ),
            PIIPattern(
                pattern_id="EXPORT_CONTROL_001",
                name="Export Control Classification",
                regex_pattern=r'\b(ITAR|EAR|ECCN)\s?[A-Z0-9.-]+\b',
                applicable_frameworks=[PIIFramework.ITAR, PIIFramework.FISMA],
                pii_type=PIIType.GOVERNMENT,
                sensitivity_level=5,
                field_name_indicators=["export_classification", "eccn", "itar_category", "export_control"],
                data_type_indicators=["varchar", "char", "text"]
            ),
            
            # Biometric Data
            PIIPattern(
                pattern_id="BIOMETRIC_001",
                name="Biometric Data",
                regex_pattern=r'\b(fingerprint|retina|iris|facial|biometric)\b',
                applicable_frameworks=[PIIFramework.GDPR, PIIFramework.HIPAA, PIIFramework.FISMA],
                pii_type=PIIType.BIOMETRIC,
                sensitivity_level=5,
                field_name_indicators=["fingerprint", "biometric", "facial_recognition", "iris_scan"],
                data_type_indicators=["blob", "binary", "varbinary", "text"]
            ),
            
            # Behavioral Data
            PIIPattern(
                pattern_id="IP_ADDRESS_001",
                name="IP Address",
                regex_pattern=r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                applicable_frameworks=[PIIFramework.GDPR, PIIFramework.CCPA, PIIFramework.SOC2],
                pii_type=PIIType.BEHAVIORAL,
                sensitivity_level=3,
                field_name_indicators=["ip_address", "ip_addr", "source_ip", "client_ip"],
                data_type_indicators=["varchar", "inet", "char"]
            ),
            PIIPattern(
                pattern_id="TRACKING_001",
                name="Tracking Identifiers",
                regex_pattern=r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b',
                applicable_frameworks=[PIIFramework.GDPR, PIIFramework.CCPA],
                pii_type=PIIType.BEHAVIORAL,
                sensitivity_level=4,
                field_name_indicators=["session_id", "tracking_id", "cookie_id", "device_id", "uuid"],
                data_type_indicators=["varchar", "uuid", "char", "text"]
            )
        ]
    
    def _load_framework_requirements(self) -> Dict[PIIFramework, Dict[str, Any]]:
        """Load framework-specific PII requirements"""
        return {
            PIIFramework.GDPR: {
                "consent_required": True,
                "right_to_erasure": True,
                "data_minimization": True,
                "breach_notification_hours": 72,
                "special_categories": ["health", "biometric", "genetic", "racial", "political"]
            },
            PIIFramework.HIPAA: {
                "minimum_necessary": True,
                "encryption_required": True,
                "access_logging": True,
                "breach_notification_days": 60,
                "phi_identifiers": 18
            },
            PIIFramework.FERPA: {
                "parental_consent": True,
                "directory_information": True,
                "legitimate_educational_interest": True,
                "record_retention_years": 5
            },
            PIIFramework.SOC2: {
                "security_controls": True,
                "availability_controls": True,
                "processing_integrity": True,
                "confidentiality_controls": True
            },
            PIIFramework.PCI_DSS: {
                "cardholder_data_encryption": True,
                "network_segmentation": True,
                "access_control": True,
                "regular_testing": True
            },
            PIIFramework.FISMA: {
                "security_categorization": True,
                "security_controls": True,
                "continuous_monitoring": True,
                "incident_response": True
            }
        }
    
    def detect_pii_multi_framework(self, schema_data: Dict[str, Any], 
                                 target_frameworks: List[PIIFramework] = None) -> Dict[str, PIIDetectionResult]:
        """Detect PII across multiple compliance frameworks"""
        if not target_frameworks:
            target_frameworks = list(PIIFramework)
        
        detection_results = {}
        
        # Analyze each table and column
        for table_name, table_info in schema_data.items():
            if isinstance(table_info, dict) and "columns" in table_info:
                for column_info in table_info["columns"]:
                    column_name = column_info.get("name", "")
                    data_type = column_info.get("type", "")
                    
                    result = self._analyze_field_for_pii(
                        field_name=column_name,
                        data_type=data_type,
                        table_context=table_name,
                        target_frameworks=target_frameworks
                    )
                    
                    if result.detected_pii_types:
                        full_field_name = f"{table_name}.{column_name}"
                        detection_results[full_field_name] = result
        
        return detection_results
    
    def _analyze_field_for_pii(self, field_name: str, data_type: str, 
                              table_context: str, target_frameworks: List[PIIFramework]) -> PIIDetectionResult:
        """Analyze a specific field for PII content"""
        detected_types = []
        applicable_frameworks = []
        confidence_scores = []
        recommendations = []
        compliance_notes = {}
        max_sensitivity = 0
        
        field_lower = field_name.lower()
        data_type_lower = data_type.lower()
        table_lower = table_context.lower()
        
        # Check against all PII patterns
        for pattern in self.pii_patterns:
            # Skip if pattern doesn't apply to target frameworks
            if not any(fw in pattern.applicable_frameworks for fw in target_frameworks):
                continue
            
            confidence = 0.0
            
            # Check field name indicators
            for indicator in pattern.field_name_indicators:
                if indicator in field_lower:
                    confidence += 0.4
                    break
            
            # Check data type indicators
            for indicator in pattern.data_type_indicators:
                if indicator in data_type_lower:
                    confidence += 0.2
                    break
            
            # Check table context for additional clues
            context_indicators = {
                PIIType.HEALTH: ["patient", "medical", "health", "clinical", "hospital"],
                PIIType.EDUCATION: ["student", "grade", "course", "academic", "school"],
                PIIType.FINANCIAL: ["payment", "transaction", "billing", "invoice", "account"],
                PIIType.GOVERNMENT: ["security", "clearance", "classified", "government"]
            }
            
            if pattern.pii_type in context_indicators:
                for context_word in context_indicators[pattern.pii_type]:
                    if context_word in table_lower:
                        confidence += 0.3
                        break
            
            # If confidence is high enough, include this detection
            if confidence >= 0.4:
                detected_types.append(pattern.pii_type)
                applicable_frameworks.extend(pattern.applicable_frameworks)
                confidence_scores.append(confidence)
                max_sensitivity = max(max_sensitivity, pattern.sensitivity_level)
                
                # Add framework-specific compliance notes
                for framework in pattern.applicable_frameworks:
                    if framework in target_frameworks:
                        requirements = self.framework_requirements.get(framework, {})
                        if framework == PIIFramework.GDPR and pattern.pii_type in [PIIType.HEALTH, PIIType.BIOMETRIC]:
                            compliance_notes[framework.value] = "Special category data - explicit consent required"
                        elif framework == PIIFramework.HIPAA and pattern.pii_type == PIIType.HEALTH:
                            compliance_notes[framework.value] = "PHI - minimum necessary rule applies"
                        elif framework == PIIFramework.FERPA and pattern.pii_type == PIIType.EDUCATION:
                            compliance_notes[framework.value] = "Educational record - FERPA protections apply"
                        elif framework == PIIFramework.PCI_DSS and pattern.pii_type == PIIType.FINANCIAL:
                            compliance_notes[framework.value] = "Cardholder data - PCI DSS Level 1 requirements"
        
        # Remove duplicates
        detected_types = list(set(detected_types))
        applicable_frameworks = list(set(applicable_frameworks))
        
        # Generate recommendations based on detected PII
        if detected_types:
            recommendations.extend([
                "Implement field-level encryption for sensitive data",
                "Apply appropriate access controls based on sensitivity level",
                "Enable audit logging for all access to this field",
                "Consider data masking for non-production environments"
            ])
            
            # Framework-specific recommendations
            if PIIFramework.GDPR in applicable_frameworks:
                recommendations.append("Implement consent management for GDPR compliance")
            if PIIFramework.HIPAA in applicable_frameworks:
                recommendations.append("Apply HIPAA minimum necessary access controls")
            if PIIFramework.PCI_DSS in applicable_frameworks:
                recommendations.append("Implement PCI DSS network segmentation")
        
        # Calculate overall confidence
        overall_confidence = max(confidence_scores) if confidence_scores else 0.0
        
        return PIIDetectionResult(
            field_name=field_name,
            detected_pii_types=detected_types,
            applicable_frameworks=applicable_frameworks,
            confidence_score=overall_confidence,
            sensitivity_level=max_sensitivity,
            recommendations=recommendations,
            compliance_notes=compliance_notes
        )
    
    def generate_compliance_summary(self, detection_results: Dict[str, PIIDetectionResult]) -> Dict[str, Any]:
        """Generate a comprehensive compliance summary"""
        framework_coverage = {}
        pii_type_counts = {}
        total_sensitive_fields = len(detection_results)
        high_risk_fields = 0
        
        for field_name, result in detection_results.items():
            # Count by framework
            for framework in result.applicable_frameworks:
                if framework.value not in framework_coverage:
                    framework_coverage[framework.value] = []
                framework_coverage[framework.value].append(field_name)
            
            # Count by PII type
            for pii_type in result.detected_pii_types:
                pii_type_counts[pii_type.value] = pii_type_counts.get(pii_type.value, 0) + 1
            
            # Count high-risk fields
            if result.sensitivity_level >= 4:
                high_risk_fields += 1
        
        # Calculate risk score
        risk_score = (high_risk_fields / total_sensitive_fields * 100) if total_sensitive_fields > 0 else 0
        
        # Generate recommendations
        priority_recommendations = []
        if high_risk_fields > 0:
            priority_recommendations.append(f"Immediate attention needed for {high_risk_fields} high-risk fields")
        if PIIFramework.GDPR.value in framework_coverage:
            priority_recommendations.append("GDPR compliance assessment required")
        if PIIFramework.HIPAA.value in framework_coverage:
            priority_recommendations.append("HIPAA security risk assessment needed")
        
        return {
            "total_pii_fields": total_sensitive_fields,
            "high_risk_fields": high_risk_fields,
            "risk_score": risk_score,
            "framework_coverage": framework_coverage,
            "pii_type_distribution": pii_type_counts,
            "priority_recommendations": priority_recommendations,
            "compliance_readiness": "high" if risk_score < 25 else "medium" if risk_score < 50 else "low"
        }
