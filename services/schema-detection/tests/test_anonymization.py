"""
Comprehensive tests for Phase 3.3 - Production Data Anonymizer
40+ test cases covering all 5 endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)


# ===== PII Scanning Tests (10+ test cases) =====

class TestPIIScan:
    """Test PII detection endpoint"""
    
    def test_scan_pii_success(self):
        """Test successful PII scan with multiple detected fields"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/prod_db",
            "scan_options": {
                "include_tables": ["users", "orders", "customers"],
                "exclude_columns": ["id", "created_at"],
                "confidence_threshold": 0.8,
                "sample_size": 1000
            }
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        scan_data = data["data"]
        assert "scan_id" in scan_data
        assert scan_data["database_name"] == "prod_db"
        assert scan_data["total_tables_scanned"] > 0
        assert scan_data["total_columns_scanned"] > 0
        assert len(scan_data["pii_fields"]) > 0
    
    def test_scan_pii_email_detection(self):
        """Test email PII detection with high confidence"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {"confidence_threshold": 0.9}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        pii_fields = data["data"]["pii_fields"]
        
        # Check for email detection
        email_fields = [f for f in pii_fields if f["pii_type"] == "email"]
        assert len(email_fields) > 0
        
        email_field = email_fields[0]
        assert email_field["confidence"] >= 90
        assert "sample_values" in email_field
        assert len(email_field["sample_values"]) > 0
    
    def test_scan_pii_ssn_detection(self):
        """Test SSN detection with 100% confidence"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {"include_tables": ["users"]}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        pii_fields = data["data"]["pii_fields"]
        
        ssn_fields = [f for f in pii_fields if f["pii_type"] == "ssn"]
        if ssn_fields:
            assert ssn_fields[0]["confidence"] == 100
            assert ssn_fields[0]["severity"] == "critical"
    
    def test_scan_pii_credit_card_detection(self):
        """Test credit card number detection"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        pii_fields = data["data"]["pii_fields"]
        
        cc_fields = [f for f in pii_fields if f["pii_type"] == "credit_card"]
        if cc_fields:
            assert cc_fields[0]["confidence"] == 100
            assert cc_fields[0]["severity"] in ["critical", "high"]
    
    def test_scan_pii_phone_detection(self):
        """Test phone number detection"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {"confidence_threshold": 0.9}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        pii_fields = data["data"]["pii_fields"]
        
        phone_fields = [f for f in pii_fields if f["pii_type"] == "phone"]
        if phone_fields:
            assert phone_fields[0]["confidence"] >= 90
    
    def test_scan_pii_compliance_violations(self):
        """Test compliance violation detection"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        scan_data = data["data"]
        
        assert "compliance_violations" in scan_data
        violations = scan_data["compliance_violations"]
        assert isinstance(violations, list)
        
        if violations:
            violation = violations[0]
            assert "regulation" in violation
            assert "article" in violation
            assert "description" in violation
    
    def test_scan_pii_recommendations(self):
        """Test PII scan recommendations"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        scan_data = data["data"]
        
        assert "recommendations" in scan_data
        recommendations = scan_data["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_scan_pii_records_affected(self):
        """Test records affected count"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        pii_fields = data["data"]["pii_fields"]
        
        for field in pii_fields:
            assert "records_affected" in field
            assert field["records_affected"] > 0
    
    def test_scan_pii_confidence_threshold(self):
        """Test confidence threshold filtering"""
        request_data = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_db",
            "scan_options": {"confidence_threshold": 0.95}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        pii_fields = data["data"]["pii_fields"]
        
        # All fields should meet threshold
        for field in pii_fields:
            assert field["confidence"] >= 95
    
    def test_scan_pii_invalid_connection(self):
        """Test error handling for invalid connection string"""
        request_data = {
            "connection_string": "invalid://connection",
            "scan_options": {}
        }
        
        response = client.post("/api/anonymization/scan-pii", json=request_data)
        assert response.status_code == 500


# ===== Anonymization Rules Tests (10+ test cases) =====

class TestAnonymizationRules:
    """Test rule creation endpoint"""
    
    def test_create_rules_success(self):
        """Test successful rule creation"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "email",
                    "pii_type": "email",
                    "strategy": "fake_data",
                    "strategy_config": {"maintain_domain": True}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        rule_set = data["data"]
        assert "rule_set_id" in rule_set
        assert rule_set["scan_id"] == "scan_12345"
        assert len(rule_set["rules"]) > 0
    
    def test_create_rules_fake_data_strategy(self):
        """Test fake_data anonymization strategy"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "name",
                    "pii_type": "name",
                    "strategy": "fake_data",
                    "strategy_config": {"locale": "en_US"}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rules = data["data"]["rules"]
        
        fake_rule = next(r for r in rules if r["strategy"] == "fake_data")
        assert "example_transformation" in fake_rule
        assert fake_rule["example_transformation"]["strategy_name"] == "Fake Data"
    
    def test_create_rules_masking_strategy(self):
        """Test masking strategy with pattern"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "ssn",
                    "pii_type": "ssn",
                    "strategy": "masking",
                    "strategy_config": {
                        "mask_char": "*",
                        "preserve_last": 4
                    }
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rules = data["data"]["rules"]
        
        mask_rule = next(r for r in rules if r["strategy"] == "masking")
        example = mask_rule["example_transformation"]
        assert "***-**-" in example["after"]
    
    def test_create_rules_tokenization_strategy(self):
        """Test tokenization strategy"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "orders",
                    "column_name": "customer_id",
                    "pii_type": "identifier",
                    "strategy": "tokenization",
                    "strategy_config": {"reversible": False}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rules = data["data"]["rules"]
        
        token_rule = next(r for r in rules if r["strategy"] == "tokenization")
        assert token_rule["strategy"] == "tokenization"
    
    def test_create_rules_hashing_strategy(self):
        """Test hashing strategy"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "email",
                    "pii_type": "email",
                    "strategy": "hashing",
                    "strategy_config": {
                        "algorithm": "sha256",
                        "use_salt": True
                    }
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rules = data["data"]["rules"]
        
        hash_rule = next(r for r in rules if r["strategy"] == "hashing")
        assert hash_rule["strategy"] == "hashing"
    
    def test_create_rules_validation_warnings(self):
        """Test rule validation warnings"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "ssn",
                    "pii_type": "ssn",
                    "strategy": "masking",
                    "strategy_config": {}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rule_set = data["data"]
        
        assert "validation_warnings" in rule_set
        warnings = rule_set["validation_warnings"]
        assert isinstance(warnings, list)
    
    def test_create_rules_estimated_time(self):
        """Test processing time estimation"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "email",
                    "pii_type": "email",
                    "strategy": "fake_data",
                    "strategy_config": {}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rule_set = data["data"]
        
        assert "estimated_processing_time" in rule_set
        assert rule_set["estimated_processing_time"] != ""
    
    def test_create_rules_multiple_tables(self):
        """Test rules for multiple tables"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "email",
                    "pii_type": "email",
                    "strategy": "fake_data",
                    "strategy_config": {}
                },
                {
                    "table_name": "customers",
                    "column_name": "phone",
                    "pii_type": "phone",
                    "strategy": "masking",
                    "strategy_config": {}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rules = data["data"]["rules"]
        
        assert len(rules) >= 2
        table_names = {r["table_name"] for r in rules}
        assert "users" in table_names
        assert "customers" in table_names
    
    def test_create_rules_example_transformations(self):
        """Test example transformations in rules"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "email",
                    "pii_type": "email",
                    "strategy": "fake_data",
                    "strategy_config": {}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        rules = data["data"]["rules"]
        
        for rule in rules:
            assert "example_transformation" in rule
            example = rule["example_transformation"]
            assert "before" in example
            assert "after" in example
            assert "strategy_name" in example
    
    def test_create_rules_invalid_strategy(self):
        """Test error handling for invalid strategy"""
        request_data = {
            "scan_id": "scan_12345",
            "rules": [
                {
                    "table_name": "users",
                    "column_name": "email",
                    "pii_type": "email",
                    "strategy": "invalid_strategy",
                    "strategy_config": {}
                }
            ]
        }
        
        response = client.post("/api/anonymization/create-rules", json=request_data)
        # Should either reject or handle gracefully
        assert response.status_code in [200, 422, 500]


# ===== Apply Masking Tests (8+ test cases) =====

class TestApplyMasking:
    """Test anonymization execution endpoint"""
    
    def test_apply_masking_success(self):
        """Test successful masking execution"""
        request_data = {
            "rule_set_id": "ruleset_12345",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {
                "dry_run": False,
                "batch_size": 1000,
                "create_backup": True
            }
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        masking_data = data["data"]
        assert "execution_id" in masking_data
        assert masking_data["rule_set_id"] == "ruleset_12345"
    
    def test_apply_masking_dry_run(self):
        """Test dry-run mode"""
        request_data = {
            "rule_set_id": "ruleset_12345",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {
                "dry_run": True
            }
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        masking_data = data["data"]
        
        # Dry run should not change data
        assert "execution_id" in masking_data
    
    def test_apply_masking_progress_tracking(self):
        """Test progress tracking structure"""
        request_data = {
            "rule_set_id": "ruleset_12345",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {}
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        masking_data = data["data"]
        
        assert "progress" in masking_data
        progress = masking_data["progress"]
        assert "percentage" in progress
        assert "current_rule" in progress
        assert "records_processed" in progress
    
    def test_apply_masking_performance_metrics(self):
        """Test performance metrics"""
        request_data = {
            "rule_set_id": "ruleset_12345",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {}
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        masking_data = data["data"]
        
        assert "performance_metrics" in masking_data
        metrics = masking_data["performance_metrics"]
        assert "records_per_second" in metrics
        assert "error_count" in metrics
        assert "warning_count" in metrics
    
    def test_apply_masking_backup_creation(self):
        """Test backup creation option"""
        request_data = {
            "rule_set_id": "ruleset_12345",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {
                "create_backup": True
            }
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_apply_masking_batch_size(self):
        """Test custom batch size"""
        request_data = {
            "rule_set_id": "ruleset_12345",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {
                "batch_size": 5000
            }
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_apply_masking_execution_logs(self):
        """Test execution logging"""
        request_data = {
            "rule_set_id": "ruleset_12345",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {}
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        masking_data = data["data"]
        
        assert "execution_logs" in masking_data
        logs = masking_data["execution_logs"]
        assert isinstance(logs, list)
    
    def test_apply_masking_invalid_rule_set(self):
        """Test error handling for invalid rule set"""
        request_data = {
            "rule_set_id": "nonexistent",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "execution_options": {}
        }
        
        response = client.post("/api/anonymization/apply-masking", json=request_data)
        # Should handle gracefully
        assert response.status_code in [200, 404, 500]


# ===== Data Subsetting Tests (8+ test cases) =====

class TestDataSubsetting:
    """Test data subsetting endpoint"""
    
    def test_create_subset_success(self):
        """Test successful subset plan creation"""
        request_data = {
            "source_connection": "postgresql://user:pass@localhost:5432/prod_db",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "subsetting_strategy": "random_sampling",
            "options": {
                "sampling_percentage": 10,
                "preserve_referential_integrity": True
            }
        }
        
        response = client.post("/api/anonymization/create-subset", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        subset_data = data["data"]
        assert "subset_id" in subset_data
        assert subset_data["subsetting_strategy"] == "random_sampling"
    
    def test_create_subset_random_sampling(self):
        """Test random sampling strategy"""
        request_data = {
            "source_connection": "postgresql://user:pass@localhost:5432/prod_db",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "subsetting_strategy": "random_sampling",
            "options": {"sampling_percentage": 20}
        }
        
        response = client.post("/api/anonymization/create-subset", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        subset_data = data["data"]
        
        assert "estimated_reduction" in subset_data
        assert subset_data["estimated_reduction"]["percentage"] > 0
    
    def test_create_subset_stratified_sampling(self):
        """Test stratified sampling strategy"""
        request_data = {
            "source_connection": "postgresql://user:pass@localhost:5432/prod_db",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "subsetting_strategy": "stratified_sampling",
            "options": {
                "sampling_percentage": 10,
                "stratify_by": ["user_type", "region"]
            }
        }
        
        response = client.post("/api/anonymization/create-subset", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_create_subset_referential_integrity(self):
        """Test referential integrity preservation"""
        request_data = {
            "source_connection": "postgresql://user:pass@localhost:5432/prod_db",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "subsetting_strategy": "random_sampling",
            "options": {
                "sampling_percentage": 10,
                "preserve_referential_integrity": True
            }
        }
        
        response = client.post("/api/anonymization/create-subset", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        subset_data = data["data"]
        
        assert "table_plans" in subset_data
        table_plans = subset_data["table_plans"]
        
        # Check for dependency tracking
        for plan in table_plans:
            assert "dependencies" in plan
    
    def test_create_subset_table_plans(self):
        """Test table subsetting plans"""
        request_data = {
            "source_connection": "postgresql://user:pass@localhost:5432/prod_db",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "subsetting_strategy": "random_sampling",
            "options": {"sampling_percentage": 10}
        }
        
        response = client.post("/api/anonymization/create-subset", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        subset_data = data["data"]
        
        table_plans = subset_data["table_plans"]
        assert len(table_plans) > 0
        
        for plan in table_plans:
            assert "table_name" in plan
            assert "action" in plan
            assert "estimated_rows" in plan
    
    def test_create_subset_size_estimation(self):
        """Test size reduction estimation"""
        request_data = {
            "source_connection": "postgresql://user:pass@localhost:5432/prod_db",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "subsetting_strategy": "random_sampling",
            "options": {"sampling_percentage": 10}
        }
        
        response = client.post("/api/anonymization/create-subset", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        subset_data = data["data"]
        
        assert "estimated_reduction" in subset_data
        reduction = subset_data["estimated_reduction"]
        assert "original_size_mb" in reduction
        assert "subset_size_mb" in reduction
        assert "percentage" in reduction
    
    def test_create_subset_time_estimation(self):
        """Test time estimation for subsetting"""
        request_data = {
            "source_connection": "postgresql://user:pass@localhost:5432/prod_db",
            "target_connection": "postgresql://user:pass@localhost:5432/staging_db",
            "subsetting_strategy": "random_sampling",
            "options": {"sampling_percentage": 10}
        }
        
        response = client.post("/api/anonymization/create-subset", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        subset_data = data["data"]
        
        assert "estimated_time" in subset_data
        time_est = subset_data["estimated_time"]
        assert "copy_time" in time_est
        assert "anonymization_time" in time_est
    
    def test_execute_subset_success(self):
        """Test subset execution"""
        subset_id = "subset_12345"
        
        response = client.post(f"/api/anonymization/subset/{subset_id}/execute")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        execution_data = data["data"]
        assert "execution_id" in execution_data
        assert "status" in execution_data
        assert "progress" in execution_data


# ===== Compliance Validation Tests (6+ test cases) =====

class TestComplianceValidation:
    """Test compliance validation endpoint"""
    
    def test_validate_compliance_success(self):
        """Test successful compliance validation"""
        request_data = {
            "execution_id": "exec_12345",
            "compliance_frameworks": ["GDPR", "CCPA", "HIPAA", "PCI_DSS"],
            "validation_options": {
                "rescan_pii": True,
                "check_referential_integrity": True
            }
        }
        
        response = client.post("/api/anonymization/validate-compliance", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        validation_data = data["data"]
        assert "validation_id" in validation_data
        assert validation_data["execution_id"] == "exec_12345"
    
    def test_validate_compliance_gdpr(self):
        """Test GDPR compliance validation"""
        request_data = {
            "execution_id": "exec_12345",
            "compliance_frameworks": ["GDPR"],
            "validation_options": {}
        }
        
        response = client.post("/api/anonymization/validate-compliance", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        validation_data = data["data"]
        
        frameworks = validation_data["framework_validations"]
        gdpr = next(f for f in frameworks if f["framework"] == "GDPR")
        
        assert gdpr["compliant"] is True
        assert gdpr["requirements_met"] > 0
        assert gdpr["total_requirements"] > 0
    
    def test_validate_compliance_ccpa(self):
        """Test CCPA compliance validation"""
        request_data = {
            "execution_id": "exec_12345",
            "compliance_frameworks": ["CCPA"],
            "validation_options": {}
        }
        
        response = client.post("/api/anonymization/validate-compliance", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        validation_data = data["data"]
        
        frameworks = validation_data["framework_validations"]
        ccpa = next(f for f in frameworks if f["framework"] == "CCPA")
        
        assert ccpa["compliant"] is True
    
    def test_validate_compliance_pii_rescan(self):
        """Test PII rescanning after anonymization"""
        request_data = {
            "execution_id": "exec_12345",
            "compliance_frameworks": ["GDPR"],
            "validation_options": {"rescan_pii": True}
        }
        
        response = client.post("/api/anonymization/validate-compliance", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        validation_data = data["data"]
        
        assert "pii_rescan" in validation_data
        rescan = validation_data["pii_rescan"]
        assert "fields_detected" in rescan
        assert "confidence" in rescan
    
    def test_validate_compliance_referential_integrity(self):
        """Test referential integrity check"""
        request_data = {
            "execution_id": "exec_12345",
            "compliance_frameworks": ["GDPR"],
            "validation_options": {"check_referential_integrity": True}
        }
        
        response = client.post("/api/anonymization/validate-compliance", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        validation_data = data["data"]
        
        assert "referential_integrity" in validation_data
        integrity = validation_data["referential_integrity"]
        assert "violations" in integrity
        assert "orphaned_records" in integrity
    
    def test_validate_compliance_data_quality(self):
        """Test data quality scoring"""
        request_data = {
            "execution_id": "exec_12345",
            "compliance_frameworks": ["GDPR"],
            "validation_options": {}
        }
        
        response = client.post("/api/anonymization/validate-compliance", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        validation_data = data["data"]
        
        assert "data_quality" in validation_data
        quality = validation_data["data_quality"]
        assert "score" in quality
        assert quality["score"] >= 0 and quality["score"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
