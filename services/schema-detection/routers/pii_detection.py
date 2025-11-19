"""
PII Detection Router - Priority 1 (Week 1)
POST /api/compliance/detect-pii - Detect PII fields in database schema
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List
import logging

from models.compliance_models import (
    PIIDetectionRequest,
    PIIDetectionResponse,
    PIIField,
    PIISummary,
    ErrorResponse
)
from core.pii import PIIDetectorRegistry
from core.auth import get_optional_user

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])
logger = logging.getLogger(__name__)


@router.post("/detect-pii", response_model=PIIDetectionResponse)
async def detect_pii(
    request: PIIDetectionRequest,
    current_user: Dict = Depends(get_optional_user)
):
    """
    Detect PII (Personally Identifiable Information) in database schema.
    Priority P1 (MVP - Week 1).
    Scans tables and columns to identify sensitive data fields.
    """
    try:
        logger.info(
            f"PII detection request: {len(request.schema.tables)} tables, "
            f"db_type={request.schema.database_type}, "
            f"user={current_user.get('username', 'anonymous') if current_user else 'anonymous'}"
        )
        
        # Initialize PII detector
        detector = PIIDetectorRegistry()
        
        # Scan all tables and columns
        pii_fields = []
        total_affected_records = 0
        all_frameworks = set()
        highest_risk = "low"
        
        for table in request.schema.tables:
            for column in table.columns:
                # Detect PII
                detection_result = detector.detect_pii(column.name, column.type)
                
                if detection_result:
                    # Estimate affected records (mock for now)
                    affected_records = 100000  # Would query DB in production
                    
                    pii_field = {
                        "table": table.name,
                        "column": column.name,
                        "pii_type": detection_result["pii_type"],
                        "confidence": detection_result["confidence"],
                        "severity": detection_result["severity"],
                        "affected_records": affected_records,
                        "compliance_frameworks": detection_result["frameworks"],
                        "recommendations": detection_result["recommendations"]
                    }
                    
                    pii_fields.append(pii_field)
                    total_affected_records += affected_records
                    all_frameworks.update(detection_result["frameworks"])
                    
                    # Update highest risk level
                    severity_order = ["low", "medium", "high", "critical"]
                    if severity_order.index(detection_result["severity"]) > severity_order.index(highest_risk):
                        highest_risk = detection_result["severity"]
        
        # Create summary
        summary = {
            "total_pii_fields": len(pii_fields),
            "total_affected_records": total_affected_records,
            "compliance_risk": highest_risk,
            "frameworks_affected": sorted(list(all_frameworks))
        }
        
        logger.info(
            f"PII detection completed: {len(pii_fields)} PII fields found, "
            f"risk={highest_risk}, frameworks={summary['frameworks_affected']}"
        )
        
        return {
            "success": True,
            "data": {
                "pii_fields": pii_fields,
                "summary": summary
            }
        }
        
    except ValueError as e:
        logger.error(f"Validation error in PII detection: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_SCHEMA",
                    "message": str(e),
                    "details": {"issue": "Invalid schema format"}
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Error in PII detection: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "DETECTION_ERROR",
                    "message": "Failed to detect PII",
                    "details": {"error": str(e)}
                }
            }
        )


@router.get("/health")
async def compliance_service_health():
    """Health check for compliance service"""
    return {
        "service": "compliance-analysis",
        "status": "healthy",
        "features": ["pii_detection"],
        "version": "1.0.0"
    }
