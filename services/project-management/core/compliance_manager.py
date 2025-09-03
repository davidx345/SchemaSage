"""
Universal Compliance Management System
Extends SchemaSage to be a universal compliance platform for database design and management
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import asyncio
import httpx

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Universal compliance frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa" 
    SOX = "sox"
    PCI_DSS = "pci_dss"
    FERPA = "ferpa"
    FISMA = "fisma"
    SOC2 = "soc2"
    CCPA = "ccpa"
    ISO_27001 = "iso_27001"
    NIST = "nist"
    PIPEDA = "pipeda"
    ITAR = "itar"


class IndustryType(Enum):
    """Industry sectors for compliance targeting"""
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    SAAS = "saas"
    GOVERNMENT = "government"
    FINANCIAL = "financial"
    MANUFACTURING = "manufacturing"
    NONPROFIT = "nonprofit"


class ComplianceStatus(Enum):
    """Compliance assessment status"""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


@dataclass
class ComplianceFrameworkInfo:
    """Information about a compliance framework"""
    framework: ComplianceFramework
    name: str
    description: str
    industries: List[IndustryType]
    key_requirements: List[str]
    penalty_info: str
    assessment_frequency: str  # "monthly", "quarterly", "annually"


@dataclass
class UniversalComplianceScore:
    """Multi-framework compliance scoring"""
    project_id: str
    overall_score: float  # 0-100
    framework_scores: Dict[str, float]  # framework -> score
    cross_compliance_coverage: float  # Percentage of overlapping requirements covered
    risk_level: str  # "low", "medium", "high", "critical"
    last_assessed: datetime
    next_assessment_due: datetime


@dataclass
class CrossComplianceMapping:
    """Mapping between different compliance frameworks"""
    requirement_id: str
    requirement_text: str
    applicable_frameworks: List[ComplianceFramework]
    coverage_level: str  # "full", "partial", "none"
    implementation_priority: int  # 1-5, 1 being highest


@dataclass
class ComplianceViolation:
    """Universal compliance violation"""
    violation_id: str
    framework: ComplianceFramework
    severity: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    affected_resources: List[str]
    remediation_steps: List[str]
    due_date: Optional[datetime]
    status: str  # "open", "in_progress", "resolved"
    cross_framework_impact: List[ComplianceFramework]


class UniversalComplianceManager:
    """Universal compliance management for all industries"""
    
    def __init__(self):
        self.framework_info = self._load_framework_info()
        self.cross_mappings = self._load_cross_compliance_mappings()
        self.industry_mappings = self._load_industry_framework_mappings()
        
    def _load_framework_info(self) -> Dict[ComplianceFramework, ComplianceFrameworkInfo]:
        """Load comprehensive framework information"""
        return {
            ComplianceFramework.GDPR: ComplianceFrameworkInfo(
                framework=ComplianceFramework.GDPR,
                name="General Data Protection Regulation",
                description="EU data privacy regulation with €20M fines",
                industries=[IndustryType.SAAS, IndustryType.HEALTHCARE, IndustryType.EDUCATION, IndustryType.FINANCIAL],
                key_requirements=["Data minimization", "Consent management", "Right to erasure", "Breach notification"],
                penalty_info="Up to €20M or 4% of annual revenue",
                assessment_frequency="quarterly"
            ),
            ComplianceFramework.HIPAA: ComplianceFrameworkInfo(
                framework=ComplianceFramework.HIPAA,
                name="Health Insurance Portability and Accountability Act",
                description="US healthcare data protection",
                industries=[IndustryType.HEALTHCARE],
                key_requirements=["PHI encryption", "Access controls", "Audit logging", "Breach notification"],
                penalty_info="Up to $1.5M per incident",
                assessment_frequency="annually"
            ),
            ComplianceFramework.FERPA: ComplianceFrameworkInfo(
                framework=ComplianceFramework.FERPA,
                name="Family Educational Rights and Privacy Act",
                description="Student privacy protection (underserved market)",
                industries=[IndustryType.EDUCATION],
                key_requirements=["Student record protection", "Parental consent", "Directory information limits"],
                penalty_info="Federal funding withdrawal",
                assessment_frequency="annually"
            ),
            ComplianceFramework.SOC2: ComplianceFrameworkInfo(
                framework=ComplianceFramework.SOC2,
                name="Service Organization Control 2",
                description="Every SaaS company needs this",
                industries=[IndustryType.SAAS, IndustryType.FINANCIAL],
                key_requirements=["Security controls", "Availability", "Processing integrity", "Confidentiality"],
                penalty_info="Customer contract violations",
                assessment_frequency="annually"
            ),
            ComplianceFramework.FISMA: ComplianceFrameworkInfo(
                framework=ComplianceFramework.FISMA,
                name="Federal Information Security Management Act",
                description="Government contractor compliance (high-value)",
                industries=[IndustryType.GOVERNMENT],
                key_requirements=["Security categorization", "Security controls", "Continuous monitoring"],
                penalty_info="Contract termination",
                assessment_frequency="continuously"
            ),
            ComplianceFramework.SOX: ComplianceFrameworkInfo(
                framework=ComplianceFramework.SOX,
                name="Sarbanes-Oxley Act",
                description="Financial reporting integrity",
                industries=[IndustryType.FINANCIAL],
                key_requirements=["Financial data integrity", "Audit trails", "Access controls"],
                penalty_info="Criminal penalties up to $5M",
                assessment_frequency="annually"
            ),
            ComplianceFramework.PCI_DSS: ComplianceFrameworkInfo(
                framework=ComplianceFramework.PCI_DSS,
                name="Payment Card Industry Data Security Standard",
                description="Credit card data protection",
                industries=[IndustryType.FINANCIAL, IndustryType.SAAS],
                key_requirements=["Cardholder data encryption", "Network segmentation", "Regular testing"],
                penalty_info="Fines up to $100K per month",
                assessment_frequency="annually"
            ),
            ComplianceFramework.ITAR: ComplianceFrameworkInfo(
                framework=ComplianceFramework.ITAR,
                name="International Traffic in Arms Regulations",
                description="Export control for defense data",
                industries=[IndustryType.MANUFACTURING, IndustryType.GOVERNMENT],
                key_requirements=["Export licensing", "Person screening", "Data segregation"],
                penalty_info="Criminal penalties, export license revocation",
                assessment_frequency="continuously"
            )
        }
    
    def _load_cross_compliance_mappings(self) -> List[CrossComplianceMapping]:
        """Load cross-framework compliance mappings"""
        return [
            CrossComplianceMapping(
                requirement_id="ENCRYPT_001",
                requirement_text="Sensitive data must be encrypted at rest and in transit",
                applicable_frameworks=[ComplianceFramework.GDPR, ComplianceFramework.HIPAA, 
                                     ComplianceFramework.PCI_DSS, ComplianceFramework.SOC2],
                coverage_level="full",
                implementation_priority=1
            ),
            CrossComplianceMapping(
                requirement_id="ACCESS_001", 
                requirement_text="Role-based access controls must be implemented",
                applicable_frameworks=[ComplianceFramework.SOX, ComplianceFramework.HIPAA,
                                     ComplianceFramework.FISMA, ComplianceFramework.SOC2],
                coverage_level="full",
                implementation_priority=1
            ),
            CrossComplianceMapping(
                requirement_id="AUDIT_001",
                requirement_text="Comprehensive audit logging must be maintained",
                applicable_frameworks=[ComplianceFramework.SOX, ComplianceFramework.HIPAA,
                                     ComplianceFramework.PCI_DSS, ComplianceFramework.FISMA],
                coverage_level="full", 
                implementation_priority=2
            ),
            CrossComplianceMapping(
                requirement_id="CONSENT_001",
                requirement_text="User consent must be obtained and tracked",
                applicable_frameworks=[ComplianceFramework.GDPR, ComplianceFramework.CCPA,
                                     ComplianceFramework.FERPA],
                coverage_level="partial",
                implementation_priority=2
            ),
            CrossComplianceMapping(
                requirement_id="BREACH_001",
                requirement_text="Data breaches must be reported within specified timeframes",
                applicable_frameworks=[ComplianceFramework.GDPR, ComplianceFramework.HIPAA,
                                     ComplianceFramework.CCPA],
                coverage_level="partial",
                implementation_priority=3
            )
        ]
    
    def _load_industry_framework_mappings(self) -> Dict[IndustryType, List[ComplianceFramework]]:
        """Map industries to required compliance frameworks"""
        return {
            IndustryType.HEALTHCARE: [ComplianceFramework.HIPAA, ComplianceFramework.GDPR, ComplianceFramework.SOC2],
            IndustryType.EDUCATION: [ComplianceFramework.FERPA, ComplianceFramework.GDPR, ComplianceFramework.CCPA],
            IndustryType.SAAS: [ComplianceFramework.SOC2, ComplianceFramework.GDPR, ComplianceFramework.CCPA],
            IndustryType.GOVERNMENT: [ComplianceFramework.FISMA, ComplianceFramework.NIST, ComplianceFramework.ITAR],
            IndustryType.FINANCIAL: [ComplianceFramework.SOX, ComplianceFramework.PCI_DSS, ComplianceFramework.GDPR],
            IndustryType.MANUFACTURING: [ComplianceFramework.ITAR, ComplianceFramework.ISO_27001, ComplianceFramework.GDPR],
            IndustryType.NONPROFIT: [ComplianceFramework.GDPR, ComplianceFramework.CCPA]
        }
    
    async def assess_universal_compliance(self, project_id: str, schema_data: Dict[str, Any], 
                                        selected_frameworks: List[ComplianceFramework] = None) -> UniversalComplianceScore:
        """Assess compliance across multiple frameworks"""
        if not selected_frameworks:
            selected_frameworks = list(ComplianceFramework)
        
        framework_scores = {}
        total_violations = 0
        
        # Assess each framework
        for framework in selected_frameworks:
            try:
                # Call code-generation service for compliance assessment
                score, violations = await self._assess_framework_compliance(schema_data, framework)
                framework_scores[framework.value] = score
                total_violations += len(violations)
            except Exception as e:
                logger.warning(f"Failed to assess {framework.value}: {e}")
                framework_scores[framework.value] = 0.0
        
        # Calculate overall score
        overall_score = sum(framework_scores.values()) / len(framework_scores) if framework_scores else 0.0
        
        # Calculate cross-compliance coverage
        cross_coverage = self._calculate_cross_compliance_coverage(selected_frameworks)
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score, total_violations)
        
        return UniversalComplianceScore(
            project_id=project_id,
            overall_score=overall_score,
            framework_scores=framework_scores,
            cross_compliance_coverage=cross_coverage,
            risk_level=risk_level,
            last_assessed=datetime.utcnow(),
            next_assessment_due=datetime.utcnow() + timedelta(days=90)
        )
    
    async def _assess_framework_compliance(self, schema_data: Dict[str, Any], 
                                         framework: ComplianceFramework) -> tuple[float, List[ComplianceViolation]]:
        """Assess compliance for a specific framework via code-generation service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Call the existing compliance assessment endpoint
                response = await client.post(
                    "http://localhost:8000/api/compliance/assess",
                    json={
                        "schema": schema_data,
                        "framework": framework.value,
                        "assessment_type": "full"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("overall_score", 0.0), result.get("violations", [])
                else:
                    logger.warning(f"Compliance assessment failed for {framework.value}: {response.status_code}")
                    return 0.0, []
                    
        except Exception as e:
            logger.error(f"Error assessing {framework.value} compliance: {e}")
            return 0.0, []
    
    def _calculate_cross_compliance_coverage(self, frameworks: List[ComplianceFramework]) -> float:
        """Calculate how much cross-framework compliance is achieved"""
        if len(frameworks) <= 1:
            return 100.0
        
        total_mappings = len(self.cross_mappings)
        covered_mappings = 0
        
        for mapping in self.cross_mappings:
            # Check if any of the selected frameworks apply to this mapping
            if any(fw in mapping.applicable_frameworks for fw in frameworks):
                covered_mappings += 1
        
        return (covered_mappings / total_mappings) * 100.0 if total_mappings > 0 else 0.0
    
    def _determine_risk_level(self, overall_score: float, violation_count: int) -> str:
        """Determine overall risk level"""
        if overall_score >= 90 and violation_count == 0:
            return "low"
        elif overall_score >= 75 and violation_count <= 3:
            return "medium"
        elif overall_score >= 50 and violation_count <= 10:
            return "high"
        else:
            return "critical"
    
    def get_framework_info(self, framework: ComplianceFramework = None) -> Dict[str, Any]:
        """Get information about compliance frameworks"""
        if framework:
            info = self.framework_info.get(framework)
            return info.__dict__ if info else {}
        
        return {
            fw.value: {
                "name": info.name,
                "description": info.description,
                "industries": [ind.value for ind in info.industries],
                "key_requirements": info.key_requirements,
                "penalty_info": info.penalty_info,
                "assessment_frequency": info.assessment_frequency
            }
            for fw, info in self.framework_info.items()
        }
    
    def get_industry_frameworks(self, industry: IndustryType) -> List[Dict[str, Any]]:
        """Get recommended frameworks for an industry"""
        frameworks = self.industry_mappings.get(industry, [])
        return [
            {
                "framework": fw.value,
                "name": self.framework_info[fw].name,
                "priority": "required" if i < 2 else "recommended"
            }
            for i, fw in enumerate(frameworks)
        ]
    
    def get_cross_compliance_analysis(self, frameworks: List[ComplianceFramework]) -> Dict[str, Any]:
        """Analyze compliance overlaps and conflicts between frameworks"""
        overlaps = []
        conflicts = []
        efficiency_score = 0.0
        
        # Find overlapping requirements
        for mapping in self.cross_mappings:
            applicable_selected = [fw for fw in frameworks if fw in mapping.applicable_frameworks]
            if len(applicable_selected) > 1:
                overlaps.append({
                    "requirement": mapping.requirement_text,
                    "frameworks": [fw.value for fw in applicable_selected],
                    "coverage": mapping.coverage_level,
                    "priority": mapping.implementation_priority
                })
        
        # Calculate efficiency (more overlaps = higher efficiency)
        if frameworks:
            total_possible = len(frameworks) * len(self.cross_mappings)
            actual_overlaps = sum(len(overlap["frameworks"]) for overlap in overlaps)
            efficiency_score = min(100.0, (actual_overlaps / total_possible) * 100.0) if total_possible > 0 else 0.0
        
        return {
            "selected_frameworks": [fw.value for fw in frameworks],
            "overlapping_requirements": overlaps,
            "conflicts": conflicts,  # TODO: Implement conflict detection
            "efficiency_score": efficiency_score,
            "implementation_recommendations": self._generate_implementation_recommendations(overlaps)
        }
    
    def _generate_implementation_recommendations(self, overlaps: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for efficient compliance implementation"""
        recommendations = []
        
        # Sort by priority and count
        high_priority_overlaps = [o for o in overlaps if o["priority"] <= 2]
        
        if high_priority_overlaps:
            recommendations.append(
                f"Implement {len(high_priority_overlaps)} high-priority requirements that cover multiple frameworks"
            )
        
        encryption_overlaps = [o for o in overlaps if "encrypt" in o["requirement"].lower()]
        if encryption_overlaps:
            recommendations.append(
                "Implement comprehensive encryption to satisfy multiple compliance requirements"
            )
        
        access_overlaps = [o for o in overlaps if "access" in o["requirement"].lower()]
        if access_overlaps:
            recommendations.append(
                "Deploy unified access control system for cross-framework compliance"
            )
        
        if len(overlaps) > 5:
            recommendations.append(
                "Consider compliance automation platform due to high requirement overlap"
            )
        
        return recommendations

    def generate_compliance_templates(self, industry: IndustryType, 
                                    data_type: str) -> Dict[str, Any]:
        """Generate industry-specific compliance templates"""
        frameworks = self.industry_mappings.get(industry, [])
        
        # Base template structure
        template = {
            "industry": industry.value,
            "data_type": data_type,
            "compliance_frameworks": [fw.value for fw in frameworks],
            "schema_recommendations": [],
            "required_fields": [],
            "security_controls": [],
            "audit_requirements": []
        }
        
        # Industry-specific customizations
        if industry == IndustryType.HEALTHCARE:
            template.update({
                "required_fields": ["patient_id", "medical_record_number", "phi_consent_date"],
                "security_controls": ["encryption_at_rest", "access_logging", "role_based_access"],
                "audit_requirements": ["hipaa_audit_log", "breach_notification_system"]
            })
        elif industry == IndustryType.EDUCATION:
            template.update({
                "required_fields": ["student_id", "ferpa_consent", "directory_opt_out"],
                "security_controls": ["student_record_encryption", "parental_access_controls"],
                "audit_requirements": ["ferpa_compliance_log", "directory_access_tracking"]
            })
        elif industry == IndustryType.FINANCIAL:
            template.update({
                "required_fields": ["account_id", "transaction_audit_trail", "sox_controls"],
                "security_controls": ["financial_data_encryption", "segregation_of_duties"],
                "audit_requirements": ["sox_audit_trail", "pci_compliance_monitoring"]
            })
        elif industry == IndustryType.GOVERNMENT:
            template.update({
                "required_fields": ["security_classification", "export_control_flag", "clearance_level"],
                "security_controls": ["fisma_controls", "continuous_monitoring", "data_classification"],
                "audit_requirements": ["fisma_audit_log", "security_incident_tracking"]
            })
        
        return template
