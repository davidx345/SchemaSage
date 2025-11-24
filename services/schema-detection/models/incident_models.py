"""
Pydantic Models for Phase 3.5 - Database Incident Timeline
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class EventType(str, Enum):
    DEPLOYMENT = "deployment"
    MIGRATION = "migration"
    CONFIG_CHANGE = "config_change"
    TRAFFIC_SPIKE = "traffic_spike"
    QUERY_PATTERN = "query_pattern"


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactLikelihood(str, Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FixType(str, Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class RiskLevel(str, Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    HIGH = "high"


# ============================================================================
# EVENT CORRELATION (3.5.1)
# ============================================================================

class CorrelateEventsRequest(BaseModel):
    incident_id: str
    time_window_hours: int = Field(default=24, ge=1, le=168)
    event_sources: List[EventType]


class MetricsAtIncident(BaseModel):
    cpu_usage: int
    connection_count: int
    slow_queries: int
    disk_io: int


class IncidentInfo(BaseModel):
    incident_id: str
    timestamp: str
    title: str
    severity: IncidentSeverity
    duration_minutes: int
    affected_queries: int
    metrics_at_incident: MetricsAtIncident


class EventDetails(BaseModel):
    service: Optional[str] = None
    version: Optional[str] = None
    changes: Optional[str] = None
    deployed_by: Optional[str] = None
    normal_rpm: Optional[str] = None
    peak_rpm: Optional[str] = None
    spike_percentage: Optional[str] = None
    source: Optional[str] = None
    query: Optional[str] = None
    execution_count: Optional[str] = None
    avg_duration: Optional[str] = None
    missing_index: Optional[str] = None
    parameter: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: Optional[str] = None


class CorrelatedEvent(BaseModel):
    event_id: str
    timestamp: str
    event_type: EventType
    description: str
    correlation_score: int = Field(..., ge=0, le=100)
    time_before_incident: str
    impact_likelihood: ImpactLikelihood
    details: EventDetails


class PrimaryCause(BaseModel):
    event_id: str
    confidence: int = Field(..., ge=0, le=100)
    reasoning: str


class ContributingFactor(BaseModel):
    event_id: str
    contribution: str
    explanation: str


class CausalityAnalysis(BaseModel):
    primary_cause: PrimaryCause
    contributing_factors: List[ContributingFactor]


class EventCorrelationData(BaseModel):
    incident: IncidentInfo
    correlated_events: List[CorrelatedEvent]
    causality_analysis: CausalityAnalysis


class EventCorrelationResponse(BaseModel):
    success: bool
    data: EventCorrelationData


# ============================================================================
# ROOT CAUSE ANALYSIS (3.5.2)
# ============================================================================

class RootCauseRequest(BaseModel):
    incident_id: str
    analysis_depth: str = Field(default="comprehensive", description="quick, standard, or comprehensive")
    include_historical_patterns: bool = Field(default=True)


class RootCause(BaseModel):
    cause_id: str
    category: str
    title: str
    confidence: int = Field(..., ge=0, le=100)
    description: str
    evidence: List[str]
    affected_components: List[str]
    typical_symptoms: List[str]
    mitigation_urgency: str


class PatternMatch(BaseModel):
    pattern_name: str
    similarity_score: int = Field(..., ge=0, le=100)
    historical_occurrences: int
    avg_resolution_time_minutes: int
    common_fix: str


class FiveWhysAnalysis(BaseModel):
    why_1: str
    answer_1: str
    why_2: str
    answer_2: str
    why_3: str
    answer_3: str
    why_4: str
    answer_4: str
    why_5: str
    answer_5: str
    root_cause: str


class RootCauseData(BaseModel):
    incident_id: str
    root_causes: List[RootCause]
    pattern_matches: List[PatternMatch]
    five_whys_analysis: FiveWhysAnalysis


class RootCauseResponse(BaseModel):
    success: bool
    data: RootCauseData


# ============================================================================
# SIMILAR INCIDENTS (3.5.3)
# ============================================================================

class CurrentIncident(BaseModel):
    incident_id: str
    title: str
    severity: IncidentSeverity


class SimilarIncident(BaseModel):
    incident_id: str
    timestamp: str
    title: str
    similarity_score: int = Field(..., ge=0, le=100)
    root_cause: str
    resolution: str
    resolution_time_minutes: int
    resolved_by: str
    prevented_recurrence: bool
    shared_symptoms: List[str]
    different_factors: List[str]
    lessons_learned: List[str]


class RecurrencePattern(BaseModel):
    pattern_name: str
    occurrences: int
    frequency: str
    avg_resolution_time_minutes: int
    trend: str
    last_occurrence: str
    prevention_status: str
    prevention_measures: List[str]


class SimilarIncidentsData(BaseModel):
    current_incident: CurrentIncident
    similar_incidents: List[SimilarIncident]
    recurrence_patterns: List[RecurrencePattern]


class SimilarIncidentsResponse(BaseModel):
    success: bool
    data: SimilarIncidentsData


# ============================================================================
# RECOMMENDED FIX (3.5.4)
# ============================================================================

class FixPreferences(BaseModel):
    risk_tolerance: str = Field(default="moderate", description="low, moderate, or high")
    downtime_acceptable: bool = Field(default=False)
    automation_level: str = Field(default="supervised", description="manual, supervised, or automated")


class GenerateFixRequest(BaseModel):
    incident_id: str
    fix_preferences: FixPreferences = Field(default_factory=FixPreferences)


class FixRecommendation(BaseModel):
    fix_id: str
    fix_type: FixType
    category: str
    title: str
    impact: str
    estimated_resolution_time_minutes: int
    risk_level: RiskLevel
    sql_commands: List[str]
    rollback_plan: str
    prerequisites: List[str]
    validation_steps: List[str]


class AutomatedFix(BaseModel):
    fix_id: str
    name: str
    description: str
    can_automate: bool
    automation_risk: str
    estimated_duration_seconds: int
    approval_required: bool


class GenerateFixData(BaseModel):
    incident_id: str
    fixes: List[FixRecommendation]
    automated_fixes: List[AutomatedFix]


class GenerateFixResponse(BaseModel):
    success: bool
    data: GenerateFixData


# ============================================================================
# PREVENTION CHECKLIST (3.5.5)
# ============================================================================

class ChecklistItem(BaseModel):
    task: str
    status: str
    estimated_effort_hours: int
    impact: str


class ChecklistCategory(BaseModel):
    category: str
    priority: str
    items: List[ChecklistItem]


class ChecklistSummary(BaseModel):
    total_items: int
    implemented: int
    not_implemented: int
    high_priority: int
    medium_priority: int
    low_priority: int
    total_estimated_effort_hours: int


class QuickWin(BaseModel):
    task: str
    effort_hours: int
    impact: str
    priority: str


class PreventionChecklistData(BaseModel):
    incident_id: str
    prevention_checklist: List[ChecklistCategory]
    summary: ChecklistSummary
    quick_wins: List[QuickWin]


class PreventionChecklistResponse(BaseModel):
    success: bool
    data: PreventionChecklistData
