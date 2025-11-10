"""
A/B Testing & Experiment Platform
Create, manage, and analyze experiments with statistical significance
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import logging
from uuid import uuid4
import math

from core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/experiments", tags=["A/B Testing"])


# Models
class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(str, Enum):
    CONTROL = "control"
    TREATMENT = "treatment"


class MetricType(str, Enum):
    CONVERSION = "conversion"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    CUSTOM = "custom"


class Variant(BaseModel):
    variant_id: str
    name: str
    variant_type: VariantType
    description: str
    traffic_allocation: float = Field(ge=0, le=100, default=50.0)
    configuration: Dict[str, Any] = {}


class ExperimentMetric(BaseModel):
    metric_name: str
    metric_type: MetricType
    goal: str  # increase, decrease, maintain
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None


class CreateExperimentRequest(BaseModel):
    name: str
    description: str
    hypothesis: str
    primary_metric: ExperimentMetric
    secondary_metrics: List[ExperimentMetric] = []
    variants: List[Variant]
    target_sample_size: Optional[int] = None
    duration_days: Optional[int] = 14


class Experiment(BaseModel):
    experiment_id: str
    user_id: str
    name: str
    description: str
    hypothesis: str
    status: ExperimentStatus
    primary_metric: ExperimentMetric
    secondary_metrics: List[ExperimentMetric]
    variants: List[Variant]
    target_sample_size: int
    current_sample_size: int = 0
    duration_days: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TrackEventRequest(BaseModel):
    experiment_id: str
    variant_id: str
    user_id: str
    metric_name: str
    value: float = 1.0
    metadata: Dict[str, Any] = {}


class VariantResult(BaseModel):
    variant_id: str
    variant_name: str
    variant_type: VariantType
    sample_size: int
    conversion_rate: Optional[float] = None
    average_value: Optional[float] = None
    total_value: Optional[float] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None


class StatisticalSignificance(BaseModel):
    is_significant: bool
    p_value: float
    confidence_level: float
    required_sample_size: int
    current_sample_size: int
    power: float  # Statistical power (1 - β)
    effect_size: float


class ExperimentResults(BaseModel):
    experiment_id: str
    experiment_name: str
    status: ExperimentStatus
    duration: int  # days
    variants: List[VariantResult]
    winner: Optional[str] = None
    statistical_significance: StatisticalSignificance
    recommendations: List[str]
    lift: Optional[float] = None  # Percentage improvement
    analyzed_at: datetime


# Statistical Analysis Engine
class StatisticalAnalyzer:
    """Perform statistical analysis on experiment results"""
    
    def __init__(self):
        self.alpha = 0.05  # Significance level (5%)
        self.power = 0.80   # Statistical power (80%)
    
    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        alpha: float = 0.05,
        power: float = 0.80
    ) -> int:
        """Calculate required sample size using normal approximation"""
        # Using simplified formula for conversion rate experiments
        # n = (Z_α/2 + Z_β)² * (p₁(1-p₁) + p₂(1-p₂)) / (p₁ - p₂)²
        
        z_alpha = 1.96  # Z-score for 95% confidence
        z_beta = 0.84   # Z-score for 80% power
        
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)
        
        numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
        denominator = (p1 - p2) ** 2
        
        if denominator == 0:
            return 1000  # Default
        
        sample_size = int(math.ceil(numerator / denominator))
        
        # Minimum 100 per variant
        return max(100, sample_size)
    
    def chi_square_test(
        self,
        control_conversions: int,
        control_total: int,
        treatment_conversions: int,
        treatment_total: int
    ) -> float:
        """Perform chi-square test for conversion rates"""
        # Calculate expected values
        total_conversions = control_conversions + treatment_conversions
        total_samples = control_total + treatment_total
        
        if total_samples == 0:
            return 1.0
        
        overall_rate = total_conversions / total_samples
        
        expected_control = control_total * overall_rate
        expected_treatment = treatment_total * overall_rate
        
        # Calculate chi-square statistic
        chi_square = 0
        
        # Control conversions
        if expected_control > 0:
            chi_square += ((control_conversions - expected_control) ** 2) / expected_control
        
        # Control non-conversions
        control_non_conv = control_total - control_conversions
        expected_control_non = control_total * (1 - overall_rate)
        if expected_control_non > 0:
            chi_square += ((control_non_conv - expected_control_non) ** 2) / expected_control_non
        
        # Treatment conversions
        if expected_treatment > 0:
            chi_square += ((treatment_conversions - expected_treatment) ** 2) / expected_treatment
        
        # Treatment non-conversions
        treatment_non_conv = treatment_total - treatment_conversions
        expected_treatment_non = treatment_total * (1 - overall_rate)
        if expected_treatment_non > 0:
            chi_square += ((treatment_non_conv - expected_treatment_non) ** 2) / expected_treatment_non
        
        # Convert to p-value (simplified approximation)
        # For df=1, critical value at 0.05 is 3.841
        p_value = 0.05 if chi_square > 3.841 else 0.5
        
        return p_value
    
    def calculate_confidence_interval(
        self,
        conversion_rate: float,
        sample_size: int,
        confidence: float = 0.95
    ) -> tuple:
        """Calculate confidence interval for conversion rate"""
        if sample_size == 0:
            return (0.0, 0.0)
        
        z_score = 1.96  # 95% confidence
        
        standard_error = math.sqrt(
            (conversion_rate * (1 - conversion_rate)) / sample_size
        )
        
        margin_of_error = z_score * standard_error
        
        lower = max(0, conversion_rate - margin_of_error)
        upper = min(1, conversion_rate + margin_of_error)
        
        return (lower, upper)
    
    def calculate_lift(
        self,
        control_rate: float,
        treatment_rate: float
    ) -> float:
        """Calculate percentage lift from control to treatment"""
        if control_rate == 0:
            return 0.0
        
        lift = ((treatment_rate - control_rate) / control_rate) * 100
        return round(lift, 2)
    
    def determine_winner(
        self,
        variants: List[VariantResult],
        p_value: float
    ) -> Optional[str]:
        """Determine winning variant if statistically significant"""
        if p_value > 0.05:
            return None  # Not significant
        
        # Find variant with highest conversion/value
        best_variant = max(
            variants,
            key=lambda v: v.conversion_rate or v.average_value or 0
        )
        
        return best_variant.variant_name


# Initialize analyzer
stat_analyzer = StatisticalAnalyzer()


# Mock storage (in production, use database)
EXPERIMENTS = {}
EXPERIMENT_EVENTS = {}


# API Endpoints
@router.post("/create")
async def create_experiment(
    request: CreateExperimentRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new A/B test experiment
    
    **Premium Feature**: Statistical experiment design
    """
    try:
        experiment_id = str(uuid4())
        
        # Calculate required sample size if not provided
        if not request.target_sample_size:
            # Assume 10% baseline conversion, 20% MDE
            request.target_sample_size = stat_analyzer.calculate_sample_size(
                baseline_rate=0.10,
                minimum_detectable_effect=0.20
            ) * len(request.variants)
        
        experiment = Experiment(
            experiment_id=experiment_id,
            user_id=user_id,
            name=request.name,
            description=request.description,
            hypothesis=request.hypothesis,
            status=ExperimentStatus.DRAFT,
            primary_metric=request.primary_metric,
            secondary_metrics=request.secondary_metrics,
            variants=request.variants,
            target_sample_size=request.target_sample_size,
            duration_days=request.duration_days or 14,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        EXPERIMENTS[experiment_id] = experiment
        EXPERIMENT_EVENTS[experiment_id] = []
        
        logger.info(f"Created experiment {experiment_id} for user {user_id}")
        
        return {
            "success": True,
            "data": {
                "experiment": experiment.dict(),
                "message": "Experiment created successfully",
                "next_steps": [
                    "Review experiment configuration",
                    "Start experiment when ready",
                    "Begin tracking events"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_experiments(
    user_id: str = Depends(get_current_user),
    status: Optional[ExperimentStatus] = None,
    limit: int = 20
):
    """List all experiments for user"""
    try:
        user_experiments = [
            exp for exp in EXPERIMENTS.values()
            if exp.user_id == user_id
        ]
        
        if status:
            user_experiments = [
                exp for exp in user_experiments
                if exp.status == status
            ]
        
        # Sort by created date
        user_experiments.sort(key=lambda x: x.created_at, reverse=True)
        user_experiments = user_experiments[:limit]
        
        return {
            "success": True,
            "data": {
                "experiments": [exp.dict() for exp in user_experiments],
                "total": len(user_experiments),
                "active": len([e for e in user_experiments if e.status == ExperimentStatus.RUNNING])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Start an experiment"""
    try:
        experiment = EXPERIMENTS.get(experiment_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        if experiment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        if experiment.status != ExperimentStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Experiment already started")
        
        # Start experiment
        experiment.status = ExperimentStatus.RUNNING
        experiment.start_date = datetime.now()
        experiment.end_date = datetime.now() + timedelta(days=experiment.duration_days)
        experiment.updated_at = datetime.now()
        
        logger.info(f"Started experiment {experiment_id}")
        
        return {
            "success": True,
            "data": {
                "experiment_id": experiment_id,
                "status": "running",
                "start_date": experiment.start_date.isoformat(),
                "end_date": experiment.end_date.isoformat(),
                "message": "Experiment started successfully"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/track")
async def track_event(request: TrackEventRequest):
    """
    Track an event for experiment analysis
    
    **Note**: This endpoint is typically called by your application
    """
    try:
        experiment = EXPERIMENTS.get(request.experiment_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        if experiment.status != ExperimentStatus.RUNNING:
            return {
                "success": False,
                "message": "Experiment not running"
            }
        
        # Store event
        event = {
            "event_id": str(uuid4()),
            "experiment_id": request.experiment_id,
            "variant_id": request.variant_id,
            "user_id": request.user_id,
            "metric_name": request.metric_name,
            "value": request.value,
            "metadata": request.metadata,
            "tracked_at": datetime.now().isoformat()
        }
        
        EXPERIMENT_EVENTS[request.experiment_id].append(event)
        experiment.current_sample_size += 1
        
        return {
            "success": True,
            "data": {
                "event_id": event["event_id"],
                "tracked_at": event["tracked_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{experiment_id}/analyze")
async def analyze_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Analyze experiment results with statistical significance
    
    **Premium Feature**: Statistical analysis and winner declaration
    """
    try:
        experiment = EXPERIMENTS.get(experiment_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        if experiment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        events = EXPERIMENT_EVENTS.get(experiment_id, [])
        
        # Calculate results per variant
        variant_results = []
        
        for variant in experiment.variants:
            variant_events = [
                e for e in events
                if e["variant_id"] == variant.variant_id
            ]
            
            sample_size = len(variant_events)
            conversions = len([e for e in variant_events if e["value"] > 0])
            total_value = sum(e["value"] for e in variant_events)
            
            conversion_rate = conversions / sample_size if sample_size > 0 else 0.0
            average_value = total_value / sample_size if sample_size > 0 else 0.0
            
            # Calculate confidence interval
            ci_lower, ci_upper = stat_analyzer.calculate_confidence_interval(
                conversion_rate, sample_size
            )
            
            variant_results.append(VariantResult(
                variant_id=variant.variant_id,
                variant_name=variant.name,
                variant_type=variant.variant_type,
                sample_size=sample_size,
                conversion_rate=round(conversion_rate * 100, 2),
                average_value=round(average_value, 2),
                total_value=round(total_value, 2),
                confidence_interval_lower=round(ci_lower * 100, 2),
                confidence_interval_upper=round(ci_upper * 100, 2)
            ))
        
        # Statistical significance test
        control = [v for v in variant_results if v.variant_type == VariantType.CONTROL][0]
        treatments = [v for v in variant_results if v.variant_type == VariantType.TREATMENT]
        
        if treatments:
            treatment = treatments[0]
            
            p_value = stat_analyzer.chi_square_test(
                control_conversions=int(control.conversion_rate * control.sample_size / 100),
                control_total=control.sample_size,
                treatment_conversions=int(treatment.conversion_rate * treatment.sample_size / 100),
                treatment_total=treatment.sample_size
            )
            
            is_significant = p_value < 0.05
            
            # Calculate lift
            lift = stat_analyzer.calculate_lift(
                control.conversion_rate / 100,
                treatment.conversion_rate / 100
            )
        else:
            p_value = 1.0
            is_significant = False
            lift = 0.0
        
        # Determine winner
        winner = stat_analyzer.determine_winner(variant_results, p_value) if is_significant else None
        
        # Generate recommendations
        recommendations = []
        
        if is_significant:
            if lift > 0:
                recommendations.append(f"✅ Treatment variant shows {lift}% improvement - recommend rollout")
            else:
                recommendations.append(f"⚠️ Treatment variant shows {lift}% decrease - keep control")
        else:
            recommendations.append("⏳ Not yet statistically significant - continue collecting data")
            remaining = experiment.target_sample_size - experiment.current_sample_size
            recommendations.append(f"Need {remaining} more samples to reach target")
        
        if experiment.current_sample_size < 100:
            recommendations.append("⚠️ Sample size too small for reliable conclusions")
        
        significance = StatisticalSignificance(
            is_significant=is_significant,
            p_value=round(p_value, 4),
            confidence_level=0.95,
            required_sample_size=experiment.target_sample_size,
            current_sample_size=experiment.current_sample_size,
            power=0.80,
            effect_size=abs(lift) / 100
        )
        
        results = ExperimentResults(
            experiment_id=experiment_id,
            experiment_name=experiment.name,
            status=experiment.status,
            duration=(datetime.now() - experiment.start_date).days if experiment.start_date else 0,
            variants=variant_results,
            winner=winner,
            statistical_significance=significance,
            recommendations=recommendations,
            lift=lift,
            analyzed_at=datetime.now()
        )
        
        return {
            "success": True,
            "data": {
                "results": results.dict()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get current experiment results"""
    return await analyze_experiment(experiment_id, user_id)


@router.post("/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    declare_winner: bool = False
):
    """Stop an experiment"""
    try:
        experiment = EXPERIMENTS.get(experiment_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        if experiment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_date = datetime.now()
        experiment.updated_at = datetime.now()
        
        message = "Experiment stopped successfully"
        
        if declare_winner:
            # Analyze and declare winner
            results = await analyze_experiment(experiment_id, user_id)
            winner = results.get("data", {}).get("results", {}).get("winner")
            message += f" - Winner: {winner}" if winner else " - No clear winner"
        
        return {
            "success": True,
            "data": {
                "experiment_id": experiment_id,
                "status": "completed",
                "message": message
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete an experiment"""
    try:
        experiment = EXPERIMENTS.get(experiment_id)
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        if experiment.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        del EXPERIMENTS[experiment_id]
        if experiment_id in EXPERIMENT_EVENTS:
            del EXPERIMENT_EVENTS[experiment_id]
        
        return {
            "success": True,
            "data": {
                "message": "Experiment deleted successfully"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))
