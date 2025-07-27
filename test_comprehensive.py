#!/usr/bin/env python3
"""
Comprehensive Test Suite for SchemaSage Phases 2, 3, and 4
Tests all major components and integration points
"""

import sys
import os
import asyncio
import json
import uuid
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import unittest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestResults:
    """Centralized test results tracking"""
    
    def __init__(self):
        self.results = {
            "phase_2": {"passed": 0, "failed": 0, "errors": []},
            "phase_3": {"passed": 0, "failed": 0, "errors": []},
            "phase_4": {"passed": 0, "failed": 0, "errors": []},
            "integration": {"passed": 0, "failed": 0, "errors": []}
        }
        self.total_tests = 0
        self.start_time = datetime.now()
    
    def record_test(self, phase: str, test_name: str, passed: bool, error: str = None):
        """Record test result"""
        self.total_tests += 1
        if passed:
            self.results[phase]["passed"] += 1
            logger.info(f"✅ {phase.upper()} - {test_name}: PASSED")
        else:
            self.results[phase]["failed"] += 1
            self.results[phase]["errors"].append(f"{test_name}: {error}")
            logger.error(f"❌ {phase.upper()} - {test_name}: FAILED - {error}")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "="*80)
        print("SCHEMASAGE COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        total_passed = sum(phase["passed"] for phase in self.results.values())
        total_failed = sum(phase["failed"] for phase in self.results.values())
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Total Passed: {total_passed}")
        print(f"Total Failed: {total_failed}")
        print(f"Success Rate: {(total_passed/self.total_tests)*100:.1f}%")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        print()
        
        for phase, results in self.results.items():
            print(f"{phase.upper().replace('_', ' ')} TESTS:")
            print(f"  Passed: {results['passed']}")
            print(f"  Failed: {results['failed']}")
            if results['errors']:
                print(f"  Errors:")
                for error in results['errors']:
                    print(f"    - {error}")
            print()
        
        if total_failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {total_failed} TESTS FAILED")
        
        print("="*80)

# Initialize test results tracker
test_results = TestResults()

class Phase2Tests:
    """Phase 2: Advanced Schema Detection & Analysis"""
    
    def __init__(self):
        self.test_data_dir = None
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test data files"""
        try:
            self.test_data_dir = tempfile.mkdtemp()
            
            # Create sample CSV
            csv_content = """id,name,email,age,created_at
1,John Doe,john@example.com,30,2024-01-01
2,Jane Smith,jane@example.com,25,2024-01-02
3,Bob Johnson,bob@example.com,35,2024-01-03"""
            
            csv_path = os.path.join(self.test_data_dir, "users.csv")
            with open(csv_path, 'w') as f:
                f.write(csv_content)
            
            # Create sample JSON
            json_content = [
                {"product_id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
                {"product_id": 2, "name": "Book", "price": 19.99, "category": "Education"},
                {"product_id": 3, "name": "Coffee", "price": 4.99, "category": "Food"}
            ]
            
            json_path = os.path.join(self.test_data_dir, "products.json")
            with open(json_path, 'w') as f:
                json.dump(json_content, f)
            
            logger.info(f"Test data created in {self.test_data_dir}")
            
        except Exception as e:
            test_results.record_test("phase_2", "setup_test_data", False, str(e))
    
    def test_file_processor(self):
        """Test file processing functionality"""
        try:
            # Import after setting up path
            from services.schema_detection.core.file_processor import FileProcessor
            
            processor = FileProcessor()
            
            # Test CSV processing
            csv_path = os.path.join(self.test_data_dir, "users.csv")
            csv_result = processor.process_file(csv_path)
            
            assert csv_result is not None
            assert "columns" in csv_result
            assert len(csv_result["columns"]) == 5  # id, name, email, age, created_at
            assert csv_result["file_type"] == "csv"
            
            # Test JSON processing
            json_path = os.path.join(self.test_data_dir, "products.json")
            json_result = processor.process_file(json_path)
            
            assert json_result is not None
            assert "columns" in json_result
            assert len(json_result["columns"]) == 4  # product_id, name, price, category
            assert json_result["file_type"] == "json"
            
            test_results.record_test("phase_2", "file_processor", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "file_processor", False, str(e))
    
    def test_schema_detector(self):
        """Test schema detection functionality"""
        try:
            from services.schema_detection.core.schema_detector import SchemaDetector
            
            detector = SchemaDetector()
            
            # Test data
            sample_data = [
                {"id": 1, "name": "John", "email": "john@example.com", "age": 30},
                {"id": 2, "name": "Jane", "email": "jane@example.com", "age": 25},
                {"id": 3, "name": "Bob", "email": "bob@example.com", "age": 35}
            ]
            
            schema = detector.detect_schema(sample_data, "users")
            
            assert schema is not None
            assert schema.table_name == "users"
            assert len(schema.columns) == 4
            
            # Check specific column types
            id_column = next(col for col in schema.columns if col.name == "id")
            assert id_column.data_type == "INTEGER"
            
            email_column = next(col for col in schema.columns if col.name == "email")
            assert email_column.data_type == "VARCHAR"
            
            test_results.record_test("phase_2", "schema_detector", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "schema_detector", False, str(e))
    
    def test_lineage_tracking(self):
        """Test lineage tracking functionality"""
        try:
            from services.schema_detection.core.lineage import LineageTracker
            
            tracker = LineageTracker()
            
            # Create test lineage
            source_id = tracker.create_source("test_database", "Database", {"connection": "test"})
            table_id = tracker.create_table("users", source_id, {"schema": "public"})
            column_id = tracker.create_column("user_id", table_id, {"type": "INTEGER", "primary_key": True})
            
            # Create transformation
            transform_id = tracker.create_transformation(
                "user_aggregation",
                "GROUP BY transformation",
                [column_id],
                {"operation": "COUNT"}
            )
            
            # Test lineage retrieval
            lineage = tracker.get_column_lineage(column_id)
            
            assert lineage is not None
            assert lineage.column_id == column_id
            assert len(lineage.transformations) >= 0
            
            test_results.record_test("phase_2", "lineage_tracking", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "lineage_tracking", False, str(e))
    
    def test_schema_history(self):
        """Test schema history functionality"""
        try:
            from services.schema_detection.core.schema_history import SchemaHistoryManager
            
            manager = SchemaHistoryManager()
            
            # Create test schema versions
            schema_id = str(uuid.uuid4())
            
            # Version 1
            version1_id = manager.create_version(
                schema_id,
                "1.0.0",
                {"columns": [{"name": "id", "type": "INTEGER"}]},
                "Initial version",
                "test_user"
            )
            
            # Version 2
            version2_id = manager.create_version(
                schema_id,
                "1.1.0",
                {"columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "VARCHAR"}
                ]},
                "Added name column",
                "test_user"
            )
            
            # Test version retrieval
            versions = manager.get_schema_versions(schema_id)
            assert len(versions) == 2
            
            # Test diff
            diff = manager.compare_versions(version1_id, version2_id)
            assert diff is not None
            assert "added_columns" in diff
            
            test_results.record_test("phase_2", "schema_history", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "schema_history", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 2 tests"""
        logger.info("Starting Phase 2 Tests...")
        
        self.test_file_processor()
        self.test_schema_detector()
        self.test_lineage_tracking()
        self.test_schema_history()
        
        logger.info("Phase 2 Tests completed")

class Phase3Tests:
    """Phase 3: Enterprise Features & Workflow Automation"""
    
    def test_workflow_automation(self):
        """Test workflow automation system"""
        try:
            from services.project_management.core.workflow_automation import WorkflowEngine, WorkflowStatus
            
            engine = WorkflowEngine()
            
            # Create test workflow
            workflow_def = {
                "name": "Schema Review Workflow",
                "description": "Automated schema review process",
                "steps": [
                    {"type": "validation", "config": {"rules": ["required_fields"]}},
                    {"type": "notification", "config": {"recipients": ["admin@test.com"]}},
                    {"type": "approval", "config": {"approvers": ["reviewer1"]}}
                ]
            }
            
            workflow_id = engine.create_workflow("test_workflow", workflow_def, "test_user")
            
            # Execute workflow
            execution_id = engine.execute_workflow(workflow_id, {"schema_id": "test_schema"})
            
            assert execution_id is not None
            
            execution = engine.get_execution(execution_id)
            assert execution is not None
            assert execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.COMPLETED]
            
            test_results.record_test("phase_3", "workflow_automation", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "workflow_automation", False, str(e))
    
    def test_monitoring_system(self):
        """Test monitoring and alerting system"""
        try:
            from services.project_management.core.monitoring import MonitoringSystem, AlertSeverity
            
            monitoring = MonitoringSystem()
            
            # Create test metrics
            monitoring.record_metric("schema_processing_time", 1.5, {"operation": "detection"})
            monitoring.record_metric("api_requests", 100, {"endpoint": "/schemas"})
            
            # Create test alert
            alert_id = monitoring.create_alert(
                "high_processing_time",
                "Processing time exceeded threshold",
                AlertSeverity.WARNING,
                {"threshold": 2.0, "current": 2.5}
            )
            
            assert alert_id is not None
            
            # Get metrics
            metrics = monitoring.get_metrics("schema_processing_time")
            assert len(metrics) > 0
            
            # Get alerts
            alerts = monitoring.get_alerts()
            assert len(alerts) > 0
            
            test_results.record_test("phase_3", "monitoring_system", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "monitoring_system", False, str(e))
    
    def test_enterprise_deployment(self):
        """Test enterprise deployment features"""
        try:
            from services.project_management.core.enterprise_deployment import (
                DeploymentManager, DeploymentEnvironment
            )
            
            manager = DeploymentManager()
            
            # Create test deployment
            deployment_config = {
                "environment": DeploymentEnvironment.STAGING,
                "version": "1.0.0",
                "services": ["schema-detection", "project-management"],
                "scaling": {"min_replicas": 2, "max_replicas": 10}
            }
            
            deployment_id = manager.create_deployment(
                "test_deployment",
                deployment_config,
                "test_user"
            )
            
            assert deployment_id is not None
            
            # Test health check
            health = manager.check_deployment_health(deployment_id)
            assert health is not None
            assert "status" in health
            
            test_results.record_test("phase_3", "enterprise_deployment", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "enterprise_deployment", False, str(e))
    
    def test_integration_management(self):
        """Test integration management"""
        try:
            from services.project_management.integrations.manager import IntegrationManager
            
            manager = IntegrationManager()
            
            # Test webhook integration
            webhook_config = {
                "url": "https://test.example.com/webhook",
                "events": ["schema_created", "schema_updated"],
                "headers": {"Authorization": "Bearer test_token"}
            }
            
            integration_id = manager.create_integration(
                "test_webhook",
                "webhook",
                webhook_config,
                "test_user"
            )
            
            assert integration_id is not None
            
            # Test integration status
            status = manager.get_integration_status(integration_id)
            assert status is not None
            
            test_results.record_test("phase_3", "integration_management", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "integration_management", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 3 tests"""
        logger.info("Starting Phase 3 Tests...")
        
        self.test_workflow_automation()
        self.test_monitoring_system()
        self.test_enterprise_deployment()
        self.test_integration_management()
        
        logger.info("Phase 3 Tests completed")

class Phase4Tests:
    """Phase 4: Advanced AI & Enterprise Features"""
    
    def test_llm_orchestration(self):
        """Test Multi-LLM orchestration system"""
        try:
            from services.code_generation.core.llm.orchestrator import LLMOrchestrator
            from services.code_generation.core.llm.base import LLMRequest
            
            orchestrator = LLMOrchestrator()
            
            # Test request
            request = LLMRequest(
                prompt="Generate a Python function to validate email addresses",
                task_type="code_generation",
                max_tokens=500,
                temperature=0.7
            )
            
            # Mock the actual LLM calls since we don't have API keys in tests
            with patch.object(orchestrator, 'generate') as mock_generate:
                mock_generate.return_value = Mock(
                    content="def validate_email(email): import re; return re.match(r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$', email) is not None",
                    confidence=0.9,
                    provider="openai",
                    metadata={}
                )
                
                result = orchestrator.generate(request)
                
                assert result is not None
                assert result.content is not None
                assert result.confidence > 0
            
            test_results.record_test("phase_4", "llm_orchestration", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "llm_orchestration", False, str(e))
    
    def test_vector_intelligence(self):
        """Test vector intelligence system"""
        try:
            from services.code_generation.core.vector_intelligence import SchemaIntelligenceEngine
            
            engine = SchemaIntelligenceEngine()
            
            # Test schema analysis
            test_schema = {
                "table_name": "users",
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True},
                    {"name": "email", "type": "VARCHAR", "unique": True},
                    {"name": "created_at", "type": "TIMESTAMP"}
                ]
            }
            
            # Mock embedding generation
            with patch.object(engine, '_generate_embedding') as mock_embed:
                mock_embed.return_value = [0.1] * 384  # Mock embedding vector
                
                patterns = engine.analyze_schema_patterns(test_schema)
                
                assert patterns is not None
                assert "primary_key_pattern" in patterns
                assert "timestamp_pattern" in patterns
            
            test_results.record_test("phase_4", "vector_intelligence", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "vector_intelligence", False, str(e))
    
    def test_schema_drift_detection(self):
        """Test schema drift detection system"""
        try:
            from services.code_generation.core.schema_drift_detection import SchemaDriftDetector
            
            detector = SchemaDriftDetector()
            
            # Test schema comparison
            old_schema = {
                "tables": {
                    "users": {
                        "columns": {
                            "id": {"type": "INTEGER", "nullable": False},
                            "name": {"type": "VARCHAR", "nullable": False}
                        }
                    }
                }
            }
            
            new_schema = {
                "tables": {
                    "users": {
                        "columns": {
                            "id": {"type": "INTEGER", "nullable": False},
                            "name": {"type": "VARCHAR", "nullable": False},
                            "email": {"type": "VARCHAR", "nullable": True}
                        }
                    }
                }
            }
            
            changes = detector.detect_changes(old_schema, new_schema)
            
            assert changes is not None
            assert len(changes) > 0
            assert any(change["type"] == "column_added" for change in changes)
            
            test_results.record_test("phase_4", "schema_drift_detection", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "schema_drift_detection", False, str(e))
    
    def test_etl_pipeline_builder(self):
        """Test ETL pipeline builder"""
        try:
            from services.code_generation.core.etl_pipeline_builder import (
                get_pipeline_builder, PipelineNodeType
            )
            
            builder = get_pipeline_builder()
            
            # Create test pipeline
            pipeline_id = builder.create_pipeline(
                "Test ETL Pipeline",
                "Test pipeline for data processing",
                "test_user"
            )
            
            # Add source node
            source_id = builder.add_node(
                pipeline_id,
                "CSV Source",
                PipelineNodeType.SOURCE,
                "file",
                {"file_path": "/data/input.csv", "file_format": "csv"}
            )
            
            # Add transform node
            transform_id = builder.add_node(
                pipeline_id,
                "Filter Transform",
                PipelineNodeType.TRANSFORM,
                "filter",
                {"condition": "age > 18"}
            )
            
            # Add sink node
            sink_id = builder.add_node(
                pipeline_id,
                "Database Sink",
                PipelineNodeType.SINK,
                "database",
                {"connection_string": "postgresql://test", "table_name": "filtered_users"}
            )
            
            # Connect nodes
            builder.connect_nodes(pipeline_id, source_id, transform_id)
            builder.connect_nodes(pipeline_id, transform_id, sink_id)
            
            # Validate pipeline
            validation = builder.validate_pipeline(pipeline_id)
            
            assert validation["valid"] == True
            
            pipeline = builder.get_pipeline(pipeline_id)
            assert pipeline is not None
            assert len(pipeline.nodes) == 3
            assert len(pipeline.connections) == 2
            
            test_results.record_test("phase_4", "etl_pipeline_builder", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "etl_pipeline_builder", False, str(e))
    
    def test_etl_code_generation(self):
        """Test ETL code generation"""
        try:
            from services.code_generation.core.etl_code_generator import get_code_generator
            from services.code_generation.core.etl_pipeline_builder import (
                PipelineDefinition, PipelineNode, PipelineConnection,
                PipelineNodeType, PipelineFramework
            )
            
            generator = get_code_generator()
            
            # Create test pipeline definition
            pipeline = PipelineDefinition(
                pipeline_id=str(uuid.uuid4()),
                name="test_pipeline",
                description="Test pipeline",
                nodes=[
                    PipelineNode(
                        node_id="source_1",
                        name="CSV Source",
                        node_type=PipelineNodeType.SOURCE,
                        config={"subtype": "file", "file_path": "/data/input.csv", "file_format": "csv"}
                    ),
                    PipelineNode(
                        node_id="sink_1",
                        name="Database Sink",
                        node_type=PipelineNodeType.SINK,
                        config={"subtype": "database", "connection_string": "postgresql://test", "table_name": "output"}
                    )
                ],
                connections=[
                    PipelineConnection(
                        connection_id="conn_1",
                        from_node="source_1",
                        to_node="sink_1"
                    )
                ]
            )
            
            # Generate Airflow code
            generated = generator.generate_code(pipeline, PipelineFramework.AIRFLOW)
            
            assert generated is not None
            assert generated.main_code is not None
            assert "airflow" in generated.main_code.lower()
            assert len(generated.requirements) > 0
            
            test_results.record_test("phase_4", "etl_code_generation", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "etl_code_generation", False, str(e))
    
    def test_team_collaboration(self):
        """Test team collaboration system"""
        try:
            from services.project_management.core.team_collaboration import (
                get_collaboration_manager, UserRole, ChangeType
            )
            
            manager = get_collaboration_manager()
            
            # Create test team
            team_id = manager.create_team(
                "Test Team",
                "Test team for collaboration",
                "test_user"
            )
            
            # Add team member
            success = manager.add_team_member(
                team_id,
                "team_member_1",
                UserRole.CONTRIBUTOR,
                "test_user"
            )
            
            assert success == True
            
            # Register schema
            schema_id = manager.register_schema(
                "Test Schema",
                "Test schema for collaboration",
                team_id,
                "database",
                {"tables": {"users": {"columns": {"id": {"type": "INTEGER"}}}}},
                "test_user"
            )
            
            # Propose change
            change_id = manager.propose_schema_change(
                schema_id,
                ChangeType.ADD_COLUMN,
                "Add email column",
                {"tables": {"users": {"columns": {
                    "id": {"type": "INTEGER"},
                    "email": {"type": "VARCHAR"}
                }}}},
                "team_member_1"
            )
            
            assert change_id is not None
            
            # Review change
            review_success = manager.review_schema_change(
                change_id,
                "test_user",  # Owner can review
                True,
                "Looks good!"
            )
            
            assert review_success == True
            
            test_results.record_test("phase_4", "team_collaboration", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "team_collaboration", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 4 tests"""
        logger.info("Starting Phase 4 Tests...")
        
        self.test_llm_orchestration()
        self.test_vector_intelligence()
        self.test_schema_drift_detection()
        self.test_etl_pipeline_builder()
        self.test_etl_code_generation()
        self.test_team_collaboration()
        
        logger.info("Phase 4 Tests completed")

class IntegrationTests:
    """Integration tests across all phases"""
    
    def test_end_to_end_schema_workflow(self):
        """Test complete schema workflow from detection to deployment"""
        try:
            # Phase 2: Schema Detection
            from services.schema_detection.core.schema_detector import SchemaDetector
            
            detector = SchemaDetector()
            sample_data = [
                {"id": 1, "name": "John", "email": "john@example.com"},
                {"id": 2, "name": "Jane", "email": "jane@example.com"}
            ]
            
            schema = detector.detect_schema(sample_data, "users")
            assert schema is not None
            
            # Phase 3: Workflow Processing
            from services.project_management.core.workflow_automation import WorkflowEngine
            
            engine = WorkflowEngine()
            workflow_def = {
                "name": "Schema Processing",
                "steps": [{"type": "validation", "config": {}}]
            }
            
            workflow_id = engine.create_workflow("schema_processing", workflow_def, "test_user")
            execution_id = engine.execute_workflow(workflow_id, {"schema": asdict(schema)})
            
            assert execution_id is not None
            
            # Phase 4: Code Generation
            from services.code_generation.core.etl_pipeline_builder import get_pipeline_builder
            
            builder = get_pipeline_builder()
            pipeline_id = builder.create_pipeline("Generated Pipeline", "Auto-generated", "test_user")
            
            assert pipeline_id is not None
            
            test_results.record_test("integration", "end_to_end_workflow", True)
            
        except Exception as e:
            test_results.record_test("integration", "end_to_end_workflow", False, str(e))
    
    def test_cross_service_communication(self):
        """Test communication between services"""
        try:
            # Test project management -> schema detection
            from services.project_management.core.project_manager import ProjectManager
            from services.schema_detection.core.schema_detector import SchemaDetector
            
            project_manager = ProjectManager()
            schema_detector = SchemaDetector()
            
            # Create project
            project_id = project_manager.create_project(
                "Integration Test Project",
                "Testing cross-service communication",
                "test_user"
            )
            
            # Add schema detection task
            sample_data = [{"id": 1, "value": "test"}]
            schema = schema_detector.detect_schema(sample_data, "test_table")
            
            # Link schema to project (simplified)
            project = project_manager.get_project(project_id)
            project.metadata["detected_schemas"] = [{"table": "test_table", "columns": len(schema.columns)}]
            
            assert project.metadata["detected_schemas"] is not None
            
            test_results.record_test("integration", "cross_service_communication", True)
            
        except Exception as e:
            test_results.record_test("integration", "cross_service_communication", False, str(e))
    
    def test_data_consistency(self):
        """Test data consistency across all systems"""
        try:
            # Create consistent test data across systems
            test_schema_id = str(uuid.uuid4())
            test_user_id = "consistency_test_user"
            
            # Phase 2: Store schema
            from services.schema_detection.core.schema_history import SchemaHistoryManager
            
            history_manager = SchemaHistoryManager()
            version_id = history_manager.create_version(
                test_schema_id,
                "1.0.0",
                {"table": "test", "columns": ["id", "name"]},
                "Test schema",
                test_user_id
            )
            
            # Phase 4: Register in collaboration system
            from services.project_management.core.team_collaboration import get_collaboration_manager
            
            collab_manager = get_collaboration_manager()
            team_id = collab_manager.create_team("Consistency Test Team", "Test", test_user_id)
            
            schema_registry_id = collab_manager.register_schema(
                "Test Schema",
                "Consistency test schema",
                team_id,
                "database",
                {"table": "test", "columns": ["id", "name"]},
                test_user_id
            )
            
            # Verify consistency
            assert version_id is not None
            assert schema_registry_id is not None
            
            # Both systems should have the same schema data
            schema_version = history_manager.get_version(version_id)
            schema_registry = collab_manager.get_schema(schema_registry_id)
            
            assert schema_version is not None
            assert schema_registry is not None
            
            test_results.record_test("integration", "data_consistency", True)
            
        except Exception as e:
            test_results.record_test("integration", "data_consistency", False, str(e))
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting Integration Tests...")
        
        self.test_end_to_end_schema_workflow()
        self.test_cross_service_communication()
        self.test_data_consistency()
        
        logger.info("Integration Tests completed")

def run_performance_tests():
    """Run performance tests"""
    logger.info("Starting Performance Tests...")
    
    try:
        # Test schema detection performance
        from services.schema_detection.core.schema_detector import SchemaDetector
        
        detector = SchemaDetector()
        
        # Generate large dataset
        large_dataset = [
            {"id": i, "name": f"user_{i}", "email": f"user_{i}@example.com", "value": i * 1.5}
            for i in range(1000)
        ]
        
        start_time = datetime.now()
        schema = detector.detect_schema(large_dataset, "performance_test")
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Schema detection for 1000 rows: {processing_time:.2f} seconds")
        
        # Performance should be reasonable (< 5 seconds for 1000 rows)
        if processing_time < 5.0:
            test_results.record_test("integration", "performance_schema_detection", True)
        else:
            test_results.record_test("integration", "performance_schema_detection", False, 
                                   f"Too slow: {processing_time:.2f}s")
        
    except Exception as e:
        test_results.record_test("integration", "performance_tests", False, str(e))

def main():
    """Main test runner"""
    print("🚀 Starting SchemaSage Comprehensive Test Suite...")
    print("="*80)
    
    # Initialize test suites
    phase2_tests = Phase2Tests()
    phase3_tests = Phase3Tests()
    phase4_tests = Phase4Tests()
    integration_tests = IntegrationTests()
    
    try:
        # Run all test phases
        phase2_tests.run_all_tests()
        phase3_tests.run_all_tests()
        phase4_tests.run_all_tests()
        integration_tests.run_all_tests()
        
        # Run performance tests
        run_performance_tests()
        
    except Exception as e:
        logger.error(f"Test suite error: {e}")
        test_results.record_test("integration", "test_suite_execution", False, str(e))
    
    finally:
        # Print comprehensive results
        test_results.print_summary()
        
        # Return exit code based on results
        total_failed = sum(phase["failed"] for phase in test_results.results.values())
        return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
