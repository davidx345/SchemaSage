"""
Schema Debt Tracker Router.
Handles antipattern detection, technical debt calculation, and prioritization.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.debt_models import (
    AntipatternDetectionRequest, AntipatternDetectionResponse,
    TechnicalDebtRequest, TechnicalDebtResponse,
    PrioritizationRequest, PrioritizationResponse
)
from core.debt import AntipatternDetector, ROICalculator
from core.auth import get_optional_user

router = APIRouter(prefix="/api/debt", tags=["debt"])
logger = logging.getLogger(__name__)

# Initialize core services
antipattern_detector = AntipatternDetector()
roi_calculator = ROICalculator()

@router.post("/detect-antipatterns", response_model=AntipatternDetectionResponse)
async def detect_antipatterns(
    request: AntipatternDetectionRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Detects schema antipatterns and calculates technical debt.
    """
    try:
        logger.info(f"Detecting antipatterns for {request.database_type}")
        
        result = antipattern_detector.detect(
            request.database_type,
            request.connection_string,
            request.schema_name,
            request.include_recommendations
        )
        
        return AntipatternDetectionResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error detecting antipatterns: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/calculate-debt", response_model=TechnicalDebtResponse)
async def calculate_technical_debt(
    request: TechnicalDebtRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Calculates total technical debt with cost breakdown and ROI metrics.
    """
    try:
        logger.info(f"Calculating technical debt for {request.database_type}")
        
        result = roi_calculator.calculate_debt(
            request.database_type,
            request.connection_string,
            request.schema_name,
            request.team_size,
            request.hourly_rate
        )
        
        return TechnicalDebtResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error calculating technical debt: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/prioritize", response_model=PrioritizationResponse)
async def prioritize_debt(
    request: PrioritizationRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Prioritizes technical debt fixes by ROI and generates sprint recommendations.
    """
    try:
        logger.info(f"Prioritizing technical debt with business priorities: {request.business_priorities}")
        
        result = roi_calculator.prioritize(
            request.database_type,
            request.connection_string,
            request.schema_name,
            request.business_priorities,
            request.available_hours_per_sprint
        )
        
        return PrioritizationResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error prioritizing technical debt: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
