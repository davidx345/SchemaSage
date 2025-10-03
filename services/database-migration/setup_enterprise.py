#!/usr/bin/env python3
"""
Enterprise Setup Script for SchemaSage Database Migration Service

This script sets up the complete enterprise infrastructure including:
- PostgreSQL database with proper schema
- Environment variables for security
- Alembic migrations
- Encryption key generation
- Database connection validation

Usage:
    python setup_enterprise.py --env production
    python setup_enterprise.py --env development
"""

import os
import sys
import asyncio
import secrets
import logging
from pathlib import Path
from typing import Optional
import asyncpg
from alembic import command
from alembic.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnterpriseSetup:
    """Enterprise setup and configuration manager"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.project_root = Path(__file__).parent
        
    def generate_secure_keys(self) -> dict:
        """Generate secure encryption and JWT keys"""
        logger.info("🔑 Generating secure encryption keys...")
        
        return {
            'SCHEMASAGE_MASTER_KEY': secrets.token_urlsafe(32),
            'JWT_SECRET_KEY': secrets.token_urlsafe(32),
            'API_SECRET_KEY': secrets.token_urlsafe(32)
        }
    
    def create_env_file(self, keys: dict):
        """Create .env file with secure configuration"""
        env_file = self.project_root / '.env'
        
        env_content = f"""# SchemaSage Enterprise Configuration
# Generated on: {os.popen('date').read().strip()}

# Environment
ENVIRONMENT={self.environment}

# Database Configuration
DATABASE_URL=postgresql://schemasage_user:secure_password@localhost:5432/schemasage_enterprise
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Security Keys (Keep these secret!)
SCHEMASAGE_MASTER_KEY={keys['SCHEMASAGE_MASTER_KEY']}
JWT_SECRET_KEY={keys['JWT_SECRET_KEY']}
API_SECRET_KEY={keys['API_SECRET_KEY']}

# Authentication Service
AUTH_SERVICE_URL=http://localhost:8001
AUTH_TIMEOUT=30

# Encryption Settings
ENCRYPTION_ALGORITHM=AES-256-GCM
KEY_DERIVATION_ITERATIONS=100000

# Audit Logging
AUDIT_LOG_LEVEL=INFO
AUDIT_RETENTION_DAYS=365

# Performance Settings
CONNECTION_TIMEOUT=30
QUERY_TIMEOUT=300
MAX_CONNECTIONS_PER_USER=10

# Production Settings (if environment=production)
{"SECURE_COOKIES=true" if self.environment == "production" else "# SECURE_COOKIES=false"}
{"HTTPS_ONLY=true" if self.environment == "production" else "# HTTPS_ONLY=false"}
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        logger.info(f"✅ Environment file created: {env_file}")
        logger.warning("🔒 IMPORTANT: Keep your .env file secure and never commit it to version control!")
    
    async def setup_database(self):
        """Create database and user if they don't exist"""
        logger.info("🗄️ Setting up PostgreSQL database...")
        
        try:
            # Connect to postgres database to create our database
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres',  # Default postgres password
                database='postgres'
            )
            
            # Create database if it doesn't exist
            try:
                await conn.execute("""
                    CREATE DATABASE schemasage_enterprise
                    WITH ENCODING='UTF8'
                    LC_COLLATE='en_US.UTF-8'
                    LC_CTYPE='en_US.UTF-8';
                """)
                logger.info("✅ Database 'schemasage_enterprise' created")
            except asyncpg.DuplicateDatabaseError:
                logger.info("ℹ️ Database 'schemasage_enterprise' already exists")
            
            # Create user if it doesn't exist
            try:
                await conn.execute("""
                    CREATE USER schemasage_user WITH PASSWORD 'secure_password';
                """)
                logger.info("✅ User 'schemasage_user' created")
            except asyncpg.DuplicateObjectError:
                logger.info("ℹ️ User 'schemasage_user' already exists")
            
            # Grant privileges
            await conn.execute("""
                GRANT ALL PRIVILEGES ON DATABASE schemasage_enterprise TO schemasage_user;
            """)
            
            await conn.close()
            logger.info("✅ Database setup completed")
            
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            logger.info("📝 Please ensure PostgreSQL is running and accessible")
            return False
        
        return True
    
    def run_migrations(self):
        """Run Alembic migrations to create tables"""
        logger.info("🔄 Running database migrations...")
        
        try:
            alembic_cfg = Config(str(self.project_root / "alembic.ini"))
            command.upgrade(alembic_cfg, "head")
            logger.info("✅ Database migrations completed")
            return True
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    async def validate_setup(self):
        """Validate the enterprise setup"""
        logger.info("✅ Validating enterprise setup...")
        
        try:
            # Test database connection
            conn = await asyncpg.connect(
                "postgresql://schemasage_user:secure_password@localhost:5432/schemasage_enterprise"
            )
            
            # Check if tables exist
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            table_names = [row['table_name'] for row in tables]
            expected_tables = ['connections', 'audit_logs', 'secrets', 'quotas', 'schema_snapshots']
            
            missing_tables = set(expected_tables) - set(table_names)
            if missing_tables:
                logger.error(f"❌ Missing tables: {missing_tables}")
                return False
            
            logger.info(f"✅ All enterprise tables present: {len(table_names)} tables")
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup validation failed: {e}")
            return False
    
    def create_docker_compose(self):
        """Create Docker Compose file for enterprise deployment"""
        docker_compose_content = """version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: schemasage_enterprise
      POSTGRES_USER: schemasage_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U schemasage_user -d schemasage_enterprise"]
      interval: 30s
      timeout: 10s
      retries: 5

  database-migration:
    build: .
    environment:
      - DATABASE_URL=postgresql://schemasage_user:secure_password@postgres:5432/schemasage_enterprise
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads

volumes:
  postgres_data:
"""
        
        with open(self.project_root / "docker-compose.enterprise.yml", 'w') as f:
            f.write(docker_compose_content)
        
        logger.info("✅ Docker Compose file created for enterprise deployment")

async def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup SchemaSage Enterprise")
    parser.add_argument("--env", choices=["development", "production"], 
                       default="development", help="Environment type")
    parser.add_argument("--skip-db", action="store_true", 
                       help="Skip database setup")
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting SchemaSage Enterprise Setup")
    logger.info(f"📍 Environment: {args.env}")
    
    setup = EnterpriseSetup(args.env)
    
    # Generate secure keys
    keys = setup.generate_secure_keys()
    
    # Create environment file
    setup.create_env_file(keys)
    
    # Setup database
    if not args.skip_db:
        db_success = await setup.setup_database()
        if not db_success:
            logger.error("❌ Database setup failed. Please check PostgreSQL installation.")
            sys.exit(1)
        
        # Run migrations
        migration_success = setup.run_migrations()
        if not migration_success:
            logger.error("❌ Migration failed. Please check Alembic configuration.")
            sys.exit(1)
        
        # Validate setup
        validation_success = await setup.validate_setup()
        if not validation_success:
            logger.error("❌ Setup validation failed.")
            sys.exit(1)
    
    # Create Docker Compose
    setup.create_docker_compose()
    
    logger.info("")
    logger.info("🎉 Enterprise Setup Complete!")
    logger.info("")
    logger.info("📋 Next Steps:")
    logger.info("1. Review the generated .env file")
    logger.info("2. Start the service: python main.py")
    logger.info("3. Test enterprise endpoints at http://localhost:8000/docs")
    logger.info("4. For production: docker-compose -f docker-compose.enterprise.yml up")
    logger.info("")
    logger.info("🔑 Security Notes:")
    logger.info("- Keep your .env file secure")
    logger.info("- Use strong database passwords in production")
    logger.info("- Enable SSL/TLS for production deployments")
    logger.info("- Regularly rotate encryption keys")

if __name__ == "__main__":
    asyncio.run(main())