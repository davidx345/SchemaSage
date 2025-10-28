# Frontend API Implementation Details - Complete Reference

## Overview
This document provides the exact API endpoints, request payloads, headers, and implementation details for all user actions in the SchemaSage frontend that should trigger backend metrics updates.

---

## 1. Schema Generation (new-schema page)

### Endpoint
```
POST https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/schema/generate
```

### Implementation Location
- **File:** `src/components/schema/SchemaGenerator.tsx`
- **Function:** `handleGenerate()` (line 36-59)
- **API Call:** `schemaApi.generateSchema(description, format)`

### Request Details
```typescript
// Headers
Authorization: Bearer <token>  // Auto-injected by interceptor
Content-Type: application/json

// Body
{
  "description": "<user's schema description>",
  "format": "natural_language"  // or other format
}
```

### Sample Payload
```json
{
  "description": "Create a schema for an e-commerce platform with users, products, orders, and categories",
  "format": "natural_language"
}
```

### Current Implementation
```typescript
const response = await schemaApi.generateSchema(input.description, input.format);
```

### What Backend Should Do
1. Increment `schemasGenerated` counter in database
2. Emit WebSocket event:
```json
{
  "type": "stats_update",
  "data": {
    "schemasGenerated": <new_count>,
    "apisScaffolded": <current>,
    "dataFilesCleaned": <current>,
    "activeDevelopers": <current>,
    "recentActivities": [...]
  }
}
```
3. Emit activity event:
```json
{
  "type": "activity_update",
  "data": {
    "id": "<uuid>",
    "type": "schema_generated",
    "description": "Schema generated from description",
    "timestamp": "<ISO8601>",
    "icon": "database",
    "color": "blue"
  }
}
```

### User ID Inclusion
**Currently:** ❌ Not included in payload
**Should Add:** User ID from auth token (backend can extract from JWT)

---

## 2. Code Generation (code page)

### Endpoint
```
POST https://schemasage-code-generation-56faa300323b.herokuapp.com/generate
```

### Implementation Location
- **File:** `src/app/code/page.tsx`
- **Function:** `handleGenerateCode()` (line 93-145)
- **API Call:** `schemaApi.generateCode(schema, format, options)`

### Request Details
```typescript
// Headers
Authorization: Bearer <token>  // Auto-injected
Content-Type: application/json

// Body
{
  "schema": {
    "tables": [
      {
        "name": "users",
        "columns": [
          {
            "name": "id",
            "type": "INTEGER",
            "nullable": false,
            "is_primary_key": true,
            "is_foreign_key": false,
            "unique": false
          },
          // ... more columns
        ],
        "primary_keys": ["id"],
        "foreign_keys": [],
        "indexes": [],
        "description": ""
      }
    ],
    "relationships": [],
    "metadata": { "version": "1.0" }
  },
  "format": "typescript_interfaces",  // Mapped from frontend format
  "options": {}
}
```

### Sample Payload
```json
{
  "schema": {
    "tables": [
      {
        "name": "products",
        "columns": [
          {"name": "id", "type": "INTEGER", "nullable": false, "is_primary_key": true},
          {"name": "name", "type": "VARCHAR(255)", "nullable": false},
          {"name": "price", "type": "DECIMAL(10,2)", "nullable": false}
        ],
        "primary_keys": ["id"],
        "foreign_keys": [],
        "indexes": []
      }
    ],
    "relationships": [],
    "metadata": {"version": "1.0"}
  },
  "format": "typescript_interfaces",
  "options": {}
}
```

### Current Implementation
```typescript
const response = await schemaApi.generateCode(
  currentSchema, 
  format,
  {
    includeComments,
    includeValidation,
    language,
    format
  }
);
```

### What Backend Should Do
1. Increment `dataFilesCleaned` counter (used for "Code Files Generated" metric)
2. Emit WebSocket `stats_update` event
3. Emit activity event with `type: "api_scaffolded"` or `type: "data_cleaned"`

### User ID Inclusion
**Currently:** ❌ Not included in payload
**Should Add:** Extract from JWT token

---

## 3. File Upload/Schema Detection (upload page)

### Endpoint
```
POST https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/schema/detect-from-file
```

### Implementation Location
- **File:** `src/app/upload/page.tsx`
- **Function:** `handleSampleFileSelect()` (line 30-68)
- **API Call:** `schemaApi.detectSchemaFromFile(file)`
- **Also Used By:** `FileUploader` component

### Request Details
```typescript
// Headers
Authorization: Bearer <token>  // Auto-injected
Content-Type: multipart/form-data

// Body (FormData)
file: <File object>
```

### Sample Request (FormData)
```
------WebKitFormBoundary...
Content-Disposition: form-data; name="file"; filename="ecommerce-schema.json"
Content-Type: application/json

{...file content...}
------WebKitFormBoundary...
```

### Current Implementation
```typescript
const formData = new FormData();
formData.append('file', file);
const response = await fetch(`${API_BASE}/schema/detect-from-file`, {
  method: "POST",
  body: formData,
  headers: { Authorization: `Bearer ${token}` }
});
```

### What Backend Should Do
1. Increment `schemasGenerated` counter (or create separate `schemasDetected` counter)
2. Emit WebSocket `stats_update` event
3. Emit activity event:
```json
{
  "type": "activity_update",
  "data": {
    "id": "<uuid>",
    "type": "schema_generated",
    "description": "Schema detected from file: <filename>",
    "timestamp": "<ISO8601>",
    "icon": "database",
    "color": "blue"
  }
}
```

### User ID Inclusion
**Currently:** ❌ Not included in FormData
**Should Add:** Add as form field or extract from JWT

---

## 4. API Scaffolding (tools page)

### Endpoint
```
POST https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/scaffold
```

### Implementation Location
- **File:** `src/lib/api.ts`
- **Function:** `scaffoldAPI()` (line 486-530)
- **Also:** `scaffoldAPIEnhanced()` for template mode

### Request Details
```typescript
// Headers
Authorization: Bearer <token>
Content-Type: application/json

// Body
{
  "schema_data": {
    "tables": [...],
    "relationships": [...],
    "metadata": {"version": "1.0"}
  },
  "framework": "fastapi" | "express" | "spring" | "django" | "nestjs",
  "options": {
    "authentication": boolean,
    "selectedEntities": string[],
    "features": {
      "crud": boolean,
      "pagination": boolean,
      "filtering": boolean,
      "validation": boolean
    }
  }
}
```

### Sample Payload
```json
{
  "schema_data": {
    "tables": [
      {
        "name": "users",
        "columns": [
          {"name": "id", "type": "INTEGER", "nullable": false, "is_primary_key": true},
          {"name": "email", "type": "VARCHAR(255)", "nullable": false, "unique": true}
        ],
        "primary_keys": ["id"],
        "foreign_keys": [],
        "indexes": []
      }
    ],
    "relationships": [],
    "metadata": {"version": "1.0"}
  },
  "framework": "fastapi",
  "options": {
    "authentication": true,
    "features": {
      "crud": true,
      "pagination": true,
      "filtering": true,
      "validation": true
    }
  }
}
```

### What Backend Should Do
1. Increment `apisScaffolded` counter
2. Emit WebSocket `stats_update` event
3. Emit activity event:
```json
{
  "type": "activity_update",
  "data": {
    "id": "<uuid>",
    "type": "api_scaffolded",
    "description": "FastAPI scaffold generated with CRUD operations",
    "timestamp": "<ISO8601>",
    "icon": "code",
    "color": "green"
  }
}
```

### User ID Inclusion
**Currently:** ❌ Not included in payload
**Should Add:** Extract from JWT token

---

## 5. Data Cleaning (tools page)

### Endpoint
```
POST https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com/data-cleaning/clean
```

### Implementation Location
- **File:** `src/lib/api.ts`
- **Function:** `cleanData()` (line 671-686)

### Request Details
```typescript
// Headers
Authorization: Bearer <token>
Content-Type: application/json

// Body
{
  "data": <any>,  // Raw data to clean
  "config": <any>  // Cleaning configuration
}
```

### Sample Payload
```json
{
  "data": [
    {"name": "John", "age": "25", "email": "john@example.com"},
    {"name": "Jane", "age": "invalid", "email": "not-an-email"}
  ],
  "config": {
    "remove_nulls": true,
    "validate_types": true,
    "fix_emails": true
  }
}
```

### What Backend Should Do
1. Increment `dataFilesCleaned` counter
2. Emit WebSocket `stats_update` event
3. Emit activity event:
```json
{
  "type": "activity_update",
  "data": {
    "id": "<uuid>",
    "type": "data_cleaned",
    "description": "Data cleaned: 2 records processed",
    "timestamp": "<ISO8601>",
    "icon": "shield",
    "color": "purple"
  }
}
```

### User ID Inclusion
**Currently:** ❌ Not included in payload
**Should Add:** Extract from JWT token

---

## 6. Project Creation (projects page)

### Endpoint
```
POST https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/api/projects
```

### Implementation Location
- **File:** `src/lib/api.ts`
- **Function:** `projectApi.createProject()` (line 1227-1248)

### Request Details
```typescript
// Headers
Authorization: Bearer <token>
Content-Type: application/json

// Body
{
  "name": "<project name>",
  "description": "<optional description>",
  "project_type": "<optional type>",
  "metadata": {},
  "tags": []
}
```

### Sample Payload
```json
{
  "name": "E-commerce Backend",
  "description": "Database schema for online store",
  "project_type": "web_application",
  "tags": ["ecommerce", "postgresql"]
}
```

### What Backend Should Do
1. Increment `activeProjects` counter (NEW METRIC NEEDED)
2. Emit WebSocket `stats_update` event
3. Emit activity event:
```json
{
  "type": "activity_update",
  "data": {
    "id": "<uuid>",
    "type": "project_created",
    "description": "New project created: E-commerce Backend",
    "timestamp": "<ISO8601>",
    "icon": "file-text",
    "color": "indigo"
  }
}
```

### User ID Inclusion
**Currently:** ❌ Not included in payload
**Should Add:** Extract from JWT token

---

## 7. WebSocket Connection

### WebSocket URL
```
wss://schemasage-websocket-realtime-11223b2de7f4.herokuapp.com/ws/dashboard
```

### Implementation Location
- **File:** `src/lib/hooks/useDashboardWebSocket.ts`
- **Function:** `connect()` (line 62-249)

### Authentication Message
```json
{
  "type": "authenticate",
  "data": {
    "token": "<JWT_TOKEN>",
    "userId": "<user_id_or_email>",
    "clientType": "dashboard"
  }
}
```

### Expected Backend Messages

**Stats Update:**
```json
{
  "type": "stats_update",
  "data": {
    "schemasGenerated": 42,
    "apisScaffolded": 15,
    "dataFilesCleaned": 28,
    "activeDevelopers": 3,
    "lastActivity": null,
    "recentActivities": []
  }
}
```

**Activity Update:**
```json
{
  "type": "activity_update",
  "data": {
    "id": "uuid-here",
    "type": "schema_generated",
    "description": "Schema 'Users & Products' generated",
    "timestamp": "2025-10-28T10:38:18.000Z",
    "icon": "database",
    "color": "blue"
  }
}
```

**Auth Success:**
```json
{
  "type": "auth_success"
}
```

**Auth Error:**
```json
{
  "type": "auth_error",
  "error": "Invalid token",
  "message": "Authentication failed"
}
```

### Frontend Handling
```typescript
// Frontend listens for these events and updates UI:
switch (message.type) {
  case 'stats_update':
    setStats(sanitizeStats(message.data));
    setLastUpdate(new Date());
    break;
  case 'activity_update':
    setStats(prev => ({
      ...prev,
      lastActivity: message.data,
      recentActivities: [message.data, ...prev.recentActivities.slice(0, 9)]
    }));
    break;
}
```

---

## 8. Authentication & User ID

### Token Storage
- **Location:** Zustand store (`src/lib/store.ts`)
- **Access:** `useAuth.getState().token`
- **Auto-injection:** Axios interceptor in `src/lib/api.ts` (line 58-67)

### Token Payload Structure
```json
{
  "sub": "<user_id>",
  "email": "<user_email>",
  "username": "<username>",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### How Frontend Gets User ID
```typescript
const token = useAuth.getState().token;
const user = useAuth.getState().user;
const userId = user?.id || user?.email;
```

### Request Interceptor (Auto-adds Auth Header)
```typescript
api.interceptors.request.use(
  (config) => {
    const token = useAuth.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
```

---

## 9. Response Handling

### Success Response Pattern
```typescript
if (response.success && response.data) {
  // Handle success
  toast.success("Operation successful!");
  // Update UI
} else {
  // Handle error
  toast.error(`Failed: ${response.error?.message}`);
}
```

### Error Response Pattern
```typescript
try {
  const response = await schemaApi.someFunction();
  // ...
} catch (error) {
  console.error('Operation error:', error);
  toast.error(error instanceof Error ? error.message : "Unknown error");
}
```

---

## 10. Console Logs for Debugging

### What Frontend Logs
1. **Schema Generation:**
```javascript
console.log('Schema generation response:', response.data);
```

2. **Code Generation:**
```javascript
console.log('🔍 Starting code generation with schema:', {
  tableCount: currentSchema.tables?.length || 0,
  // ... detailed schema info
});
```

3. **WebSocket:**
```javascript
console.log('✅ Dashboard WebSocket connected to backend');
console.log('🔑 Authenticating WebSocket...', { userId, clientType });
console.log('📊 Received real stats update:', message.data);
console.log('📝 Received real activity update:', activity);
```

4. **File Upload:**
```javascript
console.log('Schema detection response:', response);
console.log('Schema data received:', response.data);
```

---

## 11. Browser Console Test Commands

### Check WebSocket Connection
```javascript
// Open browser console on dashboard page
console.log('WebSocket Connected:', window.wsConnected);
console.log('Last Stats Update:', window.lastStatsUpdate);
```

### Check Auth State
```javascript
// Access Zustand store from console
const authState = JSON.parse(localStorage.getItem('auth-storage'));
console.log('Token:', authState?.state?.token?.substring(0, 20) + '...');
console.log('User:', authState?.state?.user);
```

### Monitor Network Requests
```
1. Open DevTools → Network tab
2. Filter by: XHR / Fetch
3. Perform an action (generate schema, upload file, etc.)
4. Click on the request
5. Check: Headers, Payload, Preview, Response
```

---

## 12. Missing User ID in Payloads - FIX NEEDED

### Current Status
❌ Most API calls do NOT include `user_id` in the request payload

### Backend Options:
1. **Extract from JWT (Recommended):**
   - Backend should decode the JWT token from `Authorization` header
   - Extract `sub` (subject) or `user_id` claim
   - Use this for activity tracking

2. **Add to Payload (Alternative):**
   - Frontend can add `user_id` to each request body
   - Requires updating all API call functions

### Recommended Approach for Backend
```python
# Backend middleware/decorator
def get_user_from_token(request):
    token = request.headers.get('Authorization').replace('Bearer ', '')
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    user_id = payload.get('sub') or payload.get('user_id')
    return user_id

# Then use in endpoint:
@app.post("/api/schema/generate")
async def generate_schema(request: Request, data: SchemaGenerateRequest):
    user_id = get_user_from_token(request)
    
    # Generate schema...
    
    # Track activity
    await track_activity(user_id, "schema_generated", "Schema generated from description")
    
    # Broadcast stats update via WebSocket
    await broadcast_stats_update()
```

---

## 13. Backend Implementation Checklist

- [ ] Decode JWT to extract user_id for all authenticated endpoints
- [ ] Create database table for metrics:
  - `schemasGenerated`
  - `apisScaffolded`
  - `dataFilesCleaned`
  - `activeDevelopers`
  - `activeProjects` (NEW)
- [ ] Increment counters on each action:
  - Schema generation → `schemasGenerated++`
  - Code generation → `dataFilesCleaned++`
  - File upload → `schemasGenerated++`
  - API scaffolding → `apisScaffolded++`
  - Project creation → `activeProjects++`
- [ ] Emit WebSocket `stats_update` after each counter increment
- [ ] Emit WebSocket `activity_update` with descriptive message
- [ ] Store activity history (last 100 activities)
- [ ] Test with browser console and Network tab
- [ ] Verify all connected dashboard clients receive updates

---

## 14. Testing Workflow

### Step-by-Step Test:
1. **Open Dashboard** → Check WebSocket connected (green dot)
2. **Open Console** → Run: `console.log('Monitoring stats...')`
3. **Perform Action** (e.g., generate schema)
4. **Check Console** → Should see `📊 Received real stats update`
5. **Check Dashboard** → Metrics should increment
6. **Check Recent Activity** → New activity should appear

### Expected Console Output:
```
✅ Dashboard WebSocket connected to backend
🔑 Authenticating WebSocket...
🔑 Authentication message sent successfully
📊 Received real stats update: { schemasGenerated: 1, ... }
📝 Received real activity update: { type: 'schema_generated', ... }
```

---

## Summary

**Frontend is fully functional and ready to receive backend events.**

**Backend needs to:**
1. Emit WebSocket events (`stats_update`, `activity_update`) after each action
2. Store metrics in database with proper counters
3. Extract user_id from JWT token
4. Broadcast updates to all connected dashboard clients

**All API endpoints are documented above with:**
- ✅ Exact URLs
- ✅ Request methods (POST/GET)
- ✅ Headers (Authorization, Content-Type)
- ✅ Sample payloads
- ✅ Expected responses
- ✅ WebSocket message formats
