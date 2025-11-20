"""
Encryption Scanner Core Logic.
Detects unencrypted PII and generates fix recommendations.
"""
from typing import List, Dict, Any
from models.compliance_models import (
    DatabaseSchema, EncryptionIssue, EncryptionSummary, 
    CostEstimate, Severity, ComplianceFramework, EncryptionDetectionData
)

class EncryptionScanner:
    """
    Scans database schema for unencrypted PII and sensitive data.
    """

    def __init__(self):
        self.pii_keywords = {
            "email": ["email", "e-mail", "mail"],
            "ssn": ["ssn", "social_security", "socialsecurity"],
            "credit_card": ["credit_card", "card_number", "cc_number", "pan"],
            "phone": ["phone", "mobile", "cell"],
            "password": ["password", "passwd", "pwd", "secret"],
            "address": ["address", "street", "city", "zip", "postal"]
        }

    def scan(self, schema: DatabaseSchema, connection_string: str) -> EncryptionDetectionData:
        """
        Analyzes the schema to find unencrypted sensitive columns.
        """
        issues = []
        total_affected_records = 0 # In a real scenario, we'd query the DB for counts
        
        # Simulate record count for estimation
        simulated_record_count = 10000 

        for table in schema.tables:
            for column in table.columns:
                col_name = column.get("name", "").lower()
                col_type = column.get("type", "").lower()
                
                # Skip if already encrypted (heuristic)
                if "encrypted" in col_name or "bytea" in col_type or "blob" in col_type:
                    continue

                detected_type = self._detect_pii_type(col_name)
                if detected_type:
                    issue = self._create_issue(table.name, column.get("name"), col_type, detected_type)
                    issues.append(issue)
                    total_affected_records += simulated_record_count

        summary = self._generate_summary(issues, total_affected_records)
        auto_fix_sql = self._generate_auto_fix_sql(issues)

        return EncryptionDetectionData(
            issues=issues,
            summary=summary,
            auto_fix_available=True,
            auto_fix_sql=auto_fix_sql
        )

    def _detect_pii_type(self, col_name: str) -> str:
        """Check if column name matches PII keywords."""
        for pii_type, keywords in self.pii_keywords.items():
            if any(keyword in col_name for keyword in keywords):
                return pii_type
        return ""

    def _create_issue(self, table: str, col: str, dtype: str, pii_type: str) -> EncryptionIssue:
        """Creates an EncryptionIssue object."""
        frameworks = [ComplianceFramework.GDPR, ComplianceFramework.CCPA]
        if pii_type in ["ssn", "credit_card"]:
            frameworks.append(ComplianceFramework.PCI_DSS)
        if pii_type in ["ssn", "email", "phone"]:
            frameworks.append(ComplianceFramework.HIPAA)

        return EncryptionIssue(
            table=table,
            column=col,
            data_type=dtype,
            detected_pii_type=pii_type,
            sample_data="***", # Masked
            risk_level=Severity.CRITICAL if pii_type in ["ssn", "credit_card", "password"] else Severity.HIGH,
            compliance_impact=frameworks,
            recommendation=f"Encrypt column '{col}' using pgcrypto or similar extension."
        )

    def _generate_summary(self, issues: List[EncryptionIssue], total_records: int) -> EncryptionSummary:
        """Generates summary statistics."""
        critical = sum(1 for i in issues if i.risk_level == Severity.CRITICAL)
        high = sum(1 for i in issues if i.risk_level == Severity.HIGH)
        
        # Simple estimation logic
        fix_time = len(issues) * 2.5 # 2.5 hours per issue
        
        return EncryptionSummary(
            total_issues=len(issues),
            critical_issues=critical,
            high_issues=high,
            total_affected_records=total_records,
            compliance_frameworks_at_risk=[ComplianceFramework.GDPR, ComplianceFramework.CCPA, ComplianceFramework.HIPAA],
            estimated_fix_time_hours=fix_time,
            estimated_monthly_cost_increase=CostEstimate(
                min=10.0,
                max=100.0,
                recommended=50.0
            )
        )

    def _generate_auto_fix_sql(self, issues: List[EncryptionIssue]) -> List[str]:
        """Generates SQL to fix the issues."""
        sql = ["-- Enable pgcrypto extension", "CREATE EXTENSION IF NOT EXISTS pgcrypto;", ""]
        
        for issue in issues:
            sql.append(f"-- Encrypt {issue.column} column in {issue.table}")
            sql.append(f"ALTER TABLE {issue.table} ADD COLUMN {issue.column}_encrypted bytea;")
            sql.append(f"UPDATE {issue.table} SET {issue.column}_encrypted = pgp_sym_encrypt({issue.column}::text, current_setting('app.encryption_key'));")
            sql.append(f"ALTER TABLE {issue.table} DROP COLUMN {issue.column};")
            sql.append(f"ALTER TABLE {issue.table} RENAME COLUMN {issue.column}_encrypted TO {issue.column};")
            sql.append("")
            
        return sql
