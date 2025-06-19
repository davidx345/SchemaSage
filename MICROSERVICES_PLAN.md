# SchemaSage Microservices Architecture Plan

## 📋 Current State Analysis
- **Phase**: 1.5 (Advanced MVP → Phase 2 Transition)
- **Architecture**: Monolithic FastAPI + Next.js
- **Files**: ~120 source files
- **Features**: Schema detection, Code generation, AI chat, Project management, Visualization

## 🏗️ Microservices Breakdown

### 1. 🔍 Schema Detection Service
**Purpose**: Core schema inference and validation
**Port**: 8001
**Tech Stack**: FastAPI, pandas, numpy
**Responsibilities**:
- File parsing (CSV, JSON, Excel)
- Schema inference and type detection
- Data profiling and statistics
- Validation rules

**Files to Extract**:
```
backend/app/core/schema_detector.py
backend/app/services/file_processor.py
backend/app/models/schemas.py (schema-related models)
```

### 2. 🏗️ Code Generation Service  
**Purpose**: Generate code from schemas
**Port**: 8002
**Tech Stack**: FastAPI, Jinja2
**Responsibilities**:
- Template-based code generation
- Multiple output formats (SQL, Python, TypeScript)
- Code validation and formatting

**Files to Extract**:
```
backend/app/services/code_generator.py
backend/app/templates/ (all templates)
```

### 3. 💬 AI Chat Service
**Purpose**: AI-powered assistance and suggestions
**Port**: 8003
**Tech Stack**: FastAPI, Google Gemini API
**Responsibilities**:
- Chat interactions
- Schema suggestions
- Code improvement recommendations

**Files to Extract**:
```
backend/app/services/gemini_service.py
backend/app/api/routes/chat.py
```

### 4. 📊 Project Management Service
**Purpose**: Project and schema persistence
**Port**: 8004
**Tech Stack**: FastAPI, SQLAlchemy, PostgreSQL
**Responsibilities**:
- Project CRUD operations
- Schema storage and versioning
- User data management

**Files to Extract**:
```
backend/app/api/routes/database.py
backend/app/models/orm_models.py
backend/app/core/db/
```

### 5. 👥 Authentication Service
**Purpose**: User authentication and authorization
**Port**: 8005
**Tech Stack**: FastAPI, JWT, bcrypt
**Responsibilities**:
- User registration/login
- JWT token management
- Role-based access control

**Files to Extract**:
```
backend/app/api/routes/auth.py
backend/app/models/user.py
```

### 6. 📈 Analytics Service
**Purpose**: Dashboard and analytics
**Port**: 8006
**Tech Stack**: FastAPI, PostgreSQL
**Responsibilities**:
- Usage analytics
- Performance metrics
- Dashboard data aggregation

**Files to Extract**:
```
backend/app/api/routes/dashboard.py
backend/app/visualization/
```

### 7. 🌐 API Gateway
**Purpose**: Request routing and cross-cutting concerns
**Port**: 8000
**Tech Stack**: Kong/Traefik or FastAPI
**Responsibilities**:
- Request routing
- Authentication middleware
- Rate limiting
- CORS handling

## 🔄 Communication Patterns

### Synchronous (HTTP)
- Frontend ↔ API Gateway
- API Gateway ↔ Services
- Service ↔ Service (when immediate response needed)

### Asynchronous (Event-Driven)
- Schema Detection → Code Generation
- Project Updates → Analytics
- AI Suggestions → Frontend Notifications

### Shared Resources
- **Database**: Each service has its own database schema
- **File Storage**: Shared S3/MinIO for uploaded files
- **Cache**: Redis for session/temporary data

## 📁 Directory Structure

```
SchemaSage/
├── docker-compose.yml
├── kubernetes/
├── services/
│   ├── api-gateway/
│   ├── schema-detection/
│   ├── code-generation/
│   ├── ai-chat/
│   ├── project-management/
│   ├── authentication/
│   └── analytics/
├── frontend/
├── shared/
│   ├── models/
│   ├── utils/
│   └── types/
└── infrastructure/
    ├── database/
    ├── monitoring/
    └── deployment/
```

## 🚀 Migration Strategy

### Phase 1: Preparation (Week 1-2)
1. **Extract Common Models**: Move shared types to `shared/` directory
2. **Database Schema Split**: Design separate schemas for each service
3. **API Contract Definition**: Define OpenAPI specs for each service
4. **Docker Setup**: Create Dockerfiles for each service

### Phase 2: Service Extraction (Week 3-6)
1. **Start with Schema Detection Service** (least dependencies)
2. **Code Generation Service** (depends on Schema Detection)
3. **AI Chat Service** (standalone)
4. **Project Management Service** (core data service)
5. **Authentication Service**
6. **Analytics Service**

### Phase 3: Integration (Week 7-8)
1. **API Gateway Setup**
2. **Service Communication**
3. **Event Bus Implementation**
4. **Frontend API Updates**

### Phase 4: Production Ready (Week 9-10)
1. **Monitoring & Logging**
2. **Health Checks**
3. **CI/CD Pipeline**
4. **Load Testing**

## 🛠️ Implementation Steps

### Step 1: Shared Components
```bash
mkdir -p shared/{models,utils,types,config}
# Move common types and utilities
```

### Step 2: Service Template
Each service follows this structure:
```
service-name/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── services/
│   └── api/
└── tests/
```

### Step 3: Database per Service
- **schema-detection**: File metadata, processing results
- **code-generation**: Templates, generation history
- **project-management**: Projects, schemas, relationships
- **authentication**: Users, sessions, permissions
- **analytics**: Metrics, usage data

## 📊 Benefits of Microservices for SchemaSage

### ✅ Advantages
- **Scalability**: Scale AI service separately from file processing
- **Technology Diversity**: Use best tools for each domain
- **Team Independence**: Different teams can own different services
- **Fault Isolation**: One service failure doesn't bring down everything
- **Deployment Flexibility**: Deploy services independently

### ⚠️ Challenges to Address
- **Network Latency**: Service-to-service communication overhead
- **Data Consistency**: Distributed transaction management
- **Debugging Complexity**: Tracing requests across services
- **Infrastructure Overhead**: More containers, databases, monitoring

## 🏃‍♂️ Quick Start Commands

### Development Environment
```bash
# Start all services
docker-compose up -d

# Start individual service
docker-compose up schema-detection

# View logs
docker-compose logs -f ai-chat
```

### Production Deployment
```bash
# Kubernetes
kubectl apply -f kubernetes/

# Docker Swarm
docker stack deploy -c docker-compose.prod.yml schemasage
```

## 📈 Next Steps

1. **Immediate (This Week)**:
   - Set up shared models directory
   - Create service templates
   - Design API contracts

2. **Short Term (Next Month)**:
   - Extract Schema Detection service
   - Implement API Gateway
   - Set up service discovery

3. **Medium Term (2-3 Months)**:
   - Complete all service extraction
   - Implement event-driven communication
   - Add comprehensive monitoring

4. **Long Term (3-6 Months)**:
   - Kubernetes deployment
   - Auto-scaling policies
   - Advanced observability
