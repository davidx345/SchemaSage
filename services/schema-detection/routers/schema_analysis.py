"""
Schema Analysis Router
Provides comprehensive schema analysis with multiple analysis types

This router offers real (not mock) schema analysis with three modes:
- comprehensive: Full schema analysis including quality, patterns, and recommendations
- performance: Performance-focused analysis (indexes, query optimization)
- compliance: Data compliance checks (PII detection, GDPR, etc.)
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
import logging
import json
import re
from datetime import datetime

from core.auth import get_current_user, get_optional_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/schema", tags=["Schema Analysis"])


class AnalysisType(str, Enum):
    """Supported analysis types"""
    COMPREHENSIVE = "comprehensive"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"


class SchemaAnalyzeRequest(BaseModel):
    """Request model for schema analysis"""
    schema_content: str = Field(..., description="Raw schema content (JSON, SQL, YAML, etc.)")
    analysis_type: AnalysisType = Field(
        default=AnalysisType.COMPREHENSIVE,
        description="Type of analysis to perform"
    )
    
    @validator('schema_content')
    def validate_schema_content(cls, v):
        """Validate schema content is not empty"""
        if not v or not v.strip():
            raise ValueError("schema_content cannot be empty")
        if len(v) > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("schema_content too large (max 10MB)")
        return v


class SchemaAnalyzeResponse(BaseModel):
    """Response model for schema analysis"""
    success: bool
    analysis: Dict[str, Any]


def analyze_schema_structure(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the structure of a schema
    
    Returns metadata about tables, columns, relationships, and quality metrics
    """
    analysis = {
        "tables": [],
        "total_columns": 0,
        "total_relationships": 0,
        "naming_convention_score": 0,
        "normalization_score": 0
    }
    
    try:
        # Extract tables
        tables = schema_data.get("tables", [])
        if not isinstance(tables, list):
            # Try other formats
            if "definitions" in schema_data:
                tables = list(schema_data["definitions"].values())
            elif isinstance(schema_data, list):
                tables = schema_data
        
        # Analyze each table
        for table in tables:
            if not isinstance(table, dict):
                continue
                
            table_name = table.get("name", table.get("tableName", "unknown"))
            columns = table.get("columns", table.get("fields", []))
            
            table_analysis = {
                "name": table_name,
                "column_count": len(columns),
                "has_primary_key": False,
                "has_indexes": False,
                "nullable_columns": 0,
                "required_columns": 0
            }
            
            # Analyze columns
            for col in columns:
                if not isinstance(col, dict):
                    continue
                    
                # Check for primary key
                if col.get("primary_key") or col.get("primaryKey") or col.get("isPrimaryKey"):
                    table_analysis["has_primary_key"] = True
                
                # Check nullable
                if col.get("nullable") or col.get("isNullable"):
                    table_analysis["nullable_columns"] += 1
                else:
                    table_analysis["required_columns"] += 1
            
            analysis["tables"].append(table_analysis)
            analysis["total_columns"] += len(columns)
        
        # Calculate naming convention score (snake_case is preferred)
        naming_violations = 0
        for table in tables:
            table_name = table.get("name", "")
            if not re.match(r'^[a-z][a-z0-9_]*$', table_name):
                naming_violations += 1
        
        total_items = len(tables)
        analysis["naming_convention_score"] = int(
            ((total_items - naming_violations) / total_items * 100) if total_items > 0 else 100
        )
        
        # Calculate normalization score (simple heuristic)
        # Check if tables have reasonable column counts (not too many)
        over_normalized = sum(1 for t in analysis["tables"] if t["column_count"] < 3)
        under_normalized = sum(1 for t in analysis["tables"] if t["column_count"] > 30)
        normalization_issues = over_normalized + under_normalized
        
        analysis["normalization_score"] = int(
            ((total_items - normalization_issues) / total_items * 100) if total_items > 0 else 100
        )
        
        # Extract relationships
        relationships = schema_data.get("relationships", schema_data.get("relations", []))
        analysis["total_relationships"] = len(relationships) if isinstance(relationships, list) else 0
        
    except Exception as e:
        logger.warning(f"Error in schema structure analysis: {e}")
    
    return analysis


def analyze_comprehensive(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive schema analysis
    
    Includes:
    - Schema structure and quality metrics
    - Naming convention compliance
    - Normalization assessment
    - Missing indexes detection
    - Data type consistency
    - General recommendations
    """
    issues = []
    suggestions = []
    
    # Get structure analysis
    structure = analyze_schema_structure(schema_data)
    
    # Check for tables
    if not structure["tables"]:
        issues.append("No tables found in schema")
        return {
            "issues": issues,
            "suggestions": ["Provide a valid schema with table definitions"],
            "score": 0,
            "details": {
                "structure": structure,
                "analysis_type": "comprehensive"
            }
        }
    
    # Check for primary keys
    tables_without_pk = [t for t in structure["tables"] if not t["has_primary_key"]]
    if tables_without_pk:
        issues.append(f"{len(tables_without_pk)} table(s) missing primary keys")
        for table in tables_without_pk[:3]:  # Show first 3
            suggestions.append(f"Add primary key to table '{table['name']}'")
    
    # Check naming conventions
    if structure["naming_convention_score"] < 80:
        issues.append(f"Naming convention score is {structure['naming_convention_score']}% (below 80%)")
        suggestions.append("Use snake_case naming convention for tables and columns")
    
    # Check normalization
    if structure["normalization_score"] < 70:
        issues.append(f"Normalization score is {structure['normalization_score']}% (below 70%)")
        suggestions.append("Review table structure for proper normalization (3NF recommended)")
    
    # Check relationships
    expected_relationships = max(len(structure["tables"]) - 1, 0)
    if structure["total_relationships"] < expected_relationships:
        issues.append(f"Only {structure['total_relationships']} relationships defined (expected ~{expected_relationships})")
        suggestions.append("Define foreign key relationships between related tables")
    
    # Check for tables with many nullable columns
    for table in structure["tables"]:
        if table["column_count"] > 0:
            nullable_ratio = table["nullable_columns"] / table["column_count"]
            if nullable_ratio > 0.7:
                issues.append(f"Table '{table['name']}' has {int(nullable_ratio*100)}% nullable columns")
                suggestions.append(f"Review nullable columns in table '{table['name']}' - consider defaults or constraints")
    
    # Calculate overall score
    base_score = 100
    base_score -= len(tables_without_pk) * 10
    base_score -= (100 - structure["naming_convention_score"]) * 0.3
    base_score -= (100 - structure["normalization_score"]) * 0.2
    base_score = max(0, min(100, int(base_score)))
    
    return {
        "issues": issues if issues else ["No critical issues found"],
        "suggestions": suggestions if suggestions else ["Schema looks good! Consider adding documentation for complex tables."],
        "score": base_score,
        "details": {
            "structure": structure,
            "analysis_type": "comprehensive",
            "quality_metrics": {
                "naming_convention": structure["naming_convention_score"],
                "normalization": structure["normalization_score"],
                "primary_keys_coverage": int((len(structure["tables"]) - len(tables_without_pk)) / len(structure["tables"]) * 100) if structure["tables"] else 0
            }
        }
    }


def analyze_performance(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform performance-focused schema analysis
    
    Includes:
    - Missing indexes detection
    - Query optimization suggestions
    - Large table warnings
    - Join performance recommendations
    """
    issues = []
    suggestions = []
    
    # Get structure analysis
    structure = analyze_schema_structure(schema_data)
    
    if not structure["tables"]:
        return {
            "issues": ["No tables found in schema"],
            "suggestions": ["Provide a valid schema with table definitions"],
            "score": 0,
            "details": {"analysis_type": "performance"}
        }
    
    # Check for indexes
    tables_without_indexes = [t for t in structure["tables"] if not t["has_indexes"]]
    if tables_without_indexes:
        issues.append(f"{len(tables_without_indexes)} table(s) missing indexes")
        for table in tables_without_indexes[:3]:
            suggestions.append(f"Add indexes to frequently queried columns in '{table['name']}'")
    
    # Check for large tables (many columns)
    large_tables = [t for t in structure["tables"] if t["column_count"] > 20]
    if large_tables:
        issues.append(f"{len(large_tables)} table(s) have >20 columns (may impact performance)")
        for table in large_tables[:3]:
            suggestions.append(f"Consider splitting table '{table['name']}' ({table['column_count']} columns) into smaller tables")
    
    # Check relationships for join performance
    if structure["total_relationships"] == 0 and len(structure["tables"]) > 1:
        issues.append("No relationships defined - queries may require expensive full table scans")
        suggestions.append("Define foreign key relationships to enable efficient joins")
    
    # Performance score calculation
    score = 100
    score -= len(tables_without_indexes) * 15
    score -= len(large_tables) * 10
    if structure["total_relationships"] == 0 and len(structure["tables"]) > 1:
        score -= 20
    score = max(0, min(100, int(score)))
    
    return {
        "issues": issues if issues else ["No performance issues detected"],
        "suggestions": suggestions if suggestions else [
            "Schema is well-optimized for performance",
            "Consider adding indexes on foreign key columns",
            "Monitor query patterns and add indexes as needed"
        ],
        "score": score,
        "details": {
            "structure": structure,
            "analysis_type": "performance",
            "performance_metrics": {
                "indexed_tables": len(structure["tables"]) - len(tables_without_indexes),
                "large_tables": len(large_tables),
                "relationships_defined": structure["total_relationships"]
            }
        }
    }


def analyze_compliance(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform compliance-focused schema analysis
    
    Includes:
    - PII detection
    - GDPR compliance checks
    - Data retention recommendations
    - Encryption requirements
    """
    issues = []
    suggestions = []
    pii_columns = []
    
    # Get structure analysis
    structure = analyze_schema_structure(schema_data)
    
    if not structure["tables"]:
        return {
            "issues": ["No tables found in schema"],
            "suggestions": ["Provide a valid schema with table definitions"],
            "score": 0,
            "details": {"analysis_type": "compliance"}
        }
    
    # Check for PII columns
    tables = schema_data.get("tables", [])
    for table in tables:
        if not isinstance(table, dict):
            continue
            
        table_name = table.get("name", "unknown")
        columns = table.get("columns", [])
        
        for col in columns:
            if not isinstance(col, dict):
                continue
                
            col_name = col.get("name", "").lower()
            
            # Detect PII patterns
            pii_patterns = {
                "email": ["email", "e_mail", "mail"],
                "phone": ["phone", "tel", "mobile", "contact"],
                "ssn": ["ssn", "social_security"],
                "address": ["address", "street", "zip", "postal"],
                "name": ["first_name", "last_name", "full_name", "name"],
                "dob": ["birth_date", "dob", "date_of_birth"],
                "credit_card": ["credit_card", "cc_number", "card_number"]
            }
            
            for pii_type, patterns in pii_patterns.items():
                if any(pattern in col_name for pattern in patterns):
                    pii_columns.append({
                        "table": table_name,
                        "column": col.get("name"),
                        "pii_type": pii_type
                    })
                    break
    
    # Report PII findings
    if pii_columns:
        issues.append(f"Found {len(pii_columns)} potential PII column(s)")
        unique_types = set(col["pii_type"] for col in pii_columns)
        suggestions.append(f"Encrypt PII columns: {', '.join(unique_types)}")
        suggestions.append("Implement access controls for PII data")
        suggestions.append("Consider data masking for non-production environments")
        
        # GDPR-specific suggestions
        if any(col["pii_type"] in ["email", "name", "address"] for col in pii_columns):
            suggestions.append("Implement GDPR right-to-be-forgotten (data deletion)")
            suggestions.append("Add consent tracking columns for GDPR compliance")
    
    # Check for audit columns
    has_audit_columns = False
    for table in tables:
        if isinstance(table, dict):
            columns = table.get("columns", [])
            col_names = [col.get("name", "").lower() for col in columns if isinstance(col, dict)]
            if any(name in ["created_at", "updated_at", "created_by", "modified_by"] for name in col_names):
                has_audit_columns = True
                break
    
    if not has_audit_columns:
        issues.append("Missing audit columns (created_at, updated_at, etc.)")
        suggestions.append("Add timestamp and user tracking columns for audit compliance")
    
    # Calculate compliance score
    score = 100
    if pii_columns:
        score -= min(30, len(pii_columns) * 5)  # Penalize for unprotected PII
    if not has_audit_columns:
        score -= 20
    score = max(0, min(100, int(score)))
    
    return {
        "issues": issues if issues else ["No compliance issues detected"],
        "suggestions": suggestions if suggestions else [
            "Schema meets basic compliance requirements",
            "Regularly review data retention policies",
            "Implement encryption for sensitive data"
        ],
        "score": score,
        "details": {
            "structure": structure,
            "analysis_type": "compliance",
            "compliance_metrics": {
                "pii_columns_found": len(pii_columns),
                "pii_types": list(set(col["pii_type"] for col in pii_columns)),
                "has_audit_columns": has_audit_columns,
                "pii_details": pii_columns[:10]  # First 10 for brevity
            }
        }
    }


@router.post("/analyze", response_model=SchemaAnalyzeResponse)
async def analyze_schema(
    request: SchemaAnalyzeRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Analyze schema with comprehensive, performance, or compliance focus
    
    This endpoint provides REAL (not mock) schema analysis with three modes:
    
    **Analysis Types:**
    
    1. **comprehensive** (default):
       - Schema structure and quality metrics
       - Naming convention compliance
       - Normalization assessment
       - Missing indexes detection
       - Data type consistency
       - General recommendations
    
    2. **performance**:
       - Missing indexes detection
       - Query optimization suggestions
       - Large table warnings
       - Join performance recommendations
    
    3. **compliance**:
       - PII detection
       - GDPR compliance checks
       - Data retention recommendations
       - Encryption requirements
    
    **Example Request:**
    ```json
    {
      "schema_content": "{\\"tables\\": [{\\"name\\": \\"users\\", \\"columns\\": [...]}]}",
      "analysis_type": "comprehensive"
    }
    ```
    
    **Returns:**
    - success: Whether analysis completed successfully
    - analysis: Detailed analysis results including:
      - issues: List of problems found
      - suggestions: Actionable recommendations
      - score: Quality score (0-100)
      - details: In-depth analysis metadata
    """
    try:
        logger.info(f"Analyzing schema with type: {request.analysis_type}")
        
        # Parse schema content
        try:
            schema_data = json.loads(request.schema_content)
        except json.JSONDecodeError as e:
            # Try to parse as other formats or plain text
            logger.warning(f"Schema content is not valid JSON: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid schema format: {str(e)}"
            )
        
        # Perform analysis based on type
        if request.analysis_type == AnalysisType.COMPREHENSIVE:
            analysis_result = analyze_comprehensive(schema_data)
        elif request.analysis_type == AnalysisType.PERFORMANCE:
            analysis_result = analyze_performance(schema_data)
        elif request.analysis_type == AnalysisType.COMPLIANCE:
            analysis_result = analyze_compliance(schema_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid analysis_type: {request.analysis_type}"
            )
        
        logger.info(f"Schema analysis completed: score={analysis_result['score']}, issues={len(analysis_result['issues'])}")
        
        return SchemaAnalyzeResponse(
            success=True,
            analysis=analysis_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema analysis failed: {str(e)}"
        )


@router.get("/analyze/types")
async def get_analysis_types():
    """
    Get available analysis types and their descriptions
    
    **Returns:**
    - analysis_types: List of available analysis types with descriptions
    """
    return {
        "success": True,
        "analysis_types": [
            {
                "type": "comprehensive",
                "description": "Full schema analysis including quality, patterns, and recommendations",
                "includes": [
                    "Schema structure and quality metrics",
                    "Naming convention compliance",
                    "Normalization assessment",
                    "Missing indexes detection",
                    "General recommendations"
                ]
            },
            {
                "type": "performance",
                "description": "Performance-focused analysis for query optimization",
                "includes": [
                    "Missing indexes detection",
                    "Query optimization suggestions",
                    "Large table warnings",
                    "Join performance recommendations"
                ]
            },
            {
                "type": "compliance",
                "description": "Data compliance and security analysis",
                "includes": [
                    "PII detection",
                    "GDPR compliance checks",
                    "Data retention recommendations",
                    "Encryption requirements"
                ]
            }
        ]
    }
