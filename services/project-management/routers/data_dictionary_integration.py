"""
Data Dictionary Integration API Routes

Handles data dictionary integration with project management features.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Router for data dictionary integration
router = APIRouter(prefix="/data-dictionary", tags=["data_dictionary"])


@router.post("/project/{project_id}/generate")
async def generate_project_data_dictionary(
    project_id: int,
    generation_options: Dict[str, Any]
):
    """Generate comprehensive data dictionary for a project"""
    try:
        # Mock data dictionary generation for project
        data_dictionary = {
            "project_id": project_id,
            "project_name": "E-commerce Platform",
            "generated_at": datetime.now().isoformat(),
            "version": "1.2.0",
            "metadata": {
                "total_tables": 15,
                "total_columns": 127,
                "total_relationships": 23,
                "coverage_percentage": 95.5,
                "quality_score": 8.7
            },
            "schemas": [
                {
                    "schema_name": "public",
                    "description": "Main application schema containing core business entities",
                    "tables": [
                        {
                            "table_name": "users",
                            "description": "System users including customers and administrators",
                            "purpose": "Store user account information and authentication data",
                            "business_rules": [
                                "Email addresses must be unique across all users",
                                "User accounts are soft-deleted by setting deleted_at timestamp",
                                "Password must meet complexity requirements (8+ chars, mixed case, numbers)"
                            ],
                            "data_classification": "PII - Personal Information",
                            "retention_policy": "7 years after account closure",
                            "columns": [
                                {
                                    "column_name": "id",
                                    "data_type": "INTEGER",
                                    "is_nullable": False,
                                    "is_primary_key": True,
                                    "description": "Unique identifier for user record",
                                    "business_meaning": "System-generated sequential ID for internal reference",
                                    "valid_values": "Positive integers starting from 1",
                                    "example_values": ["1", "2", "3"],
                                    "related_tables": ["orders.user_id", "user_profiles.user_id"]
                                },
                                {
                                    "column_name": "email",
                                    "data_type": "VARCHAR(255)",
                                    "is_nullable": False,
                                    "is_primary_key": False,
                                    "description": "User's email address for authentication and communication",
                                    "business_meaning": "Primary contact method and login identifier",
                                    "valid_values": "Valid email format as per RFC 5322",
                                    "example_values": ["john@example.com", "jane.smith@company.org"],
                                    "constraints": ["UNIQUE", "EMAIL_FORMAT"],
                                    "data_quality_rules": [
                                        "Must contain @ symbol",
                                        "Domain must be valid",
                                        "No duplicate emails allowed"
                                    ]
                                },
                                {
                                    "column_name": "created_at",
                                    "data_type": "TIMESTAMP",
                                    "is_nullable": False,
                                    "is_primary_key": False,
                                    "description": "Timestamp when user account was created",
                                    "business_meaning": "Account registration date for analytics and compliance",
                                    "valid_values": "UTC timestamps",
                                    "example_values": ["2024-01-15T10:30:00Z"],
                                    "default_value": "CURRENT_TIMESTAMP"
                                }
                            ],
                            "indexes": [
                                {
                                    "name": "idx_users_email",
                                    "columns": ["email"],
                                    "type": "UNIQUE",
                                    "purpose": "Ensure email uniqueness and fast login lookups"
                                }
                            ],
                            "foreign_keys": [],
                            "sample_queries": [
                                {
                                    "purpose": "Find user by email",
                                    "query": "SELECT * FROM users WHERE email = 'john@example.com'"
                                },
                                {
                                    "purpose": "Get recently registered users",
                                    "query": "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days'"
                                }
                            ]
                        },
                        {
                            "table_name": "orders",
                            "description": "Customer orders and purchase transactions",
                            "purpose": "Track all customer purchases and order lifecycle",
                            "business_rules": [
                                "Order total must be greater than 0",
                                "Order status follows defined workflow: pending -> processing -> shipped -> delivered",
                                "Orders cannot be deleted, only cancelled"
                            ],
                            "data_classification": "Business Critical",
                            "retention_policy": "10 years for financial compliance",
                            "columns": [
                                {
                                    "column_name": "id",
                                    "data_type": "INTEGER",
                                    "is_nullable": False,
                                    "is_primary_key": True,
                                    "description": "Unique identifier for order record",
                                    "business_meaning": "System-generated order number for tracking",
                                    "valid_values": "Positive integers",
                                    "example_values": ["1001", "1002", "1003"]
                                },
                                {
                                    "column_name": "user_id",
                                    "data_type": "INTEGER",
                                    "is_nullable": False,
                                    "is_primary_key": False,
                                    "description": "Reference to the user who placed the order",
                                    "business_meaning": "Links order to customer account",
                                    "valid_values": "Must exist in users.id",
                                    "example_values": ["1", "2", "5"],
                                    "foreign_key": "users.id"
                                },
                                {
                                    "column_name": "status",
                                    "data_type": "VARCHAR(50)",
                                    "is_nullable": False,
                                    "is_primary_key": False,
                                    "description": "Current status of the order",
                                    "business_meaning": "Tracks order progression through fulfillment pipeline",
                                    "valid_values": "pending, processing, shipped, delivered, cancelled",
                                    "example_values": ["pending", "processing", "delivered"],
                                    "default_value": "pending"
                                },
                                {
                                    "column_name": "total_amount",
                                    "data_type": "DECIMAL(10,2)",
                                    "is_nullable": False,
                                    "is_primary_key": False,
                                    "description": "Total order value including taxes and shipping",
                                    "business_meaning": "Final amount charged to customer",
                                    "valid_values": "Positive decimal values",
                                    "example_values": ["29.99", "156.78", "1250.00"],
                                    "constraints": ["CHECK (total_amount > 0)"]
                                }
                            ],
                            "relationships": [
                                {
                                    "type": "belongs_to",
                                    "target_table": "users",
                                    "description": "Each order belongs to one user"
                                }
                            ]
                        }
                    ]
                }
            ],
            "glossary": {
                "terms": [
                    {
                        "term": "PII",
                        "definition": "Personally Identifiable Information - data that can identify a specific individual",
                        "examples": ["email", "phone", "address", "name"]
                    },
                    {
                        "term": "Soft Delete",
                        "definition": "Marking records as deleted without physically removing them from database",
                        "implementation": "Setting deleted_at timestamp field"
                    },
                    {
                        "term": "Business Critical",
                        "definition": "Data essential for core business operations and revenue generation",
                        "examples": ["orders", "payments", "inventory"]
                    }
                ]
            },
            "compliance_info": {
                "regulations": [
                    {
                        "name": "GDPR",
                        "applicable_tables": ["users", "user_profiles"],
                        "requirements": [
                            "Right to erasure (delete user data)",
                            "Data portability (export user data)",
                            "Consent tracking"
                        ]
                    },
                    {
                        "name": "SOX",
                        "applicable_tables": ["orders", "payments"],
                        "requirements": [
                            "Financial data retention for 7 years",
                            "Audit trail for all changes",
                            "Access controls and segregation of duties"
                        ]
                    }
                ]
            }
        }
        
        return {
            "data_dictionary": data_dictionary,
            "generation_info": {
                "generated_by": generation_options.get("user_id", 1),
                "include_examples": generation_options.get("include_examples", True),
                "include_business_rules": generation_options.get("include_business_rules", True),
                "include_compliance": generation_options.get("include_compliance", True),
                "ai_enhanced": generation_options.get("ai_enhanced", True)
            },
            "download_links": {
                "pdf": f"/data-dictionary/project/{project_id}/download/pdf",
                "excel": f"/data-dictionary/project/{project_id}/download/excel",
                "html": f"/data-dictionary/project/{project_id}/download/html"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating project data dictionary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate project data dictionary")


@router.get("/project/{project_id}")
async def get_project_data_dictionary(
    project_id: int,
    version: Optional[str] = None,
    format: str = Query("json", regex="^(json|summary)$")
):
    """Get existing data dictionary for a project"""
    try:
        if format == "summary":
            # Return summary version
            summary = {
                "project_id": project_id,
                "project_name": "E-commerce Platform",
                "current_version": "1.2.0",
                "last_updated": "2024-01-15T14:30:00Z",
                "statistics": {
                    "total_tables": 15,
                    "total_columns": 127,
                    "documented_columns": 121,
                    "coverage_percentage": 95.3,
                    "quality_score": 8.7
                },
                "recent_changes": [
                    {
                        "change_type": "column_added",
                        "table": "users",
                        "column": "last_login_at",
                        "timestamp": "2024-01-15T10:30:00Z"
                    },
                    {
                        "change_type": "description_updated",
                        "table": "orders",
                        "column": "status",
                        "timestamp": "2024-01-14T16:45:00Z"
                    }
                ],
                "compliance_status": {
                    "gdpr_compliant": True,
                    "sox_compliant": True,
                    "missing_classifications": 3
                }
            }
            return summary
        else:
            # Return full data dictionary (truncated for demo)
            return {
                "project_id": project_id,
                "version": version or "1.2.0",
                "schemas": [
                    {
                        "schema_name": "public",
                        "table_count": 15,
                        "documentation_coverage": 95.3
                    }
                ],
                "message": "Full data dictionary available via generate endpoint"
            }
        
    except Exception as e:
        logger.error(f"Error getting project data dictionary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project data dictionary")


@router.put("/project/{project_id}/table/{table_name}")
async def update_table_documentation(
    project_id: int,
    table_name: str,
    documentation_data: Dict[str, Any]
):
    """Update documentation for a specific table"""
    try:
        updated_table = {
            "project_id": project_id,
            "table_name": table_name,
            "description": documentation_data.get("description", ""),
            "purpose": documentation_data.get("purpose", ""),
            "business_rules": documentation_data.get("business_rules", []),
            "data_classification": documentation_data.get("data_classification", ""),
            "retention_policy": documentation_data.get("retention_policy", ""),
            "column_updates": documentation_data.get("column_updates", {}),
            "updated_by": documentation_data.get("updated_by", 1),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "table": updated_table,
            "message": "Table documentation updated successfully",
            "impact": {
                "documentation_coverage_change": "+2.1%",
                "quality_score_change": "+0.3"
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating table documentation: {e}")
        raise HTTPException(status_code=500, detail="Failed to update table documentation")


@router.post("/project/{project_id}/table/{table_name}/auto-document")
async def auto_generate_table_documentation(
    project_id: int,
    table_name: str,
    options: Dict[str, Any]
):
    """Auto-generate documentation for a table using AI"""
    try:
        # Mock AI-generated documentation
        generated_docs = {
            "table_name": table_name,
            "generated_description": f"The {table_name} table stores and manages data related to {table_name.replace('_', ' ')} in the system. This table serves as a central repository for tracking and maintaining information throughout the application lifecycle.",
            "inferred_purpose": f"Primary storage for {table_name.replace('_', ' ')} entities with relationships to other core business objects",
            "suggested_business_rules": [
                f"Records in {table_name} must maintain referential integrity",
                f"All {table_name} records require valid timestamps",
                "Soft deletion should be implemented for data retention"
            ],
            "inferred_data_classification": _classify_table_data(table_name),
            "suggested_retention_policy": _suggest_retention_policy(table_name),
            "column_documentation": [
                {
                    "column_name": "id",
                    "suggested_description": f"Unique identifier for {table_name} record",
                    "business_meaning": "Primary key for internal system reference and relationships",
                    "confidence_score": 0.95
                },
                {
                    "column_name": "created_at",
                    "suggested_description": f"Timestamp when {table_name.rstrip('s')} was created",
                    "business_meaning": "Audit trail and temporal analysis support",
                    "confidence_score": 0.92
                }
            ],
            "generation_metadata": {
                "ai_model": "claude-3",
                "confidence_score": 0.87,
                "generated_at": datetime.now().isoformat(),
                "include_examples": options.get("include_examples", True),
                "analysis_depth": options.get("analysis_depth", "comprehensive")
            }
        }
        
        return {
            "generated_documentation": generated_docs,
            "message": "Table documentation generated successfully",
            "next_steps": [
                "Review generated descriptions for accuracy",
                "Add domain-specific business rules",
                "Validate data classification",
                "Apply suggested documentation"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error auto-generating table documentation: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-generate table documentation")


@router.get("/project/{project_id}/coverage-report")
async def get_documentation_coverage_report(
    project_id: int,
    detail_level: str = Query("summary", regex="^(summary|detailed)$")
):
    """Get documentation coverage report for a project"""
    try:
        base_report = {
            "project_id": project_id,
            "project_name": "E-commerce Platform",
            "generated_at": datetime.now().isoformat(),
            "overall_coverage": {
                "percentage": 85.7,
                "total_items": 142,
                "documented_items": 121,
                "missing_items": 21
            },
            "coverage_by_type": {
                "tables": {
                    "total": 15,
                    "with_descriptions": 13,
                    "with_purpose": 11,
                    "with_business_rules": 8,
                    "percentage": 86.7
                },
                "columns": {
                    "total": 127,
                    "with_descriptions": 108,
                    "with_business_meaning": 95,
                    "with_examples": 78,
                    "percentage": 85.0
                },
                "relationships": {
                    "total": 23,
                    "documented": 20,
                    "percentage": 87.0
                }
            },
            "quality_metrics": {
                "description_quality": 8.2,
                "business_rule_completeness": 7.5,
                "example_coverage": 6.8,
                "overall_quality": 7.5
            }
        }
        
        if detail_level == "detailed":
            base_report["detailed_breakdown"] = {
                "tables_missing_documentation": [
                    {
                        "table_name": "temp_calculations",
                        "missing": ["description", "purpose", "business_rules"]
                    },
                    {
                        "table_name": "audit_logs",
                        "missing": ["business_rules", "retention_policy"]
                    }
                ],
                "columns_missing_documentation": [
                    {
                        "table": "users",
                        "column": "metadata_json",
                        "missing": ["description", "business_meaning"]
                    },
                    {
                        "table": "orders", 
                        "column": "discount_code",
                        "missing": ["examples", "valid_values"]
                    }
                ],
                "recommendations": [
                    {
                        "priority": "high",
                        "type": "missing_description",
                        "item": "temp_calculations table",
                        "action": "Add table description and purpose"
                    },
                    {
                        "priority": "medium",
                        "type": "incomplete_column_docs",
                        "item": "metadata_json column",
                        "action": "Define JSON schema and provide examples"
                    }
                ]
            }
        
        return base_report
        
    except Exception as e:
        logger.error(f"Error getting documentation coverage report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate coverage report")


@router.post("/project/{project_id}/export")
async def export_data_dictionary(
    project_id: int,
    export_options: Dict[str, Any]
):
    """Export data dictionary in various formats"""
    try:
        export_format = export_options.get("format", "pdf")
        include_sections = export_options.get("include_sections", [
            "table_descriptions",
            "column_details", 
            "relationships",
            "business_rules",
            "compliance_info"
        ])
        
        export_job = {
            "job_id": f"export_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "project_id": project_id,
            "format": export_format,
            "status": "processing",
            "progress": 0,
            "estimated_completion": "2024-01-15T15:05:00Z",
            "created_at": datetime.now().isoformat(),
            "options": {
                "format": export_format,
                "include_sections": include_sections,
                "include_examples": export_options.get("include_examples", True),
                "include_diagrams": export_options.get("include_diagrams", True),
                "template": export_options.get("template", "standard")
            }
        }
        
        # Simulate different format capabilities
        format_info = {
            "pdf": {
                "file_extension": ".pdf",
                "supports_diagrams": True,
                "supports_styling": True,
                "estimated_size_mb": 2.5
            },
            "excel": {
                "file_extension": ".xlsx",
                "supports_diagrams": False,
                "supports_styling": True,
                "estimated_size_mb": 1.2
            },
            "html": {
                "file_extension": ".html",
                "supports_diagrams": True,
                "supports_styling": True,
                "estimated_size_mb": 0.8
            },
            "markdown": {
                "file_extension": ".md",
                "supports_diagrams": False,
                "supports_styling": False,
                "estimated_size_mb": 0.3
            }
        }
        
        return {
            "export_job": export_job,
            "format_info": format_info.get(export_format, {}),
            "download_url": f"/data-dictionary/project/{project_id}/download/{export_job['job_id']}",
            "message": "Export started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error exporting data dictionary: {e}")
        raise HTTPException(status_code=500, detail="Failed to start export")


@router.get("/project/{project_id}/compare-versions")
async def compare_data_dictionary_versions(
    project_id: int,
    version1: str,
    version2: str
):
    """Compare two versions of a data dictionary"""
    try:
        comparison = {
            "project_id": project_id,
            "comparison": {
                "version1": version1,
                "version2": version2
            },
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "tables_added": 2,
                "tables_removed": 0,
                "tables_modified": 3,
                "columns_added": 8,
                "columns_removed": 1,
                "columns_modified": 12,
                "documentation_changes": 15
            },
            "changes": [
                {
                    "type": "table_added",
                    "table_name": "user_preferences",
                    "details": "New table for storing user preference settings"
                },
                {
                    "type": "column_added",
                    "table_name": "users",
                    "column_name": "last_login_at",
                    "details": "Added timestamp tracking for user login analytics"
                },
                {
                    "type": "documentation_updated",
                    "table_name": "orders",
                    "column_name": "status",
                    "old_description": "Order status",
                    "new_description": "Current status of the order in fulfillment pipeline",
                    "change_type": "description_enhanced"
                },
                {
                    "type": "business_rule_added",
                    "table_name": "products",
                    "rule": "Product prices must be greater than 0"
                }
            ],
            "impact_analysis": {
                "breaking_changes": 0,
                "documentation_improvements": 15,
                "compliance_updates": 2,
                "recommended_actions": [
                    "Update application code to handle new user_preferences table",
                    "Review enhanced documentation for accuracy",
                    "Update API documentation to reflect schema changes"
                ]
            }
        }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing data dictionary versions: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare versions")


def _classify_table_data(table_name: str) -> str:
    """Classify data based on table name patterns"""
    sensitive_patterns = ["user", "customer", "person", "employee", "account"]
    financial_patterns = ["order", "payment", "transaction", "invoice", "billing"]
    
    table_lower = table_name.lower()
    
    if any(pattern in table_lower for pattern in sensitive_patterns):
        return "PII - Personal Information"
    elif any(pattern in table_lower for pattern in financial_patterns):
        return "Business Critical - Financial"
    else:
        return "Internal - Business Data"


def _suggest_retention_policy(table_name: str) -> str:
    """Suggest retention policy based on table type"""
    financial_patterns = ["order", "payment", "transaction", "invoice"]
    audit_patterns = ["log", "audit", "history"]
    user_patterns = ["user", "customer", "person"]
    
    table_lower = table_name.lower()
    
    if any(pattern in table_lower for pattern in financial_patterns):
        return "7 years (financial compliance requirement)"
    elif any(pattern in table_lower for pattern in audit_patterns):
        return "3 years (audit trail requirement)"
    elif any(pattern in table_lower for pattern in user_patterns):
        return "Data subject request basis (GDPR compliance)"
    else:
        return "3 years (standard business data retention)"
