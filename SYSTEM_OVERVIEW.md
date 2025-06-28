# SchemaSage System Overview

## 🏗️ Architecture Overview

SchemaSage is a modular, production-ready microservices platform for schema detection, code generation, AI chat, and project management, with a modern Next.js frontend. The system is designed for scalability, independent deployment, and ease of development.

### Components
- **Frontend**: Next.js app (now in a separate repo/folder)
- **API Gateway**: FastAPI-based proxy and router
- **Schema Detection Service**: AI-powered schema inference
- **Code Generation Service**: Generates code from schemas
- **AI Chat Service**: AI-powered chat for schema and code help
- **Project Management Service**: CRUD for projects and schemas
- **Authentication Service**: User registration, login, JWT
- **PostgreSQL Database**: Shared by backend services

---

## 🚀 Features

- Modern, animated landing page and UI (Next.js, Tailwind, Framer Motion)
- API Gateway for unified backend access
- Schema detection from files or raw data
- Code generation in multiple formats (SQLAlchemy, SQL DDL, JSON Schema, Python dataclasses)
- AI chat with OpenAI and Gemini support
- Project CRUD, schema storage, glossary, integrations
- User authentication (JWT)
- Health checks for all services
- Dockerized for easy deployment
- Hot reloading for development
- Structured logging and error handling
- Environment-based configuration
- Integration marketplace (webhooks, notifications, cloud storage, BI tools, data catalogs, custom APIs)

---

## 🧪 How to Test & Run Everything

### 1. Backend (Microservices)

#### Docker Compose (Recommended)
```powershell
# From backend repo root
.\microservices.ps1 build
.\microservices.ps1 start
```
- Or use: `docker-compose up --build -d`

#### Development Mode
```powershell
.\microservices.ps1 dev
# Then run each service in its folder:
cd services/schema-detection; python main.py
cd services/code-generation; python main.py
cd services/ai-chat; python main.py
cd services/project-management; python main.py
cd services/api-gateway; python main.py
```

#### Health Checks
- API Gateway: http://localhost:8000/health
- Schema Detection: http://localhost:8001/health
- Code Generation: http://localhost:8002/health
- AI Chat: http://localhost:8003/health
- Project Management: http://localhost:8004/health

#### Logs
```powershell
docker-compose logs -f
```

### 2. Frontend (in new repo/folder)
```bash
cd ../schemasage-frontend
npm install
npm run dev
# Visit http://localhost:3000
```
- Ensure `.env` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### 3. Testing Endpoints

#### API Gateway
```bash
curl http://localhost:8000/health
```
#### Schema Detection
```bash
curl -X POST http://localhost:8000/api/schema/detect -H "Content-Type: application/json" -d '{"data": "name,age\nJohn,25\nJane,30"}'
```
#### Code Generation
```bash
curl -X POST http://localhost:8000/api/schema/generate-code -H "Content-Type: application/json" -d '{"schema_data": {...}, "format": "sqlalchemy", "options": {}}'
```
#### AI Chat
```bash
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"messages": [{"role": "user", "content": "Help me with my schema"}]}'
```
#### Project Management
```bash
curl -X GET http://localhost:8000/api/database/projects
```
#### Authentication
```bash
curl -X POST http://localhost:8000/api/auth/signup -H "Content-Type: application/json" -d '{"username": "test", "password": "testpass"}'
```

---

## 🛠️ Troubleshooting
- Use `docker-compose logs -f` to view logs
- Check health endpoints for each service
- Ensure ports 8000-8004 (backend) and 3000 (frontend) are available
- For CORS issues, update allowed origins in API Gateway

---

## 📈 Next Steps
- Add monitoring and metrics
- Set up CI/CD pipelines
- Harden security and authentication
- Scale services independently as needed

---

## 📄 Documentation Last Updated: June 28, 2025
