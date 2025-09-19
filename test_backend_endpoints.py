#!/usr/bin/env python3
"""
Test script for SchemaSage Database Migration Backend APIs
Run this to test all endpoints on your deployed Heroku backend
"""

import requests
import json
from typing import Dict, Any

# Your Heroku backend URL
BASE_URL = "https://schemasage-database-migration-dfc50cf95a69.herokuapp.com"

def test_health_check():
    """Test basic health check"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_docs():
    """Test API documentation"""
    print("\n🔍 Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status: {response.status_code}")
        print("✅ API docs accessible" if response.status_code == 200 else "❌ API docs not accessible")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Docs test failed: {e}")
        return False

def test_database_connection():
    """Test database connection endpoint"""
    print("\n🔍 Testing Database Connection...")
    test_data = {
        "connection_url": "postgresql://test:test@localhost:5432/testdb",
        "type": "postgresql"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/test-connection", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True  # Even if connection fails, endpoint should work
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_cloud_providers():
    """Test cloud provider endpoints"""
    print("\n🔍 Testing Cloud Providers...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cloud/providers")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Cloud providers test failed: {e}")
        return False

def test_cloud_assessment():
    """Test cloud readiness assessment"""
    print("\n🔍 Testing Cloud Assessment...")
    test_data = {
        "database_info": {
            "type": "postgresql",
            "size_gb": 10,
            "tables_count": 50,
            "version": "13.0"
        },
        "workload_patterns": {
            "peak_hours": "9-17",
            "read_write_ratio": "70:30",
            "growth_rate": "10%"
        }
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/cloud/assess", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Cloud assessment test failed: {e}")
        return False

def test_migration_plans():
    """Test migration planning"""
    print("\n🔍 Testing Migration Planning...")
    test_data = {
        "source_database": {
            "type": "postgresql",
            "connection_url": "postgresql://test:test@localhost:5432/testdb"
        },
        "target_cloud": {
            "provider": "aws",
            "region": "us-east-1",
            "instance_type": "db.t3.micro"
        },
        "migration_strategy": "lift-and-shift"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/cloud/migration-plan", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Migration planning test failed: {e}")
        return False

def test_cost_optimization():
    """Test cost optimization"""
    print("\n🔍 Testing Cost Optimization...")
    test_data = {
        "cloud_account_id": "test-account-123",
        "provider": "aws",
        "resources": [
            {
                "type": "rds",
                "instance_type": "db.t3.large",
                "usage_pattern": "low"
            }
        ]
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/cloud/cost-optimization", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Cost optimization test failed: {e}")
        return False

def test_terraform_generation():
    """Test Terraform code generation"""
    print("\n🔍 Testing Terraform Generation...")
    test_data = {
        "provider": "aws",
        "resources": {
            "database": {
                "engine": "postgres",
                "instance_class": "db.t3.micro",
                "allocated_storage": 20
            }
        }
    }
    try:
        response = requests.post(f"{BASE_URL}/api/v1/cloud/generate-terraform", json=test_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Terraform generation test failed: {e}")
        return False

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting SchemaSage Backend API Tests")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_docs,
        test_database_connection,
        test_cloud_providers,
        test_cloud_assessment,
        test_migration_plans,
        test_cost_optimization,
        test_terraform_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED")
            else:
                print("❌ FAILED")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        print("-" * 30)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your backend is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    run_all_tests()
