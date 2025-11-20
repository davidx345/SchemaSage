"""
Cost Anomaly Detector Router.
Handles anomaly detection, cost spike analysis, and budget forecasting.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from models.anomaly_models import (
    AnomalyDetectionRequest, AnomalyDetectionResponse,
    CostSpikeRequest, CostSpikeResponse,
    BudgetForecastRequest, BudgetForecastResponse
)
from core.anomaly import AnomalyDetector, CostAnalyzer
from core.auth import get_optional_user

router = APIRouter(prefix="/api/anomaly", tags=["anomaly"])
logger = logging.getLogger(__name__)

# Initialize core services
anomaly_detector = AnomalyDetector()
cost_analyzer = CostAnalyzer()

@router.post("/detect", response_model=AnomalyDetectionResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Detects cost anomalies in historical data using statistical analysis.
    """
    try:
        logger.info(f"Detecting cost anomalies with sensitivity {request.sensitivity}")
        
        result = anomaly_detector.detect(
            request.cost_data,
            request.resource_type,
            request.sensitivity,
            request.lookback_days
        )
        
        return AnomalyDetectionResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/analyze-spikes", response_model=CostSpikeResponse)
async def analyze_cost_spikes(
    request: CostSpikeRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Analyzes cost spikes with root cause identification.
    """
    try:
        logger.info(f"Analyzing cost spikes with threshold {request.spike_threshold}")
        
        result = cost_analyzer.analyze_spikes(
            request.cost_data,
            request.spike_threshold,
            request.include_root_cause
        )
        
        return CostSpikeResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error analyzing cost spikes: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/forecast-budget", response_model=BudgetForecastResponse)
async def forecast_budget(
    request: BudgetForecastRequest,
    current_user: Optional[str] = Depends(get_optional_user)
):
    """
    Generates budget forecasts with trend analysis and alerts.
    """
    try:
        logger.info(f"Forecasting budget for {request.forecast_months} months")
        
        result = cost_analyzer.forecast_budget(
            request.historical_costs,
            request.forecast_months,
            request.budget_limit,
            request.growth_rate
        )
        
        return BudgetForecastResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Error forecasting budget: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
