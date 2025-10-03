# SchemaSage Enterprise Deployment Guide

## 🏗️ Enterprise Architecture Overview

The SchemaSage Database Migration Service has been enhanced with enterprise-grade features:

### 🔐 Security Features
- **AES-256-GCM Encryption**: All sensitive connection data encrypted at rest
- **JWT Authentication**: Integration with SchemaSage auth service
- **PBKDF2 Key Derivation**: Secure key generation with salt
- **Multi-user Isolation**: User-based data segregation
- **Audit Logging**: Comprehensive activity tracking

### 💾 Data Persistence
- **PostgreSQL Backend**: Real database persistence replacing in-memory storage
- **Connection Pooling**: Optimized database performance
- **Transaction Management**: ACID compliance for data integrity
- **Schema Migrations**: Alembic-based version control

### 📊 Enterprise Features
- **Connection Health Monitoring**: Real-time database status tracking
- **User Quotas**: Configurable connection limits per user
- **Encrypted Secret Storage**: Secure password and credential management
- **Schema Snapshots**: Historical schema versioning

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- SchemaSage Authentication Service running

### 1. Automated Setup
```bash
# Run the enterprise setup script
python setup_enterprise.py --env development

# For production
python setup_enterprise.py --env production
```

### 2. Manual Setup (if needed)

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Database Setup
```sql
-- Create database
CREATE DATABASE schemasage_enterprise;

-- Create user
CREATE USER schemasage_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE schemasage_enterprise TO schemasage_user;
```

#### Environment Configuration
Create `.env` file:
```env
# Database
DATABASE_URL=postgresql://schemasage_user:password@localhost:5432/schemasage_enterprise

# Security Keys (generate unique ones!)
SCHEMASAGE_MASTER_KEY=your_32_byte_base64_key
JWT_SECRET_KEY=your_jwt_secret
API_SECRET_KEY=your_api_secret

# Services
AUTH_SERVICE_URL=http://localhost:8001
```

#### Run Migrations
```bash
alembic upgrade head
```

### 3. Start the Service
```bash
python main.py
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose -f docker-compose.enterprise.yml up
```

### Production
```bash
# Set production environment variables
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@prod-db:5432/schemasage

docker-compose -f docker-compose.enterprise.yml up -d
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SCHEMASAGE_MASTER_KEY` | Master encryption key | Required |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `AUTH_SERVICE_URL` | SchemaSage auth service URL | http://localhost:8001 |
| `ENCRYPTION_ALGORITHM` | Encryption algorithm | AES-256-GCM |
| `KEY_DERIVATION_ITERATIONS` | PBKDF2 iterations | 100000 |
| `DATABASE_POOL_SIZE` | Connection pool size | 20 |
| `MAX_CONNECTIONS_PER_USER` | User connection limit | 10 |

### Security Configuration

#### Encryption Keys
Generate secure keys:
```python
import secrets
master_key = secrets.token_urlsafe(32)
jwt_secret = secrets.token_urlsafe(32)
```

#### Database Security
- Use strong passwords
- Enable SSL/TLS connections
- Restrict network access
- Regular security updates

## 📋 API Reference

### Enterprise Endpoints

All enterprise endpoints require JWT authentication:

#### Authentication
```http
Authorization: Bearer <jwt_token>
```

#### Connection Management
```http
POST /api/database/connections/
GET /api/database/connections/
GET /api/database/connections/{connection_id}
PUT /api/database/connections/{connection_id}
DELETE /api/database/connections/{connection_id}
```

#### Connection Testing
```http
POST /api/database/connections/{connection_id}/test
```

#### Health Monitoring
```http
GET /api/database/connections/{connection_id}/health
```

#### Audit Logs
```http
GET /api/database/audit-logs/
```

### Response Format
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

## 🔍 Monitoring and Debugging

### Health Checks
```bash
# Service health
curl http://localhost:8000/health

# Database connectivity
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/database/connections/{id}/test
```

### Logs
- Application logs: Console output
- Audit logs: Database `audit_logs` table
- Database logs: PostgreSQL logs

### Common Issues

#### Connection Errors
```bash
# Check database connectivity
psql -h localhost -U schemasage_user -d schemasage_enterprise

# Verify environment variables
echo $DATABASE_URL
```

#### Authentication Issues
```bash
# Verify auth service
curl http://localhost:8001/health

# Check JWT token
python -c "import jwt; print(jwt.decode('token', verify=False))"
```

#### Encryption Problems
```bash
# Verify master key
python -c "
import base64
key = 'your_master_key'
print(f'Key length: {len(base64.b64decode(key))} bytes')
"
```

## 🔄 Database Migrations

### Create New Migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>
```

### Rollback
```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

## 🚀 Production Deployment

### Pre-deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring tools setup

### Deployment Steps
1. **Database Setup**
   ```bash
   # Create production database
   createdb schemasage_enterprise_prod
   
   # Run migrations
   alembic upgrade head
   ```

2. **Application Deployment**
   ```bash
   # Pull latest code
   git pull origin main
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set production environment
   export ENVIRONMENT=production
   
   # Start with production settings
   gunicorn main:app --workers 4 --bind 0.0.0.0:8000
   ```

3. **Load Balancer Configuration**
   ```nginx
   upstream schemasage_backend {
       server 127.0.0.1:8000;
       server 127.0.0.1:8001;
   }
   
   server {
       listen 443 ssl;
       server_name api.schemasage.com;
       
       location / {
           proxy_pass http://schemasage_backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🔒 Security Best Practices

### Data Protection
- Encrypt all sensitive data at rest
- Use HTTPS for all communications
- Implement proper access controls
- Regular security audits

### Key Management
- Rotate encryption keys regularly
- Store keys securely (e.g., AWS KMS, HashiCorp Vault)
- Separate keys by environment
- Monitor key usage

### Database Security
- Use connection pooling
- Implement query timeouts
- Regular database backups
- Monitor for suspicious activity

### Authentication
- Implement token expiration
- Use secure token storage
- Monitor authentication events
- Implement rate limiting

## 📊 Performance Optimization

### Database Optimization
```sql
-- Create indexes for performance
CREATE INDEX idx_connections_user_id ON connections(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_connections_last_health_check ON connections(last_health_check);
```

### Application Optimization
- Use connection pooling
- Implement caching for frequent queries
- Optimize database queries
- Monitor resource usage

### Monitoring Metrics
- Response times
- Database query performance
- Memory usage
- Connection counts
- Error rates

## 🆘 Troubleshooting

### Common Error Messages

#### "Connection refused"
- Check if PostgreSQL is running
- Verify database URL
- Check firewall settings

#### "Authentication failed"
- Verify JWT token
- Check auth service connectivity
- Validate user permissions

#### "Encryption key invalid"
- Check master key format
- Verify environment variables
- Validate key length (32 bytes)

### Debug Commands
```bash
# Test database connection
python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('$DATABASE_URL')
    print('Database connected successfully')
    await conn.close()
asyncio.run(test())
"

# Validate encryption
python -c "
from core.encryption import EncryptionService
service = EncryptionService()
test = service.encrypt('test_data', 'test_password')
print('Encryption working:', service.decrypt(test, 'test_password') == 'test_data')
"
```

## 📞 Support

For enterprise support and advanced features:
- Email: enterprise@schemasage.com
- Documentation: https://docs.schemasage.com
- GitHub Issues: https://github.com/schemasage/enterprise

## 📄 License

Enterprise features are available under the SchemaSage Enterprise License.
Contact sales@schemasage.com for licensing information.