"""
ROI Dashboard Models - Phase 3.6
Pydantic models for ROI calculations, time series, feature analysis, competitive comparison
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum


# ===== Enums =====

class Granularity(str, Enum):
    """Time series granularity options"""
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


class ExportFormat(str, Enum):
    """Export format options"""
    pdf = "pdf"
    excel = "excel"


class ExportStatus(str, Enum):
    """Export generation status"""
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AlternativeCategory(str, Enum):
    """Competitor category"""
    enterprise_tool = "enterprise_tool"
    manual_process = "manual_process"


# ===== 3.6.1 Calculate Total Value Models =====

class TimePeriod(BaseModel):
    """Time period for ROI analysis"""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    duration_months: Optional[float] = Field(None, description="Calculated duration in months")


class AnalysisOptions(BaseModel):
    """ROI calculation options"""
    include_projections: bool = Field(True, description="Include future projections")
    confidence_level: int = Field(95, description="Statistical confidence level", ge=50, le=99)
    currency: str = Field("USD", description="Currency code")


class CalculateValueRequest(BaseModel):
    """Request for ROI value calculation"""
    organization_id: str = Field(..., description="Organization identifier")
    time_period: TimePeriod
    analysis_options: Optional[AnalysisOptions] = Field(default_factory=AnalysisOptions)


class TotalValue(BaseModel):
    """Total value metrics"""
    monthly: int = Field(..., description="Monthly value delivered")
    yearly: int = Field(..., description="Yearly value delivered")
    growth_percentage: int = Field(..., description="Growth percentage")
    confidence_level: int = Field(..., description="Confidence level percentage")


class ROIMetrics(BaseModel):
    """ROI financial metrics"""
    investment: int = Field(..., description="Total investment amount")
    roi_percentage: int = Field(..., description="ROI percentage")
    roi_ratio: float = Field(..., description="ROI ratio (value/investment)")
    payback_months: int = Field(..., description="Payback period in months")
    npv: int = Field(..., description="Net Present Value")
    irr: float = Field(..., description="Internal Rate of Return")


class ValueBreakdown(BaseModel):
    """Breakdown within a value category"""
    infrastructure_optimization: Optional[int] = None
    license_elimination: Optional[int] = None
    operational_efficiency: Optional[int] = None
    automated_schema_design: Optional[int] = None
    migration_planning: Optional[int] = None
    incident_response: Optional[int] = None
    compliance_fines_avoided: Optional[int] = None
    data_breach_prevention: Optional[int] = None
    migration_failure_avoidance: Optional[int] = None
    developer_efficiency: Optional[int] = None
    reduced_context_switching: Optional[int] = None
    knowledge_sharing: Optional[int] = None


class ValueCategory(BaseModel):
    """Value category with breakdown"""
    total: int = Field(..., description="Total value in category")
    monthly_average: int = Field(..., description="Monthly average")
    percentage_of_total: int = Field(..., description="Percentage of total value")
    confidence: int = Field(..., description="Confidence level for this category")
    breakdown: Dict[str, int] = Field(..., description="Detailed breakdown")


class ValueCategories(BaseModel):
    """All value categories"""
    cost_savings: ValueCategory
    time_savings: ValueCategory
    risk_reduction: ValueCategory
    productivity_gain: ValueCategory


class KeyAchievement(BaseModel):
    """Individual achievement"""
    achievement: str = Field(..., description="Achievement description")
    baseline: str = Field(..., description="Baseline metric")
    current: str = Field(..., description="Current metric")
    impact_value: int = Field(..., description="Dollar value impact")
    confidence: int = Field(..., description="Confidence level")


class AdoptionMetrics(BaseModel):
    """User adoption metrics"""
    total_users: int = Field(..., description="Total users")
    active_users: int = Field(..., description="Active users")
    adoption_rate: int = Field(..., description="Adoption rate percentage")
    satisfaction_score: float = Field(..., description="Satisfaction score (0-5)")
    nps_score: int = Field(..., description="Net Promoter Score")


class MethodologyConfidence(BaseModel):
    """Confidence breakdown by methodology"""
    high_confidence: int = Field(..., description="High confidence percentage")
    medium_confidence: int = Field(..., description="Medium confidence percentage")
    low_confidence: int = Field(..., description="Low confidence percentage")
    explanation: str = Field(..., description="Methodology explanation")


class CalculateValueData(BaseModel):
    """ROI calculation result data"""
    calculation_id: str
    organization_id: str
    time_period: TimePeriod
    total_value: TotalValue
    roi_metrics: ROIMetrics
    value_categories: ValueCategories
    key_achievements: List[KeyAchievement]
    adoption_metrics: AdoptionMetrics
    methodology_confidence: MethodologyConfidence


class CalculateValueResponse(BaseModel):
    """Response for ROI value calculation"""
    success: bool
    data: CalculateValueData


# ===== 3.6.2 Time Series Analysis Models =====

class TimeSeriesValueCategories(BaseModel):
    """Value categories for a specific period"""
    cost_savings: int
    time_savings: int
    risk_reduction: int
    productivity_gain: int


class TimeSeriesPoint(BaseModel):
    """Single time series data point"""
    period: str = Field(..., description="Period identifier (YYYY-MM)")
    period_label: str = Field(..., description="Human-readable label")
    monthly_value: int = Field(..., description="Value for this period")
    cumulative_value: int = Field(..., description="Cumulative value to date")
    value_categories: TimeSeriesValueCategories
    roi_percentage: int = Field(..., description="ROI percentage at this point")
    active_features: int = Field(..., description="Number of active features")
    adoption_rate: int = Field(..., description="Adoption rate percentage")


class PeakMonth(BaseModel):
    """Peak/lowest month information"""
    period: str
    value: int


class GrowthMetrics(BaseModel):
    """Growth metrics summary"""
    month_over_month_growth: float = Field(..., description="Average MoM growth percentage")
    total_growth_percentage: int = Field(..., description="Total growth percentage")
    average_monthly_value: int = Field(..., description="Average monthly value")
    peak_month: PeakMonth
    lowest_month: PeakMonth


class ConfidenceInterval(BaseModel):
    """Confidence interval for projection"""
    lower: int
    upper: int


class Projection(BaseModel):
    """Future projection"""
    period: str
    projected_value: int
    confidence_interval: ConfidenceInterval


class Projections(BaseModel):
    """Future projections"""
    next_3_months: List[Projection]


class TimeSeriesData(BaseModel):
    """Time series analysis data"""
    organization_id: str
    time_series: List[TimeSeriesPoint]
    growth_metrics: GrowthMetrics
    projections: Projections


class TimeSeriesResponse(BaseModel):
    """Response for time series analysis"""
    success: bool
    data: TimeSeriesData


# ===== 3.6.3 Feature Analysis Models =====

class UsageMetrics(BaseModel):
    """Feature usage metrics (flexible schema)"""
    total_scans: Optional[int] = None
    pii_fields_detected: Optional[int] = None
    anonymization_jobs: Optional[int] = None
    records_anonymized: Optional[int] = None
    migration_plans_created: Optional[int] = None
    successful_migrations: Optional[int] = None
    failed_migrations: Optional[int] = None
    databases_migrated: Optional[int] = None
    schemas_generated: Optional[int] = None
    hours_saved: Optional[int] = None
    queries_optimized: Optional[int] = None
    incidents_analyzed: Optional[int] = None
    root_causes_identified: Optional[int] = None
    mttr_improvement_percentage: Optional[int] = None
    similar_incidents_matched: Optional[int] = None
    code_files_generated: Optional[int] = None
    languages_supported: Optional[int] = None
    lines_of_code: Optional[int] = None
    boilerplate_eliminated: Optional[int] = None
    templates_purchased: Optional[int] = None
    templates_used: Optional[int] = None
    time_saved_hours: Optional[int] = None
    notifications_sent: Optional[int] = None
    alerts_configured: Optional[int] = None
    response_time_improvement: Optional[int] = None
    audits_generated: Optional[int] = None
    vulnerabilities_found: Optional[int] = None
    vulnerabilities_fixed: Optional[int] = None


class FeatureDetail(BaseModel):
    """Individual feature analysis"""
    feature_id: str
    feature_name: str
    category: str = Field(..., description="Feature category")
    value_delivered: int = Field(..., description="Total value delivered")
    percentage_of_total: float = Field(..., description="Percentage of total value")
    roi_percentage: int = Field(..., description="ROI percentage for this feature")
    usage_metrics: Dict[str, int] = Field(..., description="Feature-specific usage metrics")
    value_breakdown: Dict[str, int] = Field(..., description="Value breakdown")
    user_satisfaction: float = Field(..., description="User satisfaction score (0-5)")
    adoption_rate: int = Field(..., description="Adoption rate percentage")


class FeatureAnalysisSummary(BaseModel):
    """Feature analysis summary"""
    total_value: int
    total_features: int
    average_roi_percentage: int
    highest_roi_feature: str
    most_adopted_feature: str
    highest_satisfaction_feature: str


class FeatureAnalysisData(BaseModel):
    """Feature analysis data"""
    organization_id: str
    features: List[FeatureDetail]
    summary: FeatureAnalysisSummary


class FeatureAnalysisResponse(BaseModel):
    """Response for feature analysis"""
    success: bool
    data: FeatureAnalysisData


# ===== 3.6.4 Competitive Analysis Models =====

class CompetitiveAnalysisRequest(BaseModel):
    """Request for competitive analysis"""
    organization_id: str
    alternatives: List[str] = Field(..., description="List of competitor names")


class SchemaSageMetrics(BaseModel):
    """SchemaSage metrics for comparison"""
    annual_cost: int
    implementation_months: float
    value_delivered: int
    roi_percentage: int
    features_count: int
    active_users: int
    satisfaction_score: float


class CostComparison(BaseModel):
    """Cost comparison details"""
    schemasage_cost: int
    alternative_cost: int
    annual_savings: int
    savings_percentage: int


class TimeComparison(BaseModel):
    """Time comparison details"""
    schemasage_hours: int
    alternative_hours: int
    hours_saved: int
    efficiency_gain: int


class FeatureComparison(BaseModel):
    """Feature comparison details"""
    schemasage_has_but_alternative_lacks: List[str]
    alternative_has_but_schemasage_lacks: List[str]


class AlternativeDetail(BaseModel):
    """Individual competitor/alternative analysis"""
    alternative_id: str
    name: str
    category: AlternativeCategory
    annual_cost: int
    implementation_months: float
    value_delivered: int
    roi_percentage: int
    features_count: int
    cost_comparison: CostComparison
    time_comparison: TimeComparison
    feature_comparison: FeatureComparison
    schemasage_advantages: List[str]


class CompetitiveSummary(BaseModel):
    """Competitive analysis summary"""
    average_competitor_cost: int
    average_schemasage_savings: int
    average_roi_advantage: str
    feature_coverage_advantage: str
    implementation_speed_advantage: str
    value_delivery_advantage: str


class CompetitiveAnalysisData(BaseModel):
    """Competitive analysis data"""
    organization_id: str
    schemasage_metrics: SchemaSageMetrics
    alternatives: List[AlternativeDetail]
    competitive_summary: CompetitiveSummary


class CompetitiveAnalysisResponse(BaseModel):
    """Response for competitive analysis"""
    success: bool
    data: CompetitiveAnalysisData


# ===== 3.6.5 Export Summary Models =====

class ExportSections(str, Enum):
    """Available export sections"""
    executive_summary = "executive_summary"
    value_breakdown = "value_breakdown"
    feature_analysis = "feature_analysis"
    competitive_comparison = "competitive_comparison"
    time_series = "time_series"
    key_achievements = "key_achievements"


class ExportOptions(BaseModel):
    """Export configuration options"""
    format: ExportFormat
    include_charts: bool = Field(True, description="Include charts/graphs")
    include_methodology: bool = Field(True, description="Include methodology section")
    sections: List[str] = Field(..., description="Sections to include")


class Branding(BaseModel):
    """Export branding options"""
    company_name: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = Field("#1e40af", description="Hex color code")


class ExportSummaryRequest(BaseModel):
    """Request for export generation"""
    organization_id: str
    time_period: TimePeriod
    export_options: ExportOptions
    branding: Optional[Branding] = None


class ExportSummaryData(BaseModel):
    """Export generation response data"""
    export_id: str
    status: ExportStatus
    format: ExportFormat
    estimated_completion_seconds: Optional[int] = None
    sections_included: Optional[int] = None
    page_count_estimate: Optional[int] = None


class ExportSummaryResponse(BaseModel):
    """Response for export generation"""
    success: bool
    data: ExportSummaryData


class SectionGenerated(BaseModel):
    """Generated section details"""
    section: str
    pages: int
    charts_included: int


class ExportMetadata(BaseModel):
    """Export metadata"""
    generated_at: str
    generated_by: str
    organization: str
    report_period: str


class ExportStatusData(BaseModel):
    """Export status data (completed)"""
    export_id: str
    status: ExportStatus
    download_url: Optional[str] = None
    expiry_timestamp: Optional[str] = None
    file_size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    sections_generated: Optional[List[SectionGenerated]] = None
    metadata: Optional[ExportMetadata] = None
    error_message: Optional[str] = None


class ExportStatusResponse(BaseModel):
    """Response for export status check"""
    success: bool
    data: ExportStatusData
