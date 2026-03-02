"""
Security Audit Router
Comprehensive security testing and vulnerability assessment for database schemas
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json
import uuid
import asyncio
import re
import hashlib
from enum import Enum

router = APIRouter(prefix="/security", tags=["security"])

# Enums
class AuditType(str, Enum):
    basic = "basic"
    comprehensive = "comprehensive"
    penetration = "penetration"

class SeverityLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"

class VulnerabilityType(str, Enum):
    sql_injection = "sql_injection"
    privilege_escalation = "privilege_escalation"
    data_exposure = "data_exposure"
    authentication_bypass = "authentication_bypass"
    encryption_validation = "encryption_validation"
    access_control = "access_control"
    input_validation = "input_validation"

# Models
class DatabaseConfig(BaseModel):
    type: str = Field(..., description="Database type: postgresql, mysql, mongodb, etc.")
    connection_string: str = Field(..., description="Database connection string")
    username: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None

class SecurityAuditRequest(BaseModel):
    schema: Dict[str, Any]
    database_config: Optional[DatabaseConfig] = None
    audit_type: AuditType = AuditType.comprehensive
    test_categories: List[VulnerabilityType] = Field(default_factory=lambda: [
        VulnerabilityType.sql_injection,
        VulnerabilityType.data_exposure,
        VulnerabilityType.access_control
    ])

class SecurityVulnerability(BaseModel):
    id: str
    type: VulnerabilityType
    severity: SeverityLevel
    table: str
    column: Optional[str] = None
    description: str
    exploit_example: Optional[str] = None
    remediation: str
    cve_references: List[str] = Field(default_factory=list)
    business_impact: str

class ComplianceStatus(BaseModel):
    framework: str
    status: str  # compliant, non_compliant, needs_review
    issues: List[str] = Field(default_factory=list)

class SecurityRecommendation(BaseModel):
    priority: SeverityLevel
    category: str
    description: str
    implementation_effort: str

class PenetrationTestResult(BaseModel):
    attempted_attacks: int
    successful_breaches: int
    privilege_escalations: int
    data_exfiltration_possible: bool

class SecurityAuditResult(BaseModel):
    id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    overall_score: float
    security_level: str
    vulnerabilities: List[SecurityVulnerability]
    compliance_status: Dict[str, ComplianceStatus]
    recommendations: List[SecurityRecommendation]
    penetration_test_results: Optional[PenetrationTestResult] = None

# Mock storage for audit results
AUDIT_RESULTS = {}
RUNNING_AUDITS = {}

class SecurityAuditor:
    """Core security auditing engine"""
    
    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_rules = self._load_compliance_rules()
    
    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """Load vulnerability detection patterns"""
        return {
            "sql_injection": {
                "patterns": [
                    r"CONCAT\s*\(",
                    r"UNION\s+SELECT",
                    r"--\s*$",
                    r"'\s*OR\s*'",
                    r";\s*DROP\s+TABLE"
                ],
                "risk_indicators": ["dynamic_sql", "user_input", "no_parameterization"]
            },
            "privilege_escalation": {
                "patterns": [
                    r"GRANT\s+ALL",
                    r"CREATE\s+USER",
                    r"ALTER\s+USER",
                    r"DEFINER\s*=\s*ROOT"
                ],
                "risk_indicators": ["excessive_privileges", "shared_accounts", "no_rbac"]
            },
            "data_exposure": {
                "sensitive_columns": [
                    "password", "ssn", "social_security", "credit_card", "email",
                    "phone", "address", "salary", "medical", "personal"
                ],
                "risk_indicators": ["no_encryption", "public_access", "logging_sensitive"]
            },
            "encryption_validation": {
                "encrypted_types": ["password", "ssn", "credit_card", "medical_record"],
                "encryption_indicators": ["encrypted", "hashed", "cipher"]
            }
        }
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance framework rules"""
        return {
            "GDPR": {
                "required_fields": ["data_subject_consent", "retention_period"],
                "encryption_required": ["personal_data", "sensitive_data"],
                "access_controls": ["data_processor_restrictions", "right_to_deletion"]
            },
            "SOX": {
                "audit_trails": ["financial_transactions", "access_logs"],
                "segregation_duties": ["approval_workflows", "dual_control"],
                "data_integrity": ["checksums", "version_control"]
            },
            "PCI_DSS": {
                "encryption_required": ["cardholder_data", "payment_info"],
                "access_controls": ["need_to_know", "unique_user_ids"],
                "monitoring": ["access_logs", "anomaly_detection"]
            },
            "HIPAA": {
                "encryption_required": ["phi", "medical_records"],
                "access_controls": ["minimum_necessary", "user_authentication"],
                "audit_trails": ["access_logs", "modification_logs"]
            }
        }
    
    async def analyze_schema_vulnerabilities(self, schema: Dict[str, Any]) -> List[SecurityVulnerability]:
        """Analyze schema for security vulnerabilities"""
        vulnerabilities = []
        tables = schema.get("tables", {})
        
        for table_name, table_config in tables.items():
            columns = table_config.get("columns", {})
            
            # Check for data exposure vulnerabilities
            for column_name, column_config in columns.items():
                column_type = column_config.get("type", "").lower()
                
                # Check for sensitive data without encryption
                if self._is_sensitive_column(column_name, column_type):
                    if not self._is_encrypted_column(column_config):
                        vulnerability = SecurityVulnerability(
                            id=f"vuln_{uuid.uuid4().hex[:8]}",
                            type=VulnerabilityType.data_exposure,
                            severity=SeverityLevel.high,
                            table=table_name,
                            column=column_name,
                            description=f"Sensitive column '{column_name}' is not encrypted",
                            exploit_example=f"SELECT {column_name} FROM {table_name}; -- Direct access to sensitive data",
                            remediation=f"Implement column-level encryption for {column_name}",
                            business_impact="Personal/sensitive data exposure violating privacy regulations"
                        )
                        vulnerabilities.append(vulnerability)
                
                # Check for SQL injection risks
                if column_type in ["text", "varchar", "string"] and not column_config.get("validated", False):
                    vulnerability = SecurityVulnerability(
                        id=f"vuln_{uuid.uuid4().hex[:8]}",
                        type=VulnerabilityType.sql_injection,
                        severity=SeverityLevel.high,
                        table=table_name,
                        column=column_name,
                        description=f"Text column '{column_name}' lacks input validation",
                        exploit_example=f"'; DROP TABLE {table_name}; --",
                        remediation="Implement parameterized queries and input validation",
                        cve_references=["CVE-2023-1234"],
                        business_impact="Complete database compromise possible through SQL injection"
                    )
                    vulnerabilities.append(vulnerability)
            
            # Check for access control issues
            table_permissions = table_config.get("permissions", {})
            if not table_permissions or table_permissions.get("public_read", False):
                vulnerability = SecurityVulnerability(
                    id=f"vuln_{uuid.uuid4().hex[:8]}",
                    type=VulnerabilityType.access_control,
                    severity=SeverityLevel.medium,
                    table=table_name,
                    description=f"Table '{table_name}' has overly permissive access controls",
                    remediation="Implement role-based access control (RBAC)",
                    business_impact="Unauthorized data access possible"
                )
                vulnerabilities.append(vulnerability)
        
        return vulnerabilities
    
    def _is_sensitive_column(self, column_name: str, column_type: str) -> bool:
        """Check if column contains sensitive data"""
        sensitive_patterns = self.vulnerability_patterns["data_exposure"]["sensitive_columns"]
        column_lower = column_name.lower()
        return any(pattern in column_lower for pattern in sensitive_patterns)
    
    def _is_encrypted_column(self, column_config: Dict[str, Any]) -> bool:
        """Check if column is encrypted"""
        encryption_indicators = self.vulnerability_patterns["encryption_validation"]["encryption_indicators"]
        
        # Check for encryption flags
        if column_config.get("encrypted", False):
            return True
        
        # Check column type or constraints for encryption indicators
        column_type = column_config.get("type", "").lower()
        constraints = column_config.get("constraints", [])
        
        return any(indicator in column_type for indicator in encryption_indicators) or \
               any(indicator in str(constraint).lower() for constraint in constraints 
                   for indicator in encryption_indicators)
    
    async def check_compliance_status(self, schema: Dict[str, Any], vulnerabilities: List[SecurityVulnerability]) -> Dict[str, ComplianceStatus]:
        """Check compliance status against various frameworks"""
        compliance_status = {}
        
        for framework, rules in self.compliance_rules.items():
            issues = []
            
            # Check for framework-specific requirements
            if framework == "GDPR":
                # Check for consent fields and data retention
                has_consent_mechanism = self._has_gdpr_consent_fields(schema)
                if not has_consent_mechanism:
                    issues.append("Missing user consent mechanism")
                
                # Check for encryption of personal data
                personal_data_encrypted = self._check_personal_data_encryption(schema, vulnerabilities)
                if not personal_data_encrypted:
                    issues.append("Personal data not properly encrypted")
            
            elif framework == "PCI_DSS":
                # Check for payment data encryption
                payment_data_encrypted = self._check_payment_data_encryption(schema, vulnerabilities)
                if not payment_data_encrypted:
                    issues.append("Payment card data not encrypted")
            
            elif framework == "HIPAA":
                # Check for medical data encryption
                medical_data_encrypted = self._check_medical_data_encryption(schema, vulnerabilities)
                if not medical_data_encrypted:
                    issues.append("Protected health information not encrypted")
            
            # Determine compliance status
            if not issues:
                status = "compliant"
            elif len(issues) <= 2:
                status = "needs_review"
            else:
                status = "non_compliant"
            
            compliance_status[framework] = ComplianceStatus(
                framework=framework,
                status=status,
                issues=issues
            )
        
        return compliance_status
    
    def _has_gdpr_consent_fields(self, schema: Dict[str, Any]) -> bool:
        """Check if schema has GDPR consent fields"""
        tables = schema.get("tables", {})
        consent_indicators = ["consent", "gdpr_consent", "data_processing_consent"]
        
        for table in tables.values():
            columns = table.get("columns", {})
            for column_name in columns.keys():
                if any(indicator in column_name.lower() for indicator in consent_indicators):
                    return True
        return False
    
    def _check_personal_data_encryption(self, schema: Dict[str, Any], vulnerabilities: List[SecurityVulnerability]) -> bool:
        """Check if personal data is encrypted"""
        data_exposure_vulns = [v for v in vulnerabilities if v.type == VulnerabilityType.data_exposure]
        return len(data_exposure_vulns) == 0
    
    def _check_payment_data_encryption(self, schema: Dict[str, Any], vulnerabilities: List[SecurityVulnerability]) -> bool:
        """Check if payment data is encrypted"""
        # Look for payment-related vulnerabilities
        payment_related_vulns = [
            v for v in vulnerabilities 
            if v.type == VulnerabilityType.data_exposure and 
            any(payment_term in (v.column or "").lower() 
                for payment_term in ["card", "payment", "credit", "cvv"])
        ]
        return len(payment_related_vulns) == 0
    
    def _check_medical_data_encryption(self, schema: Dict[str, Any], vulnerabilities: List[SecurityVulnerability]) -> bool:
        """Check if medical data is encrypted"""
        medical_related_vulns = [
            v for v in vulnerabilities 
            if v.type == VulnerabilityType.data_exposure and 
            any(medical_term in (v.column or "").lower() 
                for medical_term in ["medical", "health", "diagnosis", "treatment"])
        ]
        return len(medical_related_vulns) == 0
    
    async def generate_recommendations(self, vulnerabilities: List[SecurityVulnerability]) -> List[SecurityRecommendation]:
        """Generate security recommendations based on found vulnerabilities"""
        recommendations = []
        
        # Group vulnerabilities by type
        vuln_by_type = {}
        for vuln in vulnerabilities:
            if vuln.type not in vuln_by_type:
                vuln_by_type[vuln.type] = []
            vuln_by_type[vuln.type].append(vuln)
        
        # Generate type-specific recommendations
        if VulnerabilityType.data_exposure in vuln_by_type:
            recommendations.append(SecurityRecommendation(
                priority=SeverityLevel.critical,
                category="data_protection",
                description="Implement column-level encryption for sensitive data",
                implementation_effort="2-3 days"
            ))
        
        if VulnerabilityType.sql_injection in vuln_by_type:
            recommendations.append(SecurityRecommendation(
                priority=SeverityLevel.high,
                category="input_validation",
                description="Implement parameterized queries and input sanitization",
                implementation_effort="1-2 days"
            ))
        
        if VulnerabilityType.access_control in vuln_by_type:
            recommendations.append(SecurityRecommendation(
                priority=SeverityLevel.medium,
                category="access_control",
                description="Implement role-based access control (RBAC)",
                implementation_effort="3-5 days"
            ))
        
        # Always recommend security monitoring
        recommendations.append(SecurityRecommendation(
            priority=SeverityLevel.medium,
            category="monitoring",
            description="Implement security monitoring and alerting",
            implementation_effort="2-3 days"
        ))
        
        return recommendations
    
    async def simulate_penetration_test(self, schema: Dict[str, Any]) -> PenetrationTestResult:
        """Simulate penetration testing results"""
        tables = schema.get("tables", {})
        total_tables = len(tables)
        
        # Simulate attack attempts based on schema complexity
        attempted_attacks = min(50, total_tables * 5)
        
        # Calculate success rate based on vulnerabilities
        # More tables and columns = more attack surface
        total_columns = sum(len(table.get("columns", {})) for table in tables.values())
        success_rate = min(0.3, (total_columns / 100) * 0.1)  # Max 30% success rate
        
        successful_breaches = int(attempted_attacks * success_rate)
        privilege_escalations = max(0, successful_breaches - 2)
        
        # Data exfiltration possible if sensitive data found without encryption
        data_exfiltration_possible = any(
            self._is_sensitive_column(col_name, col_config.get("type", ""))
            for table in tables.values()
            for col_name, col_config in table.get("columns", {}).items()
        )
        
        return PenetrationTestResult(
            attempted_attacks=attempted_attacks,
            successful_breaches=successful_breaches,
            privilege_escalations=privilege_escalations,
            data_exfiltration_possible=data_exfiltration_possible
        )
    
    def calculate_security_score(self, vulnerabilities: List[SecurityVulnerability]) -> tuple[float, str]:
        """Calculate overall security score"""
        if not vulnerabilities:
            return 10.0, "excellent"
        
        # Weight vulnerabilities by severity
        severity_weights = {
            SeverityLevel.critical: 4.0,
            SeverityLevel.high: 2.0,
            SeverityLevel.medium: 1.0,
            SeverityLevel.low: 0.5,
            SeverityLevel.info: 0.1
        }
        
        total_score_reduction = sum(severity_weights.get(vuln.severity, 1.0) for vuln in vulnerabilities)
        security_score = max(0.0, 10.0 - total_score_reduction)
        
        # Determine security level
        if security_score >= 9.0:
            level = "excellent"
        elif security_score >= 7.0:
            level = "good"
        elif security_score >= 5.0:
            level = "moderate"
        elif security_score >= 3.0:
            level = "poor"
        else:
            level = "critical"
        
        return security_score, level

# Global auditor instance
auditor = SecurityAuditor()

async def run_security_audit(audit_id: str, request: SecurityAuditRequest):
    """Run security audit in background"""
    try:
        RUNNING_AUDITS[audit_id] = {
            "status": "running",
            "started_at": datetime.now(),
            "progress": 0
        }
        
        # Simulate audit progress
        await asyncio.sleep(1)
        RUNNING_AUDITS[audit_id]["progress"] = 25
        
        # Analyze vulnerabilities
        vulnerabilities = await auditor.analyze_schema_vulnerabilities(request.schema)
        await asyncio.sleep(1)
        RUNNING_AUDITS[audit_id]["progress"] = 50
        
        # Check compliance
        compliance_status = await auditor.check_compliance_status(request.schema, vulnerabilities)
        await asyncio.sleep(1)
        RUNNING_AUDITS[audit_id]["progress"] = 75
        
        # Generate recommendations
        recommendations = await auditor.generate_recommendations(vulnerabilities)
        
        # Run penetration test if requested
        penetration_results = None
        if request.audit_type == AuditType.penetration:
            penetration_results = await auditor.simulate_penetration_test(request.schema)
        
        await asyncio.sleep(1)
        RUNNING_AUDITS[audit_id]["progress"] = 100
        
        # Calculate security score
        security_score, security_level = auditor.calculate_security_score(vulnerabilities)
        
        # Create final result
        result = SecurityAuditResult(
            id=audit_id,
            status="completed",
            started_at=RUNNING_AUDITS[audit_id]["started_at"],
            completed_at=datetime.now(),
            overall_score=security_score,
            security_level=security_level,
            vulnerabilities=vulnerabilities,
            compliance_status=compliance_status,
            recommendations=recommendations,
            penetration_test_results=penetration_results
        )
        
        # Store result
        AUDIT_RESULTS[audit_id] = result
        
        # Clean up running audit
        if audit_id in RUNNING_AUDITS:
            del RUNNING_AUDITS[audit_id]
    
    except Exception as e:
        # Handle audit failure
        RUNNING_AUDITS[audit_id] = {
            "status": "failed",
            "error": str(e),
            "started_at": RUNNING_AUDITS[audit_id]["started_at"],
            "completed_at": datetime.now()
        }

@router.post("/audit")
async def start_security_audit(
    request: SecurityAuditRequest,
    background_tasks: BackgroundTasks
):
    """Start comprehensive security audit"""
    try:
        audit_id = f"audit_{uuid.uuid4().hex[:16]}"
        
        # Start audit in background
        background_tasks.add_task(run_security_audit, audit_id, request)
        
        return {
            "success": True,
            "data": {
                "audit_id": audit_id,
                "status": "running",
                "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start security audit: {str(e)}")

@router.get("/audit/{audit_id}")
async def get_audit_results(audit_id: str):
    """Get security audit results"""
    try:
        # Check if audit is still running
        if audit_id in RUNNING_AUDITS:
            running_audit = RUNNING_AUDITS[audit_id]
            return {
                "success": True,
                "data": {
                    "audit": {
                        "id": audit_id,
                        "status": running_audit["status"],
                        "progress": running_audit.get("progress", 0),
                        "started_at": running_audit["started_at"].isoformat(),
                        "error": running_audit.get("error")
                    }
                }
            }
        
        # Check if audit is completed
        if audit_id in AUDIT_RESULTS:
            result = AUDIT_RESULTS[audit_id]
            return {
                "success": True,
                "data": {
                    "audit": {
                        "id": result.id,
                        "status": result.status,
                        "started_at": result.started_at.isoformat(),
                        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                        "overall_score": result.overall_score,
                        "security_level": result.security_level,
                        "vulnerabilities": [vuln.dict() for vuln in result.vulnerabilities],
                        "compliance_status": {k: v.dict() for k, v in result.compliance_status.items()},
                        "recommendations": [rec.dict() for rec in result.recommendations],
                        "penetration_test_results": result.penetration_test_results.dict() if result.penetration_test_results else None
                    }
                }
            }
        
        raise HTTPException(status_code=404, detail="Audit not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit results: {str(e)}")

@router.post("/quick-scan")
async def quick_security_scan(schema: Dict[str, Any]):
    """Perform quick security scan without full audit"""
    try:
        # Run quick vulnerability analysis
        vulnerabilities = await auditor.analyze_schema_vulnerabilities(schema)
        
        # Calculate security score
        security_score, security_level = auditor.calculate_security_score(vulnerabilities)
        
        # Generate basic recommendations
        recommendations = await auditor.generate_recommendations(vulnerabilities)
        
        return {
            "success": True,
            "data": {
                "security_score": security_score,
                "security_level": security_level,
                "vulnerability_count": len(vulnerabilities),
                "critical_vulnerabilities": len([v for v in vulnerabilities if v.severity == SeverityLevel.critical]),
                "high_vulnerabilities": len([v for v in vulnerabilities if v.severity == SeverityLevel.high]),
                "recommendations_count": len(recommendations),
                "scan_completed_at": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform quick scan: {str(e)}")

@router.get("/vulnerability-database")
async def get_vulnerability_database():
    """Get vulnerability patterns and detection rules"""
    try:
        return {
            "success": True,
            "data": {
                "patterns": auditor.vulnerability_patterns,
                "compliance_rules": auditor.compliance_rules,
                "supported_frameworks": list(auditor.compliance_rules.keys()),
                "vulnerability_types": [v.value for v in VulnerabilityType],
                "severity_levels": [s.value for s in SeverityLevel]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vulnerability database: {str(e)}")

@router.get("/audit-history")
async def get_audit_history(limit: int = 20):
    """Get security audit history"""
    try:
        # Get completed audits
        completed_audits = list(AUDIT_RESULTS.values())
        completed_audits.sort(key=lambda x: x.started_at, reverse=True)
        
        # Limit results
        limited_audits = completed_audits[:limit]
        
        # Create summary data
        audit_summaries = []
        for audit in limited_audits:
            audit_summaries.append({
                "id": audit.id,
                "started_at": audit.started_at.isoformat(),
                "completed_at": audit.completed_at.isoformat() if audit.completed_at else None,
                "security_score": audit.overall_score,
                "security_level": audit.security_level,
                "vulnerability_count": len(audit.vulnerabilities),
                "critical_vulnerabilities": len([v for v in audit.vulnerabilities if v.severity == SeverityLevel.critical])
            })
        
        return {
            "success": True,
            "data": {
                "audits": audit_summaries,
                "total_audits": len(AUDIT_RESULTS),
                "running_audits": len(RUNNING_AUDITS)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit history: {str(e)}")
