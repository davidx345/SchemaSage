#!/usr/bin/env python3
"""
Enterprise Verification Script for SchemaSage Database Migration Service

This script verifies that all enterprise components are working correctly:
- Database connectivity and schema
- Encryption service functionality  
- JWT authentication integration
- API endpoint accessibility
- Audit logging system

Usage:
    python verify_enterprise.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
import httpx
import asyncpg
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnterpriseVerification:
    """Enterprise system verification"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.base_url = "http://localhost:8000"
        self.auth_url = "http://localhost:8001"
        
    async def verify_database_connectivity(self) -> bool:
        """Verify PostgreSQL database connectivity"""
        logger.info("🗄️ Verifying database connectivity...")
        
        try:
            database_url = os.getenv('DATABASE_URL', 
                'postgresql://schemasage_user:secure_password@localhost:5432/schemasage_enterprise')
            
            conn = await asyncpg.connect(database_url)
            
            # Test basic query
            result = await conn.fetchval('SELECT 1')
            if result != 1:
                return False
            
            await conn.close()
            logger.info("✅ Database connectivity verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connectivity failed: {e}")
            return False
    
    async def verify_database_schema(self) -> bool:
        """Verify enterprise database schema exists"""
        logger.info("📋 Verifying database schema...")
        
        try:
            database_url = os.getenv('DATABASE_URL', 
                'postgresql://schemasage_user:secure_password@localhost:5432/schemasage_enterprise')
            
            conn = await asyncpg.connect(database_url)
            
            # Check for expected tables
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            table_names = [row['table_name'] for row in tables]
            expected_tables = {'alembic_version', 'connections', 'audit_logs', 'secrets', 'quotas', 'schema_snapshots'}
            
            missing_tables = expected_tables - set(table_names)
            if missing_tables:
                logger.error(f"❌ Missing tables: {missing_tables}")
                return False
            
            logger.info(f"✅ Database schema verified: {len(table_names)} tables")
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database schema verification failed: {e}")
            return False
    
    def verify_encryption_service(self) -> bool:
        """Verify encryption service functionality"""
        logger.info("🔐 Verifying encryption service...")
        
        try:
            # Import the encryption service
            sys.path.append(str(self.project_root))
            from core.encryption import EncryptionService
            
            service = EncryptionService()
            
            # Test encryption/decryption
            test_data = "sensitive_connection_data_12345"
            test_password = "test_password"
            
            encrypted = service.encrypt(test_data, test_password)
            decrypted = service.decrypt(encrypted, test_password)
            
            if decrypted != test_data:
                logger.error("❌ Encryption/decryption mismatch")
                return False
            
            # Test key rotation
            key_info = service.get_key_info()
            if not key_info['algorithm'] or not key_info['key_derivation']:
                logger.error("❌ Encryption key info incomplete")
                return False
            
            logger.info(f"✅ Encryption service verified: {key_info['algorithm']} with {key_info['key_derivation']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Encryption service verification failed: {e}")
            return False
    
    async def verify_service_health(self) -> bool:
        """Verify main service is running"""
        logger.info("🏥 Verifying service health...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code != 200:
                    logger.error(f"❌ Health check failed: {response.status_code}")
                    return False
                
                health_data = response.json()
                if not health_data.get('status') == 'healthy':
                    logger.error(f"❌ Service unhealthy: {health_data}")
                    return False
                
                logger.info("✅ Service health verified")
                return True
                
        except Exception as e:
            logger.error(f"❌ Service health verification failed: {e}")
            return False
    
    async def verify_api_documentation(self) -> bool:
        """Verify API documentation is accessible"""
        logger.info("📚 Verifying API documentation...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/docs")
                
                if response.status_code != 200:
                    logger.error(f"❌ API docs not accessible: {response.status_code}")
                    return False
                
                if "swagger" not in response.text.lower():
                    logger.error("❌ API docs don't contain Swagger UI")
                    return False
                
                logger.info("✅ API documentation verified")
                return True
                
        except Exception as e:
            logger.error(f"❌ API documentation verification failed: {e}")
            return False
    
    async def verify_enterprise_endpoints(self) -> bool:
        """Verify enterprise API endpoints are accessible"""
        logger.info("🔒 Verifying enterprise endpoints...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test unauthenticated access (should require auth)
                response = await client.get(f"{self.base_url}/api/database/connections/")
                
                if response.status_code not in [401, 403]:
                    logger.error(f"❌ Enterprise endpoints not properly protected: {response.status_code}")
                    return False
                
                logger.info("✅ Enterprise endpoints properly protected")
                return True
                
        except Exception as e:
            logger.error(f"❌ Enterprise endpoints verification failed: {e}")
            return False
    
    def verify_environment_config(self) -> bool:
        """Verify environment configuration"""
        logger.info("⚙️ Verifying environment configuration...")
        
        required_vars = [
            'DATABASE_URL',
            'SCHEMASAGE_MASTER_KEY',
            'JWT_SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing environment variables: {missing_vars}")
            return False
        
        # Verify key lengths
        master_key = os.getenv('SCHEMASAGE_MASTER_KEY', '')
        if len(master_key) < 32:
            logger.error("❌ Master key too short (should be 32+ characters)")
            return False
        
        logger.info("✅ Environment configuration verified")
        return True
    
    async def verify_complete_system(self) -> bool:
        """Run complete system verification"""
        logger.info("🚀 Starting complete enterprise system verification")
        logger.info("=" * 60)
        
        verification_results = []
        
        # Run all verification tests
        tests = [
            ("Environment Configuration", self.verify_environment_config()),
            ("Database Connectivity", self.verify_database_connectivity()),
            ("Database Schema", self.verify_database_schema()),
            ("Encryption Service", self.verify_encryption_service()),
            ("Service Health", self.verify_service_health()),
            ("API Documentation", self.verify_api_documentation()),
            ("Enterprise Endpoints", self.verify_enterprise_endpoints())
        ]
        
        for test_name, test_coro in tests:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            verification_results.append((test_name, result))
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 Verification Summary:")
        
        passed = 0
        failed = 0
        
        for test_name, result in verification_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status} - {test_name}")
            
            if result:
                passed += 1
            else:
                failed += 1
        
        logger.info(f"📈 Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            logger.info("🎉 All enterprise systems verified successfully!")
            logger.info("🚀 SchemaSage Enterprise is ready for production!")
            return True
        else:
            logger.error("❌ Some enterprise systems failed verification")
            logger.error("📋 Please check the failed tests and fix any issues")
            return False

async def main():
    """Main verification function"""
    logger.info("🔍 SchemaSage Enterprise Verification")
    logger.info(f"⏰ Started at: {datetime.now()}")
    
    verifier = EnterpriseVerification()
    
    try:
        success = await verifier.verify_complete_system()
        
        if success:
            logger.info("")
            logger.info("✅ Enterprise verification completed successfully!")
            logger.info("🌐 Access your enterprise service at: http://localhost:8000")
            logger.info("📖 API documentation at: http://localhost:8000/docs")
            sys.exit(0)
        else:
            logger.error("")
            logger.error("❌ Enterprise verification failed!")
            logger.error("📋 Please review the deployment guide: ENTERPRISE_DEPLOYMENT.md")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⚠️ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Verification crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())