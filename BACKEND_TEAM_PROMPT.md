# Backend Team: Dashboard Metrics Implementation

## URGENT: Metrics Not Updating After User Actions

The dashboard WebSocket connection is working (Active Developers updates correctly), but other metrics are not incrementing when users perform actions.

---

## Problem

When users perform these actions:
- Generate schema
- Generate code
- Upload file
- Scaffold API
- Clean data
- Create project

**Expected:** Dashboard metrics increment and Recent Activity updates
**Actual:** Metrics stay at 0, Recent Activity empty

---

## Root Cause

Backend is not:
1. Tracking actions in database
2. Emitting WebSocket events after actions
3. Broadcasting stats updates to dashboard clients

---

## Required Implementation

### 1. Database Schema

Create table for metrics tracking:

```sql
CREATE TABLE dashboard_metrics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    schemas_generated INTEGER DEFAULT 0,
    apis_scaffolded INTEGER DEFAULT 0,
    data_files_cleaned INTEGER DEFAULT 0,
    active_projects INTEGER DEFAULT 0,
    active_developers INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recent_activities (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    type VARCHAR(50),  -- 'schema_generated', 'api_scaffolded', etc.
    description TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    icon VARCHAR(50),
    color VARCHAR(50),
    metadata JSONB
);
```

### 2. Extract User ID from JWT

All endpoints must extract user_id from Authorization header:

```python
def get_user_from_token(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    return payload.get('sub') or payload.get('user_id')
```

### 3. Endpoints to Update

#### A. Schema Generation
**Endpoint:** `POST /api/schema/generate`

**After successful generation:**
```python
# 1. Increment counter
increment_metric(user_id, 'schemas_generated')

# 2. Log activity
log_activity(user_id, 'schema_generated', f"Schema generated from description")

# 3. Broadcast via WebSocket
await broadcast_stats_update(user_id)
```

#### B. Code Generation
**Endpoint:** `POST /generate` (code-generation service)

**After successful generation:**
```python
increment_metric(user_id, 'data_files_cleaned')  # Used for "Code Files Generated"
log_activity(user_id, 'api_scaffolded', f"Code generated: {format}")
await broadcast_stats_update(user_id)
```

#### C. File Upload/Schema Detection
**Endpoint:** `POST /api/schema/detect-from-file`

**After successful detection:**
```python
increment_metric(user_id, 'schemas_generated')
log_activity(user_id, 'schema_generated', f"Schema detected from file: {filename}")
await broadcast_stats_update(user_id)
```

#### D. API Scaffolding
**Endpoint:** `POST /api/scaffold`

**After successful scaffolding:**
```python
increment_metric(user_id, 'apis_scaffolded')
log_activity(user_id, 'api_scaffolded', f"{framework} API scaffold generated")
await broadcast_stats_update(user_id)
```

#### E. Data Cleaning
**Endpoint:** `POST /data-cleaning/clean`

**After successful cleaning:**
```python
increment_metric(user_id, 'data_files_cleaned')
log_activity(user_id, 'data_cleaned', f"Data cleaned: {record_count} records")
await broadcast_stats_update(user_id)
```

#### F. Project Creation
**Endpoint:** `POST /api/api/projects`

**After successful creation:**
```python
increment_metric(user_id, 'active_projects')
log_activity(user_id, 'project_created', f"New project: {project_name}")
await broadcast_stats_update(user_id)
```

### 4. WebSocket Broadcast Function

```python
async def broadcast_stats_update(user_id: str = None):
    """
    Broadcast stats update to all connected dashboard clients.
    If user_id provided, send personalized stats; otherwise send global stats.
    """
    # Get current metrics
    metrics = get_current_metrics(user_id)
    activities = get_recent_activities(user_id, limit=10)
    
    # Format message
    message = {
        "type": "stats_update",
        "data": {
            "schemasGenerated": metrics.schemas_generated,
            "apisScaffolded": metrics.apis_scaffolded,
            "dataFilesCleaned": metrics.data_files_cleaned,
            "activeDevelopers": metrics.active_developers,
            "lastActivity": activities[0] if activities else None,
            "recentActivities": activities
        }
    }
    
    # Send to all connected WebSocket clients
    await websocket_manager.broadcast(message)
```

### 5. Activity Log Function

```python
def log_activity(user_id: str, activity_type: str, description: str, metadata: dict = None):
    """
    Log user activity and return activity object.
    """
    activity = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": activity_type,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
        "icon": get_icon_for_type(activity_type),
        "color": get_color_for_type(activity_type),
        "metadata": metadata or {}
    }
    
    # Save to database
    save_activity_to_db(activity)
    
    # Broadcast activity update
    asyncio.create_task(broadcast_activity_update(activity))
    
    return activity

def get_icon_for_type(activity_type: str) -> str:
    icons = {
        'schema_generated': 'database',
        'api_scaffolded': 'code',
        'data_cleaned': 'shield',
        'schema_analyzed': 'trending-up',
        'project_created': 'file-text',
        'user_joined': 'users'
    }
    return icons.get(activity_type, 'activity')

def get_color_for_type(activity_type: str) -> str:
    colors = {
        'schema_generated': 'blue',
        'api_scaffolded': 'green',
        'data_cleaned': 'purple',
        'schema_analyzed': 'orange',
        'project_created': 'indigo',
        'user_joined': 'pink'
    }
    return colors.get(activity_type, 'gray')
```

### 6. WebSocket Message Formats

**Stats Update:**
```json
{
  "type": "stats_update",
  "data": {
    "schemasGenerated": 42,
    "apisScaffolded": 15,
    "dataFilesCleaned": 28,
    "activeDevelopers": 3,
    "lastActivity": {
      "id": "uuid",
      "type": "schema_generated",
      "description": "Schema generated from description",
      "timestamp": "2025-10-28T10:38:18.000Z",
      "icon": "database",
      "color": "blue"
    },
    "recentActivities": [...]
  }
}
```

**Activity Update:**
```json
{
  "type": "activity_update",
  "data": {
    "id": "uuid",
    "type": "schema_generated",
    "description": "Schema 'E-commerce Platform' generated",
    "timestamp": "2025-10-28T10:38:18.000Z",
    "icon": "database",
    "color": "blue",
    "metadata": {}
  }
}
```

---

## Testing Checklist

1. **Generate Schema:**
   - [ ] Counter increments in database
   - [ ] WebSocket `stats_update` sent
   - [ ] WebSocket `activity_update` sent
   - [ ] Dashboard shows new count
   - [ ] Recent Activity shows new entry

2. **Generate Code:**
   - [ ] Counter increments
   - [ ] Stats update sent
   - [ ] Activity update sent
   - [ ] Dashboard updates

3. **Upload File:**
   - [ ] Counter increments
   - [ ] Stats/activity updates sent
   - [ ] Dashboard updates

4. **All Actions:**
   - [ ] Multiple browser tabs receive same updates
   - [ ] WebSocket stays connected (ping/pong working)
   - [ ] Activities show in chronological order
   - [ ] Metrics persist across page reloads

---

## Complete API Reference

See `FRONTEND_API_IMPLEMENTATION_DETAILS.md` for:
- Exact API endpoints with full URLs
- Complete request payloads with examples
- Response formats
- Authentication details
- WebSocket connection details
- User ID extraction methods

---

## Frontend Confirmation

The frontend is **READY** and listening for these events:
- ✅ WebSocket connection established
- ✅ Authentication message sent
- ✅ Listening for `stats_update` events
- ✅ Listening for `activity_update` events
- ✅ UI updates when events received
- ✅ All API calls include `Authorization: Bearer <token>` header

**Active Developers metric already works** - proves WebSocket is functional!

---

## Priority

**HIGH PRIORITY** - This blocks dashboard functionality in production.

Expected completion: 2-3 hours for full implementation.

---

## Questions?

If you need:
- Exact request/response logs
- Browser console screenshots
- Network tab captures
- WebSocket message examples

Let me know and I can provide them immediately.
