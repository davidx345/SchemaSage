"""
Compliance Report Generator Core Logic.
Generates comprehensive compliance reports.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
from models.compliance_models import (
    ComplianceReportData, ExecutiveSummary, FrameworkScore, 
    Finding, ComplianceControl, RemediationRoadmap, RemediationPhase,
    ComplianceFramework, DatabaseType, Severity
)

class ReportGenerator:
    """
    Generates compliance reports.
    """

    def generate(self, db_type: DatabaseType, connection_string: str, frameworks: List[ComplianceFramework]) -> ComplianceReportData:
        """
        Generates a full compliance report.
        """
        # In a real system, this would aggregate data from EncryptionScanner and AccessAuditor
        # and potentially other sources.
        
        report_id = f"rpt_{datetime.now().strftime('%Y_%m_%d')}_{str(uuid4())[:6]}"
        
        return ComplianceReportData(
            report_id=report_id,
            generated_at=datetime.now(),
            database_name="production_db", # Extracted from connection string in real app
            frameworks_assessed=frameworks,
            overall_compliance_score=68,
            executive_summary=self._generate_executive_summary(),
            framework_scores=self._generate_framework_scores(frameworks),
            findings_by_severity=self._generate_findings(),
            compliance_controls=self._generate_controls(frameworks),
            remediation_roadmap=self._generate_roadmap(),
            auto_fix_sql=self._generate_auto_fix(),
            report_download_url=f"https://schemasage.com/reports/{report_id}.pdf",
            report_expires_at=datetime.now() + timedelta(days=30)
        )

    def _generate_executive_summary(self) -> ExecutiveSummary:
        return ExecutiveSummary(
            status="non_compliant",
            critical_findings=3,
            high_findings=5,
            medium_findings=8,
            low_findings=12,
            compliant_controls=42,
            total_controls_assessed=70,
            estimated_remediation_time_hours=48,
            estimated_cost=12500.0
        )

    def _generate_framework_scores(self, frameworks: List[ComplianceFramework]) -> Dict[str, FrameworkScore]:
        scores = {}
        for fw in frameworks:
            scores[fw.value] = FrameworkScore(
                score=70, # Mock score
                compliant_controls=15,
                total_controls=20,
                critical_gaps=2
            )
        return scores

    def _generate_findings(self) -> List[Dict[str, Any]]:
        return [
            {
                "severity": Severity.CRITICAL,
                "count": 3,
                "items": [
                    {"title": "Unencrypted PII", "description": "SSN column in users table is plain text"}
                ]
            },
            {
                "severity": Severity.HIGH,
                "count": 5,
                "items": [
                    {"title": "Excessive Privileges", "description": "Admin user has superuser role"}
                ]
            }
        ]

    def _generate_controls(self, frameworks: List[ComplianceFramework]) -> List[ComplianceControl]:
        controls = []
        if ComplianceFramework.GDPR in frameworks:
            controls.append(ComplianceControl(
                control_id="GDPR-Art32",
                status="failed",
                description="Encryption of personal data",
                remediation="Enable transparent data encryption"
            ))
        return controls

    def _generate_roadmap(self) -> RemediationRoadmap:
        return RemediationRoadmap(
            phase_1_critical=RemediationPhase(
                duration_days=3,
                tasks=["Encrypt PII", "Revoke Superuser"],
                estimated_cost=5000.0
            ),
            phase_2_high=RemediationPhase(
                duration_days=5,
                tasks=["Implement Audit Logging", "Rotate Keys"],
                estimated_cost=7500.0
            )
        )

    def _generate_auto_fix(self) -> List[str]:
        return [
            "-- Phase 1: Critical Fixes",
            "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
            "ALTER ROLE admin NOSUPERUSER;"
        ]
