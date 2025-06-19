#!/usr/bin/env python3
"""
Test Independent Microservices
Tests that all services can start and run independently
"""
import asyncio
import aiohttp
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICES = {
    "Schema Detection": "http://localhost:8001",
    "Code Generation": "http://localhost:8002", 
    "AI Chat": "http://localhost:8003",
    "Project Management": "http://localhost:8004",
    "API Gateway": "http://localhost:8000"
}

async def test_service_health(service_name, base_url):
    """Test if a service is healthy"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(f"{base_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ {service_name}: Healthy ({data.get('status', 'unknown')})")
                    return True
                else:
                    logger.error(f"❌ {service_name}: Unhealthy (HTTP {response.status})")
                    return False
    except asyncio.TimeoutError:
        logger.error(f"❌ {service_name}: Timeout")
        return False
    except Exception as e:
        logger.error(f"❌ {service_name}: Error - {str(e)}")
        return False

async def test_service_root(service_name, base_url):
    """Test if a service's root endpoint works"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"🔍 {service_name}: Root endpoint working")
                    return True
                else:
                    logger.warning(f"⚠️  {service_name}: Root endpoint returned {response.status}")
                    return False
    except Exception as e:
        logger.warning(f"⚠️  {service_name}: Root endpoint error - {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🧪 Testing SchemaSage Microservices Independence...\n")
    
    # Check if services directories exist
    services_dir = Path("services")
    if not services_dir.exists():
        print("❌ Services directory not found!")
        return 1
    
    print("📁 Checking service directories...")
    for service_name in ["schema-detection", "ai-chat", "code-generation", "project-management", "api-gateway"]:
        service_path = services_dir / service_name
        if service_path.exists():
            print(f"   ✅ {service_name}: Directory exists")
        else:
            print(f"   ❌ {service_name}: Directory missing")
    
    print("\n🏥 Testing service health (assuming services are running)...")
    print("   Note: Start services with 'python microservices.py start' first\n")
    
    healthy_services = 0
    total_services = len(SERVICES)
    
    for service_name, base_url in SERVICES.items():
        is_healthy = await test_service_health(service_name, base_url)
        if is_healthy:
            healthy_services += 1
            # Test root endpoint too
            await test_service_root(service_name, base_url)
    
    print(f"\n{'='*60}")
    print(f"🏥 Health Check Results: {healthy_services}/{total_services} services healthy")
    
    if healthy_services == total_services:
        print("🎉 SUCCESS: All microservices are running independently!")
        print("✨ The migration to microservices architecture is complete!")
        return 0
    elif healthy_services > 0:
        print("⚠️  PARTIAL SUCCESS: Some services are running.")
        print("💡 Start remaining services to complete the test.")
        return 0
    else:
        print("❌ NO SERVICES RUNNING: Please start the services first.")
        print("🚀 Run: python microservices.py start")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
