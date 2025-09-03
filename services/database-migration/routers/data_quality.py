"""
Data Quality & Cleaning API Routes
Handles data analysis, cleaning, and transformation operations
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import uuid
import json
import pandas as pd
import io
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data", tags=["Data Quality & Cleaning"])

# Data Quality Models
class DataQualityIssueType(str, Enum):
    MISSING_VALUES = "missing_values"
    DUPLICATE_RECORDS = "duplicate_records"
    OUTLIERS = "outliers"
    INCONSISTENT_FORMAT = "inconsistent_format"
    INVALID_VALUES = "invalid_values"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    DATA_TYPE_MISMATCH = "data_type_mismatch"

class CleaningOperation(str, Enum):
    REMOVE_DUPLICATES = "remove_duplicates"
    FILL_MISSING = "fill_missing"
    STANDARDIZE_FORMAT = "standardize_format"
    REMOVE_OUTLIERS = "remove_outliers"
    VALIDATE_CONSTRAINTS = "validate_constraints"
    NORMALIZE_TEXT = "normalize_text"
    CONVERT_DATATYPES = "convert_datatypes"

# In-memory storage for demo
cleaning_operations = {}
data_quality_reports = {}
cleaning_stats = {
    "total_operations": 0,
    "successful_operations": 0,
    "failed_operations": 0,
    "total_records_processed": 0,
    "total_issues_fixed": 0,
    "avg_processing_time_seconds": 0.0
}

def create_sample_data_quality_report(data_source: str) -> Dict[str, Any]:
    """Create a sample data quality report"""
    return {
        "report_id": str(uuid.uuid4()),
        "data_source": data_source,
        "analysis_date": datetime.now().isoformat(),
        "total_records": 10000,
        "total_fields": 25,
        "overall_quality_score": 78.5,
        "issues_found": [
            {
                "issue_type": DataQualityIssueType.MISSING_VALUES.value,
                "severity": "high",
                "affected_fields": ["email", "phone_number", "address"],
                "count": 1500,
                "percentage": 15.0,
                "description": "Missing values in critical customer fields"
            },
            {
                "issue_type": DataQualityIssueType.DUPLICATE_RECORDS.value,
                "severity": "medium",
                "affected_fields": ["customer_id", "email"],
                "count": 350,
                "percentage": 3.5,
                "description": "Duplicate customer records found"
            },
            {
                "issue_type": DataQualityIssueType.INCONSISTENT_FORMAT.value,
                "severity": "medium",
                "affected_fields": ["phone_number", "postal_code"],
                "count": 800,
                "percentage": 8.0,
                "description": "Inconsistent formatting in contact fields"
            },
            {
                "issue_type": DataQualityIssueType.OUTLIERS.value,
                "severity": "low",
                "affected_fields": ["age", "income", "purchase_amount"],
                "count": 250,
                "percentage": 2.5,
                "description": "Statistical outliers in numeric fields"
            }
        ],
        "field_quality": [
            {
                "field_name": "customer_id",
                "data_type": "integer",
                "completeness": 100.0,
                "uniqueness": 96.5,
                "validity": 100.0,
                "quality_score": 98.8
            },
            {
                "field_name": "email",
                "data_type": "string",
                "completeness": 85.0,
                "uniqueness": 96.5,
                "validity": 92.3,
                "quality_score": 91.3
            },
            {
                "field_name": "phone_number",
                "data_type": "string",
                "completeness": 88.0,
                "uniqueness": 95.2,
                "validity": 78.5,
                "quality_score": 87.2
            },
            {
                "field_name": "age",
                "data_type": "integer",
                "completeness": 95.0,
                "uniqueness": 85.0,
                "validity": 97.5,
                "quality_score": 92.5
            }
        ],
        "recommendations": [
            {
                "priority": "high",
                "action": "Implement data validation for email and phone fields",
                "estimated_impact": "Improve quality score by 8-12 points"
            },
            {
                "priority": "medium",
                "action": "Set up duplicate detection and merging processes",
                "estimated_impact": "Reduce duplicate records by 90%"
            },
            {
                "priority": "medium",
                "action": "Standardize phone number and address formats",
                "estimated_impact": "Improve consistency by 85%"
            }
        ],
        "data_profiling": {
            "numeric_fields": 8,
            "text_fields": 12,
            "date_fields": 5,
            "null_percentage": 12.3,
            "duplicate_percentage": 3.5,
            "unique_values_ratio": 0.85
        }
    }

@router.post("/clean")
async def analyze_and_clean_data(request: Dict[str, Any]):
    """Analyze and clean data with specified operations"""
    try:
        data_source = request.get("data_source", "unknown")
        cleaning_operations_list = request.get("operations", [])
        data_sample = request.get("data_sample", [])
        options = request.get("options", {})
        
        logger.info(f"Starting data cleaning for: {data_source}")
        
        operation_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Simulate data analysis
        issues_found = []
        if not cleaning_operations_list:
            # Auto-detect issues if no operations specified
            issues_found = [
                {
                    "type": DataQualityIssueType.MISSING_VALUES.value,
                    "count": 150,
                    "fields": ["email", "phone"],
                    "severity": "high"
                },
                {
                    "type": DataQualityIssueType.DUPLICATE_RECORDS.value,
                    "count": 35,
                    "fields": ["customer_id"],
                    "severity": "medium"
                },
                {
                    "type": DataQualityIssueType.INCONSISTENT_FORMAT.value,
                    "count": 80,
                    "fields": ["phone_number"],
                    "severity": "medium"
                }
            ]
            
            # Suggest operations based on issues
            cleaning_operations_list = [
                CleaningOperation.FILL_MISSING.value,
                CleaningOperation.REMOVE_DUPLICATES.value,
                CleaningOperation.STANDARDIZE_FORMAT.value
            ]
        
        # Perform cleaning operations
        cleaned_data = []
        operations_performed = []
        
        for operation in cleaning_operations_list:
            operation_result = {
                "operation": operation,
                "status": "completed",
                "records_affected": 0,
                "description": "",
                "execution_time_ms": 150
            }
            
            if operation == CleaningOperation.REMOVE_DUPLICATES.value:
                operation_result.update({
                    "records_affected": 35,
                    "description": "Removed 35 duplicate records based on customer_id",
                    "duplicate_criteria": ["customer_id", "email"]
                })
            elif operation == CleaningOperation.FILL_MISSING.value:
                operation_result.update({
                    "records_affected": 150,
                    "description": "Filled missing values using appropriate strategies",
                    "fill_strategies": {
                        "email": "default_placeholder",
                        "phone": "interpolation",
                        "age": "median"
                    }
                })
            elif operation == CleaningOperation.STANDARDIZE_FORMAT.value:
                operation_result.update({
                    "records_affected": 80,
                    "description": "Standardized phone number and address formats",
                    "format_rules": {
                        "phone": "+1-XXX-XXX-XXXX",
                        "postal_code": "XXXXX-XXXX"
                    }
                })
            elif operation == CleaningOperation.REMOVE_OUTLIERS.value:
                operation_result.update({
                    "records_affected": 25,
                    "description": "Removed statistical outliers using IQR method",
                    "outlier_fields": ["age", "income", "purchase_amount"]
                })
            elif operation == CleaningOperation.NORMALIZE_TEXT.value:
                operation_result.update({
                    "records_affected": 200,
                    "description": "Normalized text fields to lowercase and removed extra spaces",
                    "text_fields": ["name", "address", "notes"]
                })
            elif operation == CleaningOperation.CONVERT_DATATYPES.value:
                operation_result.update({
                    "records_affected": 100,
                    "description": "Converted data types for better consistency",
                    "type_conversions": {
                        "age": "string -> integer",
                        "income": "string -> float",
                        "created_date": "string -> datetime"
                    }
                })
            
            operations_performed.append(operation_result)
        
        # Calculate summary metrics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        total_records_processed = len(data_sample) if data_sample else 1000
        total_issues_fixed = sum(op["records_affected"] for op in operations_performed)
        
        # Quality improvement metrics
        original_quality_score = 65.5
        improved_quality_score = min(95.0, original_quality_score + (total_issues_fixed / 50) * 5)
        
        # Store operation record
        operation_record = {
            "operation_id": operation_id,
            "data_source": data_source,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "processing_time_seconds": processing_time,
            "status": "completed",
            "operations_performed": operations_performed,
            "total_records_processed": total_records_processed,
            "total_issues_fixed": total_issues_fixed,
            "quality_improvement": {
                "original_score": original_quality_score,
                "improved_score": improved_quality_score,
                "improvement_percentage": round(((improved_quality_score - original_quality_score) / original_quality_score) * 100, 2)
            }
        }
        
        cleaning_operations[operation_id] = operation_record
        
        # Update global stats
        cleaning_stats["total_operations"] += 1
        cleaning_stats["successful_operations"] += 1
        cleaning_stats["total_records_processed"] += total_records_processed
        cleaning_stats["total_issues_fixed"] += total_issues_fixed
        cleaning_stats["avg_processing_time_seconds"] = round(
            (cleaning_stats["avg_processing_time_seconds"] + processing_time) / 2, 2
        )
        
        return {
            "operation_id": operation_id,
            "status": "completed",
            "data_source": data_source,
            "processing_summary": {
                "total_records_processed": total_records_processed,
                "total_issues_fixed": total_issues_fixed,
                "processing_time_seconds": processing_time,
                "operations_count": len(operations_performed)
            },
            "quality_metrics": {
                "original_quality_score": original_quality_score,
                "improved_quality_score": improved_quality_score,
                "improvement_percentage": round(((improved_quality_score - original_quality_score) / original_quality_score) * 100, 2),
                "issues_resolved": len([op for op in operations_performed if op["records_affected"] > 0])
            },
            "operations_performed": operations_performed,
            "issues_detected": issues_found,
            "recommendations": [
                "Consider implementing automated data validation rules",
                "Set up periodic data quality monitoring",
                "Establish data governance policies for consistent formatting"
            ],
            "cleaned_data_preview": [
                {
                    "customer_id": 1,
                    "name": "john doe",
                    "email": "john.doe@email.com",
                    "phone": "+1-555-123-4567",
                    "age": 35,
                    "status": "cleaned"
                },
                {
                    "customer_id": 2,
                    "name": "jane smith",
                    "email": "jane.smith@email.com",
                    "phone": "+1-555-987-6543",
                    "age": 28,
                    "status": "cleaned"
                }
            ][:5]  # Show only first 5 records
        }
        
    except Exception as e:
        logger.error(f"Error in data cleaning: {e}")
        cleaning_stats["failed_operations"] += 1
        raise HTTPException(status_code=500, detail="Failed to clean data")

@router.post("/transform")
async def transform_data_with_nl(request: Dict[str, Any]):
    """Transform data using natural language instructions"""
    try:
        data_source = request.get("data_source", "unknown")
        instructions = request.get("instructions", "")
        data_sample = request.get("data_sample", [])
        
        if not instructions:
            raise HTTPException(status_code=400, detail="Instructions are required")
        
        logger.info(f"Transforming data with NL instructions: {instructions[:100]}...")
        
        transformation_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # Parse natural language instructions (mock implementation)
        parsed_operations = []
        instructions_lower = instructions.lower()
        
        if "remove duplicate" in instructions_lower:
            parsed_operations.append({
                "type": "remove_duplicates",
                "description": "Remove duplicate records",
                "confidence": 0.95
            })
        
        if "fill missing" in instructions_lower or "handle null" in instructions_lower:
            parsed_operations.append({
                "type": "fill_missing",
                "description": "Fill missing values",
                "confidence": 0.90
            })
        
        if "standardize" in instructions_lower or "normalize" in instructions_lower:
            parsed_operations.append({
                "type": "standardize_format",
                "description": "Standardize data formats",
                "confidence": 0.85
            })
        
        if "convert" in instructions_lower and "type" in instructions_lower:
            parsed_operations.append({
                "type": "convert_datatypes",
                "description": "Convert data types",
                "confidence": 0.80
            })
        
        if "remove outlier" in instructions_lower:
            parsed_operations.append({
                "type": "remove_outliers",
                "description": "Remove statistical outliers",
                "confidence": 0.88
            })
        
        # If no specific operations detected, provide general data cleaning
        if not parsed_operations:
            parsed_operations = [
                {
                    "type": "general_cleaning",
                    "description": "General data cleaning and validation",
                    "confidence": 0.70
                }
            ]
        
        # Execute transformations
        transformation_results = []
        for operation in parsed_operations:
            result = {
                "operation": operation["type"],
                "description": operation["description"],
                "confidence": operation["confidence"],
                "records_affected": 50 + len(operation["type"]) * 10,  # Mock calculation
                "status": "completed",
                "execution_time_ms": 200
            }
            transformation_results.append(result)
        
        # Generate transformed data sample
        transformed_sample = []
        if data_sample:
            # Mock transformation of sample data
            for record in data_sample[:5]:  # Process first 5 records
                transformed_record = record.copy()
                transformed_record["_transformation_applied"] = True
                transformed_record["_transformation_id"] = transformation_id
                transformed_sample.append(transformed_record)
        else:
            # Generate mock transformed data
            transformed_sample = [
                {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "+1-555-123-4567",
                    "age": 35,
                    "_transformation_applied": True,
                    "_transformation_id": transformation_id
                },
                {
                    "id": 2,
                    "name": "Jane Smith", 
                    "email": "jane.smith@email.com",
                    "phone": "+1-555-987-6543",
                    "age": 28,
                    "_transformation_applied": True,
                    "_transformation_id": transformation_id
                }
            ]
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        total_records = len(data_sample) if data_sample else 1000
        total_affected = sum(result["records_affected"] for result in transformation_results)
        
        return {
            "transformation_id": transformation_id,
            "status": "completed",
            "data_source": data_source,
            "original_instructions": instructions,
            "parsed_operations": parsed_operations,
            "transformation_summary": {
                "total_records_processed": total_records,
                "total_records_affected": total_affected,
                "operations_executed": len(transformation_results),
                "processing_time_seconds": processing_time,
                "success_rate": 100.0
            },
            "transformation_results": transformation_results,
            "transformed_data_preview": transformed_sample,
            "nl_processing": {
                "instructions_understood": True,
                "confidence_score": round(sum(op["confidence"] for op in parsed_operations) / len(parsed_operations), 2),
                "operations_detected": len(parsed_operations),
                "suggestions": [
                    "Be more specific about field names for better accuracy",
                    "Include data type conversion requirements if needed",
                    "Specify validation rules for transformed data"
                ]
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "processing_method": "natural_language",
                "version": "1.0"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in NL data transformation: {e}")
        raise HTTPException(status_code=500, detail="Failed to transform data")

@router.get("/cleaning/recent")
async def get_recent_cleaning_operations(
    limit: int = Query(20, ge=1, le=100, description="Number of operations to return"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get recent data cleaning operations"""
    try:
        operations = list(cleaning_operations.values())
        
        # Apply status filter
        if status:
            operations = [op for op in operations if op["status"] == status]
        
        # Sort by start time (newest first)
        operations.sort(key=lambda x: x["start_time"], reverse=True)
        
        # Apply limit
        operations = operations[:limit]
        
        # Add summary statistics
        total_operations = len(cleaning_operations)
        successful_operations = len([op for op in cleaning_operations.values() if op["status"] == "completed"])
        failed_operations = total_operations - successful_operations
        
        return {
            "recent_operations": operations,
            "summary": {
                "total_shown": len(operations),
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "filter_applied": status is not None
            },
            "performance_metrics": {
                "avg_processing_time": cleaning_stats["avg_processing_time_seconds"],
                "total_records_processed": cleaning_stats["total_records_processed"],
                "total_issues_fixed": cleaning_stats["total_issues_fixed"],
                "success_rate": round((successful_operations / max(1, total_operations)) * 100, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting recent cleaning operations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent operations")

@router.get("/quality/analyze/{data_source}")
async def analyze_data_quality(data_source: str):
    """Analyze data quality for a specific data source"""
    try:
        logger.info(f"Analyzing data quality for: {data_source}")
        
        # Generate or retrieve data quality report
        if data_source not in data_quality_reports:
            data_quality_reports[data_source] = create_sample_data_quality_report(data_source)
        
        report = data_quality_reports[data_source]
        
        # Add real-time quality metrics
        current_metrics = {
            "analysis_timestamp": datetime.now().isoformat(),
            "data_freshness_hours": 2.5,
            "monitoring_status": "active",
            "quality_trend": "improving",  # "improving", "stable", "declining"
            "last_quality_check": (datetime.now() - timedelta(hours=1)).isoformat()
        }
        
        report["current_metrics"] = current_metrics
        
        return report
        
    except Exception as e:
        logger.error(f"Error analyzing data quality: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze data quality")

@router.post("/quality/rules")
async def create_data_quality_rule(request: Dict[str, Any]):
    """Create a custom data quality rule"""
    try:
        rule_name = request.get("rule_name", "")
        rule_type = request.get("rule_type", "validation")  # "validation", "completeness", "consistency"
        field_name = request.get("field_name", "")
        conditions = request.get("conditions", {})
        severity = request.get("severity", "medium")  # "low", "medium", "high", "critical"
        
        if not rule_name or not field_name:
            raise HTTPException(status_code=400, detail="rule_name and field_name are required")
        
        rule_id = str(uuid.uuid4())
        
        quality_rule = {
            "rule_id": rule_id,
            "rule_name": rule_name,
            "rule_type": rule_type,
            "field_name": field_name,
            "conditions": conditions,
            "severity": severity,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "violations_count": 0,
            "last_executed": None
        }
        
        return {
            "rule_id": rule_id,
            "status": "created",
            "rule": quality_rule,
            "message": f"Data quality rule '{rule_name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data quality rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create data quality rule")

@router.get("/stats")
async def get_data_cleaning_statistics():
    """Get comprehensive data cleaning and quality statistics"""
    try:
        # Calculate additional metrics
        total_operations = len(cleaning_operations)
        if total_operations > 0:
            success_rate = (cleaning_stats["successful_operations"] / total_operations) * 100
            avg_issues_per_operation = cleaning_stats["total_issues_fixed"] / total_operations
        else:
            success_rate = 0
            avg_issues_per_operation = 0
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_operations = [
            op for op in cleaning_operations.values()
            if datetime.fromisoformat(op["start_time"]) > seven_days_ago
        ]
        
        # Data quality trends
        quality_trends = {
            "weekly_operations": len(recent_operations),
            "weekly_records_processed": sum(op["total_records_processed"] for op in recent_operations),
            "weekly_issues_fixed": sum(op["total_issues_fixed"] for op in recent_operations),
            "average_quality_improvement": 12.5,  # Mock percentage
            "trending_issues": [
                {"type": "missing_values", "count": 450, "trend": "increasing"},
                {"type": "duplicate_records", "count": 125, "trend": "stable"},
                {"type": "format_inconsistency", "count": 280, "trend": "decreasing"}
            ]
        }
        
        # Performance metrics
        performance_metrics = {
            "fastest_operation_seconds": 0.5,
            "slowest_operation_seconds": 45.2,
            "median_processing_time_seconds": 5.8,
            "operations_per_day": round(len(recent_operations) / 7, 1),
            "peak_processing_hours": ["14:00-16:00", "09:00-11:00"]
        }
        
        return {
            "overview": cleaning_stats,
            "performance": {
                **performance_metrics,
                "success_rate_percentage": round(success_rate, 2),
                "average_issues_per_operation": round(avg_issues_per_operation, 2),
                "total_data_sources_processed": len(set(op.get("data_source", "unknown") for op in cleaning_operations.values()))
            },
            "recent_activity": quality_trends,
            "data_quality_health": {
                "monitored_sources": len(data_quality_reports),
                "active_quality_rules": 15,  # Mock count
                "average_quality_score": 82.3,
                "quality_violations_last_week": 45,
                "data_freshness_score": 94.5
            },
            "operational_insights": {
                "most_common_issues": [
                    {"issue": "missing_values", "frequency": 35.2},
                    {"issue": "duplicate_records", "frequency": 18.7},
                    {"issue": "format_inconsistency", "frequency": 22.1},
                    {"issue": "outliers", "frequency": 12.4},
                    {"issue": "invalid_values", "frequency": 11.6}
                ],
                "most_effective_operations": [
                    {"operation": "remove_duplicates", "avg_improvement": 15.2},
                    {"operation": "fill_missing", "avg_improvement": 12.8},
                    {"operation": "standardize_format", "avg_improvement": 10.5}
                ],
                "recommendations": [
                    "Implement proactive data validation to reduce missing values",
                    "Set up automated duplicate detection workflows",
                    "Consider real-time data quality monitoring for critical sources"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting data cleaning statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/operations/{operation_id}")
async def get_cleaning_operation_details(operation_id: str):
    """Get detailed information about a specific cleaning operation"""
    try:
        if operation_id not in cleaning_operations:
            raise HTTPException(status_code=404, detail="Operation not found")
        
        operation = cleaning_operations[operation_id]
        
        # Add additional details for the specific operation
        detailed_operation = operation.copy()
        detailed_operation["detailed_logs"] = [
            f"[{operation['start_time']}] Operation started",
            f"[{operation['start_time']}] Analyzing data source: {operation['data_source']}",
            f"[{operation['start_time']}] Detected {len(operation['operations_performed'])} cleaning operations needed",
            f"[{operation['end_time']}] Successfully processed {operation['total_records_processed']} records",
            f"[{operation['end_time']}] Fixed {operation['total_issues_fixed']} data quality issues",
            f"[{operation['end_time']}] Operation completed successfully"
        ]
        
        return detailed_operation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get operation details")
