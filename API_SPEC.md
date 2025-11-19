have # SchemaSage API Specification

**Last updated:** 2025-11-16  
**Status:** Based on actual codebase implementation

This document describes HTTP and WebSocket endpoints across all SchemaSage services. It combines the implementation roadmap features with actual existing endpoints discovered from the codebase.

## CONVENTIONS & COMMON PATTERNS

### Authentication
- Bearer JWT in `Authorization: Bearer <token>` header
- JWT payload includes: `sub` (username), `user_id` (integer), `is_admin` (boolean)
- Refresh via `POST /refresh-token`
- Optional auth on some endpoints (specified below)

### Content-Type
- `application/json` for POST/PUT/PATCH (unless multipart/form-data for file uploads)
- Responses always JSON unless specified

### Error Format
```json
{
  "message": "Human readable error",
  "details": {"field": "additional context"},
  "status": "error"
}
```
Common HTTP codes: 200 OK, 201 Created, 202 Accepted, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Validation Error, 429 Rate Limited, 500 Server Error

### Pagination
- Query params: `?page=1&per_page=25` (or `limit`/`offset` in some endpoints)
- Response meta: `{ "total": 123, "page": 1, "per_page": 25 }`

### Date/Time
- ISO 8601 UTC: `2025-11-16T12:34:56Z`

### Versioning
- Most endpoints use `/api/<resource>` (implied v1)
- Gateway proxies to: `/api/auth/*`, `/api/detection/*`, `/api/code/*`, `/api/project/*`, `/api/chat/*`, `/api/database/*`

---

## AUTHENTICATION SERVICE (`authentication/`)

Base path (via gateway): `/api/auth/*` → `authentication/`

### Core Authentication

**POST `/signup`**
- Create new user account
- Auth: none
- Request:
  ```json
  {
    "username": "alice",
    "password": "SecureP@ss123",
    "is_admin": false
  }
  ```
- Response 200:
  ```json
  {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "expires_in": 86400
  }
  ```
- Notes: Password must have uppercase, lowercase, digit, min 8 chars. Username alphanumeric + underscore. Triggers AI chat pre-authentication and WebSocket notification.

**POST `/login`**
- Authenticate user
- Auth: none
- Request:
  ```json
  {
    "username": "alice",
    "password": "SecureP@ss123"
  }
  ```
- Response 200:
  ```json
  {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 123,
      "username": "alice",
      "is_admin": false,
      "created_at": "2025-01-15T10:30:00Z",
      "last_login": "2025-11-16T08:00:00Z"
    }
  }
  ```
- Notes: Rate limited (5 attempts/min per IP). Failed attempts trigger account lock after threshold. Triggers instant dashboard stats broadcast.

**POST `/token`** (OAuth2-compatible)
- Same as `/login` but uses form-encoded credentials
- Auth: none
- Request (form-data): `username=alice&password=SecureP@ss123`
- Response: same as `/login`

**POST `/refresh-token`**
- Refresh access token
- Auth: bearer (current user)
- Response: same as `/login` (new token + user)

**POST `/logout`**
- Logout (client discards token)
- Auth: bearer
- Response: `{ "message": "Successfully logged out" }`

**GET `/me`**
- Get current user profile
- Auth: bearer
- Response:
  ```json
  {
    "id": 123,
    "username": "alice",
    "is_admin": false,
    "created_at": "2025-01-15T10:30:00Z",
    "last_login": "2025-11-16T08:00:00Z"
  }
  ```

**GET `/users`**
- List all users (admin only)
- Auth: bearer (admin)
- Response: array of user objects (same shape as `/me`)

### Google OAuth

**GET `/google`**
**POST `/google`**
- Redirect to Google OAuth consent screen
- Auth: none
- Query params: none
- Redirects to Google login

**GET `/google/callback`**
- OAuth callback handler
- Auth: none (receives `code` from Google)
- Creates/updates user based on Google account
- Redirects to frontend with token

---

## API GATEWAY (`api-gateway/`)

The gateway is a **pure proxy** that routes to backend microservices. It forwards all requests with proper CORS, auth headers, and timeout handling (60s for long operations).

### Routing Pattern
All requests to gateway are forwarded to backend services:
- `/api/auth/*` → authentication service
- `/api/detection/*` → schema-detection service
- `/api/code/*` → code-generation service
- `/api/project/*` → project-management service
- `/api/chat/*` → ai-chat service
- `/api/database/*` → database-migration service
- `/ws/*` → websocket-realtime service (WebSocket upgrade)

### Health Check
**GET `/health`**
- Overall system health
- Response:
  ```json
  {
    "status": "ok",
    "services": {
      "auth": "ok",
      "schema-detection": "ok",
      "code-generation": "ok",
      "ai-chat": "ok",
      "database-migration": "ok"
    }
  }
  ```

### Gateway-Specific Endpoints (Future)
These are planned aggregation endpoints (from roadmap):

**POST `/api/roi/calculate`** (planned)
- ROI calculator widget
- Auth: optional
- Request: `{ "company_size": 100, "databases": 5, "monthly_cloud_spend": 12000, "compliance": ["gdpr"], "current_tools": ["datagrip"] }`
- Response: `{ "savings": 146102, "payback_days": 6, "breakdown": {...} }`

**POST `/api/costs/compare`** (planned)
- Multi-cloud cost comparison
- See database-migration service for implementation

---

## SCHEMA DETECTION SERVICE (`schema-detection/`)

Base path (via gateway): `/api/detection/*` → `schema-detection/`

Performs schema scanning, PII detection, data lineage, compliance checks, security audits, query generation, health scoring, and AI-powered insights.

### Health & Service Info

**GET `/health`**
- Service health check
- Response: `{ "status": "healthy", "service": "schema-detection", "version": "1.0.0" }`

**GET `/`**
- Service root with stats
- Response: `{ "service": "Schema Detection", "status": "online", "endpoints": [...] }`

**GET `/stats`**
- Service statistics
- Response: `{ "total_jobs": 150, "active_jobs": 3, "completed_jobs": 147 }`

### Schema Detection & Jobs

**POST `/api/detection-jobs`**
- Create a new detection job
- Auth: bearer (optional)
- Request:
  ```json
  {
    "job_type": "schema_detection",
    "data_source": { "type": "postgresql", "host": "db.example.com", "port": 5432, "database": "app", "user": "readonly", "password": "***" },
    "parameters": { "deep_scan": true, "pii_detect": true }
  }
  ```
- Response 202:
  ```json
  {
    "job_id": "uuid",
    "status": "queued",
    "created_at": "2025-11-16T10:00:00Z"
  }
  ```

**GET `/api/detection-jobs`**
- List all detection jobs for current user
- Auth: bearer (optional)
- Query params: `?status=completed&limit=10`
- Response: array of job objects

**GET `/api/detection-jobs/{job_id}`**
- Get job status and results
- Auth: bearer (optional)
- Response:
  ```json
  {
    "job_id": "uuid",
    "status": "completed",
    "progress": 100,
    "result": {
      "tables": [...],
      "relationships": [...],
      "detected_pii": 12
    }
  }
  ```

**POST `/api/schemas`**
- Create/save a detected schema
- Request: `{ "schema_name": "my_app", "schema_data": {...} }`
- Response: `{ "schema_id": "uuid", "schema_name": "my_app" }`

### Frontend API (File Upload)

**POST `/api/frontend/detect-from-file`**
- Detect schema from uploaded SQL/CSV file
- Auth: bearer (optional)
- Request: multipart/form-data with `file` field
- Response:
  ```json
  {
    "schema": {
      "tables": { "users": { "columns": {...} } },
      "relationships": [...]
    },
    "stats": {
      "tables_count": 5,
      "relationships_count": 8
    }
  }
  ```

**POST `/api/frontend/detect`**
- Detect schema from SQL text
- Request: `{ "sql": "CREATE TABLE users (...)" }`
- Response: same as `/detect-from-file`

**GET `/api/frontend/history`**
- Get detection history
- Response: array of past detections

**GET `/api/frontend/tables`**
- List tables in current schema
- Response: array of table objects

**GET `/api/frontend/relationships`**
- Get table relationships
- Response: array of relationships

**GET `/api/frontend/health`**
- Frontend API health
- Response: `{ "status": "healthy" }`

### Data Lineage

**POST `/api/lineage/table`**
- Get lineage for a table
- Request: `{ "table_name": "orders", "depth": 2 }`
- Response:
  ```json
  {
    "table": "orders",
    "upstream": ["users", "products"],
    "downstream": ["order_items", "invoices"],
    "depth": 2
  }
  ```

**POST `/api/lineage/column`**
- Get lineage for a column
- Request: `{ "table_name": "users", "column_name": "email", "depth": 2 }`
- Response: column-level lineage graph

**GET `/api/lineage/tables/{table_name}/summary`**
- Lineage summary for table

**GET `/api/lineage/columns/{table_name}/{column_name}/summary`**
- Lineage summary for column

**GET `/api/lineage/search`**
- Search lineage (e.g., find all tables containing PII)
- Query params: `?query=email&type=column`

**GET `/api/lineage/stats`**
- Lineage statistics

**POST `/api/lineage/impact-analysis`**
- Analyze impact of dropping/changing a table/column
- Request: `{ "table": "users", "action": "drop" }`
- Response: list of affected downstream objects

### Enhanced Lineage

**GET `/api/enhanced-lineage/table/{table_name}`**
- Enhanced lineage with more metadata
- Response: full lineage graph with relationships, data flows, dependencies

**GET `/api/enhanced-lineage/column/{table_name}/{column_name}`**
- Column-level enhanced lineage

### Security Audit

**POST `/api/security/audit`**
- Start comprehensive security audit
- Request: `{ "schema": {...}, "audit_options": {...} }`
- Response: `{ "audit_id": "uuid", "status": "running" }`

**GET `/api/security/audit/{audit_id}`**
- Get audit results
- Response:
  ```json
  {
    "audit_id": "uuid",
    "status": "completed",
    "score": 73,
    "vulnerabilities": [
      {
        "severity": "high",
        "type": "unencrypted_pii",
        "table": "users",
        "column": "email",
        "recommendation": "Enable encryption"
      }
    ]
  }
  ```

**POST `/api/security/quick-scan`**
- Quick security scan (subset of full audit)
- Request: `{ "schema": {...} }`
- Response: simplified audit results

**GET `/api/security/vulnerability-database`**
- Get known vulnerability patterns
- Response: array of vulnerability definitions

**GET `/api/security/audit-history`**
- Past audit results

### Schema Analysis

**POST `/api/schema-analysis/analyze`**
- Comprehensive schema analysis
- Request: `{ "schema": {...}, "analysis_types": ["quality", "performance", "security"] }`
- Response:
  ```json
  {
    "quality_score": 73,
    "performance_issues": [...],
    "security_issues": [...],
    "recommendations": [...]
  }
  ```

**GET `/api/schema-analysis/analyze/types`**
- Available analysis types
- Response: `["quality", "performance", "security", "compliance"]`

### Query Tools

**POST `/api/query/generate`**
- Generate SQL queries from natural language
- Request: `{ "prompt": "Get all users who signed up last week", "schema": {...} }`
- Response: `{ "sql": "SELECT * FROM users WHERE created_at > ...", "explanation": "..." }`

**POST `/api/query/execute`**
- Execute a query (read-only)
- Request: `{ "sql": "SELECT * FROM users LIMIT 10", "connection": {...} }`
- Response: `{ "rows": [...], "columns": [...], "row_count": 10 }`

**POST `/api/query/validate`**
- Validate SQL syntax
- Request: `{ "sql": "SELCT * FROM users" }`
- Response: `{ "valid": false, "errors": ["Syntax error near 'SELCT'"] }`

**POST `/api/query/optimize`**
- Optimize a query
- Request: `{ "sql": "SELECT * FROM users WHERE email = 'test@example.com'", "schema": {...} }`
- Response: `{ "optimized_sql": "...", "improvements": ["Added index suggestion"], "estimated_speedup": "120x" }`

**GET `/api/query/history`**
- Query execution history

### Search

**POST `/api/search/semantic`**
- Semantic search across schema (AI-powered)
- Request: `{ "query": "find customer email addresses", "schema": {...} }`
- Response: ranked list of matching tables/columns

**POST `/api/search/schema`**
- Text search in schema
- Request: `{ "query": "email" }`
- Response: matching tables/columns

**GET `/api/search/suggestions`**
- Search suggestions / autocomplete

**GET `/api/search/recent`**
- Recent searches

**DELETE `/api/search/recent`**
- Clear recent searches

### Schema History & Versioning

**GET `/api/history/history/{table_name}`**
- Get version history for a table
- Response: list of snapshots with timestamps

**POST `/api/history/snapshot`**
- Create a schema snapshot
- Request: `{ "schema": {...}, "comment": "Pre-migration snapshot" }`
- Response: `{ "snapshot_id": "uuid", "created_at": "..." }`

**GET `/api/history/diff/{table_name}`**
- Get diff between two versions
- Query params: `?from_version=1&to_version=2`
- Response: diff object

**POST `/api/history/documentation/generate`**
- Auto-generate schema documentation
- Request: `{ "schema": {...}, "format": "markdown" }`
- Response: `{ "documentation": "# Schema Documentation\n..." }`

**POST `/api/history/documentation/export`**
- Export documentation to file
- Response: file download URL

**POST `/api/history/cleaning/analyze`**
- Analyze data quality issues
- Request: `{ "schema": {...}, "sample_data": [...] }`
- Response: list of data quality issues

**POST `/api/history/cleaning/apply`**
- Apply data cleaning rules
- Request: `{ "cleaning_plan": {...} }`
- Response: results of cleaning operations

**GET `/api/history/versions`**
- List all schema versions

**DELETE `/api/history/history/{table_name}/{version}`**
- Delete a specific version

**POST `/api/history/diagram/save`**
- Save an ER diagram
- Request: `{ "diagram_data": {...}, "name": "Production Schema v2" }`
- Response: `{ "diagram_id": "uuid" }`

**GET `/api/history/diagram/{diagram_id}`**
- Get saved diagram

**PUT `/api/history/diagram/{diagram_id}`**
- Update diagram

**DELETE `/api/history/diagram/{diagram_id}`**
- Delete diagram

**GET `/api/history/diagrams/list`**
- List all saved diagrams

### Health Score

**POST `/api/health/analyze`**
- Analyze schema health
- Request: `{ "schema": {...} }`
- Response:
  ```json
  {
    "overall_score": 73,
    "categories": {
      "indexing": 22,
      "naming": 15,
      "normalization": 18,
      "security": 18
    },
    "issues": [...],
    "recommendations": [...]
  }
  ```

**GET `/api/health/history`**
- Health score history

**POST `/api/health/monitor`**
- Set up health monitoring alerts
- Request: `{ "threshold": 70, "alert_channels": ["email", "slack"] }`
- Response: `{ "monitor_id": "uuid" }`

**GET `/api/health/benchmarks`**
- Industry benchmarks
- Response: `{ "saas_50-500": 68, "ecommerce": 72, ... }`

**GET `/api/health/alerts`**
- Get active health alerts

### Cloud Provisioning (Quick Deploy)

**POST `/api/cloud/provision`** (planned - from roadmap)
- Start cloud database provisioning
- Request: `{ "provider": "aws", "region": "us-east-1", "instance_type": "r5.large", "schema": {...} }`
- Response: `{ "provision_id": "uuid", "status": "provisioning", "estimated_time_min": 15 }`

**GET `/api/cloud/provision/{provision_id}`** (planned)
- Get provisioning status

### AI Insights

**POST `/api/ai/insights`** (planned - from roadmap)
- Get AI-powered schema insights
- Request: `{ "schema": {...}, "focus": ["performance", "security"] }`
- Response: `{ "insights": [...], "recommendations": [...] }`

### Compliance Detection

**POST `/api/compliance/detect`** (planned - from roadmap)
- Detect compliance issues (GDPR, SOC2, HIPAA)
- Request: `{ "schema": {...}, "frameworks": ["gdpr", "soc2"] }`
- Response:
  ```json
  {
    "gdpr_compliant": false,
    "issues": [
      {
        "framework": "gdpr",
        "severity": "high",
        "issue": "No data retention policy",
        "tables": ["users", "orders"]
      }
    ]
  }
  ```

**POST `/api/compliance/auto-fix`** (planned - from roadmap)
- Generate compliance fixes
- See code-generation service for implementation

---

## AI CHAT SERVICE (`ai-chat/`)

Base path (via gateway): `/api/chat/*` → `ai-chat/`

Provides AI-powered chat for schema design, query assistance, and natural language database interactions using OpenAI GPT-4.

### Health Check

**GET `/health`**
- Service health + AI provider status
- Response:
  ```json
  {
    "status": "healthy",
    "service": "AI Chat Service",
    "version": "1.0.0",
    "ai_providers": {
      "openai": true
    }
  }
  ```

### Chat Endpoint

**POST `/chat`**
- Main AI chat interface
- Auth: bearer (required)
- Rate limit: 20 requests/minute per IP
- Request:
  ```json
  {
    "message": "I need to design a schema for a blog with users, posts, and comments",
    "session_id": "uuid",
    "context": {
      "schema": {...},
      "previous_messages": [...]
    },
    "api_key": "sk-..." // optional, overrides server key
  }
  ```
- Response 200:
  ```json
  {
    "message": "Here's a schema design for your blog...",
    "session_id": "uuid",
    "artifacts": {
      "sql": "CREATE TABLE users ...",
      "orm_models": "...",
      "migrations": "..."
    },
    "suggestions": [
      "Add full-text search",
      "Consider soft deletes for posts"
    ]
  }
  ```
- Errors:
  - 401: Authentication required
  - 429: Rate limit exceeded
  - 503: OpenAI API key not configured

**OPTIONS `/chat`**
- CORS preflight for `/chat`

### AI Features (via chat interface)
The AI chat can handle:
- Schema design from natural language
- Query generation and optimization
- Cost explanation (via query analysis)
- Migration planning
- Best practices recommendations
- Security and compliance advice

### Database Persistence
- All chat sessions are stored in PostgreSQL
- Sessions linked to user_id (integer from users table)
- Session history queryable via database (not exposed as separate endpoint currently)

### Pre-Authentication
The authentication service pre-authenticates users with AI chat on login/signup, establishing session context.

---

## CODE GENERATION SERVICE (`code-generation/`)

Base path (via gateway): `/api/code/*` → `code-generation/`

Generates code, migrations, ORM models, API scaffolds, and compliance fixes from database schemas.

### Health Check

**GET `/health`**
- Service health
- Response: `{ "status": "healthy", "service": "Code Generation Service", "version": "1.0.0", "ai_enhanced": true/false }`

### Schema Code Generation

**POST `/api/schema/generate`**
- Generate code in multiple formats from schema
- Auth: bearer (optional)
- Request:
  ```json
  {
    "schema": {
      "tables": {
        "users": {
          "columns": {
            "id": {"type": "uuid", "primary_key": true},
            "email": {"type": "varchar", "unique": true}
          }
        }
      }
    },
    "formats": ["sql", "django", "sqlalchemy", "typescript"],
    "options": {
      "include_migrations": true,
      "include_tests": false
    }
  }
  ```
- Response 200:
  ```json
  {
    "generated_code": {
      "sql": "CREATE TABLE users ...",
      "django": "class User(models.Model): ...",
      "sqlalchemy": "class User(Base): ...",
      "typescript": "interface User { ... }"
    },
    "migrations": {
      "sql": ["001_create_users.sql", "..."]
    },
    "notes": ["Remember to run migrations in order", "..."]
  }
  ```

**GET `/api/schema/health`**
- Schema generation health check

### Full-Stack Code Generation

**POST `/api/generate/generate-code`**
- Generate full-stack code (backend API + frontend models)
- Request:
  ```json
  {
    "schema": {...},
    "backend_framework": "fastapi",
    "frontend_framework": "react",
    "features": ["crud", "auth", "pagination"]
  }
  ```
- Response: ZIP file or structured code objects

**POST `/api/generate/scaffold`**
- Generate API scaffold with CRUD endpoints
- Request:
  ```json
  {
    "schema": {...},
    "framework": "fastapi",
    "include_auth": true
  }
  ```
- Response:
  ```json
  {
    "files": {
      "main.py": "...",
      "models.py": "...",
      "routers/users.py": "...",
      "schemas.py": "..."
    },
    "structure": "..."
  }
  ```

### Compliance Code Generation

**POST `/api/compliance/generate-compliant-schema`**
- Generate GDPR/SOC2/HIPAA compliant schema
- Request:
  ```json
  {
    "base_schema": {...},
    "compliance_frameworks": ["gdpr", "soc2"],
    "options": {
      "encryption": "pgcrypto",
      "audit_logging": true
    }
  }
  ```
- Response:
  ```json
  {
    "compliant_schema": {...},
    "migrations": ["ALTER TABLE users ADD COLUMN deleted_at ...", "..."],
    "code_changes": {
      "models": "...",
      "migrations": "..."
    },
    "compliance_checklist": [
      {"framework": "gdpr", "requirement": "Right to deletion", "status": "implemented"},
      ...
    ]
  }
  ```

**GET `/api/compliance/templates`**
- Get compliance templates
- Query params: `?framework=gdpr`
- Response: array of template objects

**GET `/api/compliance/templates/{template_id}`**
- Get specific compliance template

**POST `/api/compliance/generate-custom-template`**
- Generate custom compliance template
- Request: `{ "requirements": [...], "industry": "healthcare" }`
- Response: custom template object

**GET `/api/compliance/industry/{industry}/recommendations`**
- Get industry-specific compliance recommendations
- Path: `healthcare`, `finance`, `saas`, etc.
- Response: array of recommendations

**GET `/api/compliance/health`**
- Compliance generation health

### Code Generation Jobs (Planned)
Future: async job system for large codebases
- POST `/api/jobs/generate`
- GET `/api/jobs/{job_id}`

---

## DATABASE MIGRATION SERVICE (`database-migration/`)

Base path (via gateway): `/api/database/*` → `database-migration/`

**Enterprise Edition** with PostgreSQL persistence, JWT auth, AES-256 encryption, multi-user isolation, real-time health monitoring.

### Health & Info

**GET `/health`**
- Service health
- Response: `{ "status": "healthy", "service": "Database Migration - Enterprise", "version": "2.0.0" }`

### Universal Migration

**GET `/api/universal/supported`**
- List supported databases
- Response:
  ```json
  {
    "source_databases": ["mysql", "postgresql", "sqlite", "sqlserver", "oracle"],
    "target_databases": ["mysql", "postgresql", "sqlite", "mongodb"]
  }
  ```

**POST `/api/universal/test-connection-url`**
- Test database connection
- Request: `{ "connection_url": "postgresql://user:pass@host:5432/db" }`
- Response: `{ "success": true, "database_type": "postgresql", "version": "15.2" }`

**GET `/api/universal/test/history`**
- Connection test history

**POST `/api/universal/import-from-url`**
- Import schema from database URL
- Request: `{ "source_url": "...", "target_url": "...", "options": {...} }`
- Response 202: `{ "task_id": "uuid", "status": "running" }`

**GET `/api/universal/import-status/{task_id}`**
- Get import task status
- Response:
  ```json
  {
    "task_id": "uuid",
    "status": "completed",
    "progress": 100,
    "tables_imported": 47,
    "rows_imported": 2340000
  }
  ```

**POST `/api/universal/import/{task_id}/cancel`**
- Cancel running import

**POST `/api/universal/create-migration-plan`**
- Create migration plan
- Request: `{ "source": {...}, "target": {...}, "options": {...} }`
- Response: `{ "plan_id": "uuid", "steps": [...], "estimated_time_min": 45 }`

**POST `/api/universal/execute-migration`**
- Execute migration plan
- Request: `{ "plan_id": "uuid", "options": {...} }`
- Response 202: `{ "execution_id": "uuid", "status": "running" }`

**GET `/api/universal/migration-status/{execution_id}`**
- Get migration execution status

### Cloud Migration (Simple)

**GET `/api/cloud/cloud-providers`**
- List supported cloud providers
- Response:
  ```json
  {
    "providers": [
      {"id": "aws", "name": "Amazon Web Services", "databases": ["rds-postgres", "rds-mysql", "aurora"]},
      {"id": "gcp", "name": "Google Cloud Platform", "databases": ["cloud-sql-postgres", "cloud-sql-mysql"]},
      {"id": "azure", "name": "Microsoft Azure", "databases": ["azure-db-postgres", "azure-db-mysql"]}
    ]
  }
  ```

**POST `/api/cloud/assess-readiness`**
- Assess cloud migration readiness
- Request: `{ "current_database": {...}, "target_cloud": "aws" }`
- Response:
  ```json
  {
    "readiness_score": 85,
    "blockers": [],
    "warnings": ["Large BLOB columns may increase costs"],
    "recommendations": [...]
  }
  ```

**POST `/api/cloud/create-migration-plan`**
- Create cloud migration plan
- Request: `{ "source": {...}, "target_cloud": "aws", "target_region": "us-east-1" }`
- Response: migration plan with steps, costs, downtime estimates

**GET `/api/cloud/migration-status/{migration_id}`**
- Get cloud migration status

### Multi-Cloud Comparison

**POST `/api/multi-cloud/compare`**
- Compare costs/features across AWS, GCP, Azure
- Request:
  ```json
  {
    "workload": {
      "database_size_gb": 200,
      "monthly_queries": 10000000,
      "peak_connections": 500,
      "backup_retention_days": 30
    },
    "providers": ["aws", "gcp", "azure"],
    "regions": ["us-east-1", "us-central1", "eastus"]
  }
  ```
- Response 200:
  ```json
  {
    "comparisons": [
      {
        "provider": "aws",
        "region": "us-east-1",
        "monthly_cost": 127.45,
        "breakdown": {"compute": 60, "storage": 40, "backup": 20, "egress": 7.45},
        "instance_recommendation": "r5.large",
        "features": ["Multi-AZ", "Read replicas", "Auto-scaling"]
      },
      {
        "provider": "gcp",
        "region": "us-central1",
        "monthly_cost": 89.20,
        "...": "..."
      }
    ],
    "recommendation": "gcp"
  }
  ```

**GET `/api/multi-cloud/pricing/{provider}`**
- Get pricing details for a provider

### Performance & Cost Calculator

**POST `/api/performance-cost/cost-analysis`**
- Analyze database costs
- Request: `{ "database_config": {...}, "usage_patterns": {...} }`
- Response: cost breakdown, optimization suggestions

**GET `/api/performance-cost/pricing-info`**
- Get current pricing info for all clouds

**POST `/api/performance-cost/estimate-migration-cost`**
- Estimate one-time migration costs
- Request: `{ "source": {...}, "target": {...}, "data_size_gb": 500 }`
- Response: `{ "one_time_cost": 1250, "ongoing_monthly_cost": 180, "break_even_months": 7 }`

**GET `/api/performance-cost/optimization-templates`**
- Get cost optimization templates

### Smart Rollback

**POST `/api/rollback/smart-rollback`**
- Generate smart rollback plan
- Request: `{ "migration_id": "uuid", "target_state": "before_migration" }`
- Response: `{ "rollback_id": "uuid", "confidence": 0.95, "steps": [...] }`

**POST `/api/rollback/rollback/{rollback_id}/execute`**
- Execute rollback plan
- Response 202: `{ "execution_id": "uuid", "status": "running" }`

**GET `/api/rollback/rollback/{rollback_id}/status`**
- Get rollback status

**GET `/api/rollback/rollback-plans`**
- List all rollback plans

**GET `/api/rollback/migrations/{migration_id}/rollback-analysis`**
- Analyze rollback feasibility

**GET `/api/rollback/rollback-templates`**
- Get rollback templates

**POST `/api/rollback/validate-rollback-plan/{rollback_id}`**
- Validate rollback plan before execution

### Migration Management

**POST `/api/migrations/{migration_id}/rollback`**
- Rollback a completed migration
- Response: rollback execution details

**GET `/api/migrations/rollback/{rollback_id}/status`**
- Get rollback status

**POST `/api/migrations/{migration_id}/cancel`**
- Cancel running migration

**POST `/api/migrations/{migration_id}/pause`**
- Pause migration

**POST `/api/migrations/{migration_id}/resume`**
- Resume paused migration

**GET `/api/migrations/{migration_id}/dependencies`**
- Get migration dependencies

**POST `/api/migrations/batch`**
- Execute batch migrations
- Request: `{ "migration_ids": ["uuid1", "uuid2"], "execution_order": "sequential" }`
- Response: `{ "batch_id": "uuid" }`

**GET `/api/migrations/batch/{batch_id}/status`**
- Get batch migration status

### Monitoring & Alerts

**GET `/api/monitoring/metrics`**
- Real-time metrics
- Response:
  ```json
  {
    "active_migrations": 2,
    "queued_migrations": 5,
    "completed_today": 23,
    "success_rate": 0.96,
    "avg_migration_time_min": 18
  }
  ```

**GET `/api/monitoring/services`**
- Service health statuses

**GET `/api/monitoring/migrations`**
- All migrations with status

**GET `/api/monitoring/dashboard/summary`**
- Dashboard summary

**GET `/api/monitoring/alerts`**
- Active alerts

**POST `/api/monitoring/alerts/{alert_id}/acknowledge`**
- Acknowledge an alert

**GET `/api/monitoring/performance`**
- Performance metrics

### Workspaces (Multi-Tenant)

**POST `/api/workspaces`**
- Create workspace
- Request: `{ "name": "Production", "description": "...", "owner_id": 123 }`
- Response: `{ "workspace_id": "uuid", "name": "Production" }`

**GET `/api/workspaces`**
- List workspaces for current user

**GET `/api/workspaces/{workspace_id}`**
- Get workspace details

**POST `/api/workspaces/{workspace_id}/members`**
- Add member to workspace
- Request: `{ "user_id": 456, "role": "editor" }`

**GET `/api/workspaces/{workspace_id}/members`**
- List workspace members

**GET `/api/workspaces/{workspace_id}/audit-logs`**
- Get audit logs for workspace

### Version Control Integration

**POST `/api/version-control/workspaces/{workspace_id}/git-repositories`**
- Link Git repository to workspace
- Request: `{ "repo_url": "https://github.com/...", "branch": "main" }`
- Response: `{ "repo_id": "uuid" }`

**POST `/api/version-control/git-repositories/{repo_id}/branches`**
- Create schema branch
- Request: `{ "branch_name": "feature/new-schema", "base_branch": "main" }`

**POST `/api/version-control/workspaces/{workspace_id}/pipelines`**
- Create CI/CD pipeline
- Request: pipeline configuration

**POST `/api/version-control/pipelines/{pipeline_id}/execute`**
- Execute pipeline

### Environment Management

**POST `/api/environments`** (planned - from roadmap)
- Manage dev/staging/prod environments
- Planned for Phase 3

### Cost Tracking & Optimization

**POST `/api/cost-tracking/track`** (planned)
- Track ongoing costs
- Planned for Phase 2

### Infrastructure Optimization

**POST `/api/infrastructure/optimize`** (planned)
- Auto-optimize infrastructure
- Planned for Phase 3

### Full-Stack Deployment

**POST `/api/full-stack/deploy`** (planned)
- Deploy full-stack applications
- Planned for Phase 3

### ETL Pipelines

**POST `/api/etl/create-pipeline`** (planned - from roadmap Phase 1)
- Create ETL pipeline
- Request: source/target config, transformations
- Response: pipeline_id

**POST `/api/etl/execute-pipeline`** (planned)
- Execute ETL pipeline

### Anonymization (Planned - from roadmap Phase 3)

**POST `/api/anonymize/plan`**
- Create anonymization plan
- Request: tables, strategies, sampling rules
- Response: plan with estimated time/size

**POST `/api/anonymize/execute`**
- Execute anonymization
- Response 202: job_id

---

## PROJECT MANAGEMENT SERVICE (`project-management/`)

Base path (via gateway): `/api/project/*` → `project-management/`

Manages projects, schemas, team collaboration, integrations, compliance tracking, marketplace, payments, and multi-tenancy.

### Health Check

**GET `/health`**
- Service health
- Response: `{ "status": "healthy", "service": "Project Management", "version": "1.0.0" }`

### Projects

**POST `/api/projects`**
- Create new project
- Auth: bearer
- Request:
  ```json
  {
    "name": "E-commerce Platform",
    "description": "Main database for online store",
    "tags": ["production", "ecommerce"]
  }
  ```
- Response 201:
  ```json
  {
    "id": "uuid",
    "name": "E-commerce Platform",
    "description": "...",
    "owner_id": 123,
    "created_at": "2025-11-16T10:00:00Z",
    "tags": ["production", "ecommerce"]
  }
  ```

**GET `/api/projects`**
- List all projects for current user
- Query params: `?page=1&per_page=25&tags=production`
- Response:
  ```json
  {
    "projects": [...],
    "meta": {"total": 42, "page": 1, "per_page": 25}
  }
  ```

**GET `/api/projects/{project_id}`**
- Get project details
- Response: project object

**PUT `/api/projects/{project_id}`**
- Update project
- Request: `{ "name": "Updated name", "description": "..." }`
- Response: updated project object

**DELETE `/api/projects/{project_id}`**
- Delete project
- Response 204: no content

**GET `/api/projects/search/{query}`**
- Search projects
- Path param: search query
- Response: array of matching projects

### Comments & Collaboration

**POST `/api/projects/{project_id}/comments`**
- Add comment to project
- Request: `{ "content": "This schema looks good", "mentions": [456] }`
- Response: comment object

**GET `/api/projects/{project_id}/comments`**
- Get project comments
- Response: array of comments

**DELETE `/api/projects/{project_id}/comments/{comment_idx}`**
- Delete comment

**POST `/api/collaboration/lock`** (from collaboration router)
- Lock a resource for editing
- Request: `{ "resource_type": "schema", "resource_id": "uuid" }`
- Response: `{ "lock_id": "uuid", "expires_at": "..." }`

**DELETE `/api/collaboration/lock/{lock_id}`**
- Release lock

### File Uploads

**POST `/api/upload/file`**
- Upload single file
- Auth: bearer
- Request: multipart/form-data with `file` field
- Response:
  ```json
  {
    "file_id": "uuid",
    "filename": "schema.sql",
    "size_bytes": 15420,
    "url": "/files/uuid/schema.sql"
  }
  ```

**POST `/api/upload/files`**
- Upload multiple files
- Request: multipart/form-data with multiple `files` fields
- Response: array of file objects

**DELETE `/api/upload/file/{file_id}`**
- Delete uploaded file

### Stats & Analytics

**GET `/api/stats/overview`** (from stats router)
- Project statistics overview
- Response:
  ```json
  {
    "total_projects": 42,
    "active_projects": 28,
    "total_schemas": 156,
    "team_members": 12
  }
  ```

### Integrations

**POST `/api/integrations/connect`** (from integrations router)
- Connect external integration
- Request: `{ "provider": "github", "credentials": {...} }`
- Response: `{ "integration_id": "uuid", "status": "connected" }`

**GET `/api/integrations`**
- List connected integrations

**DELETE `/api/integrations/{integration_id}`**
- Disconnect integration

### Data Dictionary Integration

**POST `/api/data-dictionary/sync`** (from data_dictionary_integration router)
- Sync with external data dictionary
- Request: `{ "source": "collibra", "project_id": "uuid" }`
- Response: sync status

### Glossary

**GET `/api/glossary/terms`** (from glossary router)
- Get business glossary terms
- Response: array of terms

**POST `/api/glossary/terms`**
- Add glossary term
- Request: `{ "term": "Customer", "definition": "...", "related_tables": ["customers", "orders"] }`

### Team Management

**GET `/api/team/members`** (from team router)
- List team members
- Response: array of team members

**POST `/api/team/invite`**
- Invite team member
- Request: `{ "email": "alice@example.com", "role": "editor" }`
- Response: invitation object

### Compliance

**GET `/api/compliance/status`** (from compliance router)
- Get project compliance status
- Response:
  ```json
  {
    "project_id": "uuid",
    "frameworks": {
      "gdpr": {"compliant": true, "last_check": "..."},
      "soc2": {"compliant": false, "issues": 3}
    }
  }
  ```

**POST `/api/compliance/scan`**
- Run compliance scan
- Request: `{ "project_id": "uuid", "frameworks": ["gdpr", "soc2"] }`
- Response 202: `{ "scan_id": "uuid", "status": "running" }`

### Compliance Alerts

**GET `/api/compliance-alerts/active`** (from compliance_alerts router)
- Get active compliance alerts
- Response: array of alerts

**POST `/api/compliance-alerts/{alert_id}/resolve`**
- Mark alert as resolved

### Regulatory Notifications

**GET `/api/regulations/updates`**
- Get regulatory updates
- Response:
  ```json
  {
    "updates": [
      {
        "regulation": "GDPR",
        "title": "New data portability requirements",
        "effective_date": "2026-01-01",
        "impact": "high"
      }
    ]
  }
  ```

**POST `/api/regulations/subscribe`**
- Subscribe to regulatory updates
- Request: `{ "frameworks": ["gdpr", "ccpa"], "notification_channel": "email" }`

**GET `/api/regulations/subscriptions`**
- Get active subscriptions

**DELETE `/api/regulations/subscriptions/{subscription_id}`**
- Unsubscribe

**POST `/api/regulations/impact-analysis`**
- Analyze regulatory impact
- Request: `{ "regulation": "GDPR", "project_id": "uuid" }`
- Response: impact analysis report

**GET `/api/regulations/frameworks`**
- List supported regulatory frameworks

**GET `/api/regulations/compliance-checklist/{regulation}`**
- Get compliance checklist for regulation
- Path: `gdpr`, `soc2`, `hipaa`, etc.

**GET `/api/regulations/deadlines`**
- Upcoming compliance deadlines

**GET `/api/regulations/stats`**
- Regulatory compliance statistics

### Marketplace

**GET `/api/marketplace/templates`** (from marketplace router)
- Browse schema templates
- Response: array of template listings

**POST `/api/marketplace/templates/purchase`**
- Purchase template
- Request: `{ "template_id": "uuid", "payment_method": "stripe_pm_..." }`

**GET `/api/marketplace/my-purchases`**
- List purchased templates

### Payments & Analytics

**POST `/api/payments/create-intent`**
- Create Stripe payment intent
- Request: `{ "amount": 4900, "currency": "usd", "description": "Professional Plan" }`
- Response: `{ "client_secret": "pi_...", "payment_intent_id": "pi_..." }`

**POST `/api/payments/create-subscription`**
- Create Stripe subscription
- Request: `{ "price_id": "price_...", "payment_method": "pm_..." }`
- Response: subscription object

**POST `/api/payments/webhook`**
- Stripe webhook handler
- Request: Stripe webhook payload
- Response 200: `{ "received": true }`

**GET `/api/payments/analytics/marketplace`**
- Marketplace analytics
- Response: revenue, top sellers, etc.

**GET `/api/payments/analytics/security`**
- Security product analytics

**GET `/api/payments/analytics/compliance`**
- Compliance product analytics

**GET `/api/payments/analytics/dashboard`**
- Overall analytics dashboard

**GET `/api/payments/history`**
- Payment history for current user

**GET `/api/payments/subscriptions`**
- Active subscriptions

**GET `/api/payments/pricing`**
- Pricing tiers
- Response:
  ```json
  {
    "tiers": [
      {"id": "starter", "name": "Starter", "price_monthly": 49, "features": [...]},
      {"id": "professional", "name": "Professional", "price_monthly": 199, "features": [...]},
      {"id": "enterprise", "name": "Enterprise", "price_monthly": 999, "features": [...]}
    ]
  }
  ```

**GET `/api/payments/analytics/export`**
- Export analytics data (CSV)

**GET `/api/payments/revenue/forecast`**
- Revenue forecast

### Multi-Tenant Management

**POST `/api/tenants`**
- Create tenant
- Request: `{ "name": "Acme Corp", "plan": "professional" }`
- Response: tenant object

**GET `/api/tenants/{tenant_id}`**
- Get tenant details

**GET `/api/tenants/{tenant_id}/schema`**
- Get tenant schema

**POST `/api/tenants/{tenant_id}/migrate`**
- Migrate tenant schema

**GET `/api/tenants`**
- List all tenants (admin)

**PUT `/api/tenants/{tenant_id}`**
- Update tenant

### Activity Tracking

**POST `/api/activity/track`** (from activity_tracking router)
- Track user activity
- Request: `{ "action": "view_project", "resource_id": "uuid", "metadata": {...} }`
- Response 201: `{ "activity_id": "uuid" }`

**GET `/api/activity/recent`**
- Recent activity feed

**GET `/api/activity/user/{user_id}`**
- Activity for specific user

### WebSocket (Real-time)

**WS `/ws/projects/{project_id}`** (from websocket router)
- Real-time project updates
- Connect with `?token=<jwt>`
- Events: `schema_updated`, `comment_added`, `member_joined`, etc.

**GET `/api/ws/status/{project_id}`**
- WebSocket connection status for project

**GET `/api/ws/stats`**
- WebSocket service stats

---

## WEBSOCKET REALTIME SERVICE (`websocket-realtime/`)

Base path (via gateway): `/ws/*` → `websocket-realtime/`

Provides real-time updates, dashboard stats, and collaboration events via WebSocket connections.

### HTTP Endpoints

**GET `/health`**
- Service health
- Response: `{ "status": "healthy" }`

**GET `/`**
- Service info
- Response: `{ "service": "WebSocket Realtime", "version": "1.0.0" }`

**GET `/stats`**
- Real-time statistics
- Response:
  ```json
  {
    "active_connections": 42,
    "total_messages_sent": 15420,
    "uptime_seconds": 86400
  }
  ```

**GET `/connections`**
- List active WebSocket connections (admin)
- Response: array of connection objects

**POST `/webhooks/user-joined`**
- Webhook triggered when user joins (called by auth service)
- Request: `{ "user": "alice", "timestamp": "..." }`
- Response 200: broadcasts event to dashboard subscribers

### WebSocket Endpoints

**WS `/ws/dashboard`**
- Dashboard-wide real-time updates
- Auth: query param `?token=<jwt>` (optional for anonymous stats)
- Events sent to client:
  ```json
  {
    "type": "stats_update",
    "data": {
      "active_developers": 12,
      "active_migrations": 3,
      "projects_count": 156
    }
  }
  ```

**WS `/ws/{user_id}`**
- User-specific notifications
- Auth: query param `?token=<jwt>` (required, must match user_id)
- Events sent to client:
  ```json
  {
    "type": "notification",
    "title": "Migration completed",
    "message": "Your migration to AWS RDS completed successfully",
    "severity": "success",
    "timestamp": "2025-11-16T10:00:00Z"
  }
  ```

### Event Types

Dashboard events (`/ws/dashboard`):
- `stats_update`: Real-time stats (active users, migrations, etc.)
- `user_joined`: New user signed up
- `migration_started`: Migration initiated
- `migration_completed`: Migration finished

User events (`/ws/{user_id}`):
- `notification`: General notification
- `scan_completed`: Schema scan finished
- `job_update`: Long-running job progress
- `approval_requested`: Schema change needs approval
- `cost_anomaly`: Cost spike detected
- `compliance_alert`: Compliance issue found

### Frontend Integration

```typescript
// Dashboard connection
const ws = new WebSocket('wss://api.schemasage.com/ws/dashboard');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'stats_update') {
    updateDashboard(data.data);
  }
};

// User-specific connection
const token = localStorage.getItem('access_token');
const userWs = new WebSocket(`wss://api.schemasage.com/ws/${userId}?token=${token}`);
userWs.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  showNotification(notification);
};
```

---

## COST MONITORING & ANOMALY DETECTION

Planned for Phase 2 (from roadmap). Will be integrated into database-migration service.

**POST `/api/costs/anomaly/subscribe`** (planned)
- Subscribe to cost anomaly alerts
- Request: `{ "channel": "slack", "target": "#ops", "threshold_pct": 50 }`
- Response: `{ "subscription_id": "uuid" }`

**GET `/api/costs/anomaly/{job_id}`** (planned)
- Get detected anomalies
- Response: `{ "anomalies": [...] }`

---

## APPENDICES

### A. Common Error Codes

- `400` `validation_error`: Request validation failed (includes `details` with field errors)
- `401` `invalid_credentials`: Authentication failed or missing
- `401` `token_expired`: JWT token expired (use refresh token)
- `403` `forbidden`: Insufficient permissions (e.g., non-admin trying admin action)
- `404` `not_found`: Resource not found
- `409` `conflict`: Resource already exists or state conflict
- `422` `unprocessable_entity`: Semantic validation error
- `429` `rate_limited`: Too many requests (see `Retry-After` header)
- `500` `internal_server_error`: Server error
- `503` `service_unavailable`: Service temporarily unavailable (e.g., OpenAI API down)

### B. Example Workflows

#### Workflow 1: Schema Detection → PII Analysis → Compliance Fix

1. **Upload SQL file for detection**
   ```
   POST /api/detection/frontend/detect-from-file
   Content-Type: multipart/form-data
   ```

2. **Review detected schema**
   ```
   GET /api/detection/frontend/tables
   ```

3. **Run security audit**
   ```
   POST /api/security/audit
   Body: { "schema": {...} }
   → Response: { "audit_id": "uuid" }
   ```

4. **Get audit results**
   ```
   GET /api/security/audit/{audit_id}
   → Response: { "vulnerabilities": [...], "score": 73 }
   ```

5. **Generate compliance fix**
   ```
   POST /api/code/compliance/generate-compliant-schema
   Body: { "base_schema": {...}, "compliance_frameworks": ["gdpr"] }
   → Response: { "migrations": [...], "code_changes": {...} }
   ```

6. **Apply fix** (if user has admin role)
   ```
   POST /api/database/universal/execute-migration
   Body: { "plan_id": "...", "target_url": "..." }
   → Response: { "execution_id": "uuid", "status": "running" }
   ```

7. **Monitor via WebSocket**
   ```
   WS /ws/{user_id}
   → Event: { "type": "migration_completed", "execution_id": "uuid" }
   ```

#### Workflow 2: Cloud Cost Comparison → Migration

1. **Compare cloud costs**
   ```
   POST /api/database/multi-cloud/compare
   Body: { "workload": {...}, "providers": ["aws", "gcp", "azure"] }
   → Response: { "comparisons": [...], "recommendation": "gcp" }
   ```

2. **Assess migration readiness**
   ```
   POST /api/database/cloud/assess-readiness
   Body: { "current_database": {...}, "target_cloud": "gcp" }
   → Response: { "readiness_score": 85, "blockers": [] }
   ```

3. **Create migration plan**
   ```
   POST /api/database/cloud/create-migration-plan
   Body: { "source": {...}, "target_cloud": "gcp", "target_region": "us-central1" }
   → Response: { "plan_id": "uuid", "steps": [...], "estimated_cost": 450 }
   ```

4. **Execute migration**
   ```
   POST /api/database/universal/execute-migration
   Body: { "plan_id": "uuid" }
   → Response: { "execution_id": "uuid", "status": "running" }
   ```

5. **Monitor progress**
   ```
   GET /api/database/universal/migration-status/{execution_id}
   Poll every 5s until status = "completed"
   ```

#### Workflow 3: AI Schema Design → Code Generation → Deployment

1. **Design schema with AI**
   ```
   POST /api/chat/chat
   Body: { "message": "I need a schema for a blog with users, posts, comments", "session_id": "uuid" }
   → Response: { "message": "...", "artifacts": { "sql": "CREATE TABLE..." } }
   ```

2. **Generate full-stack code**
   ```
   POST /api/code/generate/generate-code
   Body: { "schema": {...}, "backend_framework": "fastapi", "frontend_framework": "react" }
   → Response: { "files": {...} }
   ```

3. **Create project**
   ```
   POST /api/project/projects
   Body: { "name": "Blog Platform", "description": "..." }
   → Response: { "id": "uuid", "name": "Blog Platform" }
   ```

4. **Deploy to cloud**
   ```
   POST /api/database/full-stack/deploy
   Body: { "schema": {...}, "code": {...}, "target_cloud": "aws" }
   → Response: { "deployment_id": "uuid", "status": "deploying" }
   ```

### C. TypeScript Type Definitions

Frontend developers should create TypeScript interfaces matching these schemas:

```typescript
// Authentication
interface LoginRequest {
  username: string;
  password: string;
}

interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserResponse;
}

interface UserResponse {
  id: number;
  username: string;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
}

// Schema Detection
interface DetectionJobRequest {
  job_type: "schema_detection" | "compliance_scan";
  data_source: DatabaseConnection;
  parameters?: Record<string, any>;
}

interface DatabaseConnection {
  type: "postgresql" | "mysql" | "sqlite";
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}

interface DetectionJobResponse {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress?: number;
  result?: SchemaResult;
}

interface SchemaResult {
  tables: Record<string, TableSchema>;
  relationships: Relationship[];
  detected_pii?: number;
}

interface TableSchema {
  columns: Record<string, ColumnSchema>;
  indexes?: IndexSchema[];
}

interface ColumnSchema {
  type: string;
  pii?: boolean;
  pii_confidence?: number; // 0-1
  nullable?: boolean;
}

// WebSocket Events
interface WebSocketEvent {
  type: "notification" | "stats_update" | "scan_completed" | "job_update";
  [key: string]: any;
}

interface Notification extends WebSocketEvent {
  type: "notification";
  title: string;
  message: string;
  severity: "info" | "success" | "warning" | "error";
  timestamp: string;
}

// ... (add more as needed)
```

### D. Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/login` | 5 requests | 1 minute (per IP) |
| `/api/auth/signup` | 3 requests | 5 minutes (per IP) |
| `/api/chat/chat` | 20 requests | 1 minute (per IP) |
| Most GET endpoints | 100 requests | 1 minute (per user) |
| Most POST endpoints | 30 requests | 1 minute (per user) |
| Admin endpoints | 60 requests | 1 minute (per user) |

Rate limit headers included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### E. Environment Variables (Backend Setup)

For backend developers deploying services:

```bash
# Authentication Service
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://...
WEBSOCKET_SERVICE_URL=https://...
AI_CHAT_SERVICE_URL=https://...

# AI Chat Service
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...

# Schema Detection Service
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...

# Database Migration Service (Enterprise)
DATABASE_URL=postgresql://...
ENCRYPTION_KEY=base64-encoded-key
JWT_SECRET_KEY=...

# Project Management Service
DATABASE_URL=postgresql://...
USE_S3=true/false
S3_BUCKET_NAME=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### F. Deployment Architecture

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │  (api-gateway)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼─────┐      ┌───────▼──────┐    ┌───────▼──────┐
  │   Auth    │      │   Schema     │    │      AI      │
  │  Service  │      │  Detection   │    │     Chat     │
  └───────────┘      └──────────────┘    └──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼─────┐      ┌───────▼──────┐    ┌───────▼──────┐
  │   Code    │      │  Database    │    │   Project    │
  │Generation │      │  Migration   │    │  Management  │
  └───────────┘      └──────────────┘    └──────────────┘
                             │
                     ┌───────▼──────┐
                     │  WebSocket   │
                     │   Realtime   │
                     └──────────────┘
                             │
                    ┌────────▼────────┐
                    │   PostgreSQL    │
                    │    (Shared)     │
                    └─────────────────┘
```

---

## NEXT STEPS FOR FRONTEND DEVELOPMENT

1. **Generate TypeScript Client**
   - Use this spec to generate typed API client
   - Consider using `openapi-typescript-codegen` or similar

2. **Implement Authentication Flow**
   - Login/signup pages
   - JWT token storage (localStorage/sessionStorage)
   - Token refresh logic
   - Protected routes

3. **Set Up WebSocket Connections**
   - Dashboard stats connection
   - User-specific notifications
   - Reconnection logic

4. **Build Core Features**
   - Schema upload/detection UI
   - PII/security audit visualization
   - Cost comparison dashboard
   - Migration planning wizard
   - AI chat interface

5. **Implement Polling for Long-Running Jobs**
   - Detection jobs
   - Migration executions
   - Security audits
   - Fall back to polling if WebSocket unavailable

6. **Add Error Handling**
   - Display user-friendly error messages
   - Handle rate limiting (show retry time)
   - Network error retry logic

7. **Optimize Performance**
   - Cache frequently accessed data
   - Lazy load heavy components
   - Implement pagination for large lists

---

**END OF API SPECIFICATION**

For questions or additions, refer to the IMPLEMENTATION_ROADMAP.md for planned features and timelines.
