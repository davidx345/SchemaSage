# Database Connection API Specification

## Overview
This document specifies the API endpoints needed for the database connection feature on the `/upload` page (Database tab). The frontend allows users to connect to various databases using connection URLs and import their schemas.

---

## Supported Database Types
- **PostgreSQL** (including Supabase, Neon, etc.)
- **MySQL** (including PlanetScale, etc.)
- **MongoDB**
- **SQLite**
- **Redis**

---

## API Endpoints

### 1. Test Database Connection

**Endpoint**: `POST /api/database/test-connection-url`

**Purpose**: Test if the provided database connection URL is valid and accessible.

**Request Payload**:
```json
{
  "connection_url": "postgresql://username:password@host:5432/database",
  "type": "postgresql"
}
```

**Request Fields**:
- `connection_url` (string, required): The database connection string
- `type` (string, required): Database type - one of: `postgresql`, `mysql`, `mongodb`, `sqlite`, `redis`

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Connection successful",
  "connection_info": {
    "database_name": "mydb",
    "database_type": "postgresql",
    "database_version": "15.2",
    "server_info": {
      "host": "localhost",
      "port": 5432
    },
    "connection_time_ms": 145,
    "tested_at": "2025-10-30T13:15:22.123Z"
  }
}
```

**Error Response** (400/500):
```json
{
  "success": false,
  "error": {
    "message": "Connection failed: could not connect to server",
    "code": "CONNECTION_FAILED",
    "details": {
      "reason": "Authentication failed for user 'username'",
      "database_type": "postgresql"
    }
  }
}
```

**Common Error Codes**:
- `CONNECTION_FAILED` - Cannot reach database server
- `AUTH_FAILED` - Invalid credentials
- `INVALID_URL` - Malformed connection URL
- `UNSUPPORTED_DB` - Database type not supported
- `TIMEOUT` - Connection attempt timed out
- `SSL_ERROR` - SSL/TLS configuration issue

---

### 2. Import Schema from Database

**Endpoint**: `POST /api/database/import-from-url`

**Purpose**: Connect to the database and extract the complete schema structure.

**Request Payload**:
```json
{
  "connection_url": "postgresql://username:password@host:5432/database",
  "type": "postgresql",
  "options": {
    "include_views": true,
    "include_indexes": true,
    "include_constraints": true,
    "include_sample_data": false,
    "max_tables": 100
  }
}
```

**Request Fields**:
- `connection_url` (string, required): The database connection string
- `type` (string, required): Database type
- `options` (object, optional): Import configuration
  - `include_views` (boolean, default: false): Include database views
  - `include_indexes` (boolean, default: true): Include indexes
  - `include_constraints` (boolean, default: true): Include foreign keys and constraints
  - `include_sample_data` (boolean, default: false): Include sample data rows
  - `max_tables` (number, default: 100): Maximum number of tables to import

**Success Response** (200 OK):
```json
{
  "success": true,
  "schema": {
    "database_name": "ecommerce_db",
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
            "is_primary_key": false,
            "is_unique": true,
            "default_value": null,
            "max_length": 255,
            "numeric_precision": null,
            "numeric_scale": null,
            "column_comment": "User email address"
          },
          {
            "name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": false,
            "is_primary_key": false,
            "is_unique": false,
            "default_value": "CURRENT_TIMESTAMP",
            "max_length": null,
            "numeric_precision": null,
            "numeric_scale": null,
            "column_comment": null
          }
        ],
        "primary_key": ["id"],
        "indexes": [
          {
            "name": "users_pkey",
            "columns": ["id"],
            "is_unique": true,
            "index_type": "btree"
          },
          {
            "name": "users_email_idx",
            "columns": ["email"],
            "is_unique": true,
            "index_type": "btree"
          }
        ],
        "foreign_keys": [],
        "row_count": 1250,
        "table_size_bytes": 245760,
        "table_comment": "Application users"
      },
      {
        "name": "orders",
        "schema": "public",
        "columns": [
          {
            "name": "id",
            "data_type": "integer",
            "is_nullable": false,
            "is_primary_key": true,
            "is_unique": true,
            "default_value": "nextval('orders_id_seq'::regclass)",
            "max_length": null,
            "numeric_precision": 32,
            "numeric_scale": 0,
            "column_comment": null
          },
          {
            "name": "user_id",
            "data_type": "integer",
            "is_nullable": false,
            "is_primary_key": false,
            "is_unique": false,
            "default_value": null,
            "max_length": null,
            "numeric_precision": 32,
            "numeric_scale": 0,
            "column_comment": "References users table"
          },
          {
            "name": "total_amount",
            "data_type": "numeric",
            "is_nullable": false,
            "is_primary_key": false,
            "is_unique": false,
            "default_value": "0",
            "max_length": null,
            "numeric_precision": 10,
            "numeric_scale": 2,
            "column_comment": "Order total in USD"
          },
          {
            "name": "status",
            "data_type": "character varying",
            "is_nullable": false,
            "is_primary_key": false,
            "is_unique": false,
            "default_value": "'pending'::character varying",
            "max_length": 50,
            "numeric_precision": null,
            "numeric_scale": null,
            "column_comment": "Order status"
          },
          {
            "name": "created_at",
            "data_type": "timestamp with time zone",
            "is_nullable": false,
            "is_primary_key": false,
            "is_unique": false,
            "default_value": "CURRENT_TIMESTAMP",
            "max_length": null,
            "numeric_precision": null,
            "numeric_scale": null,
            "column_comment": null
          }
        ],
        "primary_key": ["id"],
        "indexes": [
          {
            "name": "orders_pkey",
            "columns": ["id"],
            "is_unique": true,
            "index_type": "btree"
          },
          {
            "name": "orders_user_id_idx",
            "columns": ["user_id"],
            "is_unique": false,
            "index_type": "btree"
          }
        ],
        "foreign_keys": [
          {
            "name": "orders_user_id_fkey",
            "columns": ["user_id"],
            "referenced_table": "users",
            "referenced_columns": ["id"],
            "on_delete": "CASCADE",
            "on_update": "NO ACTION"
          }
        ],
        "row_count": 5430,
        "table_size_bytes": 1048576,
        "table_comment": "Customer orders"
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
        "on_delete": "CASCADE",
        "on_update": "NO ACTION"
      }
    ],
    "views": [],
    "stats": {
      "total_tables": 2,
      "total_columns": 8,
      "total_relationships": 1,
      "total_indexes": 4,
      "estimated_size_bytes": 1294336,
      "import_duration_ms": 2345
    }
  }
}
```

**Error Response** (400/500):
```json
{
  "success": false,
  "error": {
    "message": "Failed to import schema: permission denied for schema public",
    "code": "IMPORT_FAILED",
    "details": {
      "reason": "User does not have SELECT permission on information_schema",
      "tables_attempted": 0,
      "tables_imported": 0
    }
  }
}
```

**Common Error Codes**:
- `IMPORT_FAILED` - Schema import failed
- `PERMISSION_DENIED` - Insufficient database permissions
- `NO_TABLES_FOUND` - No tables found in database
- `TIMEOUT` - Import operation timed out
- `PARTIAL_IMPORT` - Some tables failed to import
- `UNSUPPORTED_FEATURES` - Database features not supported

---

## Connection URL Formats

### PostgreSQL
```
postgresql://username:password@host:port/database
postgresql://username:password@host:port/database?sslmode=require
postgresql://username:password@host:port/database?schema=public
```

**Examples**:
- Direct connection: `postgresql://admin:pass123@localhost:5432/mydb`
- Supabase: `postgresql://postgres:[PASSWORD]@db.project.supabase.co:5432/postgres`
- Neon: `postgresql://user:password@ep-cool-name-123456.region.neon.tech/dbname?sslmode=require`
- Railway: `postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway`

### MySQL
```
mysql://username:password@host:port/database
mysql://username:password@host:port/database?ssl=true
```

**Examples**:
- Direct connection: `mysql://root:password@localhost:3306/mydb`
- PlanetScale: `mysql://user:pscale_pw_xxx@aws.connect.psdb.cloud/database?ssl={"rejectUnauthorized":true}`

### MongoDB
```
mongodb://username:password@host:port/database
mongodb+srv://username:password@cluster.mongodb.net/database
```

**Examples**:
- Direct connection: `mongodb://admin:password@localhost:27017/mydb`
- MongoDB Atlas: `mongodb+srv://user:password@cluster0.abc123.mongodb.net/mydb`

### SQLite
```
sqlite:///absolute/path/to/database.db
sqlite:///:memory:
```

**Examples**:
- File-based: `sqlite:///var/data/app.db`
- Memory: `sqlite:///:memory:`

### Redis
```
redis://username:password@host:port/database_number
redis://host:port
```

**Examples**:
- Direct connection: `redis://localhost:6379/0`
- With auth: `redis://default:password@redis-server:6379/0`
- Redis Cloud: `redis://default:password@redis-12345.cloud.redislabs.com:12345`

---

## Backend Implementation Checklist

### 1. Security Requirements
- [ ] **Validate connection URLs** - Reject malformed URLs
- [ ] **Sanitize credentials** - Never log passwords or tokens
- [ ] **Connection pooling** - Reuse connections when possible
- [ ] **Timeout handling** - Set connection and query timeouts (30 seconds recommended)
- [ ] **Rate limiting** - Limit connection attempts per user/IP
- [ ] **SSL/TLS support** - Support encrypted connections
- [ ] **Firewall whitelist** - Document IP addresses that need access

### 2. Database Permissions Needed
For the backend to import schemas, the database user must have:

**PostgreSQL**:
```sql
GRANT USAGE ON SCHEMA information_schema TO schemasage_user;
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO schemasage_user;
GRANT USAGE ON SCHEMA public TO schemasage_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO schemasage_user;
```

**MySQL**:
```sql
GRANT SELECT ON information_schema.* TO 'schemasage_user'@'%';
GRANT SELECT ON mysql.* TO 'schemasage_user'@'%';
```

**MongoDB**:
```javascript
db.grantRolesToUser("schemasage_user", [
  { role: "read", db: "your_database" },
  { role: "listDatabases", db: "admin" }
])
```

### 3. Database Queries to Execute

**PostgreSQL - Get Tables**:
```sql
SELECT 
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;
```

**PostgreSQL - Get Columns**:
```sql
SELECT 
    table_schema,
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length,
    numeric_precision,
    numeric_scale
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

**PostgreSQL - Get Primary Keys**:
```sql
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'public';
```

**PostgreSQL - Get Foreign Keys**:
```sql
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.update_rule,
    rc.delete_rule,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public';
```

**PostgreSQL - Get Indexes**:
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

**PostgreSQL - Get Table Row Counts**:
```sql
SELECT
    schemaname,
    relname AS table_name,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

### 4. Error Handling
- [ ] Catch connection timeouts
- [ ] Handle authentication errors
- [ ] Detect unsupported database versions
- [ ] Handle SSL/TLS errors
- [ ] Detect firewall/network issues
- [ ] Handle database permission errors
- [ ] Detect empty databases
- [ ] Handle malformed connection URLs

### 5. Response Time Optimization
- [ ] Cache database metadata for repeat imports
- [ ] Use parallel queries when possible
- [ ] Limit initial table scan (max 100 tables)
- [ ] Stream large result sets
- [ ] Implement pagination for large schemas

### 6. Testing
Test with these connection types:
- [ ] PostgreSQL (local, Supabase, Neon)
- [ ] MySQL (local, PlanetScale)
- [ ] MongoDB (local, Atlas)
- [ ] SQLite (file-based)
- [ ] Redis (local, cloud)
- [ ] Connection pooling (e.g., PgBouncer)
- [ ] Session pooling (e.g., Supabase)
- [ ] Transaction pooling

---

## Frontend Usage

The frontend calls these endpoints in sequence:

```typescript
// 1. Test connection
const testResult = await databaseApi.testConnectionUrl({
  connection_url: "postgresql://user:pass@host:5432/db",
  type: "postgresql"
});

if (testResult.success) {
  // 2. Import schema
  const importResult = await databaseApi.importFromDatabaseUrl({
    connection_url: "postgresql://user:pass@host:5432/db",
    type: "postgresql"
  });
  
  if (importResult.success && importResult.data) {
    // 3. Store schema and navigate to visualization
    setCurrentSchema(importResult.data);
    router.push("/schema");
  }
}
```

---

## Common Issues & Solutions

### Issue 1: "Connection timeout"
**Cause**: Database server not accessible from backend server
**Solution**: Check firewall rules, ensure backend IP is whitelisted

### Issue 2: "Authentication failed"
**Cause**: Invalid credentials in connection URL
**Solution**: Verify username/password, check if user exists

### Issue 3: "SSL required"
**Cause**: Database requires encrypted connection
**Solution**: Add `?sslmode=require` to PostgreSQL URL or appropriate SSL parameter for other databases

### Issue 4: "Permission denied"
**Cause**: Database user lacks read permissions
**Solution**: Grant SELECT permission on information_schema and target tables

### Issue 5: "No tables found"
**Cause**: Database is empty or user can't see tables
**Solution**: Check schema name, verify permissions

---

## API Base URLs

**Development**: `http://localhost:8000/api/database`
**Production**: `https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/database`

---

## Questions for Backend Team?

1. What is the maximum timeout for database connections?
2. Are there rate limits on connection attempts?
3. Should we cache database metadata? If so, for how long?
4. What IP addresses will the backend use (for firewall whitelisting)?
5. Is there a limit on the number of tables we can import at once?
6. Do you support connection poolers (PgBouncer, Supabase Transaction mode)?
7. What database versions are supported for each type?
