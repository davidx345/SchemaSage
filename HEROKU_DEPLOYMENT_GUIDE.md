# SchemaSage Heroku Deployment Guide

## Overview

This comprehensive guide will walk you through deploying your SchemaSage microservices architecture on Heroku using Supabase as your PostgreSQL database provider. This setup provides a scalable, production-ready deployment without the complexity of managing your own database infrastructure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Supabase Database Setup](#supabase-database-setup)
3. [Heroku Preparation](#heroku-preparation)
4. [Service Deployment Strategy](#service-deployment-strategy)
5. [Environment Configuration](#environment-configuration)
6. [Deploying Each Service](#deploying-each-service)
7. [Service Communication Setup](#service-communication-setup)
8. [Database Migrations](#database-migrations)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Scaling and Performance](#scaling-and-performance)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Accounts
- **Heroku Account**: [Sign up at heroku.com](https://signup.heroku.com/)
- **Supabase Account**: [Sign up at supabase.com](https://supabase.com/)
- **Git**: Ensure Git is installed and configured

### Required Tools
```bash
# Install Heroku CLI
# Windows (using Chocolatey)
choco install heroku-cli

# Or download from: https://devcenter.heroku.com/articles/heroku-cli

# Verify installation
heroku --version
heroku login
```

### Your Current Services
Based on your project structure, you have these services:
- **API Gateway** (`services/api-gateway`)
- **Authentication Service** (`services/authentication`)
- **AI Chat Service** (`services/ai-chat`)
- **Code Generation Service** (`services/code-generation`)
- **Schema Detection Service** (`services/schema-detection`)
- **Project Management Service** (`services/project-management`)

## Supabase Database Setup

### 1. Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Click "New Project"
3. Choose your organization
4. Fill in project details:
   - **Name**: `schemasage-production`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
5. Click "Create new project"

### 2. Configure Database Settings

1. Navigate to **Settings** → **Database**
2. Note down these connection details:
   - **Host**: `db.xxx.supabase.co`
   - **Port**: `5432`
   - **Database name**: `postgres`
   - **Username**: `postgres`
   - **Password**: Your chosen password

### 3. Get Connection String

In your Supabase dashboard:
1. Go to **Settings** → **Database**
2. Under "Connection string", copy the **URI** format:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```

### 4. Enable Required Extensions (if needed)

In the Supabase SQL Editor, run:
```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable additional extensions as needed
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

## Heroku Preparation

### 1. Organize Your Deployment Strategy

Since Heroku deploys from Git repositories and you have multiple services, you'll need to deploy each service as a separate Heroku app:

```
schemasage-api-gateway       (API Gateway)
schemasage-auth             (Authentication)
schemasage-ai-chat          (AI Chat)
schemasage-code-gen         (Code Generation)
schemasage-schema-detect    (Schema Detection)
schemasage-project-mgmt     (Project Management)
```

### 2. Create Heroku Apps

```bash
# Create apps for each service
heroku create schemasage-api-gateway
heroku create schemasage-auth
heroku create schemasage-ai-chat
heroku create schemasage-code-gen
heroku create schemasage-schema-detect
heroku create schemasage-project-mgmt

# Verify apps were created
heroku apps
```

### 3. Add Heroku Remote Origins

You'll need to set up Git subtree deployments for each service:

```bash
# Add remotes for each service
heroku git:remote -a schemasage-api-gateway -r heroku-gateway
heroku git:remote -a schemasage-auth -r heroku-auth
heroku git:remote -a schemasage-ai-chat -r heroku-chat
heroku git:remote -a schemasage-code-gen -r heroku-codegen
heroku git:remote -a schemasage-schema-detect -r heroku-schema
heroku git:remote -a schemasage-project-mgmt -r heroku-project
```

## Environment Configuration

### 1. Shared Environment Variables

Create a base environment configuration that all services will use:

```bash
# Database Configuration (Supabase)
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres"
POSTGRES_HOST="db.xxx.supabase.co"
POSTGRES_PORT="5432"
POSTGRES_DB="postgres"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="[YOUR-PASSWORD]"

# Application Configuration
ENVIRONMENT="production"
DEBUG="false"
LOG_LEVEL="info"

# Security
JWT_SECRET_KEY="[GENERATE-STRONG-SECRET]"
ENCRYPTION_KEY="[GENERATE-ENCRYPTION-KEY]"

# Service URLs (will be updated after deployment)
API_GATEWAY_URL="https://schemasage-api-gateway.herokuapp.com"
AUTH_SERVICE_URL="https://schemasage-auth.herokuapp.com"
AI_CHAT_SERVICE_URL="https://schemasage-ai-chat.herokuapp.com"
CODE_GEN_SERVICE_URL="https://schemasage-code-gen.herokuapp.com"
SCHEMA_DETECT_SERVICE_URL="https://schemasage-schema-detect.herokuapp.com"
PROJECT_MGMT_SERVICE_URL="https://schemasage-project-mgmt.herokuapp.com"

# External Services
GEMINI_API_KEY="[YOUR-GEMINI-API-KEY]"
```

### 2. Generate Required Secrets

```bash
# Generate JWT Secret (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Encryption Key (Python)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Deploying Each Service

### Service Deployment Template

For each service, follow this pattern:

#### 1. API Gateway Deployment

```bash
# Set environment variables
heroku config:set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres" -a schemasage-api-gateway
heroku config:set ENVIRONMENT="production" -a schemasage-api-gateway
heroku config:set DEBUG="false" -a schemasage-api-gateway
heroku config:set AUTH_SERVICE_URL="https://schemasage-auth.herokuapp.com" -a schemasage-api-gateway
heroku config:set AI_CHAT_SERVICE_URL="https://schemasage-ai-chat.herokuapp.com" -a schemasage-api-gateway
heroku config:set CODE_GEN_SERVICE_URL="https://schemasage-code-gen.herokuapp.com" -a schemasage-api-gateway
heroku config:set SCHEMA_DETECT_SERVICE_URL="https://schemasage-schema-detect.herokuapp.com" -a schemasage-api-gateway
heroku config:set PROJECT_MGMT_SERVICE_URL="https://schemasage-project-mgmt.herokuapp.com" -a schemasage-api-gateway

# Deploy using git subtree
git subtree push --prefix=services/api-gateway heroku-gateway main
```

#### 2. Authentication Service Deployment

```bash
# Set environment variables
heroku config:set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres" -a schemasage-auth
heroku config:set ENVIRONMENT="production" -a schemasage-auth
heroku config:set DEBUG="false" -a schemasage-auth
heroku config:set JWT_SECRET_KEY="[YOUR-JWT-SECRET]" -a schemasage-auth
heroku config:set ENCRYPTION_KEY="[YOUR-ENCRYPTION-KEY]" -a schemasage-auth

# Deploy
git subtree push --prefix=services/authentication heroku-auth main
```

#### 3. AI Chat Service Deployment

```bash
# Set environment variables
heroku config:set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres" -a schemasage-ai-chat
heroku config:set ENVIRONMENT="production" -a schemasage-ai-chat
heroku config:set DEBUG="false" -a schemasage-ai-chat
heroku config:set GEMINI_API_KEY="[YOUR-GEMINI-API-KEY]" -a schemasage-ai-chat
heroku config:set AUTH_SERVICE_URL="https://schemasage-auth.herokuapp.com" -a schemasage-ai-chat

# Deploy
git subtree push --prefix=services/ai-chat heroku-chat main
```

#### 4. Code Generation Service Deployment

```bash
# Set environment variables
heroku config:set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres" -a schemasage-code-gen
heroku config:set ENVIRONMENT="production" -a schemasage-code-gen
heroku config:set DEBUG="false" -a schemasage-code-gen
heroku config:set AUTH_SERVICE_URL="https://schemasage-auth.herokuapp.com" -a schemasage-code-gen

# Deploy
git subtree push --prefix=services/code-generation heroku-codegen main
```

#### 5. Schema Detection Service Deployment

```bash
# Set environment variables
heroku config:set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres" -a schemasage-schema-detect
heroku config:set ENVIRONMENT="production" -a schemasage-schema-detect
heroku config:set DEBUG="false" -a schemasage-schema-detect
heroku config:set AUTH_SERVICE_URL="https://schemasage-auth.herokuapp.com" -a schemasage-schema-detect

# Deploy
git subtree push --prefix=services/schema-detection heroku-schema main
```

#### 6. Project Management Service Deployment

```bash
# Set environment variables
heroku config:set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres" -a schemasage-project-mgmt
heroku config:set ENVIRONMENT="production" -a schemasage-project-mgmt
heroku config:set DEBUG="false" -a schemasage-project-mgmt
heroku config:set AUTH_SERVICE_URL="https://schemasage-auth.herokuapp.com" -a schemasage-project-mgmt

# Deploy
git subtree push --prefix=services/project-management heroku-project main
```

## Service Communication Setup

### 1. Update Service URLs

After all services are deployed, update the API Gateway with the correct service URLs:

```bash
heroku config:set AUTH_SERVICE_URL="https://schemasage-auth.herokuapp.com" -a schemasage-api-gateway
heroku config:set AI_CHAT_SERVICE_URL="https://schemasage-ai-chat.herokuapp.com" -a schemasage-api-gateway
heroku config:set CODE_GEN_SERVICE_URL="https://schemasage-code-gen.herokuapp.com" -a schemasage-api-gateway
heroku config:set SCHEMA_DETECT_SERVICE_URL="https://schemasage-schema-detect.herokuapp.com" -a schemasage-api-gateway
heroku config:set PROJECT_MGMT_SERVICE_URL="https://schemasage-project-mgmt.herokuapp.com" -a schemasage-api-gateway
```

### 2. Configure CORS

Ensure your services allow cross-origin requests:

```python
# In each service's main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://schemasage-api-gateway.herokuapp.com",
        "https://your-frontend-domain.com"  # Add your frontend domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Database Migrations

### 1. Run Initial Migrations

Choose one service (usually authentication) to run database migrations:

```bash
# Connect to authentication service
heroku run bash -a schemasage-auth

# Inside the Heroku dyno, run migrations
python -c "
from shared.utils.database import engine
from shared.models.base import Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
```

### 2. Create Admin User (if needed)

```bash
# Run admin user creation script
heroku run python create_admin_user.py -a schemasage-auth
```

### 3. Set up Database Backup

In Supabase Dashboard:
1. Go to **Settings** → **Database**
2. Enable **Point-in-time Recovery** (recommended)
3. Configure automated backups

## Monitoring and Logging

### 1. Enable Heroku Logs

```bash
# View logs for each service
heroku logs --tail -a schemasage-api-gateway
heroku logs --tail -a schemasage-auth
heroku logs --tail -a schemasage-ai-chat
heroku logs --tail -a schemasage-code-gen
heroku logs --tail -a schemasage-schema-detect
heroku logs --tail -a schemasage-project-mgmt
```

### 2. Add Logging Add-ons (Optional)

```bash
# Add Papertrail for centralized logging
heroku addons:create papertrail:choklad -a schemasage-api-gateway
heroku addons:create papertrail:choklad -a schemasage-auth
# ... repeat for other services
```

### 3. Health Check Endpoints

Ensure each service has a health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "service-name"}
```

### 4. Monitor Service Status

```bash
# Check service status
heroku ps -a schemasage-api-gateway
heroku ps -a schemasage-auth
# ... for all services
```

## Scaling and Performance

### 1. Dyno Scaling

```bash
# Scale to multiple dynos for high traffic
heroku ps:scale web=2 -a schemasage-api-gateway
heroku ps:scale web=1 -a schemasage-auth  # Keep auth service lean
```

### 2. Database Performance

1. In Supabase Dashboard:
   - Monitor database performance
   - Set up connection pooling if needed
   - Consider upgrading plan for better performance

### 3. Optimize for Production

```python
# In each service's main.py
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1,  # Heroku recommends 1 worker per dyno
        access_log=False,  # Disable in production
        log_level="warning"  # Reduce log verbosity
    )
```

## Deployment Scripts

### Automated Deployment Script

Create a PowerShell script for easy deployment:

```powershell
# deploy-to-heroku.ps1
Write-Host "Deploying SchemaSage to Heroku..." -ForegroundColor Green

# Deploy each service
Write-Host "Deploying API Gateway..." -ForegroundColor Yellow
git subtree push --prefix=services/api-gateway heroku-gateway main

Write-Host "Deploying Authentication Service..." -ForegroundColor Yellow
git subtree push --prefix=services/authentication heroku-auth main

Write-Host "Deploying AI Chat Service..." -ForegroundColor Yellow
git subtree push --prefix=services/ai-chat heroku-chat main

Write-Host "Deploying Code Generation Service..." -ForegroundColor Yellow
git subtree push --prefix=services/code-generation heroku-codegen main

Write-Host "Deploying Schema Detection Service..." -ForegroundColor Yellow
git subtree push --prefix=services/schema-detection heroku-schema main

Write-Host "Deploying Project Management Service..." -ForegroundColor Yellow
git subtree push --prefix=services/project-management heroku-project main

Write-Host "All services deployed successfully!" -ForegroundColor Green
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Build Failures

```bash
# Check build logs
heroku logs --tail -a [APP-NAME]

# Common fixes:
# - Ensure requirements.txt is in service root
# - Check Python version compatibility
# - Verify Procfile syntax
```

#### 2. Database Connection Issues

```bash
# Test database connection
heroku run python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.environ['DATABASE_URL'])
connection = engine.connect()
result = connection.execute('SELECT 1')
print('Database connected successfully')
connection.close()
" -a [APP-NAME]
```

#### 3. Service Communication Issues

```bash
# Test service-to-service communication
heroku run python -c "
import httpx
import os
response = httpx.get(f\"{os.environ['AUTH_SERVICE_URL']}/health\")
print(f'Auth service status: {response.status_code}')
" -a schemasage-api-gateway
```

#### 4. Memory Issues

```bash
# Check memory usage
heroku logs --tail -a [APP-NAME] | grep "memory"

# Solution: Upgrade dyno type or optimize code
heroku ps:type Standard-1X -a [APP-NAME]
```

### Service-Specific Debugging

#### API Gateway Issues
- Check service URL configurations
- Verify route mappings
- Test individual service endpoints

#### Authentication Issues
- Verify JWT secret configuration
- Check database user table
- Test token generation/validation

#### AI Chat Issues
- Verify Gemini API key
- Check API rate limits
- Monitor response times

### Performance Optimization

#### 1. Database Optimization
```sql
-- In Supabase SQL Editor
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_schemas_project_id ON schemas(project_id);
```

#### 2. Caching Strategy
Consider adding Redis for caching:
```bash
# Add Redis addon
heroku addons:create heroku-redis:mini -a schemasage-api-gateway
```

#### 3. CDN for Static Assets
If you have static files, consider using a CDN or Heroku's built-in asset pipeline.

## Security Considerations

### 1. Environment Variables
- Never commit secrets to Git
- Use Heroku Config Vars for all sensitive data
- Rotate secrets regularly

### 2. Database Security
- Use Supabase Row Level Security (RLS)
- Implement proper authentication
- Regular security updates

### 3. API Security
- Implement rate limiting
- Use HTTPS only
- Validate all inputs
- Implement proper CORS policies

## Cost Optimization

### 1. Dyno Management
```bash
# Scale down during low traffic
heroku ps:scale web=0 -a [APP-NAME]  # Stop dyno

# Scale up when needed
heroku ps:scale web=1 -a [APP-NAME]  # Start dyno
```

### 2. Database Usage
- Monitor Supabase usage in dashboard
- Optimize queries to reduce database load
- Consider upgrading plan only when necessary

### 3. Monitoring Costs
```bash
# Check current usage
heroku ps -a [APP-NAME]
heroku addons -a [APP-NAME]
```

## Maintenance and Updates

### 1. Regular Updates
```bash
# Update dependencies
# In each service directory, update requirements.txt
# Then redeploy affected services
```

### 2. Database Maintenance
- Regular backups through Supabase
- Monitor performance metrics
- Clean up old data periodically

### 3. Monitoring and Alerts
- Set up Supabase alerts for database performance
- Monitor Heroku dyno performance
- Set up uptime monitoring for critical endpoints

## Quick Reference Commands

```bash
# Deploy all services
./deploy-to-heroku.ps1

# Check all app status
heroku ps -a schemasage-api-gateway && heroku ps -a schemasage-auth && heroku ps -a schemasage-ai-chat

# View logs for all services
heroku logs --tail -a schemasage-api-gateway &
heroku logs --tail -a schemasage-auth &

# Scale all services
heroku ps:scale web=1 -a schemasage-api-gateway
heroku ps:scale web=1 -a schemasage-auth
# ... repeat for other services

# Update environment variable across all services
heroku config:set NEW_VAR="value" -a schemasage-api-gateway
heroku config:set NEW_VAR="value" -a schemasage-auth
# ... repeat for other services
```

## Next Steps

1. **Deploy Services**: Follow the deployment steps for each service
2. **Test Integration**: Verify all services communicate correctly
3. **Set Up Monitoring**: Implement logging and health checks
4. **Configure Frontend**: Update your frontend to use the new API Gateway URL
5. **Performance Testing**: Load test your application
6. **Documentation**: Update your API documentation with new URLs

## Support Resources

- **Heroku Documentation**: [devcenter.heroku.com](https://devcenter.heroku.com/)
- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)

---

This guide provides a comprehensive roadmap for deploying your SchemaSage microservices architecture on Heroku with Supabase. Follow each section carefully, and you'll have a production-ready deployment with proper monitoring, scaling, and maintenance capabilities.
