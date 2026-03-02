"""
Query Generation and Execution API Routes

Routes for generating and executing SQL queries from natural language or schema.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import sqlparse
import json

from models.schemas import SchemaResponse

logger = logging.getLogger(__name__)

# Router for query endpoints
router = APIRouter(prefix="/query", tags=["query"])


@router.post("/generate")
async def generate_sql_query(
    description: str,
    schema_context: Optional[Dict[str, Any]] = None,
    database_type: str = "postgresql",
    include_explanation: bool = True
):
    """Generate SQL queries from natural language description"""
    try:
        # Mock SQL query generation based on description
        generated_queries = []
        
        description_lower = description.lower()
        
        # Simple pattern matching for demo
        if "users" in description_lower and "active" in description_lower:
            query = {
                "sql": "SELECT * FROM users WHERE status = 'active';",
                "type": "SELECT",
                "tables": ["users"],
                "columns": ["*"],
                "conditions": ["status = 'active'"],
                "explanation": "Retrieves all active users from the users table"
            }
            generated_queries.append(query)
        
        if "orders" in description_lower and "today" in description_lower:
            query = {
                "sql": "SELECT * FROM orders WHERE DATE(created_at) = CURRENT_DATE;",
                "type": "SELECT", 
                "tables": ["orders"],
                "columns": ["*"],
                "conditions": ["DATE(created_at) = CURRENT_DATE"],
                "explanation": "Retrieves all orders created today"
            }
            generated_queries.append(query)
        
        if "count" in description_lower and "users" in description_lower:
            query = {
                "sql": "SELECT COUNT(*) as user_count FROM users;",
                "type": "SELECT",
                "tables": ["users"],
                "columns": ["COUNT(*)"],
                "conditions": [],
                "explanation": "Counts the total number of users"
            }
            generated_queries.append(query)
        
        if "join" in description_lower or "user" in description_lower and "order" in description_lower:
            query = {
                "sql": """SELECT u.username, o.id as order_id, o.total 
                         FROM users u 
                         JOIN orders o ON u.id = o.user_id;""",
                "type": "SELECT",
                "tables": ["users", "orders"],
                "columns": ["u.username", "o.id", "o.total"],
                "conditions": ["u.id = o.user_id"],
                "explanation": "Joins users with their orders to show username, order ID, and total"
            }
            generated_queries.append(query)
        
        # If no patterns match, generate a generic query
        if not generated_queries:
            query = {
                "sql": f"-- Query for: {description}\\nSELECT * FROM table_name;",
                "type": "SELECT",
                "tables": ["table_name"],
                "columns": ["*"],
                "conditions": [],
                "explanation": f"Generated placeholder query for: {description}"
            }
            generated_queries.append(query)
        
        return {
            "description": description,
            "database_type": database_type,
            "generated_queries": generated_queries,
            "schema_context": schema_context,
            "include_explanation": include_explanation,
            "generation_time_ms": 120,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate SQL query")


@router.post("/execute")
async def execute_query(
    sql: str,
    database_connection: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    limit: int = Query(default=100, le=1000)
):
    """Execute generated SQL queries (mock implementation)"""
    try:
        # Parse the SQL query
        try:
            parsed = sqlparse.parse(sql)[0]
            query_type = parsed.get_type()
        except:
            query_type = "UNKNOWN"
        
        # Mock execution results
        if dry_run:
            return {
                "sql": sql,
                "query_type": query_type,
                "dry_run": True,
                "validation": {
                    "is_valid": True,
                    "syntax_errors": [],
                    "warnings": []
                },
                "estimated_rows": 150,
                "estimated_execution_time_ms": 45,
                "timestamp": datetime.now().isoformat()
            }
        
        # Mock actual execution
        mock_results = []
        
        if "users" in sql.lower():
            mock_results = [
                {"id": 1, "username": "john_doe", "email": "john@example.com", "status": "active"},
                {"id": 2, "username": "jane_smith", "email": "jane@example.com", "status": "active"},
                {"id": 3, "username": "bob_johnson", "email": "bob@example.com", "status": "inactive"}
            ]
        
        elif "orders" in sql.lower():
            mock_results = [
                {"id": 101, "user_id": 1, "total": 99.99, "status": "completed", "created_at": "2024-01-15T10:30:00Z"},
                {"id": 102, "user_id": 2, "total": 149.50, "status": "pending", "created_at": "2024-01-15T11:15:00Z"}
            ]
        
        elif "count" in sql.lower():
            mock_results = [{"count": 1250}]
        
        else:
            mock_results = [{"message": "Query executed successfully"}]
        
        # Apply limit
        if len(mock_results) > limit:
            mock_results = mock_results[:limit]
            has_more = True
        else:
            has_more = False
        
        return {
            "sql": sql,
            "query_type": query_type,
            "dry_run": False,
            "execution_status": "success",
            "results": mock_results,
            "row_count": len(mock_results),
            "has_more": has_more,
            "execution_time_ms": 67,
            "database_connection": database_connection is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute SQL query")


@router.post("/validate")
async def validate_query(
    sql: str,
    database_type: str = "postgresql",
    schema_context: Optional[Dict[str, Any]] = None
):
    """Validate SQL query syntax and structure"""
    try:
        # Parse and validate SQL
        errors = []
        warnings = []
        
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                errors.append("Empty or invalid SQL statement")
            else:
                query_type = parsed[0].get_type()
                
                # Basic validation checks
                if query_type == "UNKNOWN":
                    warnings.append("Could not determine query type")
                
                # Check for potential issues
                if "SELECT *" in sql.upper():
                    warnings.append("Using SELECT * may impact performance")
                
                if "WHERE" not in sql.upper() and query_type == "SELECT":
                    warnings.append("Query has no WHERE clause - may return large result set")
                
        except Exception as parse_error:
            errors.append(f"SQL parsing error: {str(parse_error)}")
        
        is_valid = len(errors) == 0
        
        return {
            "sql": sql,
            "database_type": database_type,
            "is_valid": is_valid,
            "query_type": query_type if 'query_type' in locals() else "UNKNOWN",
            "syntax_errors": errors,
            "warnings": warnings,
            "schema_context": schema_context,
            "validation_time_ms": 25,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query validation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate SQL query")


@router.post("/optimize")
async def optimize_query(
    sql: str,
    database_type: str = "postgresql",
    optimization_level: str = Query(default="standard", regex="^(basic|standard|aggressive)$")
):
    """Optimize SQL query for better performance"""
    try:
        # Mock query optimization
        optimizations = []
        optimized_sql = sql
        
        # Simple optimization suggestions
        if "SELECT *" in sql.upper():
            optimizations.append({
                "type": "column_selection",
                "description": "Replace SELECT * with specific column names",
                "impact": "medium",
                "suggestion": "Specify only needed columns to reduce data transfer"
            })
        
        if "WHERE" not in sql.upper() and "SELECT" in sql.upper():
            optimizations.append({
                "type": "filtering", 
                "description": "Add WHERE clause to filter results",
                "impact": "high",
                "suggestion": "Add appropriate WHERE conditions to limit result set"
            })
        
        if "ORDER BY" in sql.upper() and "LIMIT" not in sql.upper():
            optimizations.append({
                "type": "pagination",
                "description": "Consider adding LIMIT clause",
                "impact": "medium", 
                "suggestion": "Add LIMIT to prevent large result sets"
            })
        
        # Mock optimized query
        if optimization_level in ["standard", "aggressive"]:
            optimized_sql = sql.replace("SELECT *", "SELECT id, name, status")
            if "WHERE" not in sql.upper():
                optimized_sql += " WHERE status = 'active'"
            if "LIMIT" not in sql.upper():
                optimized_sql += " LIMIT 100"
        
        return {
            "original_sql": sql,
            "optimized_sql": optimized_sql,
            "database_type": database_type,
            "optimization_level": optimization_level,
            "optimizations": optimizations,
            "estimated_improvement": "25% faster execution, 60% less data transfer",
            "optimization_time_ms": 85,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query optimization error: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize SQL query")


@router.get("/history")
async def get_query_history(
    user_id: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    query_type: Optional[str] = None
):
    """Get query execution history"""
    try:
        # Mock query history
        history = [
            {
                "id": "q1",
                "sql": "SELECT * FROM users WHERE status = 'active'",
                "query_type": "SELECT",
                "executed_at": "2024-01-15T10:30:00Z",
                "execution_time_ms": 45,
                "row_count": 150,
                "status": "success"
            },
            {
                "id": "q2", 
                "sql": "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURRENT_DATE",
                "query_type": "SELECT",
                "executed_at": "2024-01-15T09:15:00Z",
                "execution_time_ms": 23,
                "row_count": 1,
                "status": "success"
            },
            {
                "id": "q3",
                "sql": "UPDATE users SET last_login = NOW() WHERE id = 123",
                "query_type": "UPDATE", 
                "executed_at": "2024-01-15T08:45:00Z",
                "execution_time_ms": 12,
                "row_count": 1,
                "status": "success"
            }
        ]
        
        # Filter by query type if specified
        if query_type:
            history = [q for q in history if q["query_type"].lower() == query_type.lower()]
        
        # Apply limit
        history = history[:limit]
        
        return {
            "user_id": user_id,
            "query_history": history,
            "total_count": len(history),
            "query_type_filter": query_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get query history")
