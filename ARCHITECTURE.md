# SchemaSage Architecture

## System Overview

SchemaSage is a microservices-based platform for database schema detection, migration, and code generation with real-time collaboration features.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                  │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   React UI   │  │   Mobile     │  │   CLI Tool   │                  │
│  │   (Web App)  │  │   Clients    │  │              │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                  │                  │                          │
│         └──────────────────┼──────────────────┘                          │
│                            │                                             │
└────────────────────────────┼─────────────────────────────────────────────┘
                             │
                             │ HTTPS / WebSocket
                             │
┌────────────────────────────▼─────────────────────────────────────────────┐
│                        API GATEWAY (Port 8000)                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  • JWT Authentication Middleware                                   │ │
│  │  • Request Routing & Load Balancing                                │ │
│  │  • Rate Limiting & CORS                                            │ │
│  │  • Authorization Header Forwarding                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐  ┌───────▼────────┐  ┌──────▼─────────┐
│  Authentication │  │   WebSocket    │  │  Project Mgmt  │
│  Service        │  │   Real-time    │  │  Service       │
│  (Port 8001)    │  │   (Port 8006)  │  │  (Port 8005)   │
└────────┬────────┘  └───────┬────────┘  └──────┬─────────┘
         │                   │                   │
         │           ┌───────┼───────┐           │
         │           │       │       │           │
┌────────▼────────┐  │  ┌────▼────┐  │  ┌───────▼────────┐
│  Schema         │  │  │ AI Chat │  │  │  Code          │
│  Detection      │  │  │ Service │  │  │  Generation    │
│  (Port 8002)    │  │  │ (8003)  │  │  │  (Port 8004)   │
└────────┬────────┘  │  └────┬────┘  │  └───────┬────────┘
         │           │       │       │          │
         └───────────┼───────┴───────┼──────────┘
                     │               │
                ┌────▼────┐     ┌────▼────────┐
                │ Database│     │  Message    │
                │ Migration│     │  Queue      │
                │ (8007)  │     │  (RabbitMQ) │
                └────┬────┘     └─────────────┘
                     │
┌────────────────────┼─────────────────────────────────────────────────────┐
│                    │         DATA LAYER                                  │
│                    │                                                     │
│  ┌─────────────────▼──────────────┐   ┌──────────────────────────────┐ │
│  │    Supabase PostgreSQL         │   │       Redis Cache            │ │
│  │                                 │   │                              │ │
│  │  • users                        │   │  • Session Storage           │ │
│  │  • projects                     │   │  • Real-time Data Cache      │ │
│  │  • chat_sessions                │   │  • Celery Task Queue         │ │
│  │  • chat_messages                │   └──────────────────────────────┘ │
│  │  • detected_schemas             │                                    │
│  │  • project_activities           │                                    │
│  │  • generated_files              │                                    │
│  │  • api_endpoints                │                                    │
│  │  • integration_connections      │                                    │
│  └─────────────────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Service Architecture Details

### 1. **API Gateway** (Port 8000)
**Technology**: FastAPI  
**Responsibilities**:
- Central entry point for all client requests
- JWT token verification and validation
- Routes requests to appropriate microservices
- Handles CORS and rate limiting
- Forwards `Authorization` headers to downstream services

**Key Files**:
- `services/api-gateway/main.py`
- `services/api-gateway/middleware/auth.py`

---

### 2. **Authentication Service** (Port 8001)
**Technology**: FastAPI + JWT (HS256)  
**Responsibilities**:
- User registration and login
- JWT token generation and validation
- Password hashing (bcrypt)
- OAuth integration (GitHub, Google)
- User profile management
- Webhook notifications for user events

**Key Files**:
- `services/authentication/main.py`
- `services/authentication/core/security.py`
- `services/authentication/models/user.py`

**JWT Payload Structure**:
```json
{
  "sub": "username",
  "user_id": "uuid",
  "is_admin": false,
  "exp": 1234567890
}
```

---

### 3. **Project Management Service** (Port 8005)
**Technology**: FastAPI + SQLAlchemy  
**Responsibilities**:
- Project CRUD operations
- Activity tracking (schema generation, API creation, etc.)
- Dashboard statistics
- File upload management
- Real-time activity broadcasting via WebSocket

**Key Files**:
- `services/project-management/main.py`
- `services/project-management/routers/projects.py`
- `services/project-management/routers/activity_tracking.py`
- `services/project-management/routers/dashboard.py`

**Database Tables**:
- `projects`
- `project_activities`
- `uploads`

---

### 4. **WebSocket Real-time Service** (Port 8006)
**Technology**: FastAPI WebSockets  
**Responsibilities**:
- Real-time WebSocket connections per user
- Broadcasting activity updates to connected clients
- Dashboard statistics collection and distribution
- Connection management with user isolation

**Key Files**:
- `services/websocket-realtime/main.py`
- `services/websocket-realtime/core/connection_manager.py`
- `services/websocket-realtime/services/stats_collector.py`
- `services/websocket-realtime/routes/websocket_routes.py`

**Connection Model**:
```python
active_connections: Dict[user_id, Set[WebSocket]]
```

---

### 5. **AI Chat Service** (Port 8003)
**Technology**: FastAPI + OpenAI API  
**Responsibilities**:
- AI-powered chat for schema assistance
- Context-aware responses
- Chat session management
- Message history storage
- Integration with project context

**Key Files**:
- `services/ai-chat/main.py`
- `services/ai-chat/core/openai_service.py`
- `services/ai-chat/models/chat.py`

**Database Tables**:
- `chat_sessions`
- `chat_messages`

---

### 6. **Schema Detection Service** (Port 8002)
**Technology**: FastAPI + Celery + Redis  
**Responsibilities**:
- Automated database schema detection
- Support for multiple database types (PostgreSQL, MySQL, MongoDB)
- Asynchronous schema analysis via Celery
- Schema visualization and export
- Connection string validation

**Key Files**:
- `services/schema-detection/main.py`
- `services/schema-detection/core/detector.py`
- `services/schema-detection/routers/detection.py`
- `services/schema-detection/celery_app.py`

**Database Tables**:
- `detected_schemas`

---

### 7. **Code Generation Service** (Port 8004)
**Technology**: FastAPI + Jinja2 Templates  
**Responsibilities**:
- REST API scaffolding generation
- ORM model generation (SQLAlchemy, Prisma, TypeORM)
- CRUD endpoint generation
- Documentation generation (OpenAPI/Swagger)
- Template-based code generation

**Key Files**:
- `services/code-generation/main.py`
- `services/code-generation/routers/generation.py`
- `services/code-generation/templates/`

**Database Tables**:
- `generated_files`
- `api_endpoints`

---

### 8. **Database Migration Service** (Port 8007)
**Technology**: FastAPI + Alembic + Celery  
**Responsibilities**:
- Database migration job management
- Alembic migration generation
- Schema comparison and diff
- Migration execution and rollback
- Asynchronous long-running migrations

**Key Files**:
- `services/database-migration/main.py`
- `services/database-migration/tasks.py`
- `services/database-migration/alembic/`

**Database Tables**:
- `migration_jobs`
- `migration_history`

---

## Data Flow Diagrams

### User Authentication Flow
```
┌─────────┐                ┌─────────┐                ┌──────────────┐
│ Client  │                │   API   │                │     Auth     │
│         │                │ Gateway │                │   Service    │
└────┬────┘                └────┬────┘                └──────┬───────┘
     │                          │                            │
     │  POST /api/auth/login    │                            │
     ├─────────────────────────>│                            │
     │                          │   Forward Request          │
     │                          ├───────────────────────────>│
     │                          │                            │
     │                          │                     ┌──────▼──────┐
     │                          │                     │ Verify      │
     │                          │                     │ Credentials │
     │                          │                     └──────┬──────┘
     │                          │                            │
     │                          │                     ┌──────▼──────┐
     │                          │                     │ Generate    │
     │                          │                     │ JWT Token   │
     │                          │                     └──────┬──────┘
     │                          │       JWT Token            │
     │                          │<───────────────────────────┤
     │       JWT Token          │                            │
     │<─────────────────────────┤                            │
     │                          │                            │
```

### Schema Detection Flow
```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌────────┐     ┌──────────┐
│ Client  │     │   API   │     │ Schema   │     │ Celery │     │ Database │
│         │     │ Gateway │     │ Detection│     │ Worker │     │          │
└────┬────┘     └────┬────┘     └────┬─────┘     └───┬────┘     └────┬─────┘
     │               │               │                │               │
     │ POST /detect  │               │                │               │
     ├──────────────>│               │                │               │
     │               │ Forward       │                │               │
     │               ├──────────────>│                │               │
     │               │               │ Queue Task     │               │
     │               │               ├───────────────>│               │
     │               │  Task ID      │                │               │
     │               │<──────────────┤                │               │
     │    Task ID    │               │                │               │
     │<──────────────┤               │                │               │
     │               │               │                │ Connect       │
     │               │               │                ├──────────────>│
     │               │               │                │ Read Schema   │
     │               │               │                │<──────────────┤
     │               │               │ Save Result    │               │
     │               │               │<───────────────┤               │
     │               │               │                │               │
     │ GET /status   │               │                │               │
     ├──────────────>│               │                │               │
     │               ├──────────────>│                │               │
     │               │   Result      │                │               │
     │               │<──────────────┤                │               │
     │    Result     │               │                │               │
     │<──────────────┤               │                │               │
```

### Real-time Activity Broadcasting
```
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌───────────┐
│ Client  │     │ WebSocket│     │ Project │     │  Connected│
│         │     │ Service  │     │   Mgmt  │     │   Clients │
└────┬────┘     └────┬─────┘     └────┬────┘     └─────┬─────┘
     │               │                │                 │
     │ WS Connect    │                │                 │
     ├──────────────>│                │                 │
     │               │ Store Connection                 │
     │               │ (user_id -> ws)                  │
     │               │                │                 │
     │ Create Project│                │                 │
     ├──────────────────────────────> │                 │
     │               │                │ Save to DB      │
     │               │                │                 │
     │               │ Broadcast Activity               │
     │               │<───────────────┤                 │
     │               │                │                 │
     │               │ Send to user's sockets           │
     │               ├─────────────────────────────────>│
     │               │                │                 │
     │ Activity Event│                │                 │
     │<──────────────┤                │                 │
```

## Security Architecture

### User-Level Isolation Model
```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY BOUNDARIES                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   User A     │  │   User B     │  │   User C     │         │
│  │   user_id: 1 │  │   user_id: 2 │  │   user_id: 3 │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                 │
│         │  JWT Token       │  JWT Token       │  JWT Token      │
│         │  {user_id: 1}    │  {user_id: 2}    │  {user_id: 3}  │
│         │                  │                  │                 │
│  ┌──────▼──────────────────▼──────────────────▼────────┐       │
│  │              API Gateway + Auth Middleware           │       │
│  │  • Verifies JWT                                      │       │
│  │  • Extracts user_id                                  │       │
│  │  • Forwards to services                              │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │            All Microservices                         │       │
│  │  • Decode JWT → get user_id                          │       │
│  │  • All DB queries: WHERE user_id = current_user      │       │
│  │  • WebSocket: connections[user_id]                   │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Supabase PostgreSQL                     │       │
│  │  • All tables have user_id column                    │       │
│  │  • Composite unique keys (user_id, resource_id)      │       │
│  │  • Optional: Row Level Security policies             │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Security Features Implemented

1. **JWT Authentication** (✅ Implemented)
   - HS256 algorithm
   - User ID embedded in token payload
   - Verified at API Gateway
   - Token expiration handling

2. **Service-to-Service Auth** (✅ Implemented)
   - Internal HTTP calls include `Authorization` header
   - Uses `INTERNAL_SERVICE_TOKEN` or `JWT_SECRET_KEY`
   - Prevents unauthorized internal access

3. **User Data Isolation** (✅ Implemented)
   - All database writes include authenticated `user_id`
   - Endpoint parameters validate against JWT user
   - Cannot spoof user_id via request body

4. **WebSocket Security** (✅ Implemented)
   - Per-user connection mapping
   - Messages only sent to user's own sockets
   - JWT required for WebSocket connection

5. **Database Security** (⚠️ Optional)
   - Row Level Security (RLS) policies available
   - Requires setting `app.current_user_id` context
   - Type casting needed for UUID columns

## Technology Stack

### Backend Services
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (PyJWT)
- **Password Hashing**: Passlib (bcrypt)
- **Async HTTP**: httpx
- **WebSockets**: FastAPI native WebSocket support

### Task Queue & Caching
- **Message Queue**: RabbitMQ (aio_pika)
- **Task Worker**: Celery
- **Cache**: Redis
- **Background Jobs**: Celery + Redis

### Database
- **Primary DB**: Supabase (PostgreSQL)
- **Schema**: User-scoped with UUID keys
- **Migrations**: Alembic

### AI/ML
- **AI Provider**: OpenAI API (GPT-4)
- **Use Cases**: Schema recommendations, code generation assistance

### Deployment
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Docker Compose (dev), Kubernetes (production)
- **Reverse Proxy**: Nginx (production)
- **Cloud Platforms**: Heroku, Railway, AWS, Azure

## Database Schema

### Core Tables

#### `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `projects`
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);
```

#### `chat_sessions`
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `chat_messages`
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `project_activities`
```sql
CREATE TABLE project_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    activity_type VARCHAR(50) NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `detected_schemas`
```sql
CREATE TABLE detected_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    database_type VARCHAR(50) NOT NULL,
    schema_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `generated_files`
```sql
CREATE TABLE generated_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Deployment Architecture

### Development Environment
```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Setup                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ api-gateway  │  │ authentication│  │ project-mgmt │         │
│  │ :8000        │  │ :8001        │  │ :8005        │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ websocket    │  │ ai-chat      │  │ schema-detect│         │
│  │ :8006        │  │ :8003        │  │ :8002        │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ code-gen     │  │ db-migration │  │ rabbitmq     │         │
│  │ :8004        │  │ :8007        │  │ :5672        │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐                                              │
│  │ redis        │                                              │
│  │ :6379        │                                              │
│  └──────────────┘                                              │
│                                                                 │
│  External: Supabase PostgreSQL (Cloud)                         │
└─────────────────────────────────────────────────────────────────┘
```

### Production Environment
```
                          ┌──────────────┐
                          │  Load        │
                          │  Balancer    │
                          │  (Nginx)     │
                          └──────┬───────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
    ┌────▼────┐            ┌─────▼────┐           ┌─────▼────┐
    │ Gateway │            │ Gateway  │           │ Gateway  │
    │ Pod 1   │            │ Pod 2    │           │ Pod 3    │
    └────┬────┘            └─────┬────┘           └─────┬────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
            ┌───────▼───┐  ┌─────▼────┐  ┌───▼──────┐
            │  Service  │  │ Service  │  │ Service  │
            │  Pods     │  │ Pods     │  │ Pods     │
            │(Replicas) │  │(Replicas)│  │(Replicas)│
            └───────────┘  └──────────┘  └──────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
            ┌───────▼───┐  ┌─────▼────┐  ┌───▼──────┐
            │ PostgreSQL│  │ Redis    │  │ RabbitMQ │
            │ (Managed) │  │ (Managed)│  │ (Managed)│
            └───────────┘  └──────────┘  └──────────┘
```

## API Endpoints Summary

### Authentication Service (8001)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user profile
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/oauth/{provider}` - OAuth login

### Project Management (8005)
- `GET /api/projects` - List user projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/activity/track` - Track activity
- `GET /api/activity/stats` - Get activity statistics
- `GET /api/dashboard/stats` - Dashboard statistics

### WebSocket Service (8006)
- `WS /ws/connect` - WebSocket connection
- `POST /api/dashboard/broadcast-stats` - Broadcast dashboard updates

### AI Chat Service (8003)
- `POST /api/chat/sessions` - Create chat session
- `GET /api/chat/sessions` - List chat sessions
- `POST /api/chat/message` - Send chat message
- `GET /api/chat/sessions/{id}/messages` - Get chat history

### Schema Detection (8002)
- `POST /api/schema/detect` - Start schema detection
- `GET /api/schema/status/{job_id}` - Check detection status
- `GET /api/schema/{id}` - Get detected schema
- `POST /api/schema/validate-connection` - Validate DB connection

### Code Generation (8004)
- `POST /api/generate/api` - Generate REST API code
- `POST /api/generate/models` - Generate ORM models
- `GET /api/generate/templates` - List available templates
- `GET /api/files/{id}` - Download generated file

### Database Migration (8007)
- `POST /api/migrations/jobs` - Create migration job
- `GET /api/migrations/jobs/{id}` - Get job status
- `POST /api/migrations/execute` - Execute migration
- `POST /api/migrations/rollback` - Rollback migration

## Environment Variables

```bash
# Common across all services
JWT_SECRET_KEY=your-secret-key-here
INTERNAL_SERVICE_TOKEN=your-service-token-here
DATABASE_URL=postgresql://user:pass@host:5432/db

# Service-specific
OPENAI_API_KEY=sk-...                    # AI Chat Service
REDIS_URL=redis://localhost:6379         # Schema Detection, DB Migration
RABBITMQ_URL=amqp://guest:guest@localhost:5672  # Message Queue

# WebSocket Service
WEBSOCKET_SERVICE_URL=http://localhost:8006

# Project Management
PROJECT_MANAGEMENT_URL=http://localhost:8005
```

## Performance Considerations

1. **Horizontal Scaling**: All services are stateless (except WebSocket connections)
2. **Caching**: Redis used for frequently accessed data
3. **Async Processing**: Celery handles long-running tasks (schema detection, migrations)
4. **Connection Pooling**: SQLAlchemy connection pools per service
5. **Load Balancing**: API Gateway can be replicated behind Nginx/HAProxy

## Monitoring & Observability

- **Logging**: Structured JSON logs per service
- **Metrics**: Prometheus-compatible metrics endpoints
- **Tracing**: OpenTelemetry integration ready
- **Health Checks**: `/health` endpoint on each service

---

**Last Updated**: December 19, 2025  
**Version**: 1.0.0
