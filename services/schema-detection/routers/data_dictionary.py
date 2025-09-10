"""
Data Dictionary Management API Routes

Routes for managing data dictionaries and schema metadata.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Router for data dictionary endpoints
router = APIRouter(prefix="/data-dictionary", tags=["data_dictionary"])

# Mock data dictionary storage
data_dictionaries = {}


@router.get("/get")
async def get_data_dictionary(
    table_name: Optional[str] = None,
    project_id: Optional[str] = None,
    include_columns: bool = True,
    include_relationships: bool = True
):
    """Get data dictionary for tables or entire project"""
    try:
        # Mock data dictionary structure
        dictionary = {
            "project_id": project_id,
            "tables": {}
        }
        
        if table_name:
            # Return dictionary for specific table
            dictionary["tables"][table_name] = {
                "table_name": table_name,
                "description": f"Data table containing {table_name} information",
                "created_date": "2024-01-01",
                "last_modified": "2024-01-15",
                "record_count": 1250,
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "INTEGER",
                        "is_primary_key": True,
                        "is_nullable": False,
                        "description": "Unique identifier for each record",
                        "business_rules": ["Auto-incrementing", "Always required"],
                        "example_values": ["1", "2", "3"]
                    },
                    {
                        "column_name": "name",
                        "data_type": "VARCHAR(255)",
                        "is_nullable": False,
                        "description": "Full name of the entity",
                        "business_rules": ["Must be unique", "No special characters"],
                        "example_values": ["John Doe", "Jane Smith", "Bob Johnson"]
                    },
                    {
                        "column_name": "email",
                        "data_type": "VARCHAR(255)",
                        "is_nullable": True,
                        "description": "Email address for contact",
                        "business_rules": ["Must follow email format", "Optional field"],
                        "example_values": ["john@example.com", "jane@company.org"]
                    },
                    {
                        "column_name": "status",
                        "data_type": "VARCHAR(50)",
                        "is_nullable": False,
                        "description": "Current status of the record",
                        "business_rules": ["Must be one of: active, inactive, pending"],
                        "example_values": ["active", "inactive", "pending"],
                        "enum_values": ["active", "inactive", "pending", "suspended"]
                    },
                    {
                        "column_name": "created_at",
                        "data_type": "TIMESTAMP",
                        "is_nullable": False,
                        "description": "Date and time when record was created",
                        "business_rules": ["Auto-generated on insert", "Immutable"],
                        "example_values": ["2024-01-15T10:30:00Z"]
                    }
                ] if include_columns else [],
                "relationships": [
                    {
                        "type": "foreign_key",
                        "column": "category_id",
                        "references_table": "categories",
                        "references_column": "id",
                        "relationship_type": "many_to_one"
                    },
                    {
                        "type": "one_to_many",
                        "related_table": "orders",
                        "foreign_key_column": "user_id",
                        "relationship_description": "One user can have many orders"
                    }
                ] if include_relationships else [],
                "indexes": [
                    {
                        "index_name": f"idx_{table_name}_email",
                        "columns": ["email"],
                        "is_unique": True,
                        "index_type": "btree"
                    },
                    {
                        "index_name": f"idx_{table_name}_status",
                        "columns": ["status"],
                        "is_unique": False,
                        "index_type": "btree"
                    }
                ],
                "constraints": [
                    {
                        "constraint_name": f"pk_{table_name}",
                        "constraint_type": "PRIMARY KEY",
                        "columns": ["id"]
                    },
                    {
                        "constraint_name": f"chk_{table_name}_status",
                        "constraint_type": "CHECK",
                        "condition": "status IN ('active', 'inactive', 'pending')"
                    }
                ],
                "business_glossary": {
                    "domain": "User Management",
                    "data_classification": "PII",
                    "retention_policy": "7 years",
                    "access_level": "restricted"
                }
            }
        else:
            # Return dictionary for multiple tables
            sample_tables = ["users", "orders", "products", "categories"]
            for table in sample_tables:
                dictionary["tables"][table] = {
                    "table_name": table,
                    "description": f"Data table containing {table} information",
                    "record_count": 500 + len(table) * 100,
                    "column_count": 5 + len(table) % 3,
                    "last_modified": "2024-01-15",
                    "data_classification": "PII" if table == "users" else "General"
                }
        
        return {
            "data_dictionary": dictionary,
            "generated_at": datetime.now().isoformat(),
            "include_columns": include_columns,
            "include_relationships": include_relationships,
            "table_count": len(dictionary["tables"]),
            "metadata": {
                "dictionary_version": "1.0",
                "last_updated": "2024-01-15T10:30:00Z",
                "total_tables": len(dictionary["tables"]),
                "total_columns": sum(len(table.get("columns", [])) for table in dictionary["tables"].values())
            }
        }
        
    except Exception as e:
        logger.error(f"Get data dictionary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get data dictionary")


@router.post("/update")
async def update_data_dictionary(
    table_name: str,
    updates: Dict[str, Any],
    project_id: Optional[str] = None,
    update_type: str = "merge"
):
    """Update data dictionary for a table"""
    try:
        # Mock updating data dictionary
        update_summary = {
            "table_name": table_name,
            "project_id": project_id,
            "update_type": update_type,
            "changes_applied": [],
            "validation_errors": []
        }
        
        # Process different types of updates
        if "description" in updates:
            update_summary["changes_applied"].append({
                "field": "table_description",
                "old_value": f"Previous description for {table_name}",
                "new_value": updates["description"],
                "change_type": "modified"
            })
        
        if "columns" in updates:
            columns_updates = updates["columns"]
            for col_name, col_updates in columns_updates.items():
                if "description" in col_updates:
                    update_summary["changes_applied"].append({
                        "field": f"column.{col_name}.description",
                        "old_value": f"Previous description for {col_name}",
                        "new_value": col_updates["description"],
                        "change_type": "modified"
                    })
                
                if "business_rules" in col_updates:
                    update_summary["changes_applied"].append({
                        "field": f"column.{col_name}.business_rules",
                        "old_value": [],
                        "new_value": col_updates["business_rules"],
                        "change_type": "added"
                    })
        
        if "business_glossary" in updates:
            glossary_updates = updates["business_glossary"]
            for key, value in glossary_updates.items():
                update_summary["changes_applied"].append({
                    "field": f"business_glossary.{key}",
                    "old_value": f"Previous {key}",
                    "new_value": value,
                    "change_type": "modified"
                })
        
        # Validate updates
        if not table_name or len(table_name.strip()) == 0:
            update_summary["validation_errors"].append({
                "field": "table_name",
                "error": "Table name cannot be empty"
            })
        
        # Check for duplicate column names if columns are being updated
        if "columns" in updates:
            column_names = list(updates["columns"].keys())
            if len(column_names) != len(set(column_names)):
                update_summary["validation_errors"].append({
                    "field": "columns",
                    "error": "Duplicate column names detected"
                })
        
        success = len(update_summary["validation_errors"]) == 0
        
        return {
            "status": "success" if success else "failed",
            "update_summary": update_summary,
            "changes_count": len(update_summary["changes_applied"]),
            "validation_errors_count": len(update_summary["validation_errors"]),
            "updated_at": datetime.now().isoformat(),
            "next_steps": [
                "Review changes in data dictionary",
                "Update dependent documentation",
                "Notify team members of changes"
            ] if success else ["Fix validation errors and retry"]
        }
        
    except Exception as e:
        logger.error(f"Update data dictionary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update data dictionary")


@router.post("/generate")
async def generate_data_dictionary(
    schema_data: Dict[str, Any],
    project_id: Optional[str] = None,
    include_ai_descriptions: bool = True,
    include_business_rules: bool = True
):
    """Generate data dictionary from schema data"""
    try:
        # Mock generating data dictionary from schema
        generated_dictionary = {
            "project_id": project_id,
            "generation_settings": {
                "include_ai_descriptions": include_ai_descriptions,
                "include_business_rules": include_business_rules,
                "generation_method": "automated_analysis"
            },
            "tables": {}
        }
        
        # Process schema data to generate dictionary
        if "tables" in schema_data:
            for table_info in schema_data["tables"]:
                table_name = table_info.get("table_name", "unknown_table")
                
                generated_table = {
                    "table_name": table_name,
                    "description": f"Auto-generated: Data table for {table_name} entities",
                    "generated_at": datetime.now().isoformat(),
                    "columns": [],
                    "inferred_relationships": [],
                    "suggested_indexes": [],
                    "data_quality_notes": []
                }
                
                # Process columns
                for column in table_info.get("columns", []):
                    col_name = column.get("column_name", "unknown_column")
                    col_type = column.get("data_type", "UNKNOWN")
                    
                    generated_column = {
                        "column_name": col_name,
                        "data_type": col_type,
                        "is_nullable": column.get("is_nullable", True),
                        "is_primary_key": column.get("is_primary_key", False),
                        "description": f"Auto-generated: {col_name} field of type {col_type}",
                        "inferred_purpose": _infer_column_purpose(col_name, col_type),
                        "suggested_validation": _suggest_validation_rules(col_name, col_type),
                        "business_importance": _assess_business_importance(col_name)
                    }
                    
                    if include_ai_descriptions:
                        generated_column["ai_description"] = _generate_ai_description(col_name, col_type)
                    
                    if include_business_rules:
                        generated_column["suggested_business_rules"] = _generate_business_rules(col_name, col_type)
                    
                    generated_table["columns"].append(generated_column)
                
                # Suggest relationships
                generated_table["inferred_relationships"] = _infer_relationships(table_name, generated_table["columns"])
                
                # Suggest indexes
                generated_table["suggested_indexes"] = _suggest_indexes(generated_table["columns"])
                
                generated_dictionary["tables"][table_name] = generated_table
        
        generation_stats = {
            "tables_processed": len(generated_dictionary["tables"]),
            "columns_processed": sum(len(table["columns"]) for table in generated_dictionary["tables"].values()),
            "relationships_inferred": sum(len(table["inferred_relationships"]) for table in generated_dictionary["tables"].values()),
            "indexes_suggested": sum(len(table["suggested_indexes"]) for table in generated_dictionary["tables"].values())
        }
        
        return {
            "status": "generated",
            "data_dictionary": generated_dictionary,
            "generation_stats": generation_stats,
            "confidence_score": 0.85,  # Mock confidence score
            "generation_time_ms": 1200,
            "recommendations": [
                "Review AI-generated descriptions for accuracy",
                "Validate inferred relationships with domain experts",
                "Consider adding business context to generic descriptions",
                "Update data classifications based on content sensitivity"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Generate data dictionary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate data dictionary")


def _infer_column_purpose(col_name: str, col_type: str) -> str:
    """Infer the purpose of a column based on name and type"""
    col_name_lower = col_name.lower()
    
    if "id" == col_name_lower or col_name_lower.endswith("_id"):
        return "identifier"
    elif "name" in col_name_lower:
        return "label"
    elif "email" in col_name_lower:
        return "contact_info"
    elif "date" in col_name_lower or "time" in col_name_lower:
        return "temporal"
    elif "status" in col_name_lower or "state" in col_name_lower:
        return "status_indicator"
    elif "count" in col_name_lower or "amount" in col_name_lower:
        return "metric"
    else:
        return "data_field"


def _suggest_validation_rules(col_name: str, col_type: str) -> List[str]:
    """Suggest validation rules for a column"""
    rules = []
    col_name_lower = col_name.lower()
    
    if "email" in col_name_lower:
        rules.append("Email format validation")
    if "id" in col_name_lower:
        rules.append("Positive integer validation")
    if "status" in col_name_lower:
        rules.append("Enum value validation")
    if "INTEGER" in col_type.upper():
        rules.append("Numeric range validation")
    if "VARCHAR" in col_type.upper():
        rules.append("Length validation")
    
    return rules or ["Basic format validation"]


def _assess_business_importance(col_name: str) -> str:
    """Assess business importance of a column"""
    col_name_lower = col_name.lower()
    
    if any(key in col_name_lower for key in ["id", "key", "primary"]):
        return "critical"
    elif any(key in col_name_lower for key in ["name", "email", "status"]):
        return "high"
    elif any(key in col_name_lower for key in ["description", "notes", "comment"]):
        return "medium"
    else:
        return "standard"


def _generate_ai_description(col_name: str, col_type: str) -> str:
    """Generate AI-enhanced description"""
    return f"AI-enhanced: This {col_type} field '{col_name}' appears to be used for {_infer_column_purpose(col_name, col_type)} purposes based on naming patterns and data type analysis."


def _generate_business_rules(col_name: str, col_type: str) -> List[str]:
    """Generate suggested business rules"""
    rules = []
    col_name_lower = col_name.lower()
    
    if "id" in col_name_lower:
        rules.extend(["Must be unique", "Cannot be null", "Auto-generated preferred"])
    if "email" in col_name_lower:
        rules.extend(["Must be valid email format", "Should be unique per user"])
    if "status" in col_name_lower:
        rules.extend(["Must be from predefined list", "Default value required"])
    if "date" in col_name_lower or "time" in col_name_lower:
        rules.extend(["Cannot be future date for creation timestamps", "Format consistency required"])
    
    return rules or ["Standard data validation applies"]


def _infer_relationships(table_name: str, columns: List[Dict]) -> List[Dict]:
    """Infer potential relationships"""
    relationships = []
    
    for column in columns:
        col_name = column["column_name"].lower()
        if col_name.endswith("_id") and col_name != "id":
            referenced_table = col_name[:-3] + "s"  # Simple pluralization
            relationships.append({
                "type": "foreign_key",
                "column": column["column_name"],
                "references_table": referenced_table,
                "confidence": 0.8,
                "suggestion": f"Likely references {referenced_table} table"
            })
    
    return relationships


def _suggest_indexes(columns: List[Dict]) -> List[Dict]:
    """Suggest appropriate indexes"""
    indexes = []
    
    for column in columns:
        col_name = column["column_name"].lower()
        
        if column.get("is_primary_key"):
            indexes.append({
                "columns": [column["column_name"]],
                "type": "primary_key",
                "purpose": "Primary key constraint"
            })
        elif "email" in col_name:
            indexes.append({
                "columns": [column["column_name"]],
                "type": "unique",
                "purpose": "Ensure email uniqueness"
            })
        elif col_name.endswith("_id"):
            indexes.append({
                "columns": [column["column_name"]],
                "type": "btree",
                "purpose": "Foreign key performance"
            })
        elif "status" in col_name:
            indexes.append({
                "columns": [column["column_name"]],
                "type": "btree", 
                "purpose": "Status filtering performance"
            })
    
    return indexes


@router.delete("/{table_name}")
async def delete_data_dictionary(
    table_name: str,
    project_id: Optional[str] = None,
    confirm: bool = False
):
    """Delete data dictionary for a table"""
    try:
        if not confirm:
            return {
                "message": "Data dictionary deletion requires confirmation",
                "table_name": table_name,
                "project_id": project_id,
                "warning": "This action cannot be undone",
                "confirmation_required": True
            }
        
        # Mock deletion
        return {
            "status": "deleted",
            "table_name": table_name,
            "project_id": project_id,
            "deleted_at": datetime.now().isoformat(),
            "message": f"Data dictionary for table '{table_name}' has been deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Delete data dictionary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete data dictionary")
