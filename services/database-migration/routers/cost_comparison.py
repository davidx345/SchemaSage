"""
Cost Comparison Router - Priority 1 (Week 1)
POST /api/cost/compare - Compare database costs across AWS, GCP, and Azure
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict
import logging

from models.cost_models import (
    CostComparisonRequest,
    CostComparisonResponse,
    ErrorResponse
)
from core.pricing.pricing_calculator import PricingCalculator
from core.auth import auth_service

router = APIRouter(prefix="/api/cost", tags=["Cost Analysis"])
logger = logging.getLogger(__name__)


@router.post("/compare", response_model=CostComparisonResponse)
async def compare_costs(
    request: CostComparisonRequest,
    current_user: Dict = Depends(auth_service.get_current_user_optional)
):
    """
    Compare database deployment costs across AWS, GCP, and Azure.
    Priority P1 (MVP - Week 1).
    Calculates monthly costs for running a database with specified requirements.
    """
    try:
        logger.info(
            f"Cost comparison request: {request.database_type}, "
            f"{request.storage_gb}GB, region={request.region}, "
            f"user={current_user.get('username', 'anonymous') if current_user else 'anonymous'}"
        )
        
        # Validate region
        valid_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        if request.region not in valid_regions:
            logger.warning(f"Invalid region requested: {request.region}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": {
                        "code": "INVALID_REGION",
                        "message": f"Invalid region: {request.region}",
                        "details": {
                            "field": "region",
                            "issue": f"Region must be one of: {', '.join(valid_regions)}"
                        }
                    }
                }
            )
        
        # Calculate costs across all providers
        comparison_data = PricingCalculator.compare_all_providers(
            database_type=request.database_type.value,
            storage_gb=request.storage_gb,
            region=request.region,
            qps=request.performance_requirements.qps,
            connections=request.performance_requirements.connections,
            iops=request.performance_requirements.iops
        )
        
        logger.info(
            f"Cost comparison completed. Recommendation: {comparison_data['recommendation']}, "
            f"Savings: ${comparison_data.get('savings', {})}"
        )
        
        return {
            "success": True,
            "data": comparison_data
        }
        
    except ValueError as e:
        logger.error(f"Validation error in cost comparison: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": str(e),
                    "details": {"issue": "Invalid input parameters"}
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Error in cost comparison: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "CALCULATION_ERROR",
                    "message": "Failed to calculate cost comparison",
                    "details": {"error": str(e)}
                }
            }
        )


@router.get("/health")
async def cost_service_health():
    """Health check for cost analysis service"""
    return {
        "service": "cost-analysis",
        "status": "healthy",
        "features": ["cost_comparison"],
        "version": "1.0.0"
    }
