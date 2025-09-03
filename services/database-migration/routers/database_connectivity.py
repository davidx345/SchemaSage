"""
Database Connectivity API Routes
Provides database connection testing and schema import functionality
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
import uuid
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["Database Connectivity"])

# Mock connection configurations for different database types
supported_databases = {
    "postgresql": {
        "name": "PostgreSQL",
        "default_port": 5432,
        "connection_string_format": "postgresql://user:password@host:port/database",
        "supported_versions": ["12", "13", "14", "15", "16"],
        "features": ["schemas", "foreign_keys", "triggers", "functions", "views"]
    },
    "mysql": {
        "name": "MySQL",
        "default_port": 3306,
        "connection_string_format": "mysql://user:password@host:port/database",
        "supported_versions": ["5.7", "8.0", "8.1"],
        "features": ["foreign_keys", "triggers", "functions", "views"]
    },
    "sqlite": {
        "name": "SQLite",
        "default_port": None,
        "connection_string_format": "sqlite:///path/to/database.db",
        "supported_versions": ["3.36", "3.37", "3.38", "3.39"],
        "features": ["foreign_keys", "triggers", "views"]
    },
    "oracle": {
        "name": "Oracle Database",
        "default_port": 1521,
        "connection_string_format": "oracle://user:password@host:port/service_name",
        "supported_versions": ["12c", "18c", "19c", "21c"],
        "features": ["schemas", "foreign_keys", "triggers", "functions", "views", "packages"]
    },
    "sqlserver": {
        "name": "Microsoft SQL Server",
        "default_port": 1433,
        "connection_string_format": "mssql://user:password@host:port/database",
        "supported_versions": ["2017", "2019", "2022"],
        "features": ["schemas", "foreign_keys", "triggers", "functions", "views", "procedures"]
    },
    "mongodb": {
        "name": "MongoDB",
        "default_port": 27017,
        "connection_string_format": "mongodb://user:password@host:port/database",
        "supported_versions": ["5.0", "6.0", "7.0"],
        "features": ["collections", "indexes", "aggregation_pipelines"]
    }
}

# Mock connection test results
connection_test_history = []

def generate_mock_schema_info(db_type: str) -> Dict[str, Any]:
    """Generate mock schema information for different database types"""
    
    if db_type in ["postgresql", "oracle", "sqlserver"]:
        # SQL databases with schema support
        schemas = []
        for i in range(random.randint(2, 6)):
            schema_name = random.choice(["public", "users", "products", "orders", "analytics", "reporting"])
            if schema_name not in [s["name"] for s in schemas]:
                tables = []
                for j in range(random.randint(3, 12)):
                    table_name = random.choice([
                        "users", "products", "orders", "categories", "reviews", 
                        "payments", "inventory", "customers", "suppliers", "transactions"
                    ])
                    if table_name not in [t["name"] for t in tables]:
                        columns = []
                        for k in range(random.randint(3, 10)):
                            col_name = random.choice([
                                "id", "name", "email", "created_at", "updated_at", 
                                "status", "price", "quantity", "description", "category_id"
                            ])
                            if col_name not in [c["name"] for c in columns]:
                                columns.append({
                                    "name": col_name,
                                    "type": random.choice(["integer", "varchar", "text", "timestamp", "decimal", "boolean"]),
                                    "nullable": random.choice([True, False]),
                                    "primary_key": col_name == "id",
                                    "foreign_key": col_name.endswith("_id") and col_name != "id"
                                })
                        
                        tables.append({
                            "name": table_name,
                            "columns": columns,
                            "row_count": random.randint(100, 100000),
                            "size_mb": random.randint(1, 500)
                        })
                
                schemas.append({
                    "name": schema_name,
                    "tables": tables,
                    "table_count": len(tables)
                })
        
        return {
            "database_type": db_type,
            "schemas": schemas,
            "total_tables": sum(s["table_count"] for s in schemas),
            "total_columns": sum(len(t["columns"]) for s in schemas for t in s["tables"]),
            "supports_schemas": True
        }
    
    elif db_type == "mysql":
        # MySQL - no schema support, just databases
        tables = []
        for i in range(random.randint(5, 15)):
            table_name = random.choice([
                "users", "products", "orders", "categories", "reviews", 
                "payments", "inventory", "customers", "suppliers", "transactions"
            ])
            if table_name not in [t["name"] for t in tables]:
                columns = []
                for j in range(random.randint(3, 10)):
                    col_name = random.choice([
                        "id", "name", "email", "created_at", "updated_at", 
                        "status", "price", "quantity", "description", "category_id"
                    ])
                    if col_name not in [c["name"] for c in columns]:
                        columns.append({
                            "name": col_name,
                            "type": random.choice(["int", "varchar", "text", "datetime", "decimal", "tinyint"]),
                            "nullable": random.choice([True, False]),
                            "primary_key": col_name == "id",
                            "foreign_key": col_name.endswith("_id") and col_name != "id"
                        })
                
                tables.append({
                    "name": table_name,
                    "columns": columns,
                    "row_count": random.randint(100, 100000),
                    "size_mb": random.randint(1, 500)
                })
        
        return {
            "database_type": db_type,
            "tables": tables,
            "total_tables": len(tables),
            "total_columns": sum(len(t["columns"]) for t in tables),
            "supports_schemas": False
        }
    
    elif db_type == "mongodb":
        # MongoDB - collections instead of tables
        collections = []
        for i in range(random.randint(4, 10)):
            collection_name = random.choice([
                "users", "products", "orders", "categories", "reviews", 
                "sessions", "logs", "analytics", "configurations", "notifications"
            ])
            if collection_name not in [c["name"] for c in collections]:
                # Sample documents to infer schema
                sample_docs = []
                for j in range(3):  # Generate 3 sample documents
                    doc = {
                        "_id": str(uuid.uuid4()),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Add collection-specific fields
                    if collection_name == "users":
                        doc.update({
                            "email": f"user{j}@example.com",
                            "name": f"User {j}",
                            "active": random.choice([True, False])
                        })
                    elif collection_name == "products":
                        doc.update({
                            "name": f"Product {j}",
                            "price": random.uniform(10, 1000),
                            "category": random.choice(["electronics", "clothing", "books"])
                        })
                    # Add more fields based on collection type...
                    
                    sample_docs.append(doc)
                
                collections.append({
                    "name": collection_name,
                    "document_count": random.randint(100, 50000),
                    "size_mb": random.randint(1, 200),
                    "sample_documents": sample_docs,
                    "indexes": [
                        {"fields": ["_id"], "unique": True},
                        {"fields": ["created_at"], "unique": False}
                    ]
                })
        
        return {
            "database_type": db_type,
            "collections": collections,
            "total_collections": len(collections),
            "total_documents": sum(c["document_count"] for c in collections),
            "supports_schemas": False
        }
    
    else:
        return {
            "database_type": db_type,
            "error": "Unsupported database type for schema introspection"
        }

@router.get("/supported")
async def get_supported_databases():
    """Get list of supported database types and their configurations"""
    try:
        logger.info("Getting supported database types")
        
        return {
            "supported_databases": supported_databases,
            "total_supported": len(supported_databases),
            "categories": {
                "sql_databases": ["postgresql", "mysql", "oracle", "sqlserver", "sqlite"],
                "nosql_databases": ["mongodb"],
                "cloud_databases": ["postgresql", "mysql", "oracle", "sqlserver", "mongodb"],
                "on_premise_databases": ["postgresql", "mysql", "oracle", "sqlserver", "sqlite", "mongodb"]
            },
            "connection_requirements": {
                "sql_databases": ["host", "port", "username", "password", "database_name"],
                "sqlite": ["file_path"],
                "mongodb": ["host", "port", "username", "password", "database_name", "auth_database"]
            },
            "security_features": [
                "SSL/TLS encryption support",
                "Connection string encryption",
                "Password hashing",
                "Connection timeout configuration",
                "IP whitelist support"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting supported databases: {e}")
        raise HTTPException(status_code=500, detail="Failed to get supported databases")

@router.post("/connect/test")
async def test_database_connection(connection_config: Dict[str, Any]):
    """Test database connection with provided configuration"""
    try:
        db_type = connection_config.get("database_type")
        host = connection_config.get("host")
        port = connection_config.get("port")
        username = connection_config.get("username")
        database_name = connection_config.get("database_name")
        
        logger.info(f"Testing connection to {db_type} database at {host}:{port}")
        
        # Validate required fields
        if not db_type or db_type not in supported_databases:
            raise HTTPException(status_code=400, detail="Invalid or unsupported database type")
        
        # Simulate connection test with some realistic delays and results
        test_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Simulate connection attempt
        await asyncio.sleep(random.uniform(0.5, 2.0))  # Realistic connection time
        
        # Simulate success/failure (90% success rate for demo)
        connection_successful = random.random() < 0.9
        
        if connection_successful:
            # Generate mock connection details
            connection_details = {
                "server_version": random.choice(supported_databases[db_type]["supported_versions"]),
                "server_info": f"{supported_databases[db_type]['name']} Server",
                "connection_time_ms": random.randint(50, 500),
                "max_connections": random.randint(100, 1000),
                "current_connections": random.randint(5, 50),
                "database_size_mb": random.randint(100, 10000),
                "uptime_hours": random.randint(24, 8760),  # 1 day to 1 year
                "charset": "UTF-8" if db_type != "mongodb" else None,
                "timezone": "UTC"
            }
            
            # Database-specific details
            if db_type == "postgresql":
                connection_details.update({
                    "postgres_version": connection_details["server_version"],
                    "available_extensions": ["pg_stat_statements", "uuid-ossp", "postgis"]
                })
            elif db_type == "mongodb":
                connection_details.update({
                    "replica_set": "rs0",
                    "shard_count": random.randint(1, 5),
                    "storage_engine": "WiredTiger"
                })
            
            test_result = {
                "test_id": test_id,
                "status": "success",
                "message": "Connection successful",
                "connection_details": connection_details,
                "test_duration_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "tested_at": start_time.isoformat(),
                "capabilities": supported_databases[db_type]["features"]
            }
        else:
            # Simulate connection failure
            error_messages = [
                "Connection timeout - unable to reach database server",
                "Authentication failed - invalid username or password",
                "Database does not exist or access denied",
                "Network error - host unreachable",
                "SSL connection required but not configured"
            ]
            
            test_result = {
                "test_id": test_id,
                "status": "failed",
                "message": "Connection failed",
                "error": random.choice(error_messages),
                "error_code": random.choice(["CONN_TIMEOUT", "AUTH_FAILED", "DB_NOT_FOUND", "NETWORK_ERROR", "SSL_REQUIRED"]),
                "test_duration_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "tested_at": start_time.isoformat(),
                "troubleshooting_tips": [
                    "Verify database server is running and accessible",
                    "Check firewall settings and network connectivity",
                    "Confirm username and password are correct",
                    "Ensure database name exists and user has access",
                    "Check SSL/TLS configuration if required"
                ]
            }
        
        # Store test result in history
        connection_test_history.append(test_result)
        
        # Keep only last 100 test results
        if len(connection_test_history) > 100:
            connection_test_history.pop(0)
        
        return test_result
        
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to test database connection")

@router.get("/connect/history")
async def get_connection_test_history(limit: int = 20):
    """Get history of database connection tests"""
    try:
        logger.info(f"Getting connection test history (limit: {limit})")
        
        # Return most recent tests first
        recent_tests = sorted(connection_test_history, 
                            key=lambda x: x["tested_at"], 
                            reverse=True)[:limit]
        
        # Calculate statistics
        total_tests = len(connection_test_history)
        successful_tests = len([t for t in connection_test_history if t["status"] == "success"])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group by database type
        tests_by_db_type = {}
        for test in connection_test_history:
            # Extract db_type from connection details or set to "unknown"
            db_type = "unknown"  # In real implementation, store this info
            if db_type not in tests_by_db_type:
                tests_by_db_type[db_type] = {"total": 0, "successful": 0, "failed": 0}
            
            tests_by_db_type[db_type]["total"] += 1
            if test["status"] == "success":
                tests_by_db_type[db_type]["successful"] += 1
            else:
                tests_by_db_type[db_type]["failed"] += 1
        
        return {
            "recent_tests": recent_tests,
            "statistics": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate_percentage": round(success_rate, 2),
                "tests_by_database_type": tests_by_db_type
            },
            "common_errors": [
                {"error": "Connection timeout", "count": 12, "percentage": 35.3},
                {"error": "Authentication failed", "count": 8, "percentage": 23.5},
                {"error": "Database not found", "count": 7, "percentage": 20.6},
                {"error": "Network error", "count": 4, "percentage": 11.8},
                {"error": "SSL required", "count": 3, "percentage": 8.8}
            ],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_available": len(connection_test_history),
                "returned_count": len(recent_tests)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting connection test history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get connection test history")

@router.post("/import/schema")
async def import_database_schema(
    background_tasks: BackgroundTasks,
    import_config: Dict[str, Any]
):
    """Import schema from an existing database"""
    try:
        db_type = import_config.get("database_type")
        connection_config = import_config.get("connection_config", {})
        import_options = import_config.get("import_options", {})
        
        logger.info(f"Starting schema import from {db_type} database")
        
        # Validate database type
        if not db_type or db_type not in supported_databases:
            raise HTTPException(status_code=400, detail="Invalid or unsupported database type")
        
        # Generate import job ID
        import_job_id = str(uuid.uuid4())
        
        # Create import job record
        import_job = {
            "job_id": import_job_id,
            "status": "in_progress",
            "database_type": db_type,
            "started_at": datetime.now().isoformat(),
            "progress_percentage": 0,
            "current_step": "connecting_to_database",
            "total_steps": 5,
            "completed_steps": 0,
            "estimated_duration_minutes": random.randint(5, 30),
            "import_options": import_options
        }
        
        # Start background import process
        background_tasks.add_task(process_schema_import, import_job_id, db_type, connection_config, import_options)
        
        return {
            "import_job": import_job,
            "message": "Schema import started successfully",
            "estimated_completion": (datetime.now() + 
                                   timedelta(minutes=import_job["estimated_duration_minutes"])).isoformat(),
            "status_endpoint": f"/api/database/import/{import_job_id}/status",
            "cancel_endpoint": f"/api/database/import/{import_job_id}/cancel"
        }
        
    except Exception as e:
        logger.error(f"Error starting schema import: {e}")
        raise HTTPException(status_code=500, detail="Failed to start schema import")

# Mock import jobs storage
import_jobs = {}

async def process_schema_import(job_id: str, db_type: str, connection_config: Dict, import_options: Dict):
    """Background task to process schema import"""
    try:
        # Update job status
        import_jobs[job_id] = {
            "job_id": job_id,
            "status": "in_progress",
            "database_type": db_type,
            "started_at": datetime.now().isoformat(),
            "progress_percentage": 0,
            "current_step": "connecting_to_database",
            "steps": [
                {"name": "connecting_to_database", "status": "in_progress", "started_at": datetime.now().isoformat()},
                {"name": "discovering_schemas", "status": "pending"},
                {"name": "extracting_tables", "status": "pending"},
                {"name": "analyzing_relationships", "status": "pending"},
                {"name": "generating_metadata", "status": "pending"}
            ],
            "imported_objects": {
                "schemas": 0,
                "tables": 0,
                "columns": 0,
                "indexes": 0,
                "foreign_keys": 0,
                "views": 0,
                "procedures": 0
            }
        }
        
        steps = [
            ("connecting_to_database", 2),
            ("discovering_schemas", 3),
            ("extracting_tables", 4),
            ("analyzing_relationships", 2),
            ("generating_metadata", 1)
        ]
        
        total_work = sum(duration for _, duration in steps)
        completed_work = 0
        
        for step_name, duration in steps:
            # Update current step
            job = import_jobs[job_id]
            job["current_step"] = step_name
            
            # Update step status
            for step in job["steps"]:
                if step["name"] == step_name:
                    step["status"] = "in_progress"
                    step["started_at"] = datetime.now().isoformat()
                    break
            
            # Simulate work with progress updates
            for i in range(duration):
                await asyncio.sleep(1)  # Simulate work
                completed_work += 1
                progress = (completed_work / total_work) * 100
                job["progress_percentage"] = round(progress, 1)
                
                # Update imported objects count during extraction steps
                if step_name == "extracting_tables":
                    job["imported_objects"]["tables"] = i * 3
                    job["imported_objects"]["columns"] = i * 15
                elif step_name == "analyzing_relationships":
                    job["imported_objects"]["foreign_keys"] = i * 2
                    job["imported_objects"]["indexes"] = i * 5
            
            # Mark step as completed
            for step in job["steps"]:
                if step["name"] == step_name:
                    step["status"] = "completed"
                    step["completed_at"] = datetime.now().isoformat()
                    break
        
        # Generate final schema information
        schema_info = generate_mock_schema_info(db_type)
        
        # Mark job as completed
        job = import_jobs[job_id]
        job.update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "progress_percentage": 100,
            "current_step": "completed",
            "schema_info": schema_info,
            "imported_objects": {
                "schemas": len(schema_info.get("schemas", [])) if "schemas" in schema_info else 0,
                "tables": schema_info.get("total_tables", len(schema_info.get("tables", []))),
                "columns": schema_info.get("total_columns", 0),
                "indexes": random.randint(20, 100),
                "foreign_keys": random.randint(15, 80),
                "views": random.randint(3, 25),
                "procedures": random.randint(0, 15) if db_type in ["postgresql", "sqlserver", "oracle"] else 0
            },
            "import_summary": {
                "total_duration_seconds": 12,
                "objects_per_second": round((schema_info.get("total_tables", 0) + schema_info.get("total_columns", 0)) / 12, 2),
                "data_size_analyzed_mb": random.randint(100, 5000),
                "warnings": [],
                "errors": []
            }
        })
        
        logger.info(f"Schema import job {job_id} completed successfully")
        
    except Exception as e:
        # Mark job as failed
        import_jobs[job_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e),
            "error_details": {
                "error_type": "import_error",
                "step_failed": import_jobs[job_id]["current_step"],
                "troubleshooting_tips": [
                    "Verify database connection is still active",
                    "Check if user has sufficient permissions",
                    "Ensure database is not under heavy load",
                    "Try importing smaller subset of objects"
                ]
            }
        })
        logger.error(f"Schema import job {job_id} failed: {e}")

@router.get("/import/{job_id}/status")
async def get_import_job_status(job_id: str):
    """Get status of a schema import job"""
    try:
        logger.info(f"Getting status for import job: {job_id}")
        
        if job_id not in import_jobs:
            raise HTTPException(status_code=404, detail="Import job not found")
        
        job = import_jobs[job_id]
        
        # Calculate additional metrics
        if job["status"] == "in_progress":
            started_at = datetime.fromisoformat(job["started_at"])
            elapsed_seconds = (datetime.now() - started_at).total_seconds()
            
            if job["progress_percentage"] > 0:
                estimated_total_seconds = elapsed_seconds / (job["progress_percentage"] / 100)
                remaining_seconds = estimated_total_seconds - elapsed_seconds
                estimated_completion = (datetime.now() + timedelta(seconds=remaining_seconds)).isoformat()
            else:
                estimated_completion = None
            
            job["runtime_info"] = {
                "elapsed_seconds": round(elapsed_seconds, 1),
                "estimated_completion": estimated_completion,
                "estimated_remaining_seconds": round(remaining_seconds, 1) if 'remaining_seconds' in locals() else None
            }
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import job status")

@router.post("/import/{job_id}/cancel")
async def cancel_import_job(job_id: str):
    """Cancel a running schema import job"""
    try:
        logger.info(f"Cancelling import job: {job_id}")
        
        if job_id not in import_jobs:
            raise HTTPException(status_code=404, detail="Import job not found")
        
        job = import_jobs[job_id]
        
        if job["status"] not in ["in_progress", "pending"]:
            raise HTTPException(status_code=400, detail="Cannot cancel job that is not in progress")
        
        # Update job status
        job.update({
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "cancel_reason": "User requested cancellation"
        })
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Import job cancelled successfully",
            "cancelled_at": job["cancelled_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling import job: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel import job")

@router.get("/import/jobs")
async def get_import_jobs(
    status: Optional[str] = None,
    limit: int = 20
):
    """Get list of schema import jobs"""
    try:
        logger.info(f"Getting import jobs with status filter: {status}")
        
        jobs = list(import_jobs.values())
        
        # Filter by status if provided
        if status:
            jobs = [job for job in jobs if job["status"] == status]
        
        # Sort by started_at (newest first)
        jobs.sort(key=lambda x: x["started_at"], reverse=True)
        
        # Apply limit
        jobs = jobs[:limit]
        
        # Calculate statistics
        all_jobs = list(import_jobs.values())
        stats = {
            "total_jobs": len(all_jobs),
            "completed_jobs": len([j for j in all_jobs if j["status"] == "completed"]),
            "failed_jobs": len([j for j in all_jobs if j["status"] == "failed"]),
            "in_progress_jobs": len([j for j in all_jobs if j["status"] == "in_progress"]),
            "cancelled_jobs": len([j for j in all_jobs if j["status"] == "cancelled"])
        }
        
        if stats["total_jobs"] > 0:
            stats["success_rate_percentage"] = round((stats["completed_jobs"] / stats["total_jobs"]) * 100, 2)
        else:
            stats["success_rate_percentage"] = 0
        
        return {
            "jobs": jobs,
            "statistics": stats,
            "filters_applied": {
                "status": status,
                "limit": limit
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_available": len(all_jobs),
                "returned_count": len(jobs)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting import jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import jobs")

@router.get("/schemas/{schema_id}/export")
async def export_schema_definition(
    schema_id: str,
    format: str = "json",
    include_data: bool = False
):
    """Export schema definition in various formats"""
    try:
        logger.info(f"Exporting schema {schema_id} in {format} format")
        
        # Generate mock schema data
        schema_data = {
            "schema_id": schema_id,
            "name": f"Exported Schema {schema_id}",
            "database_type": "postgresql",
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "integer", "primary_key": True, "nullable": False},
                        {"name": "email", "type": "varchar(255)", "primary_key": False, "nullable": False},
                        {"name": "name", "type": "varchar(100)", "primary_key": False, "nullable": True},
                        {"name": "created_at", "type": "timestamp", "primary_key": False, "nullable": False}
                    ],
                    "indexes": [
                        {"name": "idx_users_email", "columns": ["email"], "unique": True},
                        {"name": "idx_users_created_at", "columns": ["created_at"], "unique": False}
                    ],
                    "constraints": [
                        {"name": "pk_users", "type": "PRIMARY KEY", "columns": ["id"]},
                        {"name": "uk_users_email", "type": "UNIQUE", "columns": ["email"]}
                    ]
                }
            ],
            "relationships": [
                {
                    "name": "fk_orders_user_id",
                    "from_table": "orders",
                    "from_column": "user_id",
                    "to_table": "users",
                    "to_column": "id",
                    "on_delete": "CASCADE",
                    "on_update": "RESTRICT"
                }
            ]
        }
        
        # Include sample data if requested
        if include_data:
            schema_data["sample_data"] = {
                "users": [
                    {"id": 1, "email": "john@example.com", "name": "John Doe", "created_at": "2023-01-15T10:00:00Z"},
                    {"id": 2, "email": "jane@example.com", "name": "Jane Smith", "created_at": "2023-01-16T11:30:00Z"}
                ]
            }
        
        # Format-specific export
        if format == "json":
            export_content = schema_data
            content_type = "application/json"
            file_extension = "json"
        
        elif format == "sql":
            # Generate SQL DDL
            sql_statements = [
                "-- Exported Schema Definition",
                f"-- Generated on: {datetime.now().isoformat()}",
                "",
                "CREATE TABLE users (",
                "    id INTEGER PRIMARY KEY NOT NULL,",
                "    email VARCHAR(255) NOT NULL,",
                "    name VARCHAR(100),",
                "    created_at TIMESTAMP NOT NULL",
                ");",
                "",
                "CREATE UNIQUE INDEX idx_users_email ON users(email);",
                "CREATE INDEX idx_users_created_at ON users(created_at);",
                "",
                "-- End of schema definition"
            ]
            
            export_content = {"sql_content": "\n".join(sql_statements)}
            content_type = "text/sql"
            file_extension = "sql"
        
        elif format == "yaml":
            # Generate YAML representation
            yaml_content = f"""# Schema Definition
schema_id: {schema_id}
name: Exported Schema {schema_id}
database_type: postgresql
exported_at: {datetime.now().isoformat()}
version: "1.0"

tables:
  - name: users
    columns:
      - name: id
        type: integer
        primary_key: true
        nullable: false
      - name: email
        type: varchar(255)
        nullable: false
      - name: name
        type: varchar(100)
        nullable: true
      - name: created_at
        type: timestamp
        nullable: false
    
    indexes:
      - name: idx_users_email
        columns: [email]
        unique: true
      - name: idx_users_created_at
        columns: [created_at]
        unique: false

relationships:
  - name: fk_orders_user_id
    from_table: orders
    from_column: user_id
    to_table: users
    to_column: id
    on_delete: CASCADE
    on_update: RESTRICT
"""
            
            export_content = {"yaml_content": yaml_content}
            content_type = "text/yaml"
            file_extension = "yaml"
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        return {
            "schema_id": schema_id,
            "export_format": format,
            "content_type": content_type,
            "file_extension": file_extension,
            "exported_at": datetime.now().isoformat(),
            "include_data": include_data,
            "content": export_content,
            "metadata": {
                "total_tables": len(schema_data["tables"]),
                "total_relationships": len(schema_data["relationships"]),
                "export_size_bytes": len(str(export_content)),
                "supported_formats": ["json", "sql", "yaml"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting schema: {e}")
        raise HTTPException(status_code=500, detail="Failed to export schema")
