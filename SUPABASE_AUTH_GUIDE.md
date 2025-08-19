# Supabase Auth Integration Guide

This guide explains how to update your SchemaSage application to use Supabase Auth with the new enterprise UUID-based schema.

## 1. Key Changes Made

### Models Updated:
- **BaseModel**: Now uses UUID instead of string for `id` field
- **ProjectModel**: `user_id` is now UUID, references `auth.users(id)`
- **FileModel**: `project_id` is now UUID, enhanced with enterprise features
- **SchemaModel**: Enhanced with confidence scores, detection metadata
- **New Models**: ChatSessionModel, ChatMessageModel, IntegrationModel

### Database Schema:
- All primary keys are now UUIDs
- Integration with Supabase `auth.users` table
- Row Level Security (RLS) enabled
- Enterprise features: full-text search, audit trails, soft deletes

## 2. Authentication Flow Changes

### Before (Custom Auth):
```python
# OLD: Custom username/password authentication
@app.post("/login")
def login(user: UserLogin):
    db_user = authenticate_user(db, user.username, user.password)
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token}

# OLD: Getting current user from database
def get_current_user(token: str):
    username = decode_token(token)
    return db.query(User).filter(User.username == username).first()
```

### After (Supabase Auth):
```python
# NEW: Use Supabase Auth
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Authentication is handled by Supabase Auth
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid auth header")
    
    token = auth_header.split(" ")[1]
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        return user.user
    except Exception as e:
        raise HTTPException(401, "Invalid token")
```

## 3. Updated FastAPI Dependencies

Create a new authentication dependency:

```python
# services/shared/auth.py
from fastapi import Depends, HTTPException, Request
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

async def get_current_user(request: Request):
    """Get current authenticated user from Supabase Auth."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Authentication required"
        )
    
    token = auth_header.split(" ")[1]
    try:
        response = supabase.auth.get_user(token)
        if response.user:
            return response.user
        else:
            raise HTTPException(401, "Invalid token")
    except Exception as e:
        raise HTTPException(401, f"Authentication failed: {str(e)}")
```

## 4. Updated API Endpoints

### Project Management Example:

```python
# services/project-management/routers/projects.py
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from shared.models import ProjectModel, ProjectCreateRequest
from shared.auth import get_current_user

router = APIRouter()

@router.post("/projects/", response_model=ProjectModel)
async def create_project(
    project_data: ProjectCreateRequest,
    current_user = Depends(get_current_user)
):
    # current_user.id is now a UUID from Supabase Auth
    project = ProjectModel(
        name=project_data.name,
        description=project_data.description,
        user_id=current_user.id,  # UUID from auth.users
        settings=project_data.settings,
        tags=project_data.tags
    )
    
    # Save to database using Supabase client
    response = supabase.table("projects").insert(project.dict()).execute()
    return ProjectModel(**response.data[0])

@router.get("/projects/", response_model=List[ProjectModel])
async def list_projects(current_user = Depends(get_current_user)):
    # RLS automatically filters by user_id
    response = supabase.table("projects").select("*").execute()
    return [ProjectModel(**item) for item in response.data]

@router.get("/projects/{project_id}", response_model=ProjectModel)
async def get_project(
    project_id: UUID,  # Now UUID instead of string
    current_user = Depends(get_current_user)
):
    response = supabase.table("projects").select("*").eq("id", str(project_id)).execute()
    if not response.data:
        raise HTTPException(404, "Project not found")
    return ProjectModel(**response.data[0])
```

## 5. Frontend Changes

### JavaScript/TypeScript:

```javascript
// OLD: String IDs
const projectId = "123";
const userId = "456";

// NEW: UUID IDs
const projectId = "550e8400-e29b-41d4-a716-446655440000";
const userId = "6ba7b810-9dad-11d1-80b4-00c04fd430c8";

// Authentication with Supabase
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

// Get current user
const { data: { user } } = await supabase.auth.getUser()

// Make authenticated API calls
const { data: projects } = await supabase
  .from('projects')
  .select('*')
  // RLS automatically filters by user
```

## 6. Environment Variables

Update your environment configuration:

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Remove old database URL if using Supabase directly
# DATABASE_URL=postgresql://... (not needed for Supabase)
```

## 7. Database Client Updates

### Instead of SQLAlchemy (if switching to Supabase client):

```python
# OLD: SQLAlchemy
from sqlalchemy.orm import Session
from models.user import User

def get_user_projects(db: Session, user_id: int):
    return db.query(Project).filter(Project.user_id == user_id).all()

# NEW: Supabase client
from supabase import create_client

def get_user_projects(user_id: str):
    response = supabase.table("projects").select("*").execute()
    # RLS automatically filters by user_id
    return response.data
```

## 8. Testing the Integration

### Create a Test User:

1. Go to your Supabase Dashboard
2. Navigate to Authentication > Users
3. Click "Add User"
4. Enter email and password
5. Note the UUID generated for the user

### Test API Endpoints:

```python
# Test script
import requests

# 1. Authenticate with Supabase (frontend handles this)
# 2. Get the JWT token from Supabase Auth
# 3. Use token in API calls

headers = {
    "Authorization": f"Bearer {supabase_jwt_token}",
    "Content-Type": "application/json"
}

# Test project creation
response = requests.post(
    "http://localhost:8000/projects/",
    headers=headers,
    json={
        "name": "Test Project",
        "description": "Testing UUID integration"
    }
)

print(response.json())
```

## 9. Migration Checklist

- [ ] Run the enterprise database schema in Supabase
- [ ] Update all model imports to use new UUID-based models
- [ ] Replace custom auth dependencies with Supabase auth
- [ ] Update API endpoints to handle UUID parameters
- [ ] Update frontend to use Supabase Auth SDK
- [ ] Test user registration and login flow
- [ ] Test CRUD operations with RLS policies
- [ ] Verify data isolation between users

## 10. Benefits of the New Architecture

✅ **Enterprise Security**: RLS ensures data isolation  
✅ **Scalable IDs**: UUIDs work better in distributed systems  
✅ **Managed Auth**: Supabase handles authentication, password reset, etc.  
✅ **Real-time Features**: Built-in real-time subscriptions  
✅ **Performance**: Optimized indexes and search capabilities  
✅ **Audit Trails**: Comprehensive tracking of all changes  

Your SchemaSage platform is now ready for enterprise deployment with production-grade security and scalability!
