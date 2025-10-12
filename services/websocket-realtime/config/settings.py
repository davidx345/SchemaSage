"""
Configuration settings for WebSocket service
"""
import os

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_jwt_secret_key_not_for_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Service URLs
SCHEMA_SERVICE_URL = os.getenv("SCHEMA_DETECTION_SERVICE_URL", "https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com")
PROJECT_SERVICE_URL = os.getenv("PROJECT_MANAGEMENT_SERVICE_URL", "https://schemasage-project-management-48496f02644b.herokuapp.com")
CODE_SERVICE_URL = os.getenv("CODE_GENERATION_SERVICE_URL", "https://schemasage-code-generation-56faa300323b.herokuapp.com")
AUTH_SERVICE_URL = os.getenv("AUTHENTICATION_SERVICE_URL", "https://schemasage-auth-9d6de1a32af9.herokuapp.com")
DATABASE_MIGRATION_SERVICE_URL = os.getenv("DATABASE_MIGRATION_SERVICE_URL", "https://schemasage-database-migration-b8c3d2e1f4a5.herokuapp.com")

# CORS Origins - Allow your frontend
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://schemasage.vercel.app,http://localhost:3000").split(",")

# WebSocket Configuration
STATS_UPDATE_INTERVAL = int(os.getenv("STATS_UPDATE_INTERVAL", "60"))  # seconds