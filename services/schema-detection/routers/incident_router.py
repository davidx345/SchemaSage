"""
Database Incident Timeline Router - Phase 3.5
5 endpoints for incident correlation, RCA, similar incidents, fixes, and prevention
"""
from fastapi import APIRouter, HTTPException

from models.incident_models import (
    CorrelateEventsRequest, EventCorrelationResponse,
    RootCauseRequest, RootCauseResponse,
    SimilarIncidentsResponse,
    GenerateFixRequest, GenerateFixResponse,
    PreventionChecklistResponse
)
from core.incidents.incident_engine import (
    IncidentCorrelator, RootCauseAnalyzer, SimilarIncidentFinder,
    FixGenerator, PreventionChecklistGenerator
)

router = APIRouter(prefix="/api/incidents", tags=["Database Incident Timeline"])

# Initialize core components
incident_correlator = IncidentCorrelator()
root_cause_analyzer = RootCauseAnalyzer()
similar_incident_finder = SimilarIncidentFinder()
fix_generator = FixGenerator()
prevention_checklist_generator = PreventionChecklistGenerator()


@router.post("/correlate-events", response_model=EventCorrelationResponse)
async def correlate_incident_events(request: CorrelateEventsRequest):
    """
    Correlate incidents with deployments, migrations, and system changes.
    
    **Event Sources:**
    - `deployments`: Application/service deployments
    - `migrations`: Database schema migrations
    - `config_changes`: Database configuration changes
    - `traffic_spikes`: Unusual traffic patterns
    - `query_patterns`: New or changed query patterns
    
    **Features:**
    - Time-based correlation (configurable window: 1-168 hours)
    - Correlation scoring (0-100)
    - Impact likelihood assessment (very_high, high, medium, low)
    - Causality analysis with primary cause + contributing factors
    - Detailed event metadata
    - Time-before-incident calculation
    
    **Output:**
    - Incident details with metrics at time of incident
    - List of correlated events sorted by correlation score
    - Primary cause with confidence level
    - Contributing factors with explanations
    """
    try:
        correlation_data = incident_correlator.correlate_events(
            incident_id=request.incident_id,
            time_window_hours=request.time_window_hours,
            event_sources=[et.value for et in request.event_sources]
        )
        
        return EventCorrelationResponse(success=True, data=correlation_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event correlation failed: {str(e)}")


@router.post("/analyze-root-cause", response_model=RootCauseResponse)
async def analyze_root_cause(request: RootCauseRequest):
    """
    ML-powered root cause detection with evidence and confidence.
    
    **Analysis Depths:**
    - `quick`: Basic analysis (< 5 sec)
    - `standard`: Standard analysis with pattern matching (< 15 sec)
    - `comprehensive`: Deep analysis with Five Whys (< 30 sec)
    
    **Features:**
    - Multiple root causes with confidence scores
    - Evidence collection (logs, metrics, query plans)
    - Affected components identification
    - Typical symptoms recognition
    - Historical pattern matching
    - Five Whys analysis for comprehensive depth
    - Mitigation urgency assessment
    
    **Root Cause Categories:**
    - `query_performance`: Slow/inefficient queries
    - `connection_exhaustion`: Connection pool saturation
    - `lock_contention`: Deadlocks and lock waits
    - `resource_exhaustion`: CPU/memory/disk/IO limits
    - `schema_design`: Suboptimal schema structure
    - `configuration`: Misconfigured parameters
    """
    try:
        root_cause_data = root_cause_analyzer.analyze_root_cause(
            incident_id=request.incident_id,
            analysis_depth=request.analysis_depth,
            include_historical=request.include_historical_patterns
        )
        
        return RootCauseResponse(success=True, data=root_cause_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Root cause analysis failed: {str(e)}")


@router.get("/similar/{incident_id}", response_model=SimilarIncidentsResponse)
async def find_similar_incidents(incident_id: str):
    """
    Find historical incidents with similar symptoms and resolutions.
    
    **Matching Criteria:**
    - Shared symptoms (CPU spikes, query patterns, error types)
    - Similar metrics (CPU %, connection count, query duration)
    - Common root causes
    - Event patterns (deployment-triggered, traffic-related)
    
    **Features:**
    - Similarity scoring (0-100)
    - Resolution details with time-to-resolve
    - Lessons learned from each incident
    - Recurrence pattern analysis
    - Prevention measure effectiveness
    - Trend analysis (increasing/stable/decreasing)
    
    **Output:**
    - List of similar incidents sorted by similarity score
    - Resolution strategies that worked
    - Differences to consider
    - Recurrence patterns over time
    - Prevention status and measures
    """
    try:
        similar_data = similar_incident_finder.find_similar_incidents(incident_id=incident_id)
        
        return SimilarIncidentsResponse(success=True, data=similar_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar incident search failed: {str(e)}")


@router.post("/generate-fix", response_model=GenerateFixResponse)
async def generate_fix_recommendations(request: GenerateFixRequest):
    """
    Generate immediate, short-term, and long-term fixes with SQL.
    
    **Fix Types:**
    - `immediate`: Quick fixes (< 30 min) - indexes, config changes
    - `short_term`: Medium fixes (hours to days) - caching, query optimization
    - `long_term`: Strategic fixes (weeks to months) - architecture changes
    
    **Features:**
    - Ready-to-execute SQL commands
    - Rollback plans for safety
    - Prerequisites checklist
    - Validation steps
    - Risk assessment (safe, moderate, high)
    - Estimated resolution time
    - Impact analysis
    - Automated fix detection
    
    **Fix Categories:**
    - `query_optimization`: Index creation, query rewriting
    - `configuration`: Parameter tuning
    - `scaling`: Resource scaling (vertical/horizontal)
    - `architecture`: Fundamental design changes
    - `monitoring`: Alerting and observability
    
    **Automation:**
    - Identifies fixes that can be auto-applied
    - Approval workflow for high-risk changes
    - Estimated duration for automated execution
    """
    try:
        fix_data = fix_generator.generate_fixes(
            incident_id=request.incident_id,
            fix_preferences=request.fix_preferences.dict()
        )
        
        return GenerateFixResponse(success=True, data=fix_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {str(e)}")


@router.get("/prevention-checklist/{incident_id}", response_model=PreventionChecklistResponse)
async def get_prevention_checklist(incident_id: str):
    """
    Generate preventive measures to avoid recurrence.
    
    **Checklist Categories:**
    - **Testing**: Query performance tests, load testing, staging validation
    - **Monitoring**: Alerts, dashboards, query plan tracking
    - **Deployment**: Gradual rollout, DBA approval, change management
    - **Architecture**: Scaling strategies, caching, read replicas
    
    **Priority Levels:**
    - `high`: Implement within 1 week (critical preventions)
    - `medium`: Implement within 1 month
    - `low`: Consider for future roadmap
    
    **Features:**
    - Task status tracking (implemented/not_implemented)
    - Effort estimation (hours)
    - Impact assessment
    - Quick wins identification (high impact, low effort)
    - Summary statistics
    
    **Output:**
    - Categorized checklist with priorities
    - Total effort estimation
    - Implementation status
    - Quick wins (implement this week)
    - ROI analysis per task
    """
    try:
        checklist_data = prevention_checklist_generator.generate_checklist(incident_id=incident_id)
        
        return PreventionChecklistResponse(success=True, data=checklist_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prevention checklist generation failed: {str(e)}")
