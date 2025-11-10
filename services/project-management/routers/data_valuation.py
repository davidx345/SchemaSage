"""
Data Valuation Engine
AI-powered data pricing and monetization recommendations
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging
from uuid import uuid4

from core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/valuation", tags=["Data Valuation"])


# Models
class DataCategory(str, Enum):
    BEHAVIORAL = "behavioral"
    DEMOGRAPHIC = "demographic"
    TRANSACTIONAL = "transactional"
    LOCATION = "location"
    SENSOR = "sensor"
    SOCIAL = "social"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"


class DataQuality(str, Enum):
    PREMIUM = "premium"  # 90-100%
    HIGH = "high"        # 75-89%
    MEDIUM = "medium"    # 50-74%
    LOW = "low"          # 0-49%


class MonetizationStrategy(str, Enum):
    DIRECT_SALE = "direct_sale"
    SUBSCRIPTION = "subscription"
    API_ACCESS = "api_access"
    AGGREGATED_INSIGHTS = "aggregated_insights"
    MARKETPLACE = "marketplace"


class DataValuationRequest(BaseModel):
    dataset_name: str
    category: DataCategory
    row_count: int
    column_count: int
    update_frequency: str  # daily, weekly, monthly
    data_quality_score: Optional[float] = None
    has_pii: bool = False
    industry: str
    description: str


class DataValuationResult(BaseModel):
    valuation_id: str
    dataset_name: str
    estimated_value_low: float
    estimated_value_mid: float
    estimated_value_high: float
    recommended_price_monthly: float
    recommended_price_yearly: float
    recommended_price_per_record: float
    confidence_score: float = Field(ge=0, le=100)
    valuation_factors: Dict[str, Any]
    monetization_strategies: List[Dict[str, Any]]
    market_comparables: List[Dict[str, Any]]
    valued_at: datetime


class MonetizationRecommendation(BaseModel):
    strategy: MonetizationStrategy
    estimated_monthly_revenue: float
    estimated_yearly_revenue: float
    setup_complexity: str  # low, medium, high
    time_to_revenue: str  # immediate, 1-3 months, 3-6 months
    recommended_pricing: Dict[str, float]
    pros: List[str]
    cons: List[str]
    action_items: List[str]


# Data Valuation Engine
class DataValuationEngine:
    """Calculate data value using industry benchmarks and AI analysis"""
    
    def __init__(self):
        # Price per record by category (in USD)
        self.base_prices = {
            DataCategory.BEHAVIORAL: 0.25,
            DataCategory.DEMOGRAPHIC: 0.15,
            DataCategory.TRANSACTIONAL: 0.50,
            DataCategory.LOCATION: 0.30,
            DataCategory.SENSOR: 0.10,
            DataCategory.SOCIAL: 0.20,
            DataCategory.FINANCIAL: 0.75,
            DataCategory.HEALTHCARE: 1.00
        }
        
        # Industry multipliers
        self.industry_multipliers = {
            "healthcare": 2.5,
            "financial": 2.0,
            "e-commerce": 1.5,
            "saas": 1.3,
            "manufacturing": 1.2,
            "education": 0.9,
            "nonprofit": 0.7
        }
        
        # Quality multipliers
        self.quality_multipliers = {
            DataQuality.PREMIUM: 2.0,
            DataQuality.HIGH: 1.5,
            DataQuality.MEDIUM: 1.0,
            DataQuality.LOW: 0.5
        }
    
    def calculate_valuation(self, request: DataValuationRequest) -> DataValuationResult:
        """Calculate comprehensive data valuation"""
        
        # Base value calculation
        base_price_per_record = self.base_prices.get(request.category, 0.20)
        
        # Apply industry multiplier
        industry_multiplier = self.industry_multipliers.get(
            request.industry.lower(), 1.0
        )
        
        # Apply quality multiplier
        quality = self._determine_quality(request.data_quality_score)
        quality_multiplier = self.quality_multipliers[quality]
        
        # Freshness bonus
        freshness_multiplier = self._get_freshness_multiplier(request.update_frequency)
        
        # Size factor (economies of scale)
        size_multiplier = self._get_size_multiplier(request.row_count)
        
        # PII penalty (privacy concerns reduce value)
        pii_multiplier = 0.7 if request.has_pii else 1.0
        
        # Calculate final price per record
        price_per_record = (
            base_price_per_record *
            industry_multiplier *
            quality_multiplier *
            freshness_multiplier *
            size_multiplier *
            pii_multiplier
        )
        
        # Total dataset value
        total_value_mid = price_per_record * request.row_count
        total_value_low = total_value_mid * 0.7
        total_value_high = total_value_mid * 1.5
        
        # Monthly/yearly pricing for subscription model
        monthly_price = total_value_mid * 0.15  # 15% of value per month
        yearly_price = monthly_price * 10  # 2 months free discount
        
        # Valuation factors
        factors = {
            "base_price": base_price_per_record,
            "industry_multiplier": industry_multiplier,
            "quality_multiplier": quality_multiplier,
            "freshness_multiplier": freshness_multiplier,
            "size_multiplier": size_multiplier,
            "pii_multiplier": pii_multiplier,
            "final_price_per_record": round(price_per_record, 4)
        }
        
        # Get monetization strategies
        strategies = self._generate_monetization_strategies(
            request, total_value_mid, monthly_price
        )
        
        # Get market comparables
        comparables = self._get_market_comparables(request.category, request.industry)
        
        # Confidence score
        confidence = self._calculate_confidence(request)
        
        return DataValuationResult(
            valuation_id=str(uuid4()),
            dataset_name=request.dataset_name,
            estimated_value_low=round(total_value_low, 2),
            estimated_value_mid=round(total_value_mid, 2),
            estimated_value_high=round(total_value_high, 2),
            recommended_price_monthly=round(monthly_price, 2),
            recommended_price_yearly=round(yearly_price, 2),
            recommended_price_per_record=round(price_per_record, 4),
            confidence_score=confidence,
            valuation_factors=factors,
            monetization_strategies=[s.dict() for s in strategies],
            market_comparables=comparables,
            valued_at=datetime.now()
        )
    
    def _determine_quality(self, score: Optional[float]) -> DataQuality:
        """Determine quality tier from score"""
        if score is None:
            return DataQuality.MEDIUM
        
        if score >= 90:
            return DataQuality.PREMIUM
        elif score >= 75:
            return DataQuality.HIGH
        elif score >= 50:
            return DataQuality.MEDIUM
        else:
            return DataQuality.LOW
    
    def _get_freshness_multiplier(self, frequency: str) -> float:
        """Calculate freshness multiplier based on update frequency"""
        frequency_multipliers = {
            "real-time": 2.0,
            "hourly": 1.8,
            "daily": 1.5,
            "weekly": 1.2,
            "monthly": 1.0,
            "quarterly": 0.7,
            "yearly": 0.5
        }
        return frequency_multipliers.get(frequency.lower(), 1.0)
    
    def _get_size_multiplier(self, row_count: int) -> float:
        """Calculate size multiplier (bulk discount/premium)"""
        if row_count < 1000:
            return 1.5  # Premium for small curated datasets
        elif row_count < 10000:
            return 1.2
        elif row_count < 100000:
            return 1.0
        elif row_count < 1000000:
            return 0.9  # Bulk discount starts
        else:
            return 0.8  # Large dataset discount
    
    def _generate_monetization_strategies(
        self,
        request: DataValuationRequest,
        base_value: float,
        monthly_price: float
    ) -> List[MonetizationRecommendation]:
        """Generate monetization strategy recommendations"""
        strategies = []
        
        # Strategy 1: Direct Sale
        strategies.append(MonetizationRecommendation(
            strategy=MonetizationStrategy.DIRECT_SALE,
            estimated_monthly_revenue=base_value * 0.08,
            estimated_yearly_revenue=base_value,
            setup_complexity="low",
            time_to_revenue="immediate",
            recommended_pricing={"one_time": base_value},
            pros=[
                "Immediate full payment",
                "Simple transaction",
                "No ongoing support needed"
            ],
            cons=[
                "One-time revenue only",
                "Buyer owns data forever",
                "Lower lifetime value"
            ],
            action_items=[
                "Package data with documentation",
                "Create sample dataset",
                "List on marketplace"
            ]
        ))
        
        # Strategy 2: Subscription
        strategies.append(MonetizationRecommendation(
            strategy=MonetizationStrategy.SUBSCRIPTION,
            estimated_monthly_revenue=monthly_price,
            estimated_yearly_revenue=monthly_price * 12,
            setup_complexity="medium",
            time_to_revenue="1-3 months",
            recommended_pricing={
                "monthly": monthly_price,
                "yearly": monthly_price * 10
            },
            pros=[
                "Recurring revenue stream",
                "Higher lifetime value",
                "Retain data ownership"
            ],
            cons=[
                "Requires ongoing updates",
                "Customer support needed",
                "Churn risk"
            ],
            action_items=[
                "Set up automated data refresh",
                "Create tiered pricing plans",
                "Build subscriber portal"
            ]
        ))
        
        # Strategy 3: API Access
        api_calls_per_month = request.row_count * 100  # Estimated
        api_price_per_call = request.recommended_price_per_record * 0.01 if hasattr(request, 'recommended_price_per_record') else 0.001
        
        strategies.append(MonetizationRecommendation(
            strategy=MonetizationStrategy.API_ACCESS,
            estimated_monthly_revenue=api_calls_per_month * api_price_per_call * 0.3,  # 30% adoption
            estimated_yearly_revenue=api_calls_per_month * api_price_per_call * 0.3 * 12,
            setup_complexity="high",
            time_to_revenue="3-6 months",
            recommended_pricing={
                "per_api_call": api_price_per_call,
                "monthly_quota_100k": monthly_price * 0.5,
                "monthly_quota_1m": monthly_price * 1.5
            },
            pros=[
                "Scalable revenue model",
                "Usage-based pricing",
                "Developer-friendly"
            ],
            cons=[
                "Complex infrastructure",
                "Rate limiting needed",
                "Higher support costs"
            ],
            action_items=[
                "Build RESTful API",
                "Implement authentication",
                "Create API documentation",
                "Set up billing integration"
            ]
        ))
        
        # Strategy 4: Aggregated Insights
        insights_value = base_value * 0.5  # Aggregated data worth less
        
        strategies.append(MonetizationRecommendation(
            strategy=MonetizationStrategy.AGGREGATED_INSIGHTS,
            estimated_monthly_revenue=insights_value * 0.2,
            estimated_yearly_revenue=insights_value * 2.4,
            setup_complexity="medium",
            time_to_revenue="1-3 months",
            recommended_pricing={
                "monthly_report": insights_value * 0.2,
                "custom_analysis": insights_value * 0.5
            },
            pros=[
                "Privacy-preserving",
                "No PII concerns",
                "Higher margins"
            ],
            cons=[
                "Requires analysis expertise",
                "Custom work needed",
                "Smaller market"
            ],
            action_items=[
                "Anonymize and aggregate data",
                "Create insight templates",
                "Build visualization tools"
            ]
        ))
        
        # Sort by estimated revenue
        strategies.sort(key=lambda x: x.estimated_yearly_revenue, reverse=True)
        
        return strategies
    
    def _get_market_comparables(
        self,
        category: DataCategory,
        industry: str
    ) -> List[Dict[str, Any]]:
        """Get comparable market data pricing"""
        comparables = [
            {
                "dataset_type": f"{category.value} data in {industry}",
                "price_range": "$5,000 - $50,000",
                "typical_buyers": ["Market research firms", "Analytics companies", "Enterprises"],
                "market_size": "Growing 15% YoY"
            },
            {
                "dataset_type": f"Similar {category.value} datasets",
                "price_range": "$10,000 - $100,000",
                "typical_buyers": ["Data brokers", "AI/ML companies", "Consultants"],
                "market_size": "$200M+ industry"
            }
        ]
        
        return comparables
    
    def _calculate_confidence(self, request: DataValuationRequest) -> float:
        """Calculate confidence in valuation"""
        confidence = 70.0  # Base confidence
        
        # More data = higher confidence
        if request.row_count > 100000:
            confidence += 10
        elif request.row_count > 10000:
            confidence += 5
        
        # Quality score provided
        if request.data_quality_score is not None:
            confidence += 10
        
        # Frequent updates
        if request.update_frequency in ["daily", "hourly", "real-time"]:
            confidence += 5
        
        # High-value industry
        if request.industry.lower() in ["healthcare", "financial"]:
            confidence += 5
        
        return min(100, confidence)


# Initialize engine
valuation_engine = DataValuationEngine()


# API Endpoints
@router.post("/analyze")
async def analyze_data_value(
    request: DataValuationRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Calculate data value using AI and market analysis
    
    **Premium Feature**: Know what your data is worth
    """
    try:
        logger.info(f"Analyzing data value for user {user_id}: {request.dataset_name}")
        
        valuation = valuation_engine.calculate_valuation(request)
        
        return {
            "success": True,
            "data": {
                "valuation": valuation.dict(),
                "summary": {
                    "estimated_value": f"${valuation.estimated_value_mid:,.2f}",
                    "monthly_potential": f"${valuation.recommended_price_monthly:,.2f}/month",
                    "top_strategy": valuation.monetization_strategies[0]["strategy"] if valuation.monetization_strategies else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Data valuation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estimate")
async def get_quick_estimate(
    category: DataCategory,
    row_count: int,
    industry: str = "general",
    user_id: str = Depends(get_current_user)
):
    """Quick data value estimate"""
    try:
        # Quick calculation
        base_price = valuation_engine.base_prices.get(category, 0.20)
        industry_mult = valuation_engine.industry_multipliers.get(industry.lower(), 1.0)
        
        estimated_value = base_price * row_count * industry_mult
        monthly_revenue = estimated_value * 0.15
        
        return {
            "success": True,
            "data": {
                "estimated_value": round(estimated_value, 2),
                "estimated_monthly_revenue": round(monthly_revenue, 2),
                "price_per_record": round(base_price * industry_mult, 4),
                "note": "This is a quick estimate. Use /analyze for detailed valuation"
            }
        }
        
    except Exception as e:
        logger.error(f"Quick estimate failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pricing")
async def get_pricing_recommendations(
    dataset_value: float,
    target_market: str = "general",
    user_id: str = Depends(get_current_user)
):
    """Get AI-powered pricing recommendations"""
    try:
        # Generate pricing tiers
        pricing_tiers = {
            "starter": {
                "price": round(dataset_value * 0.1, 2),
                "features": ["Limited API calls", "Monthly updates", "Basic support"],
                "target_customers": "Small businesses, startups"
            },
            "professional": {
                "price": round(dataset_value * 0.25, 2),
                "features": ["Unlimited API calls", "Weekly updates", "Priority support", "Custom exports"],
                "target_customers": "Medium businesses, agencies"
            },
            "enterprise": {
                "price": round(dataset_value * 0.5, 2),
                "features": ["Full access", "Real-time updates", "Dedicated support", "Custom integrations", "SLA guarantees"],
                "target_customers": "Large enterprises, data brokers"
            }
        }
        
        return {
            "success": True,
            "data": {
                "pricing_tiers": pricing_tiers,
                "recommended_tier": "professional",
                "upsell_strategy": "Start with Starter, upsell to Professional after 3 months"
            }
        }
        
    except Exception as e:
        logger.error(f"Pricing recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_monetization_advice(
    dataset_category: DataCategory,
    dataset_size: int,
    user_id: str = Depends(get_current_user)
):
    """Get personalized monetization recommendations"""
    try:
        recommendations = []
        
        # Size-based recommendations
        if dataset_size < 10000:
            recommendations.append({
                "priority": "high",
                "recommendation": "Focus on direct sales to niche markets",
                "reasoning": "Small datasets work best as curated, specialized products",
                "expected_revenue": "$5,000 - $25,000"
            })
        elif dataset_size < 100000:
            recommendations.append({
                "priority": "high",
                "recommendation": "Build API access with usage-based pricing",
                "reasoning": "Medium datasets ideal for API monetization",
                "expected_revenue": "$2,000 - $10,000/month"
            })
        else:
            recommendations.append({
                "priority": "high",
                "recommendation": "Create subscription service with tiered access",
                "reasoning": "Large datasets support recurring revenue models",
                "expected_revenue": "$5,000 - $50,000/month"
            })
        
        # Category-specific recommendations
        if dataset_category in [DataCategory.FINANCIAL, DataCategory.HEALTHCARE]:
            recommendations.append({
                "priority": "high",
                "recommendation": "Ensure compliance certifications before selling",
                "reasoning": "High-value regulated data requires proper certifications",
                "expected_revenue": "+50% premium with certifications"
            })
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "next_steps": [
                    "Get detailed valuation analysis",
                    "Anonymize sensitive data",
                    "List on data marketplace",
                    "Set up payment processing"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Monetization advice failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
