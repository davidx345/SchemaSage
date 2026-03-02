"""
Database Incident Timeline Router - Phase 3.5
10 endpoints: CRUD operations + advanced features (correlation, RCA, similar incidents, fixes, prevention)
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from models.incident_models import (
    CorrelateEventsRequest, EventCorrelationResponse,
    RootCauseRequest, RootCauseResponse,
    SimilarIncidentsResponse,
    GenerateFixRequest, GenerateFixResponse,
    PreventionChecklistResponse,
    IncidentSeverity
)
from core.incidents.incident_engine import (
    IncidentCorrelator, RootCauseAnalyzer, SimilarIncidentFinder,
    FixGenerator, PreventionChecklistGenerator
)

router = APIRouter(prefix="/api/incidents", tags=["Database Incident Timeline"])

# ===== CRUD REQUEST/RESPONSE MODELS =====

class IncidentCreateRequest(BaseModel):
    """Request model for creating a new incident."""
    title: str
    description: str
    severity: IncidentSeverity
    affected_systems: List[str] = []
    affected_queries: List[str] = []
    tags: List[str] = []

class IncidentResponse(BaseModel):
    """Response model for incident details."""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: str
    affected_systems: List[str]
    affected_queries: List[str]
    tags: List[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    duration_minutes: Optional[int] = None

class IncidentListResponse(BaseModel):
    """Response model for incident list."""
    incidents: List[IncidentResponse]
    total: int
    page: int
    limit: int

class IncidentUpdateRequest(BaseModel):
    """Request model for updating an incident."""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[str] = None
    affected_systems: Optional[List[str]] = None
    affected_queries: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    resolved_at: Optional[str] = None

# Initialize core components
incident_correlator = IncidentCorrelator()
root_cause_analyzer = RootCauseAnalyzer()
similar_incident_finder = SimilarIncidentFinder()
fix_generator = FixGenerator()
prevention_checklist_generator = PreventionChecklistGenerator()

# In-memory incident storage (replace with database in production)
incidents_db: Dict[str, dict] = {}


# ===== CRUD OPERATIONS =====

@router.post("/create", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(request: IncidentCreateRequest):
    """
    Create a new database incident.
    
    **Required Fields:**
    - `title`: Brief incident title
    - `description`: Detailed incident description
    - `severity`: critical | high | medium | low
    
    **Optional Fields:**
    - `affected_systems`: List of affected database systems/services
    - `affected_queries`: List of affected query IDs
    - `tags`: Custom tags for categorization
    
    **Auto-generated:**
    - `incident_id`: Unique identifier (UUID format)
    - `status`: Initially set to "open"
    - `created_at`, `updated_at`: ISO 8601 timestamps
    """
    try:
        # Generate unique incident ID
        from uuid import uuid4
        incident_id = str(uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        
        # Create incident record
        incident = {
            "incident_id": incident_id,
            "title": request.title,
            "description": request.description,
            "severity": request.severity.value,
            "status": "open",
            "affected_systems": request.affected_systems,
            "affected_queries": request.affected_queries,
            "tags": request.tags,
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
            "duration_minutes": None
        }
        
        # Store incident
        incidents_db[incident_id] = incident
        
        return IncidentResponse(**incident)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create incident: {str(e)}"
        )


@router.get("/list", response_model=IncidentListResponse)
async def list_incidents(
    status_filter: Optional[str] = Query(None, description="Filter by status: open, investigating, resolved"),
    severity_filter: Optional[IncidentSeverity] = Query(None, description="Filter by severity"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    List all incidents with optional filtering and pagination.
    
    **Query Parameters:**
    - `status_filter`: Filter by incident status (open, investigating, resolved)
    - `severity_filter`: Filter by severity (critical, high, medium, low)
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 10, max: 100)
    
    **Response:**
    - `incidents`: List of incident objects
    - `total`: Total number of incidents matching filters
    - `page`, `limit`: Pagination info
    """
    try:
        # Get all incidents
        all_incidents = list(incidents_db.values())
        
        # Apply filters
        filtered_incidents = all_incidents
        if status_filter:
            filtered_incidents = [inc for inc in filtered_incidents if inc["status"] == status_filter]
        if severity_filter:
            filtered_incidents = [inc for inc in filtered_incidents if inc["severity"] == severity_filter.value]
        
        # Sort by created_at descending (most recent first)
        filtered_incidents.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        total = len(filtered_incidents)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_incidents = filtered_incidents[start_idx:end_idx]
        
        # Convert to response models
        incident_responses = [IncidentResponse(**inc) for inc in paginated_incidents]
        
        return IncidentListResponse(
            incidents=incident_responses,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list incidents: {str(e)}"
        )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    """
    Get detailed information about a specific incident.
    
    **Path Parameters:**
    - `incident_id`: Unique incident identifier
    
    **Response:**
    - Complete incident details including all fields
    
    **Errors:**
    - 404: Incident not found
    """
    if incident_id not in incidents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    incident = incidents_db[incident_id]
    return IncidentResponse(**incident)


@router.put("/{incident_id}/update", response_model=IncidentResponse)
async def update_incident(incident_id: str, request: IncidentUpdateRequest):
    """
    Update an existing incident.
    
    **Path Parameters:**
    - `incident_id`: Unique incident identifier
    
    **Updatable Fields (all optional):**
    - `title`: Update incident title
    - `description`: Update description
    - `severity`: Change severity level
    - `status`: Update status (open, investigating, resolved)
    - `affected_systems`: Update affected systems list
    - `affected_queries`: Update affected queries list
    - `tags`: Update tags
    - `resolved_at`: Set resolution timestamp (auto-calculates duration)
    
    **Auto-updated:**
    - `updated_at`: Automatically set to current timestamp
    - `duration_minutes`: Calculated if resolved_at is set
    
    **Errors:**
    - 404: Incident not found
    """
    if incident_id not in incidents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    try:
        incident = incidents_db[incident_id]
        now = datetime.utcnow().isoformat() + "Z"
        
        # Update fields if provided
        if request.title is not None:
            incident["title"] = request.title
        if request.description is not None:
            incident["description"] = request.description
        if request.severity is not None:
            incident["severity"] = request.severity.value
        if request.status is not None:
            incident["status"] = request.status
        if request.affected_systems is not None:
            incident["affected_systems"] = request.affected_systems
        if request.affected_queries is not None:
            incident["affected_queries"] = request.affected_queries
        if request.tags is not None:
            incident["tags"] = request.tags
        if request.resolved_at is not None:
            incident["resolved_at"] = request.resolved_at
            # Calculate duration if resolved
            if incident["created_at"]:
                created = datetime.fromisoformat(incident["created_at"].replace("Z", ""))
                resolved = datetime.fromisoformat(request.resolved_at.replace("Z", ""))
                incident["duration_minutes"] = int((resolved - created).total_seconds() / 60)
        
        incident["updated_at"] = now
        
        return IncidentResponse(**incident)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update incident: {str(e)}"
        )


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: str):
    """
    Delete an incident permanently.
    
    **Path Parameters:**
    - `incident_id`: Unique incident identifier
    
    **Response:**
    - 204 No Content on success
    
    **Errors:**
    - 404: Incident not found
    
    **Warning:**
    - This operation is permanent and cannot be undone
    - All associated data (correlations, RCA results, etc.) will be lost
    - Consider marking incident as "resolved" instead for record-keeping
    """
    if incident_id not in incidents_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    del incidents_db[incident_id]
    return None


# ===== ADVANCED FEATURES =====

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
