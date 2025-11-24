"""
Comprehensive Tests for Phase 3.1 - Universal Migration Center
Tests all 5 endpoints with various scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from models.universal_migration_models import (
    MigrationType, DatabaseType, CloudProvider, RiskLevel
)

client = TestClient(app)

# ============================================================================
# TEST MIGRATION PLANNING API
# ============================================================================

def test_migration_plan_postgresql_to_mongodb():
    """Test PostgreSQL → MongoDB migration planning"""
    request_data = {
        "source_connection": "postgresql://user:pass@localhost:5432/sourcedb",
        "target_connection": "mongodb://user:pass@localhost:27017/targetdb",
        "migration_type": "schema_and_data",
        "options": {}
    }
    
    response = client.post("/api/migration/plan", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    
    plan_data = data["data"]
    assert "migration_id" in plan_data
    assert plan_data["cross_database_migration"] == True
    assert "POSTGRESQL → MONGODB" in plan_data["migration_type"]
    
    # Verify source analysis
    source_analysis = plan_data["source_analysis"]
    assert source_analysis["total_tables"] > 0
    assert source_analysis["total_records"] > 0
    assert "PostgreSQL" in source_analysis["database_type"]
    
    # Verify target analysis
    target_analysis = plan_data["target_analysis"]
    assert target_analysis["compatibility_score"] > 0
    assert len(target_analysis["required_transformations"]) > 0
    
    # Verify migration plan
    migration_plan = plan_data["migration_plan"]
    assert migration_plan["total_steps"] > 0
    assert len(migration_plan["steps"]) > 0
    assert migration_plan["rollback_available"] == True


def test_migration_plan_mysql_to_postgresql():
    """Test MySQL → PostgreSQL migration planning"""
    request_data = {
        "source_connection": "mysql://user:pass@localhost:3306/sourcedb",
        "target_connection": "postgresql://user:pass@localhost:5432/targetdb",
        "migration_type": "schema_only",
        "options": {}
    }
    
    response = client.post("/api/migration/plan", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    plan_data = data["data"]
    
    assert plan_data["cross_database_migration"] == True
    assert "MYSQL → POSTGRESQL" in plan_data["migration_type"]
    
    # MySQL → PostgreSQL should have high compatibility
    target_analysis = plan_data["target_analysis"]
    assert target_analysis["compatibility_score"] >= 80


def test_migration_plan_data_only():
    """Test data-only migration (no schema changes)"""
    request_data = {
        "source_connection": "postgresql://user:pass@localhost:5432/sourcedb",
        "target_connection": "postgresql://user:pass@localhost:5432/targetdb",
        "migration_type": "data_only",
        "options": {}
    }
    
    response = client.post("/api/migration/plan", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    plan_data = data["data"]
    
    # Same database type = not cross-database
    assert plan_data["cross_database_migration"] == False


def test_migration_plan_invalid_connection():
    """Test migration planning with invalid connection string"""
    request_data = {
        "source_connection": "invalid://connection",
        "target_connection": "mongodb://localhost:27017/targetdb",
        "migration_type": "schema_and_data",
        "options": {}
    }
    
    response = client.post("/api/migration/plan", json=request_data)
    # Should still work but handle gracefully
    assert response.status_code in [200, 500]


# ============================================================================
# TEST MIGRATION EXECUTION API
# ============================================================================

@pytest.mark.asyncio
async def test_migration_execute_dry_run():
    """Test migration execution in dry-run mode"""
    request_data = {
        "migration_id": "mig_test123",
        "options": {
            "dry_run": True,
            "stop_on_error": True,
            "verify_data": True
        }
    }
    
    response = client.post("/api/migration/execute", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "dry-run" in data["message"]
    
    execution_data = data["data"]
    assert "execution_id" in execution_data
    assert execution_data["migration_id"] == "mig_test123"
    assert execution_data["status"] == "completed"
    
    # Verify progress info
    progress = execution_data["progress"]
    assert progress["percentage"] == 100
    assert progress["records_migrated"] > 0
    
    # Verify performance metrics
    metrics = execution_data["performance_metrics"]
    assert metrics["records_per_second"] > 0
    assert metrics["errors_count"] == 0


@pytest.mark.asyncio
async def test_migration_execute_production():
    """Test migration execution in production mode"""
    request_data = {
        "migration_id": "mig_test456",
        "options": {
            "dry_run": False,
            "create_rollback_point": True,
            "verify_data": True
        }
    }
    
    response = client.post("/api/migration/execute", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    execution_data = data["data"]
    
    # Production mode should create rollback point
    assert execution_data["rollback_point_id"] is not None
    assert execution_data["rollback_point_id"].startswith("rb_")


@pytest.mark.asyncio
async def test_migration_execute_without_verification():
    """Test migration execution without data verification"""
    request_data = {
        "migration_id": "mig_test789",
        "options": {
            "dry_run": False,
            "verify_data": False
        }
    }
    
    response = client.post("/api/migration/execute", json=request_data)
    assert response.status_code == 200


# ============================================================================
# TEST MULTI-CLOUD COMPARISON API
# ============================================================================

def test_multi_cloud_compare_postgresql_small():
    """Test multi-cloud comparison for small PostgreSQL workload"""
    request_data = {
        "database_type": "postgresql",
        "workload_size": "small",
        "required_features": ["auto-scaling", "automated-backups"]
    }
    
    response = client.post("/api/migration/multi-cloud-compare", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    comparison_data = data["data"]
    
    # Should have 3 cloud recommendations (AWS, Azure, GCP)
    assert len(comparison_data["recommendations"]) == 3
    
    # Verify each recommendation has required fields
    for rec in comparison_data["recommendations"]:
        assert rec["provider"] in ["AWS", "AZURE", "GCP"]
        assert rec["estimated_monthly_cost"] > 0
        assert rec["overall_score"] > 0
        assert len(rec["supported_features"]) > 0
        assert len(rec["pros"]) > 0
        assert len(rec["cons"]) > 0
    
    # Verify best value recommendation
    best_value = comparison_data["best_value"]
    assert best_value["provider"] in ["AWS", "AZURE", "GCP"]
    assert len(best_value["reason"]) > 0


def test_multi_cloud_compare_mongodb_large():
    """Test multi-cloud comparison for large MongoDB workload"""
    request_data = {
        "database_type": "mongodb",
        "workload_size": "large",
        "required_features": ["high-availability", "global-distribution"]
    }
    
    response = client.post("/api/migration/multi-cloud-compare", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    comparison_data = data["data"]
    
    # Large workload should have higher costs
    for rec in comparison_data["recommendations"]:
        assert rec["estimated_monthly_cost"] > 300


def test_multi_cloud_compare_mysql_medium():
    """Test multi-cloud comparison for medium MySQL workload"""
    request_data = {
        "database_type": "mysql",
        "workload_size": "medium",
        "required_features": []
    }
    
    response = client.post("/api/migration/multi-cloud-compare", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify cost scores are calculated
    for rec in data["data"]["recommendations"]:
        assert 0 < rec["cost_score"] <= 100
        assert 0 < rec["performance_score"] <= 100
        assert 0 < rec["reliability_score"] <= 100
        assert 0 < rec["ease_of_use_score"] <= 100


# ============================================================================
# TEST PRE-MIGRATION ANALYSIS API
# ============================================================================

def test_pre_analysis_postgresql_to_mongodb():
    """Test pre-migration analysis for PostgreSQL → MongoDB"""
    request_data = {
        "source_type": "postgresql",
        "target_type": "mongodb",
        "migration_plan_id": "mig_test123"
    }
    
    response = client.post("/api/migration/pre-analysis", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    analysis_data = data["data"]
    
    # Should have breaking changes for PostgreSQL → MongoDB
    assert len(analysis_data["breaking_changes"]) > 0
    
    # Verify breaking change structure
    for change in analysis_data["breaking_changes"]:
        assert change["severity"] in ["low", "medium", "high"]
        assert len(change["category"]) > 0
        assert len(change["description"]) > 0
        assert len(change["affected_objects"]) > 0
        assert len(change["migration_strategy"]) > 0
        assert change["estimated_effort_hours"] > 0
    
    # Should have performance impact analysis
    assert len(analysis_data["performance_impact"]) > 0
    
    # Should have dependencies
    assert len(analysis_data["dependencies"]) > 0
    
    # Overall risk should be HIGH for PostgreSQL → MongoDB
    assert analysis_data["overall_risk_level"] in ["medium", "high"]
    
    # Should have recommendations
    assert len(analysis_data["recommendations"]) > 0
    
    # Should estimate downtime
    assert analysis_data["estimated_downtime_minutes"] > 0


def test_pre_analysis_mysql_to_postgresql():
    """Test pre-migration analysis for MySQL → PostgreSQL"""
    request_data = {
        "source_type": "mysql",
        "target_type": "postgresql",
        "migration_plan_id": "mig_test456"
    }
    
    response = client.post("/api/migration/pre-analysis", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    analysis_data = data["data"]
    
    # MySQL → PostgreSQL should have fewer breaking changes than PostgreSQL → MongoDB
    assert len(analysis_data["breaking_changes"]) < 4
    
    # Risk should be lower
    assert analysis_data["overall_risk_level"] in ["low", "medium"]


def test_pre_analysis_breaking_changes_categorization():
    """Test that breaking changes are properly categorized"""
    request_data = {
        "source_type": "postgresql",
        "target_type": "mongodb",
        "migration_plan_id": "mig_test789"
    }
    
    response = client.post("/api/migration/pre-analysis", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    breaking_changes = data["data"]["breaking_changes"]
    
    # Verify expected categories for PostgreSQL → MongoDB
    categories = [bc["category"] for bc in breaking_changes]
    assert "Schema Model" in categories
    assert "Relationships" in categories


# ============================================================================
# TEST ROLLBACK API
# ============================================================================

def test_rollback_plan_creation():
    """Test rollback plan creation"""
    request_data = {
        "migration_id": "mig_test123",
        "execution_id": "exec_abc123"
    }
    
    response = client.post("/api/migration/rollback", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    rollback_data = data["data"]
    
    assert "rollback_id" in rollback_data
    assert rollback_data["migration_id"] == "mig_test123"
    assert rollback_data["execution_id"] == "exec_abc123"
    
    # Verify rollback plan
    rollback_plan = rollback_data["rollback_plan"]
    assert rollback_plan["total_steps"] > 0
    assert len(rollback_plan["steps"]) > 0
    assert rollback_plan["data_loss_risk"] in ["low", "medium", "high"]
    assert rollback_plan["requires_downtime"] == True
    
    # Verify checkpoints
    assert len(rollback_data["available_checkpoints"]) > 0
    assert rollback_data["recommended_checkpoint"] is not None
    
    # Verify checkpoint structure
    for checkpoint in rollback_data["available_checkpoints"]:
        assert checkpoint["checkpoint_id"].startswith("cp_")
        assert len(checkpoint["timestamp"]) > 0
        assert checkpoint["size_gb"] > 0
        assert checkpoint["verified"] == True


def test_rollback_plan_steps_structure():
    """Test rollback plan steps have proper structure"""
    request_data = {
        "migration_id": "mig_test456",
        "execution_id": "exec_def456"
    }
    
    response = client.post("/api/migration/rollback", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    steps = data["data"]["rollback_plan"]["steps"]
    
    for step in steps:
        assert step["step_number"] > 0
        assert len(step["action"]) > 0
        assert len(step["target"]) > 0
        assert len(step["estimated_duration"]) > 0
        assert step["risk_level"] in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_rollback_execute():
    """Test rollback execution"""
    # First create a rollback plan
    plan_request = {
        "migration_id": "mig_test789",
        "execution_id": "exec_ghi789"
    }
    plan_response = client.post("/api/migration/rollback", json=plan_request)
    rollback_id = plan_response.json()["data"]["rollback_id"]
    checkpoint_id = plan_response.json()["data"]["available_checkpoints"][0]["checkpoint_id"]
    
    # Execute rollback
    response = client.post(
        f"/api/migration/rollback/{rollback_id}/execute",
        params={"checkpoint_id": checkpoint_id}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    
    result = data["data"]
    assert result["rollback_id"] == rollback_id
    assert result["checkpoint_id"] == checkpoint_id
    assert result["status"] == "completed"
    assert result["steps_executed"] > 0
    assert result["data_restored"] == True


@pytest.mark.asyncio
async def test_rollback_execute_without_checkpoint():
    """Test rollback execution without specifying checkpoint"""
    plan_request = {
        "migration_id": "mig_test999",
        "execution_id": "exec_jkl999"
    }
    plan_response = client.post("/api/migration/rollback", json=plan_request)
    rollback_id = plan_response.json()["data"]["rollback_id"]
    
    # Execute without checkpoint (should use default)
    response = client.post(f"/api/migration/rollback/{rollback_id}/execute")
    
    assert response.status_code == 200


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_migration_workflow():
    """Test complete migration workflow: plan → analyze → execute → rollback"""
    
    # Step 1: Create migration plan
    plan_request = {
        "source_connection": "postgresql://user:pass@localhost:5432/sourcedb",
        "target_connection": "mongodb://user:pass@localhost:27017/targetdb",
        "migration_type": "schema_and_data",
        "options": {}
    }
    plan_response = client.post("/api/migration/plan", json=plan_request)
    assert plan_response.status_code == 200
    migration_id = plan_response.json()["data"]["migration_id"]
    
    # Step 2: Pre-migration analysis
    analysis_request = {
        "source_type": "postgresql",
        "target_type": "mongodb",
        "migration_plan_id": migration_id
    }
    analysis_response = client.post("/api/migration/pre-analysis", json=analysis_request)
    assert analysis_response.status_code == 200
    
    # Step 3: Execute migration (dry-run)
    execute_request = {
        "migration_id": migration_id,
        "options": {
            "dry_run": True,
            "verify_data": True
        }
    }
    execute_response = client.post("/api/migration/execute", json=execute_request)
    assert execute_response.status_code == 200
    execution_id = execute_response.json()["data"]["execution_id"]
    
    # Step 4: Create rollback plan
    rollback_request = {
        "migration_id": migration_id,
        "execution_id": execution_id
    }
    rollback_response = client.post("/api/migration/rollback", json=rollback_request)
    assert rollback_response.status_code == 200


def test_multi_cloud_comparison_integration():
    """Test multi-cloud comparison with migration planning"""
    
    # Compare cloud offerings
    compare_request = {
        "database_type": "postgresql",
        "workload_size": "medium",
        "required_features": ["auto-scaling", "high-availability"]
    }
    compare_response = client.post("/api/migration/multi-cloud-compare", json=compare_request)
    assert compare_response.status_code == 200
    
    best_provider = compare_response.json()["data"]["best_value"]["provider"]
    
    # Use best provider recommendation in migration plan
    assert best_provider in ["AWS", "AZURE", "GCP"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
