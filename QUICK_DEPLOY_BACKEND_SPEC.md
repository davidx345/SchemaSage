# SchemaSage Quick Deploy - Backend Implementation Guide

## 🎯 Overview

This document provides complete specifications for extending the `schema-detection-service` to support the new "Quick Deploy" feature. The Quick Deploy feature allows users to describe their database needs in natural language and automatically provision cloud infrastructure with generated code, migrations, and API endpoints.

---

## 📋 Service Extension: Cloud Provisioning Module

**Service Name:** `schema-detection-service` (extended)  
**New Module:** `cloud_provisioning`  
**Base URL:** `http://localhost:8001/api` (development)

---

## 🔌 Required API Endpoints

### 1. **POST /api/cloud-provision/analyze**

**Purpose:** Analyze natural language description or uploaded file to generate schema and recommendations.

**Request:**
```typescript
Content-Type: multipart/form-data

FormData:
{
  description: string;        // Natural language description
  file?: File;               // Optional: schema file (SQL, JSON, CSV, Excel)
  preferences?: string;      // JSON string: { provider?, region?, budget? }
}
```

**Response:**
```json
{
  "analysis": {
    "databaseType": "postgresql",
    "version": "15",
    "tables": [
      {
        "name": "users",
        "columns": [
          {
            "name": "id",
            "type": "integer",
            "constraints": ["primary_key", "auto_increment"]
          },
          {
            "name": "email",
            "type": "varchar(255)",
            "constraints": ["unique", "not_null"]
          }
        ]
      }
    ],
    "relationships": [
      {
        "from": "orders",
        "to": "users",
        "type": "many_to_one",
        "foreignKey": "user_id"
      }
    ],
    "features": ["authentication", "relationships", "indexes"],
    "estimatedSize": "10GB"
  },
  "recommendations": {
    "provider": "aws",
    "instanceType": "db.t3.medium",
    "storage": 100,
    "costPerMonth": 45.50,
    "reasoning": "Based on 5 tables with moderate complexity...",
    "alternatives": [
      {
        "provider": "gcp",
        "instanceType": "db-n1-standard-1",
        "costPerMonth": 48.20
      }
    ]
  },
  "schema": {
    "sqlalchemy": "...",
    "prisma": "...",
    "typeorm": "...",
    "raw_sql": "...",
    "tables": [...]  // Full table definitions
  }
}
```

**Implementation Notes:**
- Use OpenAI GPT-4 or Anthropic Claude for natural language parsing
- Prompt should extract: database type, table names, columns, relationships, features
- Calculate estimated size based on table count and expected record volumes
- Recommend instance types based on: table complexity, estimated size, expected load
- Include cost calculations for AWS, GCP, and Azure

**Python Dependencies:**
```python
openai>=1.0.0
anthropic>=0.7.0
```

**Sample AI Prompt:**
```python
ANALYSIS_PROMPT = """
You are a database architect. Analyze the following request and return structured JSON.

User Request: {description}

Return JSON with:
{
  "databaseType": "postgresql|mysql|mongodb",
  "version": "version number",
  "tables": [{"name": "...", "columns": [...], "purpose": "..."}],
  "relationships": [{"from": "...", "to": "...", "type": "..."}],
  "features": ["auth", "full-text-search", ...],
  "estimatedSize": "estimate in GB"
}
"""
```

---

### 2. **POST /api/cloud-provision/validate-credentials**

**Purpose:** Validate cloud provider credentials and check permissions.

**Request:**
```json
{
  "provider": "aws|gcp|azure",
  "accessKey": "AKIA...",           // AWS
  "secretKey": "...",               // AWS
  "projectId": "my-project",        // GCP
  "region": "us-east-1",
  "subscriptionId": "...",          // Azure
  "tenantId": "..."                 // Azure
}
```

**Response:**
```json
{
  "valid": true,
  "permissions": [
    "rds:CreateDBInstance",
    "rds:DescribeDBInstances",
    "rds:ModifyDBInstance",
    "ec2:DescribeSecurityGroups"
  ],
  "accountId": "123456789012",
  "message": "Successfully authenticated with full RDS permissions"
}
```

**Implementation:**
```python
import boto3
from botocore.exceptions import ClientError

async def validate_aws_credentials(access_key: str, secret_key: str, region: str):
    try:
        # Create RDS client
        rds = boto3.client(
            'rds',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Test credentials by listing instances
        response = rds.describe_db_instances(MaxRecords=1)
        
        # Get account ID
        sts = boto3.client('sts', 
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
        identity = sts.get_caller_identity()
        
        return {
            "valid": True,
            "accountId": identity['Account'],
            "permissions": ["rds:*"]  # You can check specific permissions
        }
    except ClientError as e:
        return {
            "valid": False,
            "error": str(e)
        }
```

**Dependencies:**
```python
boto3>=1.28.0         # AWS SDK
google-cloud>=0.34.0  # GCP SDK
azure-mgmt-rdbms>=10.0.0  # Azure SDK
```

---

### 3. **POST /api/cloud-provision/deploy**

**Purpose:** Start cloud infrastructure deployment with schema, code generation, and migrations.

**Request:**
```json
{
  "provider": "aws",
  "credentials": {
    "accessKey": "...",
    "secretKey": "...",
    "region": "us-east-1"
  },
  "schema": {
    "tables": [...],
    "relationships": [...]
  },
  "options": {
    "generateCode": true,
    "createMigrations": true,
    "setupAPI": false,
    "language": "typescript",
    "framework": "fastapi"
  },
  "instanceConfig": {
    "instanceType": "db.t3.medium",
    "storage": 100,
    "region": "us-east-1",
    "autoScaling": true,
    "backupEnabled": true
  }
}
```

**Response:**
```json
{
  "deploymentId": "deploy_abc123xyz",
  "status": "in_progress",
  "websocketUrl": "wss://your-service.com/ws/cloud-provision/deploy_abc123xyz"
}
```

**Implementation Flow:**
```python
from celery import Celery
import uuid

# Use Celery for background processing
app = Celery('cloud_provisioning', broker='redis://localhost:6379')

@app.task
async def deploy_infrastructure(deployment_id: str, config: dict):
    """
    Main deployment task - runs in background
    """
    try:
        # Step 1: Create RDS instance (20%)
        await send_progress(deployment_id, 20, "Creating RDS instance...")
        instance_id = await create_rds_instance(config)
        
        # Step 2: Wait for instance ready (40%)
        await send_progress(deployment_id, 40, "Waiting for instance...")
        await wait_for_instance(instance_id)
        
        # Step 3: Get connection string (50%)
        connection_string = await get_connection_string(instance_id)
        await send_progress(deployment_id, 50, "Instance ready!")
        
        # Step 4: Apply schema (60%)
        await send_progress(deployment_id, 60, "Applying schema...")
        await apply_schema(connection_string, config['schema'])
        
        # Step 5: Generate code (75%)
        if config['options']['generateCode']:
            await send_progress(deployment_id, 75, "Generating code...")
            code_files = await generate_code(config['schema'], config['options']['language'])
        
        # Step 6: Generate migrations (85%)
        if config['options']['createMigrations']:
            await send_progress(deployment_id, 85, "Creating migrations...")
            migrations = await generate_migrations(config['schema'])
        
        # Step 7: Complete (100%)
        await send_progress(deployment_id, 100, "Deployment complete!")
        await send_completion(deployment_id, {
            "connectionString": connection_string,
            "cloudResourceId": instance_id,
            "generatedAssets": {
                "code": code_files,
                "migrations": migrations
            }
        })
        
    except Exception as e:
        await send_error(deployment_id, str(e))

async def send_progress(deployment_id: str, percentage: int, message: str):
    """Send progress update via WebSocket"""
    await websocket_manager.broadcast(
        deployment_id,
        {
            "type": "progress",
            "data": {
                "percentage": percentage,
                "step": message,
                "level": "info",
                "message": message
            }
        }
    )
```

**AWS RDS Creation:**
```python
async def create_rds_instance(config: dict) -> str:
    """Create AWS RDS instance"""
    rds = boto3.client('rds',
                      aws_access_key_id=config['credentials']['accessKey'],
                      aws_secret_access_key=config['credentials']['secretKey'],
                      region_name=config['credentials']['region'])
    
    # Generate unique instance ID
    instance_id = f"schemasage-{uuid.uuid4().hex[:8]}"
    
    # Generate secure password
    master_password = secrets.token_urlsafe(16)
    
    # Create instance
    response = rds.create_db_instance(
        DBInstanceIdentifier=instance_id,
        DBInstanceClass=config['instanceConfig']['instanceType'],
        Engine='postgres',
        EngineVersion='15.3',
        MasterUsername='schemasage_admin',
        MasterUserPassword=master_password,
        AllocatedStorage=config['instanceConfig']['storage'],
        StorageType='gp3',
        StorageEncrypted=True,
        BackupRetentionPeriod=7 if config['instanceConfig']['backupEnabled'] else 0,
        PubliclyAccessible=True,  # For initial setup
        VpcSecurityGroupIds=[await create_security_group(rds, config)],
        Tags=[
            {'Key': 'ManagedBy', 'Value': 'SchemaSage'},
            {'Key': 'DeploymentId', 'Value': config['deploymentId']}
        ]
    )
    
    # Store password securely (use AWS Secrets Manager)
    await store_credentials(instance_id, master_password)
    
    return instance_id

async def wait_for_instance(instance_id: str, credentials: dict):
    """Wait for RDS instance to be available"""
    rds = boto3.client('rds', ...)
    
    waiter = rds.get_waiter('db_instance_available')
    waiter.wait(
        DBInstanceIdentifier=instance_id,
        WaiterConfig={'Delay': 30, 'MaxAttempts': 40}  # Max 20 minutes
    )
```

---

### 4. **WS /ws/cloud-provision/{deployment_id}**

**Purpose:** WebSocket endpoint for real-time deployment progress updates.

**Connection:**
```javascript
// Frontend connects
const ws = new WebSocket('wss://your-service.com/ws/cloud-provision/deploy_abc123');
```

**Messages (Server → Client):**
```json
// Authentication success
{
  "type": "auth_success",
  "message": "Connected to deployment stream"
}

// Progress update
{
  "type": "progress",
  "data": {
    "status": "provisioning",
    "percentage": 45,
    "step": "Creating RDS instance...",
    "level": "info",
    "message": "Instance schemasage-abc123 is being provisioned"
  }
}

// Completion
{
  "type": "complete",
  "data": {
    "deploymentId": "deploy_abc123",
    "status": "ready",
    "connectionString": "postgresql://user:pass@instance.rds.amazonaws.com:5432/db",
    "cloudResourceId": "schemasage-abc123",
    "generatedAssets": {
      "code": {
        "language": "typescript",
        "files": [...],
        "lineCount": 342
      },
      "migrations": {
        "files": [...]
      }
    },
    "cost": {
      "estimatedMonthly": 45.50,
      "breakdown": {
        "compute": 30,
        "storage": 10,
        "backup": 5.50
      }
    },
    "metadata": {
      "provider": "aws",
      "region": "us-east-1",
      "instanceType": "db.t3.medium",
      "databaseType": "PostgreSQL 15",
      "createdAt": "2025-01-06T12:34:56Z"
    }
  }
}

// Error
{
  "type": "error",
  "error": "Failed to create RDS instance: InsufficientCapacity"
}
```

**Implementation:**
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, list[WebSocket]] = {}
    
    async def connect(self, deployment_id: str, websocket: WebSocket):
        await websocket.accept()
        if deployment_id not in self.active_connections:
            self.active_connections[deployment_id] = []
        self.active_connections[deployment_id].append(websocket)
    
    async def disconnect(self, deployment_id: str, websocket: WebSocket):
        if deployment_id in self.active_connections:
            self.active_connections[deployment_id].remove(websocket)
    
    async def broadcast(self, deployment_id: str, message: dict):
        if deployment_id in self.active_connections:
            for connection in self.active_connections[deployment_id]:
                await connection.send_json(message)

manager = WebSocketManager()

@app.websocket("/ws/cloud-provision/{deployment_id}")
async def deployment_websocket(websocket: WebSocket, deployment_id: str):
    await manager.connect(deployment_id, websocket)
    try:
        # Wait for authentication
        auth_data = await websocket.receive_json()
        
        # Validate token
        if await validate_token(auth_data.get('token')):
            await websocket.send_json({"type": "auth_success"})
            
            # Keep connection alive
            while True:
                data = await websocket.receive_text()
                # Handle ping/pong if needed
        else:
            await websocket.send_json({"type": "auth_error", "error": "Invalid token"})
            await websocket.close()
    except WebSocketDisconnect:
        manager.disconnect(deployment_id, websocket)
```

---

### 5. **GET /api/cloud-provision/deployment/{deployment_id}**

**Purpose:** Get current status and details of a deployment.

**Response:**
```json
{
  "deploymentId": "deploy_abc123",
  "status": "ready",
  "progress": {
    "percentage": 100,
    "currentStep": "Deployment complete"
  },
  "result": {
    "connectionString": "...",
    "cloudResourceId": "...",
    ...
  },
  "createdAt": "2025-01-06T12:00:00Z",
  "completedAt": "2025-01-06T12:15:00Z"
}
```

---

### 6. **POST /api/cloud-provision/estimate-cost**

**Purpose:** Estimate monthly costs for a given configuration.

**Request:**
```json
{
  "provider": "aws",
  "instanceType": "db.t3.medium",
  "storage": 100,
  "region": "us-east-1",
  "backupEnabled": true,
  "autoScaling": false
}
```

**Response:**
```json
{
  "monthlyTotal": 45.50,
  "hourlyTotal": 0.063,
  "breakdown": {
    "compute": 30.00,
    "storage": 10.00,
    "backup": 5.50,
    "network": 0.00
  },
  "comparison": {
    "aws": 45.50,
    "gcp": 48.20,
    "azure": 52.30
  }
}
```

**Implementation:**
```python
# AWS RDS Pricing (example - use real pricing API)
AWS_PRICING = {
    "us-east-1": {
        "db.t3.micro": 0.017,    # per hour
        "db.t3.small": 0.034,
        "db.t3.medium": 0.068,
        "db.t3.large": 0.136,
        "storage_gp3": 0.115,    # per GB per month
        "backup": 0.095          # per GB per month
    }
}

def estimate_aws_cost(instance_type: str, storage: int, region: str, backup_enabled: bool):
    pricing = AWS_PRICING.get(region, AWS_PRICING["us-east-1"])
    
    # Compute cost (per month = hourly * 730 hours)
    compute_hourly = pricing.get(instance_type, 0.068)
    compute_monthly = compute_hourly * 730
    
    # Storage cost
    storage_monthly = storage * pricing["storage_gp3"]
    
    # Backup cost (assume 50% of storage)
    backup_monthly = (storage * 0.5 * pricing["backup"]) if backup_enabled else 0
    
    total = compute_monthly + storage_monthly + backup_monthly
    
    return {
        "monthlyTotal": round(total, 2),
        "hourlyTotal": round(compute_hourly, 3),
        "breakdown": {
            "compute": round(compute_monthly, 2),
            "storage": round(storage_monthly, 2),
            "backup": round(backup_monthly, 2),
            "network": 0.00
        }
    }
```

---

### 7. **GET /api/cloud-provision/deployments**

**Purpose:** List all deployments for the current user.

**Query Parameters:**
```
?status=ready&provider=aws&limit=10
```

**Response:**
```json
{
  "deployments": [
    {
      "deploymentId": "deploy_abc123",
      "description": "E-commerce database",
      "provider": "aws",
      "status": "ready",
      "databaseType": "PostgreSQL 15",
      "createdAt": "2025-01-06T12:00:00Z",
      "costPerMonth": 45.50
    }
  ],
  "total": 1
}
```

---

### 8. **DELETE /api/cloud-provision/deployment/{deployment_id}**

**Purpose:** Terminate a deployment and optionally delete cloud resources.

**Request:**
```json
{
  "deleteResources": true  // If true, delete RDS instance; if false, just remove from tracking
}
```

**Response:**
```json
{
  "success": true,
  "message": "Deployment terminated and resources deleted"
}
```

---

## 🗄️ Database Schema

Add these tables to your existing database:

```sql
-- Cloud deployments table
CREATE TABLE cloud_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Input
    description TEXT NOT NULL,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('aws', 'gcp', 'azure')),
    
    -- Configuration
    database_type VARCHAR(50) NOT NULL,
    instance_type VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL,
    storage_gb INTEGER NOT NULL,
    
    -- Generated schema (stored as JSONB for querying)
    schema_json JSONB NOT NULL,
    
    -- Cloud resources
    cloud_instance_id VARCHAR(200),
    connection_string TEXT,  -- Encrypted
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'analyzing', 'provisioning', 'configuring', 'generating', 'ready', 'failed')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    error_message TEXT,
    
    -- Cost tracking
    estimated_monthly_cost DECIMAL(10,2),
    actual_monthly_cost DECIMAL(10,2),
    
    -- Generated assets metadata
    generated_code BOOLEAN DEFAULT FALSE,
    generated_migrations BOOLEAN DEFAULT FALSE,
    generated_api BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_user_deployments (user_id, created_at DESC),
    INDEX idx_status (status),
    INDEX idx_provider (provider)
);

-- Deployment logs table
CREATE TABLE deployment_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deployment_id UUID NOT NULL REFERENCES cloud_deployments(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    level VARCHAR(20) NOT NULL CHECK (level IN ('info', 'warning', 'error', 'success')),
    message TEXT NOT NULL,
    metadata JSONB,
    
    INDEX idx_deployment_logs (deployment_id, timestamp DESC)
);

-- Cloud credentials table (encrypted)
CREATE TABLE cloud_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('aws', 'gcp', 'azure')),
    
    -- Encrypted credentials (use pgcrypto or application-level encryption)
    credentials_encrypted TEXT NOT NULL,
    
    -- Metadata
    region VARCHAR(50),
    account_id VARCHAR(100),
    is_valid BOOLEAN DEFAULT TRUE,
    last_validated_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, provider)
);
```

---

## 🔐 Security Implementation

### 1. **Credential Encryption**

```python
from cryptography.fernet import Fernet
import os

# Use environment variable for encryption key
ENCRYPTION_KEY = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_credentials(credentials: dict) -> str:
    """Encrypt credentials for storage"""
    import json
    json_str = json.dumps(credentials)
    encrypted = cipher.encrypt(json_str.encode())
    return encrypted.decode()

def decrypt_credentials(encrypted: str) -> dict:
    """Decrypt stored credentials"""
    import json
    decrypted = cipher.decrypt(encrypted.encode())
    return json.loads(decrypted.decode())
```

### 2. **Rate Limiting**

```python
from fastapi import HTTPException
from datetime import datetime, timedelta

# Limit: 5 deployments per hour per user
DEPLOYMENT_RATE_LIMIT = 5
RATE_LIMIT_WINDOW = timedelta(hours=1)

async def check_rate_limit(user_id: str):
    recent_deployments = await db.count_deployments(
        user_id=user_id,
        since=datetime.now() - RATE_LIMIT_WINDOW
    )
    
    if recent_deployments >= DEPLOYMENT_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {DEPLOYMENT_RATE_LIMIT} deployments per hour."
        )
```

### 3. **IAM Best Practices**

```python
# Required AWS IAM permissions for user credentials
REQUIRED_AWS_PERMISSIONS = [
    "rds:CreateDBInstance",
    "rds:DescribeDBInstances",
    "rds:ModifyDBInstance",
    "rds:DeleteDBInstance",
    "rds:AddTagsToResource",
    "ec2:DescribeSecurityGroups",
    "ec2:CreateSecurityGroup",
    "ec2:AuthorizeSecurityGroupIngress"
]

# Recommend using AWS STS temporary credentials
def get_temporary_credentials(access_key: str, secret_key: str):
    """Get temporary credentials with limited scope"""
    sts = boto3.client('sts',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
    
    response = sts.assume_role(
        RoleArn='arn:aws:iam::ACCOUNT:role/SchemaSageDeploymentRole',
        RoleSessionName='schemasage-deployment',
        DurationSeconds=3600  # 1 hour
    )
    
    return response['Credentials']
```

---

## 📦 Required Python Dependencies

```python
# requirements.txt additions

# Cloud SDKs
boto3>=1.28.0                    # AWS SDK
google-cloud-sql>=1.5.0          # GCP Cloud SQL
azure-mgmt-rdbms>=10.0.0         # Azure Database SDK

# AI/NLP
openai>=1.0.0                    # OpenAI GPT
anthropic>=0.7.0                 # Anthropic Claude (alternative)

# Background Tasks
celery>=5.3.0                    # Task queue
redis>=5.0.0                     # Celery broker

# Security
cryptography>=41.0.0             # Credential encryption
pyjwt>=2.8.0                     # JWT validation

# Database
asyncpg>=0.29.0                  # PostgreSQL async driver
sqlalchemy>=2.0.0                # ORM

# WebSockets
websockets>=12.0                 # WebSocket support

# Utilities
python-dotenv>=1.0.0             # Environment variables
pydantic>=2.5.0                  # Data validation
```

---

## 🔄 Integration with Existing SchemaSage Features

After successful deployment, the backend should:

1. **Create Project Entry:**
```python
# POST to project-management-service
await project_api.create_project({
    "name": f"{deployment.database_type} Database",
    "description": deployment.description,
    "schema": deployment.schema_json,
    "source": "cloud_deployment",
    "deployment_id": deployment.id
})
```

2. **Add Database Connection:**
```python
# POST to database-migration-service
await database_api.add_connection({
    "name": f"{deployment.provider.upper()} {deployment.database_type}",
    "type": deployment.database_type.lower(),
    "host": extract_host(deployment.connection_string),
    "port": extract_port(deployment.connection_string),
    "database": extract_database(deployment.connection_string),
    "username": extract_username(deployment.connection_string),
    "password": extract_password(deployment.connection_string),
    "deployment_id": deployment.id
})
```

3. **Broadcast Activity:**
```python
# Send WebSocket message to dashboard
await websocket_manager.broadcast_to_user(
    user_id=deployment.user_id,
    message={
        "type": "activity_update",
        "data": {
            "type": "schema_generated",
            "description": f"{deployment.database_type} database deployed to {deployment.provider.upper()}",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "deploymentId": deployment.id,
                "provider": deployment.provider,
                "tableCount": len(deployment.schema_json.get('tables', []))
            }
        }
    }
)
```

---

## 🧪 Testing Endpoints

### Test with cURL:

```bash
# 1. Analyze deployment request
curl -X POST http://localhost:8001/api/cloud-provision/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "description=I need a PostgreSQL database for e-commerce" \
  -F "preferences={\"provider\":\"aws\",\"region\":\"us-east-1\"}"

# 2. Validate credentials
curl -X POST http://localhost:8001/api/cloud-provision/validate-credentials \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "accessKey": "AKIA...",
    "secretKey": "...",
    "region": "us-east-1"
  }'

# 3. Start deployment
curl -X POST http://localhost:8001/api/cloud-provision/deploy \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @deployment-config.json

# 4. Get deployment status
curl -X GET http://localhost:8001/api/cloud-provision/deployment/deploy_abc123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 5. Estimate cost
curl -X POST http://localhost:8001/api/cloud-provision/estimate-cost \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws",
    "instanceType": "db.t3.medium",
    "storage": 100,
    "region": "us-east-1"
  }'
```

---

## 📝 Implementation Checklist

- [ ] Set up Celery with Redis for background tasks
- [ ] Implement OpenAI/Anthropic integration for natural language analysis
- [ ] Add AWS SDK (boto3) and implement RDS provisioning
- [ ] Implement WebSocket manager for real-time updates
- [ ] Create database tables for deployments and logs
- [ ] Implement credential encryption/decryption
- [ ] Add rate limiting for deployments
- [ ] Implement cost estimation logic
- [ ] Add integration endpoints for projects and database connections
- [ ] Write unit tests for all endpoints
- [ ] Add error handling and logging
- [ ] Document all endpoints with OpenAPI/Swagger

---

## 🚀 Ready to Build!

This specification provides everything needed to extend your `schema-detection-service` with cloud provisioning capabilities. The frontend is already built and waiting for these endpoints to be implemented.

**Questions? Issues? Contact the frontend team!**
