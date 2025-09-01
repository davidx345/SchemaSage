"""
Basic API Endpoints Router (Simplified)
Root and health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime

# Simplified supported databases list
SUPPORTED_DATABASES = {
    "postgresql": "PostgreSQL",
    "mysql": "MySQL", 
    "mongodb": "MongoDB",
    "sqlserver": "SQL Server",
    "oracle": "Oracle"
}

router = APIRouter()

@router.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Database Migration Service - Enterprise Edition",
        "version": "1.0.0",
        "supported_databases": list(SUPPORTED_DATABASES.keys()),
        "features": [
            "Multi-database migration",
            "AI-powered intelligence",
            "Team collaboration",
            "Version control integration", 
            "CI/CD automation",
            "Enterprise security",
            "Audit logging",
            # Phase 4: Advanced Features
            "ETL Pipeline Engine",
            "Performance Optimization",
            "Natural Language to SQL",
            "AI-Powered Schema Optimization",
            "Real-time Monitoring & Alerting",
            "Automated Documentation Generation",
            "Health Check System",
            "Advanced Analytics & Reporting"
        ],
        "phase_4_features": {
            "etl_engine": "Advanced data migration and transformation pipelines",
            "performance_optimization": "Query analysis, index recommendations, performance monitoring",
            "ai_features": "Natural language processing, intelligent optimization suggestions",
            "monitoring_alerting": "Real-time monitoring, alerting, and health checks"
        },
        "status": "healthy"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/databases/supported")
async def get_supported_databases():
    """Get list of supported database types."""
    return {
        "supported_databases": SUPPORTED_DATABASES,
        "total_count": len(SUPPORTED_DATABASES)
    }
