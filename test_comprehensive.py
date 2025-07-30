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
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Add services to path
services_path = os.path.join(project_root, "services")
sys.path.insert(0, services_path)

# Add individual service paths
schema_detection_path = os.path.join(services_path, "schema-detection")
project_management_path = os.path.join(services_path, "project-management")
code_generation_path = os.path.join(services_path, "code-generation")
sys.path.insert(0, schema_detection_path)
sys.path.insert(0, project_management_path)
sys.path.insert(0, code_generation_path)

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
    
    def test_schema_detection_service_structure(self):
        """Test schema detection service structure and modules"""
        try:
            schema_detection_path = os.path.join(project_root, "services", "schema-detection")
            
            # Check main service file exists
            main_file = os.path.join(schema_detection_path, "main.py")
            assert os.path.exists(main_file), "main.py file missing"
            
            # Check core modules exist
            core_path = os.path.join(schema_detection_path, "core")
            assert os.path.exists(core_path), "core directory missing"
            
            expected_modules = [
                "file_processor.py", "schema_detector.py", "lineage.py", 
                "schema_history.py", "data_parser.py", "schema_analyzer.py", "ai_enhancer.py"
            ]
            
            for module in expected_modules:
                module_path = os.path.join(core_path, module)
                assert os.path.exists(module_path), f"Module {module} missing"
            
            # Check routers exist
            routers_path = os.path.join(schema_detection_path, "routers")
            assert os.path.exists(routers_path), "routers directory missing"
            
            test_results.record_test("phase_2", "schema_detection_service_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "schema_detection_service_structure", False, str(e))
    
    def test_schema_detection_config(self):
        """Test schema detection configuration"""
        try:
            schema_detection_path = os.path.join(project_root, "services", "schema-detection")
            
            # Check config file exists
            config_file = os.path.join(schema_detection_path, "config.py")
            assert os.path.exists(config_file), "config.py file missing"
            
            # Check requirements file exists
            requirements_file = os.path.join(schema_detection_path, "requirements.txt")
            assert os.path.exists(requirements_file), "requirements.txt file missing"
            
            # Check Dockerfile exists
            dockerfile = os.path.join(schema_detection_path, "Dockerfile")
            assert os.path.exists(dockerfile), "Dockerfile missing"
            
            test_results.record_test("phase_2", "schema_detection_config", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "schema_detection_config", False, str(e))
    
    def test_schema_detection_api_endpoints(self):
        """Test schema detection API endpoint structure"""
        try:
            # Read main.py to check for API endpoints
            schema_detection_path = os.path.join(project_root, "services", "schema-detection")
            main_file = os.path.join(schema_detection_path, "main.py")
            
            with open(main_file, 'r') as f:
                content = f.read()
            
            # Check for expected API patterns
            assert "FastAPI" in content, "FastAPI not found in main.py"
            assert "@app." in content or "include_router" in content, "No API endpoints found"
            assert "/health" in content, "Health endpoint missing"
            
            test_results.record_test("phase_2", "schema_detection_api_endpoints", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "schema_detection_api_endpoints", False, str(e))
    
    def test_data_models_structure(self):
        """Test data models and schemas structure"""
        try:
            schema_detection_path = os.path.join(project_root, "services", "schema-detection")
            models_path = os.path.join(schema_detection_path, "models")
            
            assert os.path.exists(models_path), "models directory missing"
            
            # Check for schemas file
            schemas_file = os.path.join(models_path, "schemas.py")
            assert os.path.exists(schemas_file), "schemas.py file missing"
            
            # Read schemas file to check for expected models
            with open(schemas_file, 'r') as f:
                content = f.read()
            
            expected_models = ["SchemaResponse", "TableInfo", "ColumnInfo"]
            for model in expected_models:
                assert model in content, f"Model {model} not found in schemas.py"
            
            test_results.record_test("phase_2", "data_models_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_2", "data_models_structure", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 2 tests"""
        logger.info("Starting Phase 2 Tests...")
        
        self.test_schema_detection_service_structure()
        self.test_schema_detection_config()
        self.test_schema_detection_api_endpoints()
        self.test_data_models_structure()
        
        logger.info("Phase 2 Tests completed")

class Phase3Tests:
    """Phase 3: Enterprise Features & Workflow Automation"""
    
    def test_project_management_service_structure(self):
        """Test project management service structure"""
        try:
            project_management_path = os.path.join(project_root, "services", "project-management")
            
            # Check main service file exists
            main_file = os.path.join(project_management_path, "main.py")
            assert os.path.exists(main_file), "main.py file missing"
            
            # Check core modules exist
            core_path = os.path.join(project_management_path, "core")
            assert os.path.exists(core_path), "core directory missing"
            
            # Check for project manager
            project_manager_file = os.path.join(core_path, "project_manager.py")
            assert os.path.exists(project_manager_file), "project_manager.py missing"
            
            # Check integrations directory
            integrations_path = os.path.join(project_management_path, "integrations")
            assert os.path.exists(integrations_path), "integrations directory missing"
            
            # Check routers exist
            routers_path = os.path.join(project_management_path, "routers")
            assert os.path.exists(routers_path), "routers directory missing"
            
            test_results.record_test("phase_3", "project_management_service_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "project_management_service_structure", False, str(e))
    
    def test_team_collaboration_structure(self):
        """Test team collaboration module structure"""
        try:
            project_management_path = os.path.join(project_root, "services", "project-management")
            team_collab_path = os.path.join(project_management_path, "core", "team_collaboration")
            
            assert os.path.exists(team_collab_path), "team_collaboration directory missing"
            
            expected_modules = [
                "models.py", "team_manager.py", "schema_registry.py", 
                "change_manager.py", "notification_manager.py", "__init__.py"
            ]
            
            for module in expected_modules:
                module_path = os.path.join(team_collab_path, module)
                assert os.path.exists(module_path), f"Team collaboration module {module} missing"
            
            test_results.record_test("phase_3", "team_collaboration_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "team_collaboration_structure", False, str(e))
    
    def test_project_management_api_endpoints(self):
        """Test project management API endpoints"""
        try:
            project_management_path = os.path.join(project_root, "services", "project-management")
            main_file = os.path.join(project_management_path, "main.py")
            
            with open(main_file, 'r') as f:
                content = f.read()
            
            # Check for expected API patterns
            assert "FastAPI" in content, "FastAPI not found in main.py"
            assert "@app." in content or "include_router" in content, "No API endpoints found"
            assert "/health" in content, "Health endpoint missing"
            
            test_results.record_test("phase_3", "project_management_api_endpoints", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "project_management_api_endpoints", False, str(e))
    
    def test_integration_modules(self):
        """Test integration management modules"""
        try:
            project_management_path = os.path.join(project_root, "services", "project-management")
            integrations_path = os.path.join(project_management_path, "integrations")
            
            expected_modules = [
                "manager.py", "base.py", "webhook.py", "notification.py"
            ]
            
            for module in expected_modules:
                module_path = os.path.join(integrations_path, module)
                assert os.path.exists(module_path), f"Integration module {module} missing"
            
            test_results.record_test("phase_3", "integration_modules", True)
            
        except Exception as e:
            test_results.record_test("phase_3", "integration_modules", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 3 tests"""
        logger.info("Starting Phase 3 Tests...")
        
        self.test_project_management_service_structure()
        self.test_team_collaboration_structure()
        self.test_project_management_api_endpoints()
        self.test_integration_modules()
        
        logger.info("Phase 3 Tests completed")

class Phase4Tests:
    """Phase 4: Advanced AI & Enterprise Features"""
    
    def test_code_generation_service_structure(self):
        """Test code generation service structure"""
        try:
            code_generation_path = os.path.join(project_root, "services", "code-generation")
            
            # Check main service file exists
            main_file = os.path.join(code_generation_path, "main.py")
            assert os.path.exists(main_file), "main.py file missing"
            
            # Check core modules exist
            core_path = os.path.join(code_generation_path, "core")
            assert os.path.exists(core_path), "core directory missing"
            
            # Check for advanced features directories
            expected_dirs = [
                "llm", "vector_intelligence", "schema_drift_detection", 
                "etl_code_generator", "workflow_automation"
            ]
            
            for dir_name in expected_dirs:
                dir_path = os.path.join(core_path, dir_name)
                assert os.path.exists(dir_path), f"Advanced feature directory {dir_name} missing"
            
            test_results.record_test("phase_4", "code_generation_service_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "code_generation_service_structure", False, str(e))
    
    def test_llm_orchestration_structure(self):
        """Test LLM orchestration module structure"""
        try:
            code_generation_path = os.path.join(project_root, "services", "code-generation")
            llm_path = os.path.join(code_generation_path, "core", "llm")
            
            assert os.path.exists(llm_path), "LLM directory missing"
            
            # Check for LLM modules
            expected_files = [
                "__init__.py", "orchestrator.py", "base.py", "router.py",
                "openai_provider.py", "claude_provider.py", "gemini_provider.py"
            ]
            for file_name in expected_files:
                file_path = os.path.join(llm_path, file_name)
                assert os.path.exists(file_path), f"LLM file {file_name} missing"
            
            test_results.record_test("phase_4", "llm_orchestration_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "llm_orchestration_structure", False, str(e))
    
    def test_vector_intelligence_structure(self):
        """Test vector intelligence module structure"""
        try:
            code_generation_path = os.path.join(project_root, "services", "code-generation")
            vector_path = os.path.join(code_generation_path, "core", "vector_intelligence")
            
            assert os.path.exists(vector_path), "Vector intelligence directory missing"
            
            # Check for vector intelligence modules
            expected_files = ["__init__.py"]
            for file_name in expected_files:
                file_path = os.path.join(vector_path, file_name)
                assert os.path.exists(file_path), f"Vector intelligence file {file_name} missing"
            
            test_results.record_test("phase_4", "vector_intelligence_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "vector_intelligence_structure", False, str(e))
    
    def test_etl_pipeline_structure(self):
        """Test ETL pipeline builder structure"""
        try:
            code_generation_path = os.path.join(project_root, "services", "code-generation")
            etl_path = os.path.join(code_generation_path, "core", "etl_code_generator")
            
            assert os.path.exists(etl_path), "ETL code generator directory missing"
            
            # Check for ETL modules
            expected_files = ["__init__.py"]
            for file_name in expected_files:
                file_path = os.path.join(etl_path, file_name)
                assert os.path.exists(file_path), f"ETL file {file_name} missing"
            
            test_results.record_test("phase_4", "etl_pipeline_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "etl_pipeline_structure", False, str(e))
    
    def test_schema_drift_detection_structure(self):
        """Test schema drift detection structure"""
        try:
            code_generation_path = os.path.join(project_root, "services", "code-generation")
            drift_path = os.path.join(code_generation_path, "core", "schema_drift_detection")
            
            assert os.path.exists(drift_path), "Schema drift detection directory missing"
            
            # Check for drift detection modules
            expected_files = ["__init__.py"]
            for file_name in expected_files:
                file_path = os.path.join(drift_path, file_name)
                assert os.path.exists(file_path), f"Drift detection file {file_name} missing"
            
            test_results.record_test("phase_4", "schema_drift_detection_structure", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "schema_drift_detection_structure", False, str(e))
    
    def test_code_generation_api_endpoints(self):
        """Test code generation API endpoints"""
        try:
            code_generation_path = os.path.join(project_root, "services", "code-generation")
            main_file = os.path.join(code_generation_path, "main.py")
            
            with open(main_file, 'r') as f:
                content = f.read()
            
            # Check for expected API patterns
            assert "FastAPI" in content, "FastAPI not found in main.py"
            assert "@app." in content, "No API endpoints found"
            assert "/health" in content, "Health endpoint missing"
            
            test_results.record_test("phase_4", "code_generation_api_endpoints", True)
            
        except Exception as e:
            test_results.record_test("phase_4", "code_generation_api_endpoints", False, str(e))
    
    def run_all_tests(self):
        """Run all Phase 4 tests"""
        logger.info("Starting Phase 4 Tests...")
        
        self.test_code_generation_service_structure()
        self.test_llm_orchestration_structure()
        self.test_vector_intelligence_structure()
        self.test_etl_pipeline_structure()
        self.test_schema_drift_detection_structure()
        self.test_code_generation_api_endpoints()
        
        logger.info("Phase 4 Tests completed")

class IntegrationTests:
    """Integration tests across all phases"""
    
    def test_all_services_present(self):
        """Test that all required services are present"""
        try:
            services_path = os.path.join(project_root, "services")
            
            required_services = [
                "schema-detection", "project-management", "code-generation",
                "ai-chat", "api-gateway", "authentication"
            ]
            
            for service in required_services:
                service_path = os.path.join(services_path, service)
                assert os.path.exists(service_path), f"Service {service} directory missing"
                
                # Check main.py exists for each service
                main_file = os.path.join(service_path, "main.py")
                assert os.path.exists(main_file), f"Service {service} main.py missing"
            
            test_results.record_test("integration", "all_services_present", True)
            
        except Exception as e:
            test_results.record_test("integration", "all_services_present", False, str(e))
    
    def test_docker_configuration(self):
        """Test Docker configuration for all services"""
        try:
            services_path = os.path.join(project_root, "services")
            
            services_with_docker = [
                "schema-detection", "project-management", "code-generation",
                "ai-chat", "api-gateway", "authentication"
            ]
            
            for service in services_with_docker:
                service_path = os.path.join(services_path, service)
                dockerfile = os.path.join(service_path, "Dockerfile")
                assert os.path.exists(dockerfile), f"Service {service} Dockerfile missing"
            
            # Check root docker-compose
            docker_compose = os.path.join(project_root, "docker-compose.yml")
            assert os.path.exists(docker_compose), "Root docker-compose.yml missing"
            
            test_results.record_test("integration", "docker_configuration", True)
            
        except Exception as e:
            test_results.record_test("integration", "docker_configuration", False, str(e))
    
    def test_shared_models_structure(self):
        """Test shared models structure"""
        try:
            shared_path = os.path.join(project_root, "shared")
            assert os.path.exists(shared_path), "Shared directory missing"
            
            # Check models directory
            models_path = os.path.join(shared_path, "models")
            assert os.path.exists(models_path), "Shared models directory missing"
            
            # Check utils directory
            utils_path = os.path.join(shared_path, "utils")
            assert os.path.exists(utils_path), "Shared utils directory missing"
            
            # Check expected shared model files
            expected_models = ["base.py", "file.py", "project.py", "schema.py", "user.py"]
            for model in expected_models:
                model_path = os.path.join(models_path, model)
                assert os.path.exists(model_path), f"Shared model {model} missing"
            
            test_results.record_test("integration", "shared_models_structure", True)
            
        except Exception as e:
            test_results.record_test("integration", "shared_models_structure", False, str(e))
    
    def test_configuration_consistency(self):
        """Test configuration consistency across services"""
        try:
            services_path = os.path.join(project_root, "services")
            
            services_to_check = ["schema-detection", "project-management", "code-generation"]
            
            for service in services_to_check:
                service_path = os.path.join(services_path, service)
                
                # Check config.py exists
                config_file = os.path.join(service_path, "config.py")
                assert os.path.exists(config_file), f"Service {service} config.py missing"
                
                # Check requirements.txt exists
                requirements_file = os.path.join(service_path, "requirements.txt")
                assert os.path.exists(requirements_file), f"Service {service} requirements.txt missing"
            
            test_results.record_test("integration", "configuration_consistency", True)
            
        except Exception as e:
            test_results.record_test("integration", "configuration_consistency", False, str(e))
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting Integration Tests...")
        
        self.test_all_services_present()
        self.test_docker_configuration()
        self.test_shared_models_structure()
        self.test_configuration_consistency()
        
        logger.info("Integration Tests completed")

def run_performance_tests():
    """Run performance tests"""
    logger.info("Starting Performance Tests...")
    
    try:
        # Test basic file system performance for large structures
        start_time = datetime.now()
        
        # Count all Python files in the project
        python_files = []
        for root, dirs, files in os.walk(os.path.join(project_root, "services")):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Found {len(python_files)} Python files in {processing_time:.2f} seconds")
        
        # Performance should be reasonable (< 2 seconds for file traversal)
        if processing_time < 2.0 and len(python_files) > 0:
            test_results.record_test("integration", "performance_file_traversal", True)
        else:
            test_results.record_test("integration", "performance_file_traversal", False, 
                                   f"Too slow or no files found: {processing_time:.2f}s, {len(python_files)} files")
        
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
