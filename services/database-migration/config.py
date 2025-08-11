"""
Database Migration Service Configuration
"""
import os
from typing import Dict, Any, Optional

# Service Configuration
SERVICE_NAME = "database-migration"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("PORT", 8005))

# Database Connection Settings
MAX_CONNECTIONS_PER_POOL = 10
CONNECTION_TIMEOUT = 30
QUERY_TIMEOUT = 300

# Supported Database Types
SUPPORTED_DATABASES = {
    "mysql": {
        "driver": "pymysql",
        "default_port": 3306,
        "ssl_support": True
    },
    "postgresql": {
        "driver": "psycopg2",
        "default_port": 5432,
        "ssl_support": True
    },
    "sqlite": {
        "driver": "sqlite3",
        "default_port": None,
        "ssl_support": False
    },
    "mongodb": {
        "driver": "pymongo",
        "default_port": 27017,
        "ssl_support": True
    },
    "sqlserver": {
        "driver": "pyodbc",
        "default_port": 1433,
        "ssl_support": True
    },
    "oracle": {
        "driver": "cx_Oracle",
        "default_port": 1521,
        "ssl_support": True
    }
}

# AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_MODEL_TEMPERATURE = 0.1  # Low temperature for consistent technical responses

# Migration Settings
MAX_MIGRATION_STEPS = 1000
MIGRATION_BATCH_SIZE = 100
ROLLBACK_STRATEGY_ENABLED = True

# Risk Assessment Thresholds
RISK_THRESHOLDS = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8,
    "critical": 0.95
}

# Performance Monitoring
ENABLE_METRICS = True
METRICS_PORT = 9090

def get_database_config(db_type: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific database type."""
    return SUPPORTED_DATABASES.get(db_type.lower())

def validate_config() -> bool:
    """Validate service configuration."""
    required_env_vars = []
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return True
