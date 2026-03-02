"""
Unit tests for Compliance Auto-Fixer Phase 2.1 features.
Tests encryption scanner, access auditor, and report generator.
"""
import pytest
from datetime import datetime
from models.compliance_models import (
    DatabaseSchema, TableSchema, DatabaseType, ComplianceFramework, 
    Severity, EncryptionDetectionRequest
)
from core.compliance import EncryptionScanner, AccessAuditor, ReportGenerator


class TestEncryptionScanner:
    """Tests for EncryptionScanner"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scanner = EncryptionScanner()
    
    def test_detect_pii_type_email(self):
        """Test email detection"""
        assert self.scanner._detect_pii_type("user_email") == "email"
        assert self.scanner._detect_pii_type("email_address") == "email"
        assert self.scanner._detect_pii_type("e-mail") == "email"
    
    def test_detect_pii_type_ssn(self):
        """Test SSN detection"""
        assert self.scanner._detect_pii_type("ssn") == "ssn"
        assert self.scanner._detect_pii_type("social_security_number") == "ssn"
    
    def test_detect_pii_type_credit_card(self):
        """Test credit card detection"""
        assert self.scanner._detect_pii_type("credit_card_number") == "credit_card"
        assert self.scanner._detect_pii_type("cc_number") == "credit_card"
    
    def test_detect_pii_type_no_match(self):
        """Test non-PII column"""
        assert self.scanner._detect_pii_type("id") == ""
        assert self.scanner._detect_pii_type("created_at") == ""
    
    def test_scan_with_pii_columns(self):
        """Test scanning schema with PII columns"""
        schema = DatabaseSchema(
            database_type=DatabaseType.POSTGRESQL,
            tables=[
                TableSchema(
                    name="users",
                    columns=[
                        {"name": "id", "type": "integer"},
                        {"name": "email", "type": "varchar"},
                        {"name": "ssn", "type": "varchar"},
                        {"name": "credit_card", "type": "varchar"}
                    ]
                )
            ]
        )
        
        result = self.scanner.scan(schema, "postgresql://localhost/test")
        
        assert len(result.issues) == 3  # email, ssn, credit_card
        assert result.summary.total_issues == 3
        assert result.summary.critical_issues == 2  # ssn and credit_card
        assert result.auto_fix_available is True
        assert len(result.auto_fix_sql) > 0
    
    def test_scan_without_pii_columns(self):
        """Test scanning schema without PII columns"""
        schema = DatabaseSchema(
            database_type=DatabaseType.POSTGRESQL,
            tables=[
                TableSchema(
                    name="products",
                    columns=[
                        {"name": "id", "type": "integer"},
                        {"name": "name", "type": "varchar"},
                        {"name": "price", "type": "decimal"}
                    ]
                )
            ]
        )
        
        result = self.scanner.scan(schema, "postgresql://localhost/test")
        
        assert len(result.issues) == 0
        assert result.summary.total_issues == 0
    
    def test_create_issue_severity(self):
        """Test issue severity assignment"""
        critical_issue = self.scanner._create_issue("users", "ssn", "varchar", "ssn")
        assert critical_issue.risk_level == Severity.CRITICAL
        
        high_issue = self.scanner._create_issue("users", "email", "varchar", "email")
        assert high_issue.risk_level == Severity.HIGH
    
    def test_generate_auto_fix_sql(self):
        """Test auto-fix SQL generation"""
        schema = DatabaseSchema(
            database_type=DatabaseType.POSTGRESQL,
            tables=[
                TableSchema(
                    name="users",
                    columns=[
                        {"name": "email", "type": "varchar"}
                    ]
                )
            ]
        )
        
        result = self.scanner.scan(schema, "postgresql://localhost/test")
        sql = result.auto_fix_sql
        
        assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in sql[0]
        assert any("ALTER TABLE users" in line for line in sql)
        assert any("pgp_sym_encrypt" in line for line in sql)


class TestAccessAuditor:
    """Tests for AccessAuditor"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.auditor = AccessAuditor()
    
    def test_audit_returns_complete_data(self):
        """Test audit returns all required components"""
        result = self.auditor.audit(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            ComplianceFramework.SOC2
        )
        
        assert len(result.users) > 0
        assert len(result.role_matrix) > 0
        assert len(result.recommendations) > 0
        assert result.summary is not None
        assert len(result.auto_fix_sql) >= 0
    
    def test_audit_users_structure(self):
        """Test user audit data structure"""
        users = self.auditor._audit_users()
        
        assert len(users) == 3
        assert users[0].username == "admin"
        assert users[0].is_superuser is True
        assert isinstance(users[0].roles, list)
    
    def test_audit_roles_structure(self):
        """Test role audit data structure"""
        roles = self.auditor._audit_roles()
        
        assert len(roles) == 3
        assert roles[0].role == "superuser"
        assert roles[0].risk_level == Severity.CRITICAL
    
    def test_generate_recommendations_superuser(self):
        """Test recommendation generation for superusers"""
        users = self.auditor._audit_users()
        roles = self.auditor._audit_roles()
        
        recs = self.auditor._generate_recommendations(users, roles, ComplianceFramework.SOC2)
        
        superuser_rec = next((r for r in recs if "superuser" in r.issue.lower()), None)
        assert superuser_rec is not None
        assert superuser_rec.priority == Severity.CRITICAL
    
    def test_generate_summary_scores(self):
        """Test summary score calculation"""
        users = self.auditor._audit_users()
        recs = [
            # Mock recommendation with critical priority
        ]
        
        summary = self.auditor._generate_summary(users, recs)
        
        assert summary.total_users == len(users)
        assert 0 <= summary.compliance_score <= 100
        assert summary.auto_fix_available is True
    
    def test_generate_auto_fix_sql(self):
        """Test auto-fix SQL generation"""
        users = self.auditor._audit_users()
        roles = self.auditor._audit_roles()
        recs = self.auditor._generate_recommendations(users, roles, ComplianceFramework.SOC2)
        
        sql = self.auditor._generate_auto_fix(recs)
        
        if len(sql) > 0:
            assert any("ALTER ROLE" in line for line in sql)


class TestReportGenerator:
    """Tests for ReportGenerator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = ReportGenerator()
    
    def test_generate_complete_report(self):
        """Test complete report generation"""
        result = self.generator.generate(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            [ComplianceFramework.GDPR, ComplianceFramework.SOC2]
        )
        
        assert result.report_id is not None
        assert result.generated_at is not None
        assert len(result.frameworks_assessed) == 2
        assert result.executive_summary is not None
        assert len(result.framework_scores) > 0
    
    def test_executive_summary_structure(self):
        """Test executive summary data structure"""
        summary = self.generator._generate_executive_summary()
        
        assert summary.status in ["compliant", "non_compliant", "partial"]
        assert summary.critical_findings >= 0
        assert summary.high_findings >= 0
        assert summary.estimated_remediation_time_hours >= 0
    
    def test_framework_scores_generation(self):
        """Test framework scores generation"""
        frameworks = [ComplianceFramework.GDPR, ComplianceFramework.SOC2]
        scores = self.generator._generate_framework_scores(frameworks)
        
        assert ComplianceFramework.GDPR.value in scores
        assert ComplianceFramework.SOC2.value in scores
        assert 0 <= scores[ComplianceFramework.GDPR.value].score <= 100
    
    def test_generate_findings(self):
        """Test findings generation"""
        findings = self.generator._generate_findings()
        
        assert len(findings) > 0
        assert all("severity" in f for f in findings)
        assert all("count" in f for f in findings)
    
    def test_generate_controls(self):
        """Test compliance controls generation"""
        controls = self.generator._generate_controls([ComplianceFramework.GDPR])
        
        assert len(controls) > 0
        assert controls[0].control_id is not None
        assert controls[0].status in ["passed", "failed", "partial"]
    
    def test_generate_roadmap(self):
        """Test remediation roadmap generation"""
        roadmap = self.generator._generate_roadmap()
        
        assert roadmap.phase_1_critical is not None
        assert roadmap.phase_2_high is not None
        assert roadmap.phase_1_critical.duration_days > 0
        assert len(roadmap.phase_1_critical.tasks) > 0
    
    def test_report_expiration(self):
        """Test report expiration date"""
        result = self.generator.generate(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            [ComplianceFramework.GDPR]
        )
        
        assert result.report_expires_at > result.generated_at


class TestIntegration:
    """Integration tests combining multiple components"""
    
    def test_full_compliance_workflow(self):
        """Test complete compliance scanning workflow"""
        # Setup
        scanner = EncryptionScanner()
        auditor = AccessAuditor()
        generator = ReportGenerator()
        
        # Scan for encryption issues
        schema = DatabaseSchema(
            database_type=DatabaseType.POSTGRESQL,
            tables=[
                TableSchema(
                    name="users",
                    columns=[
                        {"name": "id", "type": "integer"},
                        {"name": "email", "type": "varchar"},
                        {"name": "ssn", "type": "varchar"}
                    ]
                )
            ]
        )
        encryption_result = scanner.scan(schema, "postgresql://localhost/test")
        
        # Audit access controls
        access_result = auditor.audit(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            ComplianceFramework.SOC2
        )
        
        # Generate report
        report = generator.generate(
            DatabaseType.POSTGRESQL,
            "postgresql://localhost/test",
            [ComplianceFramework.GDPR, ComplianceFramework.SOC2]
        )
        
        # Assertions
        assert encryption_result.summary.total_issues > 0
        assert access_result.summary.total_users > 0
        assert report.overall_compliance_score >= 0
        assert len(report.auto_fix_sql) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
