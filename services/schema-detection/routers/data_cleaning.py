"""
Data Cleaning and Validation API Routes

Routes for data cleaning suggestions, validation rules, and data quality analysis.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# Router for data cleaning endpoints
router = APIRouter(prefix="/cleaning", tags=["data_cleaning"])


@router.post("/analyze")
async def analyze_data_quality(
    data: Dict[str, Any],
    table_name: Optional[str] = None,
    include_suggestions: bool = True
):
    """Analyze data quality and identify issues"""
    try:
        issues = []
        statistics = {}
        suggestions = []
        
        # Analyze data structure
        if isinstance(data, dict):
            if "rows" in data:
                rows = data["rows"]
                columns = data.get("columns", [])
            else:
                rows = [data]
                columns = list(data.keys()) if data else []
        else:
            rows = data if isinstance(data, list) else [data]
            columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
        
        total_rows = len(rows)
        statistics["total_rows"] = total_rows
        statistics["total_columns"] = len(columns)
        
        # Analyze each column
        column_analysis = {}
        for col in columns:
            col_data = [row.get(col) for row in rows if isinstance(row, dict)]
            
            # Basic statistics
            null_count = sum(1 for val in col_data if val is None or val == "")
            non_null_count = total_rows - null_count
            
            column_analysis[col] = {
                "null_count": null_count,
                "non_null_count": non_null_count,
                "null_percentage": (null_count / total_rows * 100) if total_rows > 0 else 0,
                "data_types": list(set(type(val).__name__ for val in col_data if val is not None))
            }
            
            # Identify issues
            if null_count / total_rows > 0.5:
                issues.append({
                    "column": col,
                    "type": "high_null_rate",
                    "severity": "high",
                    "description": f"Column '{col}' has {null_count/total_rows*100:.1f}% null values",
                    "affected_rows": null_count
                })
            
            # Check for mixed data types
            unique_types = set(type(val).__name__ for val in col_data if val is not None)
            if len(unique_types) > 1:
                issues.append({
                    "column": col,
                    "type": "mixed_data_types",
                    "severity": "medium",
                    "description": f"Column '{col}' has mixed data types: {', '.join(unique_types)}",
                    "affected_rows": len([val for val in col_data if val is not None])
                })
            
            # Check for potential email format issues
            if "email" in col.lower():
                invalid_emails = []
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                for val in col_data:
                    if val and not re.match(email_pattern, str(val)):
                        invalid_emails.append(val)
                
                if invalid_emails:
                    issues.append({
                        "column": col,
                        "type": "invalid_email_format",
                        "severity": "medium",
                        "description": f"Column '{col}' contains {len(invalid_emails)} invalid email formats",
                        "affected_rows": len(invalid_emails),
                        "sample_values": invalid_emails[:3]
                    })
        
        # Generate suggestions if requested
        if include_suggestions:
            for issue in issues:
                if issue["type"] == "high_null_rate":
                    suggestions.append({
                        "column": issue["column"],
                        "action": "handle_nulls",
                        "options": [
                            "Remove rows with null values",
                            "Fill with default value",
                            "Fill with mean/median (for numeric)",
                            "Fill with most frequent value"
                        ],
                        "priority": "high"
                    })
                
                elif issue["type"] == "mixed_data_types":
                    suggestions.append({
                        "column": issue["column"],
                        "action": "standardize_types",
                        "options": [
                            "Convert all to string",
                            "Parse and convert to most common type",
                            "Create separate columns for different types"
                        ],
                        "priority": "medium"
                    })
                
                elif issue["type"] == "invalid_email_format":
                    suggestions.append({
                        "column": issue["column"],
                        "action": "clean_emails",
                        "options": [
                            "Remove invalid email rows",
                            "Attempt to fix common email issues",
                            "Flag invalid emails for manual review"
                        ],
                        "priority": "medium"
                    })
        
        return {
            "table_name": table_name,
            "data_quality_score": max(0, 100 - len(issues) * 10),  # Simple scoring
            "total_issues": len(issues),
            "statistics": statistics,
            "column_analysis": column_analysis,
            "issues": issues,
            "suggestions": suggestions if include_suggestions else [],
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data quality analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze data quality")


@router.post("/suggest")
async def suggest_data_cleaning(
    data: Dict[str, Any],
    issue_types: Optional[List[str]] = None,
    table_name: Optional[str] = None
):
    """Suggest data cleaning operations for identified issues"""
    try:
        # First analyze data quality to identify issues
        analysis_result = await analyze_data_quality(data, table_name, include_suggestions=True)
        
        # Filter suggestions by issue types if specified
        suggestions = analysis_result["suggestions"]
        if issue_types:
            suggestions = [s for s in suggestions if any(issue_type in s["action"] for issue_type in issue_types)]
        
        # Add detailed cleaning operations
        detailed_operations = []
        for suggestion in suggestions:
            if suggestion["action"] == "handle_nulls":
                detailed_operations.append({
                    "operation_id": f"null_handling_{suggestion['column']}",
                    "column": suggestion["column"],
                    "operation": "null_handling",
                    "method": "fill_with_default",
                    "parameters": {
                        "default_value": "",
                        "strategy": "constant"
                    },
                    "estimated_impact": "Removes null values, may affect data integrity",
                    "reversible": False
                })
            
            elif suggestion["action"] == "standardize_types":
                detailed_operations.append({
                    "operation_id": f"type_conversion_{suggestion['column']}",
                    "column": suggestion["column"],
                    "operation": "type_conversion",
                    "method": "convert_to_string",
                    "parameters": {
                        "target_type": "string",
                        "handle_errors": "coerce"
                    },
                    "estimated_impact": "Standardizes data types, may lose precision",
                    "reversible": False
                })
            
            elif suggestion["action"] == "clean_emails":
                detailed_operations.append({
                    "operation_id": f"email_cleaning_{suggestion['column']}",
                    "column": suggestion["column"],
                    "operation": "email_validation",
                    "method": "fix_common_issues",
                    "parameters": {
                        "remove_invalid": False,
                        "fix_common_typos": True,
                        "normalize_format": True
                    },
                    "estimated_impact": "Fixes common email format issues",
                    "reversible": True
                })
        
        return {
            "table_name": table_name,
            "total_suggestions": len(suggestions),
            "cleaning_operations": detailed_operations,
            "execution_order": [op["operation_id"] for op in detailed_operations],
            "estimated_time_minutes": len(detailed_operations) * 2,
            "data_quality_score_before": analysis_result["data_quality_score"],
            "estimated_score_after": min(100, analysis_result["data_quality_score"] + len(detailed_operations) * 15),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data cleaning suggestions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest data cleaning operations")


@router.post("/apply")
async def apply_data_cleaning(
    operations: List[Dict[str, Any]],
    data: Dict[str, Any],
    table_name: Optional[str] = None,
    dry_run: bool = False
):
    """Apply data cleaning operations to the dataset"""
    try:
        if dry_run:
            # Return preview of what would be cleaned
            return {
                "table_name": table_name,
                "dry_run": True,
                "operations_to_apply": len(operations),
                "estimated_changes": {
                    "rows_affected": 150,
                    "columns_modified": len(set(op.get("column") for op in operations)),
                    "data_quality_improvement": "15-25%"
                },
                "preview": "Data cleaning preview - no actual changes made",
                "timestamp": datetime.now().isoformat()
            }
        
        # Mock applying cleaning operations
        cleaned_data = data.copy()
        applied_operations = []
        
        for operation in operations:
            op_result = {
                "operation_id": operation.get("operation_id"),
                "column": operation.get("column"),
                "operation": operation.get("operation"),
                "status": "success",
                "rows_affected": 45,
                "execution_time_ms": 120
            }
            applied_operations.append(op_result)
        
        return {
            "table_name": table_name,
            "dry_run": False,
            "cleaning_status": "completed",
            "applied_operations": applied_operations,
            "total_operations": len(operations),
            "successful_operations": len([op for op in applied_operations if op["status"] == "success"]),
            "failed_operations": len([op for op in applied_operations if op["status"] == "failed"]),
            "cleaned_data": cleaned_data,
            "data_quality_improvement": "22%",
            "total_execution_time_ms": sum(op["execution_time_ms"] for op in applied_operations),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data cleaning application error: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply data cleaning operations")


@router.post("/transform")
async def transform_data_natural_language(
    description: str,
    data: Dict[str, Any],
    table_name: Optional[str] = None
):
    """Transform data using natural language description"""
    try:
        # Mock natural language transformation
        transformations = []
        
        description_lower = description.lower()
        
        if "lowercase" in description_lower or "lower case" in description_lower:
            transformations.append({
                "operation": "lowercase_conversion",
                "description": "Convert text fields to lowercase",
                "affected_columns": ["name", "email", "description"],
                "estimated_changes": 75
            })
        
        if "remove duplicates" in description_lower:
            transformations.append({
                "operation": "duplicate_removal",
                "description": "Remove duplicate records",
                "affected_columns": ["all"],
                "estimated_changes": 12
            })
        
        if "fill missing" in description_lower or "fill null" in description_lower:
            transformations.append({
                "operation": "null_filling",
                "description": "Fill missing values with appropriate defaults",
                "affected_columns": ["status", "category"],
                "estimated_changes": 28
            })
        
        if "standardize" in description_lower:
            transformations.append({
                "operation": "standardization",
                "description": "Standardize data formats and values",
                "affected_columns": ["phone", "date", "status"],
                "estimated_changes": 95
            })
        
        # Apply mock transformations
        transformed_data = data.copy()
        
        return {
            "table_name": table_name,
            "transformation_description": description,
            "identified_transformations": transformations,
            "total_transformations": len(transformations),
            "transformed_data": transformed_data,
            "changes_summary": {
                "total_rows_affected": sum(t["estimated_changes"] for t in transformations),
                "columns_modified": len(set().union(*[t["affected_columns"] for t in transformations if t["affected_columns"] != ["all"]])),
                "transformation_success_rate": "98%"
            },
            "execution_time_ms": 250,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Natural language transformation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to transform data using natural language")


@router.get("/rules")
async def get_validation_rules(
    table_name: Optional[str] = None,
    rule_type: Optional[str] = None
):
    """Get validation rules for data quality"""
    try:
        # Mock validation rules
        rules = [
            {
                "rule_id": "email_format",
                "rule_name": "Email Format Validation",
                "rule_type": "format",
                "column": "email",
                "condition": "matches_email_pattern",
                "parameters": {
                    "pattern": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                },
                "severity": "error",
                "enabled": True,
                "description": "Validates email format using regex pattern"
            },
            {
                "rule_id": "age_range",
                "rule_name": "Age Range Validation", 
                "rule_type": "range",
                "column": "age",
                "condition": "between",
                "parameters": {
                    "min_value": 0,
                    "max_value": 150
                },
                "severity": "warning",
                "enabled": True,
                "description": "Validates age is within reasonable range"
            },
            {
                "rule_id": "required_fields",
                "rule_name": "Required Fields",
                "rule_type": "presence",
                "column": "user_id",
                "condition": "not_null",
                "parameters": {},
                "severity": "error",
                "enabled": True,
                "description": "Ensures required fields are not null"
            }
        ]
        
        # Filter by table name if specified
        if table_name:
            # In a real implementation, this would filter by table
            pass
        
        # Filter by rule type if specified
        if rule_type:
            rules = [rule for rule in rules if rule["rule_type"] == rule_type]
        
        return {
            "table_name": table_name,
            "rule_type_filter": rule_type,
            "validation_rules": rules,
            "total_rules": len(rules),
            "enabled_rules": len([rule for rule in rules if rule["enabled"]]),
            "rule_types": list(set(rule["rule_type"] for rule in rules)),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get validation rules error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get validation rules")


@router.post("/rules")
async def create_validation_rule(
    rule_name: str,
    rule_type: str,
    column: str,
    condition: str,
    parameters: Dict[str, Any],
    severity: str = "warning",
    description: Optional[str] = None
):
    """Create or update validation rules"""
    try:
        # Mock rule creation
        rule_id = f"{rule_type}_{column}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        new_rule = {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "rule_type": rule_type,
            "column": column,
            "condition": condition,
            "parameters": parameters,
            "severity": severity,
            "enabled": True,
            "description": description or f"Validation rule for {column}",
            "created_at": datetime.now().isoformat(),
            "created_by": "system"
        }
        
        return {
            "status": "created",
            "rule": new_rule,
            "message": f"Validation rule '{rule_name}' created successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Create validation rule error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create validation rule")


@router.post("/rules/enforce")
async def enforce_validation_rules(
    data: Dict[str, Any],
    rule_ids: Optional[List[str]] = None,
    table_name: Optional[str] = None,
    stop_on_error: bool = False
):
    """Enforce validation rules on dataset"""
    try:
        # Mock rule enforcement
        violations = []
        
        # Simulate finding violations
        violations.append({
            "rule_id": "email_format",
            "rule_name": "Email Format Validation",
            "column": "email",
            "violation_type": "format_error",
            "severity": "error",
            "affected_rows": [3, 7, 12],
            "violation_count": 3,
            "sample_values": ["invalid-email", "user@", "not.an.email"],
            "message": "Invalid email format detected"
        })
        
        violations.append({
            "rule_id": "age_range",
            "rule_name": "Age Range Validation",
            "column": "age",
            "violation_type": "range_error",
            "severity": "warning",
            "affected_rows": [5],
            "violation_count": 1,
            "sample_values": [200],
            "message": "Age value outside acceptable range"
        })
        
        # Calculate enforcement summary
        total_violations = sum(v["violation_count"] for v in violations)
        error_violations = sum(v["violation_count"] for v in violations if v["severity"] == "error")
        warning_violations = sum(v["violation_count"] for v in violations if v["severity"] == "warning")
        
        return {
            "table_name": table_name,
            "enforcement_status": "completed",
            "rules_enforced": rule_ids or ["all"],
            "validation_summary": {
                "total_violations": total_violations,
                "error_violations": error_violations,
                "warning_violations": warning_violations,
                "rules_passed": 8,
                "rules_failed": len(violations)
            },
            "violations": violations,
            "data_quality_score": max(0, 100 - total_violations * 5),
            "stop_on_error": stop_on_error,
            "execution_time_ms": 180,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enforce validation rules error: {e}")
        raise HTTPException(status_code=500, detail="Failed to enforce validation rules")
