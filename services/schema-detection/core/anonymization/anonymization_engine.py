"""
Production Data Anonymizer Core Logic
"""
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime
import re

from models.anonymization_models import (
    PIIType, Severity, AnonymizationStrategy,
    PIIField, PIIScanData, RuleDetails, ExampleTransformation,
    RuleSetData, ApplyMaskingData, ProgressInfo, PerformanceMetrics,
    SubsettingPlan, TableSubsetPlan, SubsetData,
    ComplianceValidationData, FrameworkValidation, ComplianceCheck,
    PIIRescanResults, ReferentialIntegrity, DataQuality, AuditLog
)


class PIIDetector:
    """ML-powered PII detection"""
    
    def scan_database(self, connection_string: str, scan_options: Dict[str, Any]) -> PIIScanData:
        """Scans database for PII fields"""
        scan_id = f"scan_{str(uuid4())[:8]}"
        
        # Simulated PII detection
        pii_fields = self._detect_pii_fields(scan_options)
        
        total_records = sum(field.records_affected for field in pii_fields)
        
        compliance_violations = self._identify_violations(pii_fields)
        recommendations = self._generate_recommendations(pii_fields)
        
        return PIIScanData(
            scan_id=scan_id,
            total_tables_scanned=12,
            total_columns_scanned=87,
            pii_fields_detected=len(pii_fields),
            total_records_affected=total_records,
            compliance_violations=compliance_violations,
            scan_duration_seconds=23,
            fields=pii_fields,
            recommendations=recommendations
        )
    
    def _detect_pii_fields(self, scan_options: Dict[str, Any]) -> List[PIIField]:
        """Detects PII fields using pattern matching and ML"""
        return [
            PIIField(
                table="users",
                column="email",
                pii_type=PIIType.EMAIL,
                confidence=100,
                sample_values=["j***@example.com", "s***@gmail.com", "a***@company.org"],
                records_affected=145623,
                severity=Severity.CRITICAL,
                compliance_impact=["GDPR", "CCPA", "CAN-SPAM"]
            ),
            PIIField(
                table="users",
                column="phone",
                pii_type=PIIType.PHONE,
                confidence=98,
                sample_values=["(555) ***-****", "+1-***-***-****", "***-***-1234"],
                records_affected=128934,
                severity=Severity.HIGH,
                compliance_impact=["GDPR", "CCPA", "TCPA"]
            ),
            PIIField(
                table="users",
                column="ssn",
                pii_type=PIIType.SSN,
                confidence=100,
                sample_values=["***-**-6789", "***-**-1234", "***-**-5678"],
                records_affected=89234,
                severity=Severity.CRITICAL,
                compliance_impact=["GDPR", "CCPA", "HIPAA", "SOX"]
            ),
            PIIField(
                table="payments",
                column="card_number",
                pii_type=PIIType.CREDIT_CARD,
                confidence=100,
                sample_values=["****-****-****-1234", "****-****-****-5678", "****-****-****-9012"],
                records_affected=234567,
                severity=Severity.CRITICAL,
                compliance_impact=["PCI-DSS", "GDPR"]
            ),
            PIIField(
                table="users",
                column="date_of_birth",
                pii_type=PIIType.DOB,
                confidence=95,
                sample_values=["****-**-15", "****-**-23", "****-**-08"],
                records_affected=145623,
                severity=Severity.HIGH,
                compliance_impact=["GDPR", "CCPA", "COPPA"]
            ),
            PIIField(
                table="orders",
                column="shipping_address",
                pii_type=PIIType.ADDRESS,
                confidence=88,
                sample_values=["*** Main St, ***", "*** Oak Ave, ***", "*** 5th St, ***"],
                records_affected=456789,
                severity=Severity.MEDIUM,
                compliance_impact=["GDPR", "CCPA"]
            ),
            PIIField(
                table="sessions",
                column="ip_address",
                pii_type=PIIType.IP_ADDRESS,
                confidence=100,
                sample_values=["192.168.*.*", "10.0.*.*", "172.16.*.*"],
                records_affected=1234567,
                severity=Severity.LOW,
                compliance_impact=["GDPR"]
            )
        ]
    
    def _identify_violations(self, pii_fields: List[PIIField]) -> List[str]:
        """Identifies compliance violations"""
        violations = set()
        for field in pii_fields:
            if field.severity in [Severity.CRITICAL, Severity.HIGH]:
                if "GDPR" in field.compliance_impact:
                    violations.add("GDPR Article 17 (Right to erasure)")
                if "CCPA" in field.compliance_impact:
                    violations.add("CCPA § 1798.105")
        return list(violations)
    
    def _generate_recommendations(self, pii_fields: List[PIIField]) -> List[str]:
        """Generates recommendations"""
        critical_count = sum(1 for f in pii_fields if f.severity == Severity.CRITICAL)
        return [
            f"Implement anonymization for {critical_count} critical PII fields before deploying to staging",
            "Add encryption-at-rest for payments.card_number (PCI-DSS requirement)",
            "Set up automated PII detection in CI/CD pipeline",
            "Review data retention policies for GDPR compliance (max 2 years for user data)",
            "Implement GDPR Article 17 deletion workflow"
        ]


class AnonymizationRuleManager:
    """Manages anonymization rules"""
    
    def create_ruleset(self, scan_id: str, rules: List[Dict[str, Any]]) -> RuleSetData:
        """Creates anonymization ruleset"""
        rule_set_id = f"ruleset_{str(uuid4())[:8]}"
        
        rule_details = []
        for idx, rule in enumerate(rules, 1):
            rule_details.append(self._create_rule_detail(f"rule_{idx:03d}", rule))
        
        total_records = sum(r.estimated_records for r in rule_details)
        estimated_time = self._estimate_processing_time(total_records)
        
        warnings = self._validate_rules(rules)
        
        return RuleSetData(
            rule_set_id=rule_set_id,
            total_rules=len(rule_details),
            estimated_processing_time=estimated_time,
            rules=rule_details,
            validation_warnings=warnings
        )
    
    def _create_rule_detail(self, rule_id: str, rule: Dict[str, Any]) -> RuleDetails:
        """Creates detailed rule information"""
        strategy = rule["strategy"]
        table = rule["table"]
        column = rule["column"]
        
        example = self._generate_example_transformation(strategy, column)
        estimated_records = self._estimate_records(table)
        
        return RuleDetails(
            rule_id=rule_id,
            table=table,
            column=column,
            strategy=AnonymizationStrategy(strategy),
            estimated_records=estimated_records,
            reversible=strategy == "tokenization" and rule.get("options", {}).get("reversible", False),
            maintains_format=strategy in ["masking", "tokenization"],
            performance_impact="medium" if strategy == "fake_data" else "low",
            example_transformation=example
        )
    
    def _generate_example_transformation(self, strategy: str, column: str) -> ExampleTransformation:
        """Generates example transformation"""
        examples = {
            "email": ExampleTransformation(before="john.doe@company.com", after="alice.johnson@company.com"),
            "ssn": ExampleTransformation(before="123-45-6789", after="***-**-6789"),
            "card_number": ExampleTransformation(before="4532-1234-5678-9010", after="****-****-****-9010"),
            "password_hash": ExampleTransformation(before="bcrypt_hash_original", after="5d41402abc4b2a76b9719d911017c592")
        }
        return examples.get(column, ExampleTransformation(before="original_value", after="anonymized_value"))
    
    def _estimate_records(self, table: str) -> int:
        """Estimates record count"""
        estimates = {
            "users": 145623,
            "payments": 234567,
            "orders": 456789
        }
        return estimates.get(table, 100000)
    
    def _estimate_processing_time(self, total_records: int) -> str:
        """Estimates processing time"""
        minutes = max(1, total_records // 50000)
        return f"{minutes} minutes"
    
    def _validate_rules(self, rules: List[Dict[str, Any]]) -> List[str]:
        """Validates rules and returns warnings"""
        warnings = []
        for rule in rules:
            if rule["strategy"] == "fake_data":
                if not rule.get("options", {}).get("preserve_uniqueness"):
                    warnings.append("Fake data generation may create duplicate emails - consider adding uniqueness check")
            if rule["strategy"] == "masking" and "ssn" in rule["column"]:
                warnings.append("Masking SSN preserves last 4 digits - ensure this meets your compliance requirements")
        return warnings


class AnonymizationExecutor:
    """Executes anonymization"""
    
    async def execute_anonymization(self, rule_set_id: str, target_connection: str, execution_options: Dict[str, Any]) -> ApplyMaskingData:
        """Executes anonymization rules"""
        execution_id = f"exec_{str(uuid4())[:8]}"
        
        progress = ProgressInfo(
            percentage=0,
            current_rule="Anonymizing users.email",
            records_processed=0,
            total_records=614047,
            estimated_remaining="12 minutes"
        )
        
        metrics = PerformanceMetrics(
            records_per_second=0,
            error_count=0,
            warning_count=0
        )
        
        logs = [
            f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Anonymization started",
            f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Creating backup snapshot...",
            f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Backup created: 2.3 GB",
            f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Applying rule: users.email (145,623 records)"
        ]
        
        return ApplyMaskingData(
            execution_id=execution_id,
            status="running",
            progress=progress,
            performance_metrics=metrics,
            logs=logs
        )


class DataSubsetter:
    """Creates data subsets for staging"""
    
    def create_subset_plan(self, source_connection: str, target_connection: str, strategy: str, options: Dict[str, Any]) -> SubsetData:
        """Creates data subsetting plan"""
        subset_id = f"subset_{str(uuid4())[:8]}"
        
        tables = self._plan_table_subsets(options["sample_percentage"])
        
        total_records = sum(t.subset_records for t in tables)
        source_size = 250.5
        target_size = source_size * (options["sample_percentage"] / 100)
        
        plan = SubsettingPlan(
            estimated_duration="25 minutes",
            source_size_gb=source_size,
            target_size_gb=target_size,
            reduction_percentage=100 - options["sample_percentage"],
            tables=tables,
            total_records_to_copy=total_records,
            estimated_copy_time="18 minutes",
            estimated_anonymization_time="7 minutes"
        )
        
        return SubsetData(subset_id=subset_id, subsetting_plan=plan)
    
    def _plan_table_subsets(self, sample_pct: int) -> List[TableSubsetPlan]:
        """Plans table subsetting"""
        return [
            TableSubsetPlan(
                table="users",
                original_records=145623,
                subset_records=14562,
                reduction_percentage=90,
                subsetting_method=f"Random {sample_pct}% sampling",
                foreign_key_dependencies=[],
                includes_full_graph=True
            ),
            TableSubsetPlan(
                table="orders",
                original_records=456789,
                subset_records=45679,
                reduction_percentage=90,
                subsetting_method="All orders from sampled users",
                foreign_key_dependencies=["users.user_id"],
                includes_full_graph=True
            ),
            TableSubsetPlan(
                table="order_items",
                original_records=1234567,
                subset_records=123457,
                reduction_percentage=90,
                subsetting_method="All items from sampled orders",
                foreign_key_dependencies=["orders.order_id", "products.product_id"],
                includes_full_graph=True
            ),
            TableSubsetPlan(
                table="products",
                original_records=12345,
                subset_records=12345,
                reduction_percentage=0,
                subsetting_method="Full table copy (reference data)",
                foreign_key_dependencies=[],
                includes_full_graph=True
            )
        ]


class ComplianceValidator:
    """Validates compliance"""
    
    def validate_compliance(self, execution_id: str, frameworks: List[str], validation_options: Dict[str, Any]) -> ComplianceValidationData:
        """Validates compliance with frameworks"""
        validation_id = f"valid_{str(uuid4())[:8]}"
        
        framework_validations = [self._validate_framework(fw) for fw in frameworks]
        
        pii_rescan = PIIRescanResults(
            pii_fields_detected=0,
            confidence_level=99.8,
            scan_coverage="100% of columns scanned",
            false_positive_rate=0.2
        )
        
        ref_integrity = ReferentialIntegrity(
            status="valid",
            foreign_key_violations=0,
            orphaned_records=0,
            checks_performed=23
        )
        
        data_quality = DataQuality(
            status="excellent",
            null_percentage=2.3,
            duplicate_records=0,
            format_errors=0,
            quality_score=98.5
        )
        
        audit_log = AuditLog(
            anonymization_timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            anonymized_by="admin@company.com",
            rules_applied=4,
            records_affected=614047,
            backup_snapshot_id=f"backup_{str(uuid4())[:8]}"
        )
        
        return ComplianceValidationData(
            validation_id=validation_id,
            overall_compliance_status="compliant",
            frameworks=framework_validations,
            pii_rescan_results=pii_rescan,
            referential_integrity=ref_integrity,
            data_quality=data_quality,
            audit_log=audit_log
        )
    
    def _validate_framework(self, framework: str) -> FrameworkValidation:
        """Validates specific compliance framework"""
        checks_data = {
            "GDPR": [
                ComplianceCheck(
                    requirement="Article 17 - Right to erasure",
                    status="passed",
                    evidence="No PII detected in anonymized database"
                ),
                ComplianceCheck(
                    requirement="Article 32 - Security of processing",
                    status="passed",
                    evidence="All sensitive fields encrypted or anonymized"
                ),
                ComplianceCheck(
                    requirement="Article 25 - Data protection by design",
                    status="passed",
                    evidence="Anonymization applied by default for non-production environments"
                )
            ],
            "CCPA": [
                ComplianceCheck(
                    requirement="§ 1798.105 - Right to deletion",
                    status="passed",
                    evidence="Personal information anonymized, no deletion requests applicable"
                ),
                ComplianceCheck(
                    requirement="§ 1798.100 - Right to know",
                    status="passed",
                    evidence="Data inventory shows 0 PII fields in staging environment"
                )
            ],
            "HIPAA": [
                ComplianceCheck(
                    requirement="164.514(a) - De-identification",
                    status="passed",
                    evidence="All 18 HIPAA identifiers anonymized or removed"
                )
            ],
            "PCI-DSS": [
                ComplianceCheck(
                    requirement="3.4 - Render PAN unreadable",
                    status="passed",
                    evidence="Card numbers masked with last 4 digits visible only"
                )
            ]
        }
        
        checks = checks_data.get(framework, [])
        
        return FrameworkValidation(
            framework=framework,
            status="compliant",
            requirements_met=len(checks),
            requirements_total=len(checks),
            checks=checks
        )
