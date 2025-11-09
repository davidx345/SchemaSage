# Backend User Isolation Bug - Fix Guide

## Problem Summary
User activities, statistics, and data are being shared across ALL users instead of being isolated to individual users. This is a critical security and data privacy issue.

## Root Cause
Backend API endpoints are NOT filtering queries by authenticated user ID. When User A requests their data, they see data from User B, User C, etc.

---

## What to Check and Fix in Your Backend

### 1. **Authentication Middleware**

Check your authentication middleware that decodes JWT tokens:

```python
# Example: Your auth middleware (FastAPI)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id") or payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user_id  # ⚠️ Make sure this returns the user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Check:** Does your middleware extract `user_id` from the JWT payload and make it available to endpoints?

---

### 2. **Dashboard Stats Endpoint**

Your `/api/stats` or `/api/dashboard` endpoint must filter by user:

#### ❌ WRONG (Current Implementation):
```python
@app.get("/api/stats")
async def get_stats():
    # BUG: Returns stats for ALL users
    schemas = db.query(Schema).all()
    apis = db.query(API).all()
    activities = db.query(Activity).all()
    
    return {
        "schemasGenerated": len(schemas),
        "apisScaffolded": len(apis),
        "recentActivities": activities
    }
```

#### ✅ CORRECT (Fixed):
```python
@app.get("/api/stats")
async def get_stats(user_id: str = Depends(get_current_user)):
    # FIXED: Filter by authenticated user
    schemas = db.query(Schema).filter(Schema.user_id == user_id).all()
    apis = db.query(API).filter(API.user_id == user_id).all()
    activities = db.query(Activity).filter(Activity.user_id == user_id).all()
    
    return {
        "schemasGenerated": len(schemas),
        "apisScaffolded": len(apis),
        "recentActivities": activities
    }
```

---

### 3. **Recent Activities Endpoint**

Check `/api/activities` or similar endpoints:

#### ❌ WRONG:
```python
@app.get("/api/activities")
async def get_activities():
    activities = db.query(Activity).order_by(Activity.created_at.desc()).limit(10).all()
    return activities
```

#### ✅ CORRECT:
```python
@app.get("/api/activities")
async def get_activities(user_id: str = Depends(get_current_user)):
    activities = db.query(Activity).filter(
        Activity.user_id == user_id
    ).order_by(Activity.created_at.desc()).limit(10).all()
    return activities
```

---

### 4. **Active Developers Count**

The "Active Developers" stat is showing 3 when you only have 1 user active:

#### ❌ WRONG:
```python
@app.get("/api/stats/active-developers")
async def get_active_developers():
    # BUG: Counts ALL users instead of just the current user
    five_minutes_ago = datetime.now() - timedelta(minutes=5)
    active_count = db.query(User).filter(
        User.last_active > five_minutes_ago
    ).count()
    return {"activeDevelopers": active_count}
```

#### ✅ CORRECT:
```python
@app.get("/api/stats/active-developers")
async def get_active_developers(user_id: str = Depends(get_current_user)):
    # FIXED: Returns 1 if current user is active, 0 otherwise
    five_minutes_ago = datetime.now() - timedelta(minutes=5)
    user = db.query(User).filter(
        User.id == user_id,
        User.last_active > five_minutes_ago
    ).first()
    
    return {"activeDevelopers": 1 if user else 0}
```

Or if you want to show team members who are active:

```python
@app.get("/api/stats/active-developers")
async def get_active_developers(user_id: str = Depends(get_current_user)):
    # Get user's team/organization
    user = db.query(User).filter(User.id == user_id).first()
    team_id = user.team_id
    
    # Count active developers in the same team
    five_minutes_ago = datetime.now() - timedelta(minutes=5)
    active_count = db.query(User).filter(
        User.team_id == team_id,
        User.last_active > five_minutes_ago
    ).count()
    
    return {"activeDevelopers": active_count}
```

---

### 5. **Projects Endpoint**

Check `/api/projects`:

#### ❌ WRONG:
```python
@app.get("/api/projects")
async def get_projects():
    projects = db.query(Project).all()  # Returns ALL projects
    return projects
```

#### ✅ CORRECT:
```python
@app.get("/api/projects")
async def get_projects(user_id: str = Depends(get_current_user)):
    projects = db.query(Project).filter(
        Project.user_id == user_id
    ).all()
    return projects
```

---

### 6. **Schema CRUD Endpoints**

Every endpoint that returns user data must filter by user_id:

```python
# CREATE - Set user_id when creating
@app.post("/api/schemas")
async def create_schema(schema_data: dict, user_id: str = Depends(get_current_user)):
    new_schema = Schema(**schema_data, user_id=user_id)  # ✅ Set user_id
    db.add(new_schema)
    db.commit()
    return new_schema

# READ - Filter by user_id
@app.get("/api/schemas/{schema_id}")
async def get_schema(schema_id: str, user_id: str = Depends(get_current_user)):
    schema = db.query(Schema).filter(
        Schema.id == schema_id,
        Schema.user_id == user_id  # ✅ Verify ownership
    ).first()
    
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    return schema

# UPDATE - Verify ownership
@app.put("/api/schemas/{schema_id}")
async def update_schema(schema_id: str, data: dict, user_id: str = Depends(get_current_user)):
    schema = db.query(Schema).filter(
        Schema.id == schema_id,
        Schema.user_id == user_id  # ✅ Verify ownership
    ).first()
    
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # Update schema...
    return schema

# DELETE - Verify ownership
@app.delete("/api/schemas/{schema_id}")
async def delete_schema(schema_id: str, user_id: str = Depends(get_current_user)):
    schema = db.query(Schema).filter(
        Schema.id == schema_id,
        Schema.user_id == user_id  # ✅ Verify ownership
    ).first()
    
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    db.delete(schema)
    db.commit()
    return {"message": "Deleted successfully"}
```

---

## Database Schema Requirements

Ensure your database tables have `user_id` columns:

```sql
-- Add user_id to all user-specific tables
ALTER TABLE schemas ADD COLUMN user_id VARCHAR(255);
ALTER TABLE projects ADD COLUMN user_id VARCHAR(255);
ALTER TABLE activities ADD COLUMN user_id VARCHAR(255);
ALTER TABLE api_scaffolds ADD COLUMN user_id VARCHAR(255);
ALTER TABLE migrations ADD COLUMN user_id VARCHAR(255);
ALTER TABLE connections ADD COLUMN user_id VARCHAR(255);
ALTER TABLE etl_pipelines ADD COLUMN user_id VARCHAR(255);

-- Create indexes for performance
CREATE INDEX idx_schemas_user_id ON schemas(user_id);
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_activities_user_id ON activities(user_id);
```

---

## Testing Your Fix

After implementing the fixes, test with 2 different user accounts:

### Test 1: User Isolation
1. Sign in as User A
2. Create a schema, project, or activity
3. Sign out
4. Sign in as User B
5. **Expected:** User B should NOT see User A's data
6. **Bug if:** User B sees User A's schemas, projects, or activities

### Test 2: Stats Accuracy
1. Sign in as User A
2. Check dashboard stats
3. **Expected:** Stats reflect only User A's data
4. **Bug if:** Stats include other users' data

### Test 3: Active Developers
1. Sign in as User A on Device 1
2. Sign in as User B on Device 2
3. Check "Active Developers" on User A's dashboard
4. **Expected:** Shows 1 (just User A) or shows team count if same team
5. **Bug if:** Shows 2 or more without team context

---

## Security Checklist

After fixing, verify:

- [ ] All GET endpoints filter by `user_id`
- [ ] All POST endpoints set `user_id = current_user`
- [ ] All PUT/PATCH endpoints verify ownership before updating
- [ ] All DELETE endpoints verify ownership before deleting
- [ ] JWT tokens contain `user_id` or `sub` claim
- [ ] Authentication middleware extracts and validates user_id
- [ ] Database tables have `user_id` foreign key columns
- [ ] Indexes exist on `user_id` columns for performance

---

## Common Backend Frameworks

### FastAPI Example
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def get_current_user(credentials = Depends(security)):
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload.get("user_id")

@app.get("/api/data")
def get_data(user_id: str = Depends(get_current_user)):
    return db.query(Data).filter(Data.user_id == user_id).all()
```

### Express.js Example
```javascript
const jwt = require('jsonwebtoken');

function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  const decoded = jwt.verify(token, process.env.SECRET_KEY);
  req.userId = decoded.user_id;
  next();
}

app.get('/api/data', authMiddleware, (req, res) => {
  const data = db.find({ user_id: req.userId });
  res.json(data);
});
```

### Django Example
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data(request):
    user_id = request.user.id
    data = Data.objects.filter(user_id=user_id)
    return Response(data)
```

---

## Priority Fix Order

1. **CRITICAL (Fix Immediately):**
   - Dashboard stats endpoint
   - Recent activities endpoint
   - Projects list endpoint
   - Schemas list endpoint

2. **HIGH (Fix Within 24 Hours):**
   - All CRUD endpoints (create, update, delete)
   - Active developers count
   - Database connections endpoint
   - ETL pipelines endpoint

3. **MEDIUM (Fix Within Week):**
   - Add database indexes
   - Audit logs
   - Team/workspace sharing (if applicable)

---

## Questions to Ask Your Backend Developer

1. Do you have a `get_current_user()` dependency/middleware?
2. Are JWT tokens properly validated and user_id extracted?
3. Do all database tables have a `user_id` column?
4. Are you filtering queries by `user_id`?
5. When creating records, are you setting `user_id = current_user.id`?
6. Have you tested with multiple user accounts?

---

## Expected Behavior After Fix

- User A sees only their own schemas, projects, activities
- User B sees only their own data
- Dashboard stats show per-user counts
- Active Developers shows 1 (current user) or team count
- No cross-user data leakage
- Each user has isolated workspace

---

## Still Need Help?

If you're not sure where the bug is, add logging to your backend:

```python
import logging

@app.get("/api/stats")
async def get_stats(user_id: str = Depends(get_current_user)):
    logging.info(f"📊 Stats requested by user: {user_id}")
    
    schemas = db.query(Schema).filter(Schema.user_id == user_id).all()
    logging.info(f"   Found {len(schemas)} schemas for user {user_id}")
    
    return {"schemasGenerated": len(schemas)}
```

Check your backend logs to see if `user_id` is being extracted and used correctly.
