# Backend Implementation Guide - Async Database Schema Import

## ✅ Implementation Complete!

The frontend has been updated to support **async schema import with task polling**. This document tells your backend team exactly what they need to implement.

---

## Overview

The schema import flow is now **asynchronous** using a task-based approach:

1. User clicks "Import Schema"
2. Backend starts a background task and returns a `task_id` immediately
3. Frontend polls the task status every 2 seconds
4. When complete, frontend displays the schema automatically

---

## Required Backend Endpoints

### 1️⃣ Start Schema Import (Async)

**Endpoint**: `POST /api/database/import-from-url`

**What it does**: Starts a background task to import the schema and returns a task ID immediately.

**Request Body**:
```json
{
  "connection_url": "postgresql://user:pass@host:5432/database",
  "type": "postgresql",
  "options": {
    "include_views": false,
    "include_indexes": true,
    "include_constraints": true,
    "include_sample_data": false,
    "max_tables": 100
  }
}
```

**Response (200 OK) - Immediate**:
```json
{
  "success": true,
  "task_id": "abc123-def456-ghi789",
  "message": "Schema import task started",
  "estimated_duration_seconds": 30
}
```

**Implementation Notes**:
- ✅ Use Celery, RQ, or any task queue
- ✅ Return immediately (don't wait for task completion)
- ✅ Generate a unique `task_id` (UUID recommended)
- ✅ Start the import in a background worker

**Error Response (400/500)**:
```json
{
  "success": false,
  "error": {
    "message": "Invalid connection URL",
    "code": "INVALID_URL"
  }
}
```

---

### 2️⃣ Check Import Status (Polling)

**Endpoint**: `GET /api/database/import-status/{task_id}`

**What it does**: Returns the current status of the import task.

**Path Parameter**:
- `task_id` - The task ID returned from the import endpoint

**Response - Task In Progress (200 OK)**:
```json
{
  "success": false,
  "status": "processing",
  "task_id": "abc123-def456-ghi789",
  "progress": {
    "current_step": "extracting_tables",
    "percentage": 45,
    "message": "Extracting table structures (12/27 tables)"
  }
}
```

**Response - Task Completed (200 OK)**:
```json
{
  "success": true,
  "status": "completed",
  "task_id": "abc123-def456-ghi789",
  "schema": {
    "database_name": "mydb",
    "database_type": "postgresql",
    "imported_at": "2025-10-30T13:20:45.789Z",
    "tables": [
      {
        "name": "users",
        "schema": "public",
        "columns": [
          {
            "name": "id",
            "data_type": "integer",
            "is_nullable": false,
            "is_primary_key": true,
            "is_unique": true,
            "default_value": "nextval('users_id_seq'::regclass)",
            "max_length": null,
            "numeric_precision": 32,
            "numeric_scale": 0,
            "column_comment": "User ID"
          },
          {
            "name": "email",
            "data_type": "character varying",
            "is_nullable": false,
            "is_unique": true,
            "max_length": 255
          }
        ],
        "primary_key": ["id"],
        "indexes": [
          {
            "name": "users_pkey",
            "columns": ["id"],
            "is_unique": true,
            "index_type": "btree"
          }
        ],
        "foreign_keys": [],
        "row_count": 1250,
        "table_size_bytes": 245760
      }
    ],
    "relationships": [
      {
        "name": "orders_user_id_fkey",
        "source_table": "orders",
        "source_column": "user_id",
        "target_table": "users",
        "target_column": "id",
        "relationship_type": "many-to-one",
        "on_delete": "CASCADE"
      }
    ],
    "stats": {
      "total_tables": 15,
      "total_columns": 87,
      "total_relationships": 12,
      "import_duration_ms": 5430
    }
  }
}
```

**Response - Task Failed (200 OK)**:
```json
{
  "success": false,
  "status": "failed",
  "task_id": "abc123-def456-ghi789",
  "error": {
    "message": "Permission denied for schema public",
    "code": "PERMISSION_DENIED",
    "details": {
      "reason": "User lacks SELECT permission on information_schema"
    }
  }
}
```

**Status Values**:
- `pending` - Task queued but not started
- `processing` - Task is running
- `completed` - Task finished successfully
- `failed` - Task failed with error

**Implementation Notes**:
- ✅ Return task status from your task queue
- ✅ Include progress updates (optional but recommended)
- ✅ Store results in cache/database for retrieval
- ✅ Keep task results for at least 5 minutes

---

### 3️⃣ Test Connection (Existing - No Changes Needed)

**Endpoint**: `POST /api/database/test-connection-url`

This endpoint should remain as-is (already implemented).

---

## Frontend Behavior

### Polling Logic
- **Interval**: Every 2 seconds
- **Timeout**: Max 2 minutes (60 polls)
- **On Success**: Navigate to schema visualization page
- **On Failure**: Show error message
- **On Timeout**: Show "Import timed out" error

### User Experience
1. User enters connection URL
2. User clicks "Test Connection" (optional)
3. User clicks "Import Schema"
4. Loading indicator appears with progress bar
5. Progress updates every 2 seconds (e.g., "Extracting tables (45%)")
6. When complete: Auto-navigate to visualization
7. If error: Show error message and stop polling

---

## Backend Implementation Checklist

### Required Features
- [ ] **Task Queue Setup** (Celery/RQ/Background Jobs)
- [ ] **Task ID Generation** (UUID or unique string)
- [ ] **Async Import Function** (runs in background worker)
- [ ] **Task Status Storage** (Redis/DB to store task state)
- [ ] **Progress Tracking** (optional but recommended)
- [ ] **Result Caching** (store schema for 5+ minutes)
- [ ] **Error Handling** (timeout, auth errors, permissions)

### Recommended Progress Steps
Update progress at these stages (optional but improves UX):

```python
# Example progress tracking
progress_steps = [
  {"step": "connecting", "percentage": 10, "message": "Connecting to database..."},
  {"step": "listing_tables", "percentage": 25, "message": "Listing tables..."},
  {"step": "extracting_tables", "percentage": 50, "message": "Extracting table structures..."},
  {"step": "analyzing_relationships", "percentage": 75, "message": "Analyzing relationships..."},
  {"step": "finalizing", "percentage": 90, "message": "Finalizing schema..."},
  {"step": "completed", "percentage": 100, "message": "Import complete!"}
]
```

---

## Python Example (Using Celery)

### Start Import Endpoint
```python
from celery import shared_task
from flask import request, jsonify
import uuid

@app.route('/api/database/import-from-url', methods=['POST'])
def start_import():
    data = request.json
    connection_url = data.get('connection_url')
    db_type = data.get('type')
    options = data.get('options', {})
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Start background task
    import_schema_task.apply_async(
        args=[connection_url, db_type, options],
        task_id=task_id
    )
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': 'Schema import task started',
        'estimated_duration_seconds': 30
    })

@shared_task(bind=True)
def import_schema_task(self, connection_url, db_type, options):
    """Background task to import schema"""
    try:
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'percentage': 10, 'message': 'Connecting to database...'}
        )
        
        # Connect to database
        conn = connect_to_database(connection_url, db_type)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'percentage': 25, 'message': 'Listing tables...'}
        )
        
        # Extract schema
        schema = extract_schema(conn, options)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'percentage': 75, 'message': 'Analyzing relationships...'}
        )
        
        # Analyze relationships
        relationships = analyze_relationships(schema)
        
        # Complete
        return {
            'success': True,
            'status': 'completed',
            'schema': schema,
            'relationships': relationships
        }
        
    except Exception as e:
        return {
            'success': False,
            'status': 'failed',
            'error': {
                'message': str(e),
                'code': 'IMPORT_FAILED'
            }
        }
```

### Status Check Endpoint
```python
from celery.result import AsyncResult

@app.route('/api/database/import-status/<task_id>', methods=['GET'])
def check_import_status(task_id):
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return jsonify({
            'success': False,
            'status': 'pending',
            'task_id': task_id
        })
    
    elif task.state == 'PROGRESS':
        return jsonify({
            'success': False,
            'status': 'processing',
            'task_id': task_id,
            'progress': task.info
        })
    
    elif task.state == 'SUCCESS':
        result = task.result
        return jsonify({
            'success': True,
            'status': 'completed',
            'task_id': task_id,
            'schema': result.get('schema')
        })
    
    else:  # FAILURE
        return jsonify({
            'success': False,
            'status': 'failed',
            'task_id': task_id,
            'error': {
                'message': str(task.info),
                'code': 'IMPORT_FAILED'
            }
        })
```

---

## Node.js Example (Using Bull Queue)

### Start Import Endpoint
```javascript
const Queue = require('bull');
const { v4: uuidv4 } = require('uuid');

const importQueue = new Queue('schema-import', {
  redis: { host: 'localhost', port: 6379 }
});

app.post('/api/database/import-from-url', async (req, res) => {
  const { connection_url, type, options } = req.body;
  
  // Generate task ID
  const taskId = uuidv4();
  
  // Add job to queue
  await importQueue.add({
    connection_url,
    type,
    options
  }, {
    jobId: taskId
  });
  
  res.json({
    success: true,
    task_id: taskId,
    message: 'Schema import task started',
    estimated_duration_seconds: 30
  });
});

// Worker process
importQueue.process(async (job) => {
  const { connection_url, type, options } = job.data;
  
  // Update progress
  job.progress({ percentage: 10, message: 'Connecting to database...' });
  
  // Connect and extract schema
  const conn = await connectToDatabase(connection_url, type);
  job.progress({ percentage: 25, message: 'Listing tables...' });
  
  const schema = await extractSchema(conn, options);
  job.progress({ percentage: 75, message: 'Analyzing relationships...' });
  
  const relationships = await analyzeRelationships(schema);
  
  return { schema, relationships };
});
```

### Status Check Endpoint
```javascript
app.get('/api/database/import-status/:taskId', async (req, res) => {
  const { taskId } = req.params;
  const job = await importQueue.getJob(taskId);
  
  if (!job) {
    return res.status(404).json({
      success: false,
      error: { message: 'Task not found' }
    });
  }
  
  const state = await job.getState();
  const progress = job.progress();
  
  if (state === 'completed') {
    const result = job.returnvalue;
    return res.json({
      success: true,
      status: 'completed',
      task_id: taskId,
      schema: result.schema
    });
  }
  
  if (state === 'failed') {
    return res.json({
      success: false,
      status: 'failed',
      task_id: taskId,
      error: {
        message: job.failedReason,
        code: 'IMPORT_FAILED'
      }
    });
  }
  
  // Still processing
  return res.json({
    success: false,
    status: state === 'waiting' ? 'pending' : 'processing',
    task_id: taskId,
    progress: progress || { percentage: 0, message: 'Queued...' }
  });
});
```

---

## Testing

### Test Case 1: Successful Import
```bash
# 1. Start import
curl -X POST http://localhost:8000/api/database/import-from-url \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "postgresql://user:pass@localhost:5432/testdb",
    "type": "postgresql"
  }'

# Response: {"success": true, "task_id": "abc-123", ...}

# 2. Poll status (repeat every 2 seconds)
curl http://localhost:8000/api/database/import-status/abc-123

# Response 1: {"success": false, "status": "processing", "progress": {...}}
# Response 2: {"success": true, "status": "completed", "schema": {...}}
```

### Test Case 2: Failed Import
```bash
# Wrong credentials
curl -X POST http://localhost:8000/api/database/import-from-url \
  -H "Content-Type: application/json" \
  -d '{
    "connection_url": "postgresql://wrong:wrong@localhost:5432/testdb",
    "type": "postgresql"
  }'

# Poll status
curl http://localhost:8000/api/database/import-status/abc-456

# Response: {"success": false, "status": "failed", "error": {...}}
```

---

## Summary for Backend Team

**What you need to implement:**

1. ✅ **POST /api/database/import-from-url**
   - Start async task
   - Return task_id immediately
   - Don't wait for completion

2. ✅ **GET /api/database/import-status/{task_id}**
   - Return task status (`pending`, `processing`, `completed`, `failed`)
   - Include progress updates (optional)
   - Return full schema when completed

3. ✅ **Task Queue Setup**
   - Use Celery (Python) or Bull (Node.js)
   - Store task results for 5+ minutes
   - Handle timeouts and errors gracefully

4. ✅ **Schema Extraction Logic** (same as before)
   - Query information_schema
   - Extract tables, columns, relationships
   - Return in specified JSON format

**Frontend is ready to go!** Once you implement these two endpoints, the database connection feature will work perfectly with async polling and progress updates.

---

## Questions?

Contact the frontend team if you need:
- Clarification on response formats
- Help testing the endpoints
- Changes to polling interval or timeout
- Additional progress step granularity
