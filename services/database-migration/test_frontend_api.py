"""
Test script to verify frontend API compatibility
"""
import asyncio
import json
from routers.frontend_api import test_connection_url, import_schema_url

async def test_frontend_api():
    """Test the frontend API endpoints with expected request formats"""
    
    print("🧪 Testing Frontend API Compatibility")
    print("=" * 50)
    
    # Test 1: Connection URL Testing
    print("\n1. Testing Connection URL Endpoint")
    print("-" * 30)
    
    test_request = {
        "connection_url": "postgresql://user:pass@localhost:5432/dbname",
        "type": "postgresql"
    }
    
    try:
        result = await test_connection_url(test_request)
        print("✅ Connection test successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    # Test 2: Schema Import
    print("\n2. Testing Schema Import Endpoint")
    print("-" * 30)
    
    import_request = {
        "connection_url": "postgresql://user:pass@localhost:5432/dbname",
        "type": "postgresql"
    }
    
    try:
        # Mock background tasks
        class MockBackgroundTasks:
            def add_task(self, func, *args, **kwargs):
                pass
        
        result = await import_schema_url(import_request, MockBackgroundTasks())
        print("✅ Schema import successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Schema import failed: {e}")
    
    # Test 3: Different Database Types
    print("\n3. Testing Different Database Types")
    print("-" * 30)
    
    db_tests = [
        {"connection_url": "mysql://user:pass@localhost:3306/dbname", "type": "mysql"},
        {"connection_url": "mongodb://user:pass@localhost:27017/dbname", "type": "mongodb"},
        {"connection_url": "sqlite:///path/to/database.db", "type": "sqlite"},
        {"connection_url": "redis://user:pass@localhost:6379/0", "type": "redis"}
    ]
    
    for test_case in db_tests:
        try:
            result = await test_connection_url(test_case)
            print(f"✅ {test_case['type']}: {result['success']}")
        except Exception as e:
            print(f"❌ {test_case['type']}: {e}")
    
    # Test 4: Error Handling
    print("\n4. Testing Error Handling")
    print("-" * 30)
    
    error_tests = [
        {"connection_url": "", "type": "postgresql"},  # Empty URL
        {"connection_url": "invalid://url", "type": "invalid"},  # Invalid scheme
        {"connection_url": "postgresql://user@", "type": "postgresql"},  # Incomplete URL
    ]
    
    for test_case in error_tests:
        try:
            result = await test_connection_url(test_case)
            print(f"Response for '{test_case['connection_url']}': {result['success']} - {result['message']}")
        except Exception as e:
            print(f"Exception for '{test_case['connection_url']}': {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Frontend API Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_frontend_api())
