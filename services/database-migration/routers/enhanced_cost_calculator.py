"""
Enhanced migration cost calculator endpoint.
Calculates detailed costs with TCO analysis and forecasts.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.enhanced_cost_models import EnhancedCostRequest, EnhancedCostResponse
from core.cost import calculate_enhanced_migration_cost
from core.auth import get_current_user_optional

router = APIRouter(prefix="/api/cost", tags=["cost"])
logger = logging.getLogger(__name__)


@router.post("/calculate-migration", response_model=EnhancedCostResponse)
async def enhanced_cost_calculator_endpoint(
    request: EnhancedCostRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Calculate comprehensive migration costs with TCO analysis.
    
    Provides detailed cost breakdown, 5-year forecasts, cost comparisons,
    and optimization opportunities for database migrations.
    """
    try:
        logger.info(
            f"Calculating migration cost from {request.source_database.engine} "
            f"to {request.target_cloud_provider.value}/{request.target_service.value}"
        )
        
        # Call cost calculator
        (cost_breakdown, migration_costs, comparison, optimizations,
         alternatives, forecast, statistics, summary, warnings) = calculate_enhanced_migration_cost(
            source_db=request.source_database,
            target_provider=request.target_cloud_provider,
            target_service=request.target_service,
            target_db=request.target_database,
            workload=request.workload_profile,
            complexity=request.migration_complexity,
            region=request.region,
            commitment_months=request.commitment_term_months
        )
        
        # Build response
        response = EnhancedCostResponse(
            ongoing_costs=cost_breakdown,
            migration_costs=migration_costs,
            cost_comparison=comparison,
            optimization_opportunities=optimizations,
            alternative_pricing_tiers=alternatives,
            cost_forecast=forecast,
            statistics=statistics,
            summary=summary,
            warnings=warnings
        )
        
        logger.info(
            f"Cost calculation complete: ${comparison.target_monthly_cost:.2f}/month, "
            f"ROI: {comparison.roi_percent:.1f}%, break-even: {comparison.break_even_months:.1f} months"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in cost calculation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error calculating migration cost: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to calculate migration cost",
                "detail": str(e)
            }
        )
