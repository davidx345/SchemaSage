#!/usr/bin/env python3
"""
Test script to verify database initialization across all services
"""
import asyncio
import sys
import os
from pathlib import Path

# Add services to path
sys.path.append(str(Path(__file__).parent / "services"))

async def test_ai_chat_db():
    """Test AI Chat database initialization"""
    try:
        sys.path.append("services/ai-chat")
        from core.database_service import ChatDatabaseService
        
        db_service = ChatDatabaseService()
        await db_service.initialize()
        print("✅ AI Chat database initialized successfully")
        await db_service.close()
        return True
    except Exception as e:
        print(f"❌ AI Chat database failed: {e}")
        return False

async def test_schema_detection_db():
    """Test Schema Detection database initialization"""
    try:
        sys.path.append("services/schema-detection")
        from core.database_service import SchemaDetectionDatabaseService
        
        db_service = SchemaDetectionDatabaseService()
        await db_service.initialize()
        print("✅ Schema Detection database initialized successfully")
        await db_service.close()
        return True
    except Exception as e:
        print(f"❌ Schema Detection database failed: {e}")
        return False

async def test_project_management_db():
    """Test Project Management database initialization"""
    try:
        sys.path.append("services/project-management")
        from core.database_service import ProjectManagementDatabaseService
        
        db_service = ProjectManagementDatabaseService()
        await db_service.initialize()
        print("✅ Project Management database initialized successfully")
        await db_service.close()
        return True
    except Exception as e:
        print(f"❌ Project Management database failed: {e}")
        return False

async def test_code_generation_db():
    """Test Code Generation database initialization"""
    try:
        sys.path.append("services/code-generation")
        from core.database_service import CodeGenerationDatabaseService
        
        db_service = CodeGenerationDatabaseService()
        await db_service.initialize()
        print("✅ Code Generation database initialized successfully")
        await db_service.close()
        return True
    except Exception as e:
        print(f"❌ Code Generation database failed: {e}")
        return False

async def test_database_migration_db():
    """Test Database Migration database initialization"""
    try:
        sys.path.append("services/database-migration")
        from core.database_service import EnterpriseConnectionStore
        
        db_service = EnterpriseConnectionStore()
        await db_service.initialize()
        print("✅ Database Migration database initialized successfully")
        await db_service.close()
        return True
    except Exception as e:
        print(f"❌ Database Migration database failed: {e}")
        return False

async def main():
    """Run all database tests"""
    print("🔍 Testing database initialization across all services...")
    print("=" * 60)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️  DATABASE_URL environment variable not set!")
        print("   Using default PostgreSQL connection")
    else:
        print(f"📊 Using database: {database_url[:50]}...")
    
    print()
    
    # Test all services
    results = []
    results.append(await test_ai_chat_db())
    results.append(await test_schema_detection_db())
    results.append(await test_project_management_db())
    results.append(await test_code_generation_db())
    results.append(await test_database_migration_db())
    
    print()
    print("=" * 60)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"🎉 All {total_count} database services initialized successfully!")
        print("✅ Your Supabase database should now have all the required tables")
    else:
        print(f"⚠️  {success_count}/{total_count} database services initialized successfully")
        print("   Check the error messages above for troubleshooting")
    
    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)