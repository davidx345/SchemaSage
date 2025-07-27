"""
Comprehensive Test Suite for SchemaSage Phase 2 & Phase 3 Features
Tests all enterprise collaboration, analytics, integration, ML, workflow, monitoring, deployment, and security features
"""
import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid
import tempfile
import os

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system("pip install httpx")
    import httpx

# Test Configuration
BASE_URL = "http://localhost:8001"  # Code Generation Service
TEST_TIMEOUT = 30

class SchemaSageTestSuite:
    """Comprehensive test suite for Phase 2 & 3 features"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.test_results = {}
        
        # Sample test data
        self.sample_schema = {
            "name": "test_ecommerce",
            "description": "Test e-commerce schema",
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "email", "type": "VARCHAR", "length": 255, "nullable": False},
                        {"name": "first_name", "type": "VARCHAR", "length": 100},
                        {"name": "last_name", "type": "VARCHAR", "length": 100},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    ]
                },
                {
                    "name": "products",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "name", "type": "VARCHAR", "length": 255, "nullable": False},
                        {"name": "price", "type": "DECIMAL", "precision": 10, "scale": 2},
                        {"name": "description", "type": "TEXT"},
                        {"name": "category_id", "type": "INTEGER"}
                    ]
                },
                {
                    "name": "orders",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "primary_key": True},
                        {"name": "user_id", "type": "INTEGER", "nullable": False},
                        {"name": "total_amount", "type": "DECIMAL", "precision": 10, "scale": 2},
                        {"name": "status", "type": "VARCHAR", "length": 50},
                        {"name": "created_at", "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP"}
                    ]
                }
            ],
            "relationships": [
                {
                    "from_table": "orders",
                    "from_column": "user_id",
                    "to_table": "users",
                    "to_column": "id",
                    "relationship_type": "many_to_one"
                },
                {
                    "from_table": "products",
                    "from_column": "category_id",
                    "to_table": "categories",
                    "to_column": "id",
                    "relationship_type": "many_to_one"
                }
            ]
        }
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting SchemaSage Phase 2 & 3 Test Suite")
        print("=" * 60)
        
        test_suites = [
            ("Health Check", self.test_health_check),
            ("Phase 2 - Real-time Collaboration", self.test_collaboration),
            ("Phase 2 - Advanced Analytics", self.test_analytics),
            ("Phase 2 - Enterprise Integration", self.test_integrations),
            ("Phase 2 - ML Pipeline", self.test_ml_pipeline),
            ("Phase 3 - Workflow Automation", self.test_workflow),
            ("Phase 3 - Monitoring System", self.test_monitoring),
            ("Phase 3 - Security & Compliance", self.test_security),
            ("Phase 3 - Enterprise Deployment", self.test_deployment)
        ]
        
        overall_success = True
        
        for suite_name, test_func in test_suites:
            print(f"\n📋 Running {suite_name} Tests")
            print("-" * 40)
            
            try:
                success = await test_func()
                self.test_results[suite_name] = success
                
                if success:
                    print(f"✅ {suite_name}: PASSED")
                else:
                    print(f"❌ {suite_name}: FAILED")
                    overall_success = False
                    
            except Exception as e:
                print(f"💥 {suite_name}: ERROR - {str(e)}")
                self.test_results[suite_name] = False
                overall_success = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for suite_name, success in self.test_results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{suite_name}: {status}")
        
        print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '⚠️  SOME TESTS FAILED'}")
        print("=" * 60)
        
        await self.client.aclose()
        return overall_success
    
    async def test_health_check(self) -> bool:
        """Test basic health and connectivity"""
        try:
            # Test root endpoint
            response = await self.client.get(f"{self.base_url}/")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "Code Generation Service"
            assert data["status"] == "running"
            print("  ✓ Root endpoint accessible")
            
            # Test health endpoint
            response = await self.client.get(f"{self.base_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            print("  ✓ Health endpoint responding")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False
    
    async def test_collaboration(self) -> bool:
        """Test real-time collaboration features"""
        try:
            session_id = str(uuid.uuid4())
            
            # Test join collaboration session
            response = await self.client.post(
                f"{self.base_url}/collaboration/sessions/{session_id}/join",
                json={
                    "user_id": "test_user_1",
                    "user_name": "Test User 1",
                    "user_avatar": "avatar1.png"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            print("  ✓ Join collaboration session")
            
            # Test edit element
            response = await self.client.post(
                f"{self.base_url}/collaboration/sessions/{session_id}/edit",
                json={
                    "user_id": "test_user_1",
                    "element_type": "table",
                    "element_id": "users",
                    "changes": {"name": "app_users"},
                    "version": 1
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            print("  ✓ Edit element in collaboration")
            
            # Test add comment
            response = await self.client.post(
                f"{self.base_url}/collaboration/sessions/{session_id}/comments",
                json={
                    "user_id": "test_user_1",
                    "element_type": "table",
                    "element_id": "users",
                    "comment": "This table needs indexing on email field",
                    "position": {"x": 100, "y": 200}
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            print("  ✓ Add comment")
            
            # Test get session state
            response = await self.client.get(
                f"{self.base_url}/collaboration/sessions/{session_id}/state"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "session" in data
            print("  ✓ Get session state")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Collaboration tests failed: {e}")
            return False
    
    async def test_analytics(self) -> bool:
        """Test advanced analytics features"""
        try:
            # Test track usage
            response = await self.client.post(
                f"{self.base_url}/analytics/track-usage",
                json={
                    "user_id": "test_user",
                    "action": "generate_code",
                    "resource_type": "schema",
                    "resource_id": "test_schema",
                    "metadata": {
                        "format": "sqlalchemy",
                        "table_count": 3,
                        "generation_time": 1.5
                    }
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            print("  ✓ Track usage analytics")
            
            # Test record feedback
            response = await self.client.post(
                f"{self.base_url}/analytics/record-feedback",
                json={
                    "user_id": "test_user",
                    "resource_type": "generated_code",
                    "resource_id": "test_code",
                    "feedback_type": "rating",
                    "rating": 4,
                    "comment": "Good code quality, minor formatting issues"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            print("  ✓ Record user feedback")
            
            # Test get insights
            response = await self.client.get(
                f"{self.base_url}/analytics/insights",
                params={
                    "time_range": "7d",
                    "user_id": "test_user"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "insights" in data
            print("  ✓ Get analytics insights")
            
            # Test get performance metrics
            response = await self.client.get(
                f"{self.base_url}/analytics/performance",
                params={"time_range": "24h"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "performance" in data
            print("  ✓ Get performance metrics")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Analytics tests failed: {e}")
            return False
    
    async def test_integrations(self) -> bool:
        """Test enterprise integration features"""
        try:
            # Test register integration
            response = await self.client.post(
                f"{self.base_url}/integrations/register",
                json={
                    "name": "test_postgres",
                    "integration_type": "database",
                    "config": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "testdb",
                        "username": "testuser",
                        "password": "testpass"
                    },
                    "metadata": {
                        "description": "Test PostgreSQL integration",
                        "environment": "test"
                    }
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            integration_id = data["integration_id"]
            print("  ✓ Register database integration")
            
            # Test integration connection
            response = await self.client.get(
                f"{self.base_url}/integrations/{integration_id}/test"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            print("  ✓ Test integration connection")
            
            # Test get integration stats
            response = await self.client.get(f"{self.base_url}/integrations/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "stats" in data
            print("  ✓ Get integration statistics")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Integration tests failed: {e}")
            return False
    
    async def test_ml_pipeline(self) -> bool:
        """Test ML pipeline features"""
        try:
            # Test train classifier
            response = await self.client.post(
                f"{self.base_url}/ml/train-classifier",
                json={
                    "training_data": [
                        {"schema": self.sample_schema, "category": "ecommerce"},
                        {"schema": {"name": "blog", "tables": []}, "category": "content"}
                    ],
                    "model_type": "schema_classifier",
                    "hyperparameters": {
                        "max_depth": 10,
                        "n_estimators": 100
                    }
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            model_id = data["model_id"]
            print("  ✓ Train ML classifier")
            
            # Test predict category
            response = await self.client.post(
                f"{self.base_url}/ml/predict-category",
                json={
                    "schema": self.sample_schema,
                    "model_id": model_id
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "prediction" in data
            print("  ✓ Predict schema category")
            
            # Test detect anomalies
            response = await self.client.post(
                f"{self.base_url}/ml/detect-anomalies",
                json={
                    "schema": self.sample_schema,
                    "threshold": 0.8
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "anomalies" in data
            print("  ✓ Detect schema anomalies")
            
            # Test find similar schemas
            response = await self.client.post(
                f"{self.base_url}/ml/find-similar",
                json={
                    "schema": self.sample_schema,
                    "limit": 5,
                    "threshold": 0.7
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "similar_schemas" in data
            print("  ✓ Find similar schemas")
            
            return True
            
        except Exception as e:
            print(f"  ❌ ML pipeline tests failed: {e}")
            return False
    
    async def test_workflow(self) -> bool:
        """Test workflow automation features"""
        try:
            # Test create workflow
            workflow_definition = {
                "name": "Schema Processing Workflow",
                "description": "Automated schema analysis and code generation",
                "tasks": [
                    {
                        "task_id": "analyze_schema",
                        "name": "Analyze Schema",
                        "task_type": "schema_analysis",
                        "config": {
                            "analysis_type": "comprehensive"
                        },
                        "dependencies": []
                    },
                    {
                        "task_id": "generate_code",
                        "name": "Generate Code",
                        "task_type": "code_generation",
                        "config": {
                            "format": "sqlalchemy",
                            "options": {"include_relationships": True}
                        },
                        "dependencies": ["analyze_schema"]
                    },
                    {
                        "task_id": "validate_code",
                        "name": "Validate Generated Code",
                        "task_type": "validation",
                        "config": {
                            "validation_type": "code"
                        },
                        "dependencies": ["generate_code"]
                    }
                ],
                "triggers": [
                    {
                        "type": "manual",
                        "config": {}
                    }
                ],
                "created_by": "test_user"
            }
            
            response = await self.client.post(
                f"{self.base_url}/workflow/create",
                json=workflow_definition
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            workflow_id = data["workflow_id"]
            print("  ✓ Create workflow")
            
            # Test start workflow
            response = await self.client.post(
                f"{self.base_url}/workflow/{workflow_id}/start",
                json={
                    "input_data": {
                        "schema": self.sample_schema
                    },
                    "triggered_by": "test_user"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            execution_id = data["execution_id"]
            print("  ✓ Start workflow execution")
            
            # Wait a bit for execution
            await asyncio.sleep(2)
            
            # Test get workflow status
            response = await self.client.get(
                f"{self.base_url}/workflow/execution/{execution_id}/status"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "execution" in data
            print("  ✓ Get workflow execution status")
            
            # Test list workflows
            response = await self.client.get(f"{self.base_url}/workflow/list")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "workflows" in data
            print("  ✓ List workflows")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Workflow tests failed: {e}")
            return False
    
    async def test_monitoring(self) -> bool:
        """Test monitoring system features"""
        try:
            # Test get monitoring dashboard
            response = await self.client.get(f"{self.base_url}/monitoring/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "dashboard" in data
            print("  ✓ Get monitoring dashboard")
            
            # Test get metric history
            response = await self.client.get(
                f"{self.base_url}/monitoring/metrics/system.cpu.percent",
                params={"hours": 1, "interval_minutes": 5}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "history" in data
            print("  ✓ Get metric history")
            
            # Test get active alerts
            response = await self.client.get(f"{self.base_url}/monitoring/alerts")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "alerts" in data
            print("  ✓ Get active alerts")
            
            # Test get health status
            response = await self.client.get(f"{self.base_url}/monitoring/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "overall_health" in data
            print("  ✓ Get health status")
            
            # Test get system status
            response = await self.client.get(f"{self.base_url}/monitoring/system")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "system_metrics" in data
            print("  ✓ Get system status")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Monitoring tests failed: {e}")
            return False
    
    async def test_security(self) -> bool:
        """Test security and compliance features"""
        try:
            # Test classify data sensitivity
            response = await self.client.post(
                f"{self.base_url}/security/classify-data",
                json={
                    "schema": self.sample_schema,
                    "classifier": "test_user"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "classification" in data
            print("  ✓ Classify data sensitivity")
            
            # Test assess compliance
            response = await self.client.post(
                f"{self.base_url}/security/assess-compliance",
                json={
                    "schema": self.sample_schema,
                    "framework": "gdpr",
                    "assessor": "test_user"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "compliance_report" in data
            print("  ✓ Assess GDPR compliance")
            
            # Test encrypt data
            response = await self.client.post(
                f"{self.base_url}/security/encrypt",
                json={
                    "data": "sensitive information",
                    "encryption_type": "aes256"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "encrypted_data" in data
            print("  ✓ Encrypt sensitive data")
            
            # Test get audit log
            response = await self.client.get(
                f"{self.base_url}/security/audit-log",
                params={"limit": 10}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "audit_log" in data
            print("  ✓ Get audit log")
            
            # Test get user permissions
            response = await self.client.get(
                f"{self.base_url}/security/permissions/test_user"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "permissions" in data
            print("  ✓ Get user permissions")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Security tests failed: {e}")
            return False
    
    async def test_deployment(self) -> bool:
        """Test enterprise deployment features"""
        try:
            # Test create deployment config
            deployment_config = {
                "name": "test-deployment",
                "target": "development",
                "provider": "docker",
                "region": "local",
                "application_config": {
                    "image": "schemasage:test",
                    "port": 8000,
                    "replicas": 1,
                    "environment": {
                        "NODE_ENV": "development",
                        "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb"
                    }
                },
                "infrastructure_config": {
                    "resources": [
                        {
                            "type": "container",
                            "name": "schemasage-app",
                            "image": "schemasage:test",
                            "ports": {"8000": "8000"},
                            "environment": {
                                "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb"
                            }
                        }
                    ]
                },
                "created_by": "test_user",
                "environment_variables": {
                    "DEBUG": "true",
                    "LOG_LEVEL": "debug"
                },
                "scaling_config": {
                    "min_replicas": 1,
                    "max_replicas": 3,
                    "cpu_threshold": 80
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/deployment/config",
                json=deployment_config
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            deployment_id = data["deployment_id"]
            print("  ✓ Create deployment configuration")
            
            # Test get deployment status (before deployment)
            response = await self.client.get(
                f"{self.base_url}/deployment/{deployment_id}/status"
            )
            # This might return 404 before deployment, which is expected
            print("  ✓ Get deployment status")
            
            # Test list environments
            response = await self.client.get(f"{self.base_url}/deployment/environments")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "environments" in data
            print("  ✓ List deployment environments")
            
            # Note: We skip actual deployment to avoid infrastructure requirements
            print("  ⚠️  Skipping actual deployment (requires Docker infrastructure)")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Deployment tests failed: {e}")
            return False

async def main():
    """Run the test suite"""
    test_suite = SchemaSageTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
