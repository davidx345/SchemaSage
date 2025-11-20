"""
Compliance Auto-Fixer Router.
Handles encryption detection, access control auditing, and compliance reporting.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.compliance_models import (
    EncryptionDetectionRequest, EncryptionDetectionResponse,
    AccessControlRequest, AccessControlResponse,
    ComplianceReportRequest, ComplianceReportResponse
)
from core.compliance import EncryptionScanner, AccessAuditor, ReportGenerator
from core.auth import get_optional_user

router = APIRouter(prefix="/api/compliance", tags=["compliance"])
logger = logging.getLogger(__name__)

# Initialize core services
encryption_scanner = EncryptionScanner()
access_auditor = AccessAuditor()
report_generator = ReportGenerator()

@router.post("/detect-encryption", response_model=EncryptionDetectionResponse)
async def detect_encryption(
    request: EncryptionDetectionRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Detects unencrypted PII in the provided schema.
    """
    try:
        logger.info(f"Starting encryption detection for schema with {len(request.schema_data.tables)} tables")
        
        result = encryption_scanner.scan(request.schema_data, request.connection_string)
        
        return EncryptionDetectionResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error in encryption detection: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/audit-access-control", response_model=AccessControlResponse)
async def audit_access_control(
    request: AccessControlRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Audits database access controls against compliance frameworks.
    """
    try:
        logger.info(f"Starting access control audit for {request.database_type} against {request.compliance_framework}")
        
        result = access_auditor.audit(request.database_type, request.connection_string, request.compliance_framework)
        
        return AccessControlResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error in access control audit: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/generate-report", response_model=ComplianceReportResponse)
async def generate_report(
    request: ComplianceReportRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Generates a comprehensive compliance report.
    """
    try:
        logger.info(f"Generating compliance report for frameworks: {request.frameworks}")
        
        result = report_generator.generate(request.database_type, request.connection_string, request.frameworks)
        
        return ComplianceReportResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
