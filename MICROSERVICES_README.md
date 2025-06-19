# SchemaSage Microservices Architecture

## 🏗️ Architecture Overview

Your SchemaSage project has been successfully broken down into the following microservices:

```
┌─────────────────┐    ┌──────────────────┐
│   Frontend      │    │   API Gateway    │
│   (Next.js)     │◄──►│   Port: 8000     │
│   Port: 3000    │    └──────────────────┘
└─────────────────┘             │
                                 ▼
        ┌────────────────────────────────────────┐
        │            Microservices               │
        │                                        │
        │  ┌─────────────────┐ ┌─────────────────┐│
        │  │ Schema Detection│ │ Code Generation ││
        │  │   Port: 8001    │ │   Port: 8002    ││
        │  └─────────────────┘ └─────────────────┘│
        │                                        │
        │  ┌─────────────────┐ ┌─────────────────┐│
        │  │   AI Chat       │ │ Project Mgmt    ││
        │  │   Port: 8003    │ │   Port: 8004    ││
        │  └─────────────────┘ └─────────────────┘│
        └────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────┐
                    │   PostgreSQL DB     │
                    │   Port: 5432        │
                    └─────────────────────┘
```

## 📦 Services

### 1. API Gateway (Port 8000)
- **Purpose**: Request routing and load balancing
- **Routes requests to**: All other microservices
- **Technology**: FastAPI with HTTP proxy

### 2. Schema Detection Service (Port 8001)
- **Purpose**: File processing and schema inference
- **Endpoints**: 
  - `POST /detect` - Detect schema from raw data
  - `POST /detect-file` - Detect schema from uploaded file
- **Technology**: FastAPI + pandas + your existing schema detection logic

### 3. Code Generation Service (Port 8002)
- **Purpose**: Generate code from detected schemas
- **Endpoints**:
  - `POST /generate` - Generate code from schema
  - `GET /formats` - Get supported output formats
- **Technology**: FastAPI + Jinja2 templates + your existing code generator

### 4. AI Chat Service (Port 8003)
- **Purpose**: AI-powered chat assistance
- **Endpoints**:
  - `POST /chat` - Chat with AI about schemas
- **Technology**: FastAPI + Google Gemini API

### 5. Project Management Service (Port 8004)
- **Purpose**: Project and schema storage/retrieval
- **Endpoints**:
  - `GET/POST /projects` - List/create projects
  - `GET/PUT/DELETE /projects/{id}` - Manage individual projects
- **Technology**: FastAPI + PostgreSQL + SQLAlchemy

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Start all services**:
   ```powershell
   # Windows PowerShell
   .\microservices.ps1 build
   .\microservices.ps1 start
   
   # Or use Docker Compose directly
   docker-compose up --build -d
   ```

2. **Check service health**:
   ```powershell
   .\microservices.ps1 health
   ```

3. **View logs**:
   ```powershell
   .\microservices.ps1 logs
   ```

### Option 2: Development Mode

1. **Start only the database**:
   ```powershell
   .\microservices.ps1 dev
   ```

2. **Run services individually** (in separate terminals):
   ```powershell
   # Terminal 1 - Schema Detection
   cd services/schema-detection
   pip install -r requirements.txt
   python main.py
   
   # Terminal 2 - Code Generation
   cd services/code-generation
   pip install -r requirements.txt
   python main.py
   
   # Terminal 3 - AI Chat
   cd services/ai-chat
   pip install -r requirements.txt
   python main.py
   
   # Terminal 4 - Project Management
   cd services/project-management
   pip install -r requirements.txt
   python main.py
   
   # Terminal 5 - API Gateway
   cd services/api-gateway
   pip install -r requirements.txt
   python main.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://schemasage:schemasage123@localhost:5432/schemasage

# AI Service
GEMINI_API_KEY=your_gemini_api_key_here
USE_GEMINI=true

# Service URLs (for development)
SCHEMA_DETECTION_URL=http://localhost:8001
CODE_GENERATION_URL=http://localhost:8002
AI_CHAT_URL=http://localhost:8003
PROJECT_MANAGEMENT_URL=http://localhost:8004
```

## 🔍 Testing the Services

### 1. Test API Gateway Health
```bash
curl http://localhost:8000/health
```

### 2. Test Schema Detection
```bash
curl -X POST http://localhost:8000/api/schema/detect \
  -H "Content-Type: application/json" \
  -d '{"data": "name,age\nJohn,25\nJane,30"}'
```

### 3. Test Code Generation
```bash
curl -X POST http://localhost:8000/api/schema/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "schema_data": {...},
    "format": "sqlalchemy",
    "options": {}
  }'
```

### 4. Test AI Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Help me with my schema"}]
  }'
```

### 5. Test Project Management
```bash
curl -X GET http://localhost:8000/api/database/projects
```

## 📊 Service Monitoring

### Health Checks
Each service provides a `/health` endpoint:
- http://localhost:8001/health (Schema Detection)
- http://localhost:8002/health (Code Generation)
- http://localhost:8003/health (AI Chat)
- http://localhost:8004/health (Project Management)
- http://localhost:8000/health (API Gateway - aggregates all)

### Logs
```powershell
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f schema-detection
docker-compose logs -f api-gateway
```

## 🔄 Migration from Monolith

Your original backend is preserved and the microservices extract the same functionality:

| Original Route | New Route | Service |
|---------------|-----------|---------|
| `/api/schema/detect` | `/api/schema/detect` | Schema Detection |
| `/api/schema/generate-code` | `/api/schema/generate-code` | Code Generation |
| `/api/chat` | `/api/chat` | AI Chat |
| `/api/database/projects` | `/api/database/projects` | Project Management |

**The API remains the same for your frontend!** The API Gateway handles routing transparently.

## 🛠️ Development Workflow

1. **Make changes to a service**
2. **Rebuild specific service**:
   ```bash
   docker-compose build schema-detection
   docker-compose up -d schema-detection
   ```
3. **Test the service**:
   ```bash
   curl http://localhost:8001/health
   ```

## 🔧 Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   docker-compose logs service-name
   ```

2. **Port conflicts**:
   - Check `docker-compose.yml` for port mappings
   - Make sure ports 8000-8004 are available

3. **Import errors in services**:
   - Services mount the original `backend/` directory
   - Make sure your backend dependencies are properly structured

4. **Database connection issues**:
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in environment variables

### Clean Restart
```powershell
.\microservices.ps1 cleanup
.\microservices.ps1 build
.\microservices.ps1 start
```

## 📈 Next Steps

1. **Test all functionality** - Ensure each service works correctly
2. **Update frontend API calls** - Point to API Gateway (http://localhost:8000)
3. **Add monitoring** - Implement logging and metrics
4. **Security** - Add authentication/authorization
5. **CI/CD** - Set up automated deployment pipeline

## 🎯 Benefits Achieved

✅ **Scalability**: Each service can be scaled independently
✅ **Maintainability**: Smaller, focused codebases
✅ **Technology Flexibility**: Each service can use different tech stacks
✅ **Team Independence**: Different teams can own different services
✅ **Fault Isolation**: One service failure doesn't affect others
✅ **Deployment Flexibility**: Deploy services independently
