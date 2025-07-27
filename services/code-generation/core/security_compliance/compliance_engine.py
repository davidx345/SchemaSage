"""
Compliance assessment engine
Evaluates schema compliance against various regulatory frameworks
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import uuid

from models.schemas import SchemaResponse, TableInfo, ColumnInfo
from .models import (
    ComplianceReport, ComplianceViolation, ComplianceFramework,
    DataClassification, SecurityLevel, RiskLevel
)

logger = logging.getLogger(__name__)


class ComplianceAssessmentEngine:
    """
    Assesses schema compliance against regulatory frameworks
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize compliance assessment engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.compliance_rules = self._load_compliance_rules()
        self.framework_requirements = self._load_framework_requirements()
        
        logger.info("Compliance assessment engine initialized")
    
    async def assess_compliance(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        custom_rules: Dict[str, Any] = None
    ) -> ComplianceReport:
        """
        Assess schema compliance against specified framework
        
        Args:
            schema: Schema response object
            classifications: Data classifications
            framework: Compliance framework to assess against
            custom_rules: Optional custom compliance rules
            
        Returns:
            Compliance report
        """
        try:
            assessment_date = datetime.utcnow()
            violations = []
            recommendations = []
            
            # Get framework-specific rules
            rules = custom_rules or self.compliance_rules.get(framework.value, {})
            requirements = self.framework_requirements.get(framework.value, {})
            
            # Perform assessment checks
            violations.extend(await self._check_data_encryption(schema, classifications, framework, requirements))
            violations.extend(await self._check_access_controls(schema, classifications, framework, requirements))
            violations.extend(await self._check_data_retention(schema, classifications, framework, requirements))
            violations.extend(await self._check_audit_logging(schema, classifications, framework, requirements))
            violations.extend(await self._check_data_minimization(schema, classifications, framework, requirements))
            violations.extend(await self._check_consent_management(schema, classifications, framework, requirements))
            violations.extend(await self._check_breach_notification(schema, classifications, framework, requirements))
            
            # Generate recommendations
            recommendations = self._generate_recommendations(violations, framework)
            
            # Calculate overall compliance score
            total_checks = len(self._get_all_compliance_checks(framework))
            violation_count = len(violations)
            overall_score = max(0.0, (total_checks - violation_count) / total_checks) if total_checks > 0 else 1.0
            
            # Determine compliance status
            compliance_status = self._determine_compliance_status(overall_score, violations)
            
            # Risk assessment
            risk_assessment = self._perform_risk_assessment(violations, classifications)
            
            # Next assessment date
            next_assessment_date = self._calculate_next_assessment_date(framework, overall_score)
            
            report_id = str(uuid.uuid4())
            
            report = ComplianceReport(
                report_id=report_id,
                schema_name=schema.schema_name,
                framework=framework,
                assessment_date=assessment_date,
                overall_score=overall_score,
                compliance_status=compliance_status,
                violations=violations,
                recommendations=recommendations,
                risk_assessment=risk_assessment,
                next_assessment_date=next_assessment_date,
                metadata={
                    'total_tables': len(schema.tables),
                    'total_columns': sum(len(table.columns) for table in schema.tables),
                    'total_checks': total_checks,
                    'violation_count': violation_count,
                    'assessment_version': '1.0'
                }
            )
            
            logger.info(f"Compliance assessment completed for {schema.schema_name} "
                       f"against {framework.value} - Score: {overall_score:.2f}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error assessing compliance for {schema.schema_name}: {e}")
            raise
    
    async def _check_data_encryption(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        requirements: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check data encryption compliance"""
        violations = []
        
        try:
            if not requirements.get('requires_encryption', False):
                return violations
            
            # Check table-level encryption
            for table_classification in classifications.get('tables', []):
                if table_classification.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
                    if table_classification.encryption_recommendation.value == 'none':
                        violation = ComplianceViolation(
                            violation_id=str(uuid.uuid4()),
                            framework=framework,
                            rule_id='ENCRYPT_001',
                            rule_description='Sensitive tables must be encrypted',
                            violation_type='encryption',
                            severity=RiskLevel.HIGH,
                            affected_resources=[table_classification.target_name],
                            description=f"Table {table_classification.target_name} contains sensitive data but lacks encryption",
                            remediation_steps=[
                                'Enable table-level encryption',
                                'Implement field-level encryption for sensitive columns',
                                'Configure encryption key management'
                            ],
                            discovered_at=datetime.utcnow()
                        )
                        violations.append(violation)
            
            # Check column-level encryption
            for column_classification in classifications.get('columns', []):
                sensitive_types = column_classification.sensitive_data_types
                if any(stype in ['SSN', 'Credit Card', 'Medical', 'PII'] for stype in sensitive_types):
                    if column_classification.encryption_recommendation.value == 'none':
                        violation = ComplianceViolation(
                            violation_id=str(uuid.uuid4()),
                            framework=framework,
                            rule_id='ENCRYPT_002',
                            rule_description='Personally identifiable information must be encrypted',
                            violation_type='encryption',
                            severity=RiskLevel.CRITICAL,
                            affected_resources=[column_classification.target_name],
                            description=f"Column {column_classification.target_name} contains PII but lacks encryption",
                            remediation_steps=[
                                'Implement field-level encryption',
                                'Use strong encryption algorithms (AES-256)',
                                'Implement proper key rotation policies'
                            ],
                            discovered_at=datetime.utcnow()
                        )
                        violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking data encryption compliance: {e}")
            return violations
    
    async def _check_access_controls(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        requirements: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check access control compliance"""
        violations = []
        
        try:
            if not requirements.get('access_control_required', True):
                return violations
            
            # Check for proper access restrictions
            for classification in classifications.get('tables', []) + classifications.get('columns', []):
                if classification.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
                    if not classification.access_restrictions or len(classification.access_restrictions) < 2:
                        violation = ComplianceViolation(
                            violation_id=str(uuid.uuid4()),
                            framework=framework,
                            rule_id='ACCESS_001',
                            rule_description='Sensitive data must have proper access controls',
                            violation_type='access_control',
                            severity=RiskLevel.HIGH,
                            affected_resources=[classification.target_name],
                            description=f"{classification.target_type.title()} {classification.target_name} "
                                       f"lacks adequate access controls",
                            remediation_steps=[
                                'Implement role-based access control (RBAC)',
                                'Define user roles and permissions',
                                'Regular access review and audit',
                                'Implement principle of least privilege'
                            ],
                            discovered_at=datetime.utcnow()
                        )
                        violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking access control compliance: {e}")
            return violations
    
    async def _check_data_retention(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        requirements: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check data retention policy compliance"""
        violations = []
        
        try:
            retention_limit = requirements.get('data_retention_limit_days')
            if not retention_limit:
                return violations
            
            # Check for retention policies
            for classification in classifications.get('tables', []):
                if 'PII' in classification.sensitive_data_types:
                    if not classification.retention_policy:
                        violation = ComplianceViolation(
                            violation_id=str(uuid.uuid4()),
                            framework=framework,
                            rule_id='RETENTION_001',
                            rule_description='Personal data must have defined retention policy',
                            violation_type='data_retention',
                            severity=RiskLevel.MEDIUM,
                            affected_resources=[classification.target_name],
                            description=f"Table {classification.target_name} contains PII but lacks retention policy",
                            remediation_steps=[
                                f'Define data retention policy (max {retention_limit} days)',
                                'Implement automated data purging',
                                'Document retention justification',
                                'Regular compliance audits'
                            ],
                            discovered_at=datetime.utcnow()
                        )
                        violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking data retention compliance: {e}")
            return violations
    
    async def _check_audit_logging(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        requirements: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check audit logging compliance"""
        violations = []
        
        try:
            if not requirements.get('audit_logging_required', False):
                return violations
            
            # Check for audit logging on sensitive data
            sensitive_tables = []
            for classification in classifications.get('tables', []):
                if classification.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
                    if not classification.data_lineage_tracking:
                        sensitive_tables.append(classification.target_name)
            
            if sensitive_tables:
                violation = ComplianceViolation(
                    violation_id=str(uuid.uuid4()),
                    framework=framework,
                    rule_id='AUDIT_001',
                    rule_description='Sensitive data access must be logged and audited',
                    violation_type='audit_logging',
                    severity=RiskLevel.HIGH,
                    affected_resources=sensitive_tables,
                    description=f"Tables {', '.join(sensitive_tables)} lack proper audit logging",
                    remediation_steps=[
                        'Enable audit logging for data access',
                        'Implement data lineage tracking',
                        'Configure log retention policies',
                        'Regular audit log review'
                    ],
                    discovered_at=datetime.utcnow()
                )
                violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking audit logging compliance: {e}")
            return violations
    
    async def _check_data_minimization(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        requirements: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check data minimization compliance"""
        violations = []
        
        try:
            if not requirements.get('data_minimization_required', False):
                return violations
            
            # Analyze PII collection
            pii_columns = []
            for classification in classifications.get('columns', []):
                if 'PII' in classification.sensitive_data_types:
                    pii_columns.append(classification.target_name)
            
            # Check for excessive PII collection (heuristic)
            total_columns = sum(len(table.columns) for table in schema.tables)
            pii_ratio = len(pii_columns) / total_columns if total_columns > 0 else 0
            
            if pii_ratio > 0.3:  # More than 30% PII columns might indicate over-collection
                violation = ComplianceViolation(
                    violation_id=str(uuid.uuid4()),
                    framework=framework,
                    rule_id='MINIMIZE_001',
                    rule_description='Data collection should be minimized to what is necessary',
                    violation_type='data_minimization',
                    severity=RiskLevel.MEDIUM,
                    affected_resources=pii_columns[:10],  # Limit to first 10 for readability
                    description=f"Schema collects potentially excessive PII ({len(pii_columns)} columns, "
                               f"{pii_ratio:.1%} of total)",
                    remediation_steps=[
                        'Review necessity of each PII field',
                        'Remove unnecessary data collection',
                        'Implement data collection justification',
                        'Regular data inventory review'
                    ],
                    discovered_at=datetime.utcnow()
                )
                violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking data minimization compliance: {e}")
            return violations
    
    async def _check_consent_management(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        requirements: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check consent management compliance"""
        violations = []
        
        try:
            if not requirements.get('consent_required', False):
                return violations
            
            # Look for consent-related tables/columns
            consent_indicators = ['consent', 'agreement', 'opt_in', 'permission', 'authorization']
            has_consent_mechanism = False
            
            for table in schema.tables:
                table_name = table.table_name.lower()
                if any(indicator in table_name for indicator in consent_indicators):
                    has_consent_mechanism = True
                    break
                
                for column in table.columns:
                    column_name = column.column_name.lower()
                    if any(indicator in column_name for indicator in consent_indicators):
                        has_consent_mechanism = True
                        break
                
                if has_consent_mechanism:
                    break
            
            # Check if PII is collected without consent mechanism
            has_pii = any('PII' in classification.sensitive_data_types 
                         for classification in classifications.get('columns', []))
            
            if has_pii and not has_consent_mechanism:
                violation = ComplianceViolation(
                    violation_id=str(uuid.uuid4()),
                    framework=framework,
                    rule_id='CONSENT_001',
                    rule_description='PII collection requires user consent management',
                    violation_type='consent_management',
                    severity=RiskLevel.HIGH,
                    affected_resources=[schema.schema_name],
                    description="Schema collects PII but lacks visible consent management mechanism",
                    remediation_steps=[
                        'Implement consent collection and storage',
                        'Add consent tracking tables/columns',
                        'Implement opt-out mechanisms',
                        'Document consent processes'
                    ],
                    discovered_at=datetime.utcnow()
                )
                violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking consent management compliance: {e}")
            return violations
    
    async def _check_breach_notification(
        self,
        schema: SchemaResponse,
        classifications: Dict[str, List[DataClassification]],
        framework: ComplianceFramework,
        requirements: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check breach notification compliance"""
        violations = []
        
        try:
            if not requirements.get('breach_notification_required', False):
                return violations
            
            # Check for incident tracking capabilities
            incident_indicators = ['incident', 'breach', 'security_event', 'violation', 'audit_log']
            has_incident_tracking = False
            
            for table in schema.tables:
                table_name = table.table_name.lower()
                if any(indicator in table_name for indicator in incident_indicators):
                    has_incident_tracking = True
                    break
            
            # If schema handles sensitive data but lacks incident tracking
            has_sensitive_data = any(
                classification.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]
                for classification in classifications.get('tables', []) + classifications.get('columns', [])
            )
            
            if has_sensitive_data and not has_incident_tracking:
                violation = ComplianceViolation(
                    violation_id=str(uuid.uuid4()),
                    framework=framework,
                    rule_id='BREACH_001',
                    rule_description='Systems handling sensitive data must have breach detection and notification capabilities',
                    violation_type='breach_notification',
                    severity=RiskLevel.MEDIUM,
                    affected_resources=[schema.schema_name],
                    description="Schema handles sensitive data but lacks visible incident tracking mechanism",
                    remediation_steps=[
                        'Implement security incident logging',
                        'Add breach detection mechanisms',
                        'Create notification procedures',
                        'Regular security monitoring'
                    ],
                    discovered_at=datetime.utcnow()
                )
                violations.append(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking breach notification compliance: {e}")
            return violations
    
    def _load_compliance_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load compliance rules for different frameworks"""
        return {
            'gdpr': {
                'data_protection_by_design': True,
                'explicit_consent': True,
                'data_portability': True,
                'right_to_erasure': True,
                'breach_notification_72h': True
            },
            'hipaa': {
                'minimum_necessary': True,
                'access_control': True,
                'audit_controls': True,
                'integrity': True,
                'transmission_security': True
            },
            'pci_dss': {
                'protect_cardholder_data': True,
                'encrypt_transmission': True,
                'maintain_secure_systems': True,
                'implement_access_control': True,
                'monitor_networks': True
            },
            'sox': {
                'accurate_records': True,
                'internal_controls': True,
                'audit_trail': True,
                'segregation_of_duties': True
            }
        }
    
    def _load_framework_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Load specific requirements for each framework"""
        return {
            'gdpr': {
                'requires_encryption': True,
                'data_retention_limit_days': 2555,  # 7 years
                'consent_required': True,
                'data_minimization_required': True,
                'breach_notification_required': True,
                'audit_logging_required': True,
                'access_control_required': True
            },
            'hipaa': {
                'requires_encryption': True,
                'audit_logging_required': True,
                'access_control_required': True,
                'breach_notification_required': True,
                'minimum_necessary': True
            },
            'pci_dss': {
                'requires_encryption': True,
                'access_control_required': True,
                'audit_logging_required': True,
                'network_segmentation': True,
                'vulnerability_scanning': True
            },
            'sox': {
                'audit_logging_required': True,
                'access_control_required': True,
                'data_integrity': True,
                'segregation_of_duties': True
            },
            'ccpa': {
                'consent_required': True,
                'data_minimization_required': True,
                'right_to_delete': True,
                'audit_logging_required': True
            }
        }
    
    def _get_all_compliance_checks(self, framework: ComplianceFramework) -> List[str]:
        """Get list of all compliance checks for framework"""
        checks = [
            'data_encryption',
            'access_controls',
            'audit_logging'
        ]
        
        # Add framework-specific checks
        if framework in [ComplianceFramework.GDPR, ComplianceFramework.CCPA]:
            checks.extend(['data_retention', 'data_minimization', 'consent_management'])
        
        if framework in [ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS]:
            checks.append('breach_notification')
        
        return checks
    
    def _generate_recommendations(
        self,
        violations: List[ComplianceViolation],
        framework: ComplianceFramework
    ) -> List[str]:
        """Generate compliance recommendations based on violations"""
        recommendations = []
        
        violation_types = {v.violation_type for v in violations}
        
        if 'encryption' in violation_types:
            recommendations.append("Implement comprehensive encryption strategy for sensitive data")
        
        if 'access_control' in violation_types:
            recommendations.append("Establish role-based access control (RBAC) system")
        
        if 'audit_logging' in violation_types:
            recommendations.append("Deploy comprehensive audit logging and monitoring")
        
        if 'data_retention' in violation_types:
            recommendations.append("Define and implement data retention and purging policies")
        
        if 'consent_management' in violation_types:
            recommendations.append("Implement user consent collection and management system")
        
        # Framework-specific recommendations
        if framework == ComplianceFramework.GDPR:
            recommendations.append("Conduct Data Protection Impact Assessment (DPIA)")
            recommendations.append("Appoint Data Protection Officer (DPO) if required")
        
        if framework == ComplianceFramework.HIPAA:
            recommendations.append("Conduct security risk assessment")
            recommendations.append("Implement Business Associate Agreements (BAAs)")
        
        if framework == ComplianceFramework.PCI_DSS:
            recommendations.append("Implement network segmentation for cardholder data")
            recommendations.append("Regular vulnerability scanning and penetration testing")
        
        return recommendations
    
    def _determine_compliance_status(
        self,
        overall_score: float,
        violations: List[ComplianceViolation]
    ) -> str:
        """Determine overall compliance status"""
        critical_violations = [v for v in violations if v.severity == RiskLevel.CRITICAL]
        high_violations = [v for v in violations if v.severity == RiskLevel.HIGH]
        
        if critical_violations:
            return 'non_compliant'
        elif high_violations or overall_score < 0.7:
            return 'partial'
        elif overall_score >= 0.95:
            return 'compliant'
        else:
            return 'partial'
    
    def _perform_risk_assessment(
        self,
        violations: List[ComplianceViolation],
        classifications: Dict[str, List[DataClassification]]
    ) -> Dict[str, Any]:
        """Perform risk assessment based on violations and classifications"""
        # Calculate risk scores
        risk_scores = {
            'critical': len([v for v in violations if v.severity == RiskLevel.CRITICAL]),
            'high': len([v for v in violations if v.severity == RiskLevel.HIGH]),
            'medium': len([v for v in violations if v.severity == RiskLevel.MEDIUM]),
            'low': len([v for v in violations if v.severity == RiskLevel.LOW])
        }
        
        # Calculate overall risk level
        if risk_scores['critical'] > 0:
            overall_risk = 'critical'
        elif risk_scores['high'] > 2:
            overall_risk = 'high'
        elif risk_scores['high'] > 0 or risk_scores['medium'] > 5:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        # Analyze sensitive data exposure
        sensitive_tables = len([c for c in classifications.get('tables', []) 
                              if c.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]])
        total_tables = len(classifications.get('tables', []))
        exposure_ratio = sensitive_tables / total_tables if total_tables > 0 else 0
        
        return {
            'overall_risk_level': overall_risk,
            'risk_score_breakdown': risk_scores,
            'sensitive_data_exposure': {
                'sensitive_tables': sensitive_tables,
                'total_tables': total_tables,
                'exposure_ratio': exposure_ratio
            },
            'top_risk_areas': [v.violation_type for v in violations[:5]],
            'remediation_priority': self._prioritize_remediation(violations)
        }
    
    def _prioritize_remediation(self, violations: List[ComplianceViolation]) -> List[Dict[str, Any]]:
        """Prioritize remediation efforts"""
        # Sort violations by severity and impact
        sorted_violations = sorted(violations, key=lambda v: (
            ['low', 'medium', 'high', 'critical'].index(v.severity.value),
            len(v.affected_resources)
        ), reverse=True)
        
        return [{
            'violation_id': v.violation_id,
            'violation_type': v.violation_type,
            'severity': v.severity.value,
            'affected_resources_count': len(v.affected_resources),
            'priority_score': (['low', 'medium', 'high', 'critical'].index(v.severity.value) + 1) * len(v.affected_resources)
        } for v in sorted_violations[:10]]
    
    def _calculate_next_assessment_date(
        self,
        framework: ComplianceFramework,
        overall_score: float
    ) -> datetime:
        """Calculate next compliance assessment date"""
        base_intervals = {
            ComplianceFramework.GDPR: 180,      # 6 months
            ComplianceFramework.HIPAA: 365,     # 1 year
            ComplianceFramework.PCI_DSS: 90,    # 3 months
            ComplianceFramework.SOX: 365,       # 1 year
            ComplianceFramework.CCPA: 180       # 6 months
        }
        
        base_days = base_intervals.get(framework, 180)
        
        # Adjust based on compliance score
        if overall_score < 0.7:
            base_days = base_days // 2  # More frequent if non-compliant
        elif overall_score > 0.95:
            base_days = int(base_days * 1.5)  # Less frequent if highly compliant
        
        return datetime.utcnow() + timedelta(days=base_days)
