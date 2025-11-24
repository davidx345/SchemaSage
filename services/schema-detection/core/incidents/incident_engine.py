"""
Database Incident Timeline Core Logic
"""
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from models.incident_models import (
    EventCorrelationData, IncidentInfo, MetricsAtIncident, CorrelatedEvent,
    EventDetails, CausalityAnalysis, PrimaryCause, ContributingFactor,
    RootCauseData, RootCause, PatternMatch, FiveWhysAnalysis,
    SimilarIncidentsData, CurrentIncident, SimilarIncident, RecurrencePattern,
    GenerateFixData, FixRecommendation, AutomatedFix,
    PreventionChecklistData, ChecklistCategory, ChecklistItem, ChecklistSummary, QuickWin,
    EventType, IncidentSeverity, ImpactLikelihood, FixType, RiskLevel
)


class IncidentCorrelator:
    """Correlates incidents with system events"""
    
    def correlate_events(self, incident_id: str, time_window_hours: int, event_sources: List[str]) -> EventCorrelationData:
        """Correlates incident with deployments, migrations, config changes"""
        incident = IncidentInfo(
            incident_id=incident_id,
            timestamp="2024-11-20 14:32:00",
            title="Database CPU Spike - 95% Utilization",
            severity=IncidentSeverity.CRITICAL,
            duration_minutes=18,
            affected_queries=1247,
            metrics_at_incident=MetricsAtIncident(
                cpu_usage=95,
                connection_count=487,
                slow_queries=234,
                disk_io=82
            )
        )
        
        correlated_events = self._find_correlated_events(incident_id, time_window_hours)
        causality = self._analyze_causality(correlated_events)
        
        return EventCorrelationData(
            incident=incident,
            correlated_events=correlated_events,
            causality_analysis=causality
        )
    
    def _find_correlated_events(self, incident_id: str, time_window: int) -> List[CorrelatedEvent]:
        """Finds events correlated with incident"""
        return [
            CorrelatedEvent(
                event_id="DEPLOY-2024-11-20-045",
                timestamp="2024-11-20 14:15:00",
                event_type=EventType.DEPLOYMENT,
                description="Frontend deployment v2.3.5 - Added product search feature",
                correlation_score=92,
                time_before_incident="17 minutes before",
                impact_likelihood=ImpactLikelihood.VERY_HIGH,
                details=EventDetails(
                    service="frontend-api",
                    version="2.3.5",
                    changes="New ElasticSearch integration, increased DB queries by 40%",
                    deployed_by="john.doe@company.com"
                )
            ),
            CorrelatedEvent(
                event_id="TRAFFIC-2024-11-20-112",
                timestamp="2024-11-20 14:20:00",
                event_type=EventType.TRAFFIC_SPIKE,
                description="Traffic spike detected - 3x normal load",
                correlation_score=88,
                time_before_incident="12 minutes before",
                impact_likelihood=ImpactLikelihood.VERY_HIGH,
                details=EventDetails(
                    normal_rpm="5,000 req/min",
                    peak_rpm="15,000 req/min",
                    spike_percentage="200%",
                    source="Marketing email campaign launched"
                )
            ),
            CorrelatedEvent(
                event_id="QUERY-2024-11-20-089",
                timestamp="2024-11-20 14:25:00",
                event_type=EventType.QUERY_PATTERN,
                description="New query pattern: Full table scan on products table",
                correlation_score=85,
                time_before_incident="7 minutes before",
                impact_likelihood=ImpactLikelihood.HIGH,
                details=EventDetails(
                    query="SELECT * FROM products WHERE name LIKE '%search%'",
                    execution_count="1,247 times",
                    avg_duration="2.3s per query",
                    missing_index="products.name (text search)"
                )
            ),
            CorrelatedEvent(
                event_id="CONFIG-2024-11-20-023",
                timestamp="2024-11-20 10:30:00",
                event_type=EventType.CONFIG_CHANGE,
                description="Database connection pool increased from 200 to 500",
                correlation_score=45,
                time_before_incident="4 hours before",
                impact_likelihood=ImpactLikelihood.MEDIUM,
                details=EventDetails(
                    parameter="max_connections",
                    old_value="200",
                    new_value="500",
                    changed_by="dba@company.com"
                )
            )
        ]
    
    def _analyze_causality(self, events: List[CorrelatedEvent]) -> CausalityAnalysis:
        """Analyzes causality between events and incident"""
        primary = events[0] if events else None
        
        primary_cause = PrimaryCause(
            event_id=primary.event_id if primary else "",
            confidence=92,
            reasoning="Deployment introduced inefficient search query 17 minutes before incident. Query pattern correlation shows identical timing."
        )
        
        contributing_factors = [
            ContributingFactor(
                event_id="TRAFFIC-2024-11-20-112",
                contribution="Amplified impact of inefficient query",
                explanation="3x traffic spike increased query execution from ~400/min to 1,200/min"
            ),
            ContributingFactor(
                event_id="QUERY-2024-11-20-089",
                contribution="Missing index on products.name",
                explanation="Full table scan on 1.2M rows takes 2.3s per query vs <100ms with index"
            )
        ]
        
        return CausalityAnalysis(
            primary_cause=primary_cause,
            contributing_factors=contributing_factors
        )


class RootCauseAnalyzer:
    """ML-powered root cause analysis"""
    
    def analyze_root_cause(self, incident_id: str, analysis_depth: str, include_historical: bool) -> RootCauseData:
        """Performs root cause analysis"""
        root_causes = self._identify_root_causes()
        pattern_matches = self._find_pattern_matches()
        five_whys = self._perform_five_whys_analysis()
        
        return RootCauseData(
            incident_id=incident_id,
            root_causes=root_causes,
            pattern_matches=pattern_matches,
            five_whys_analysis=five_whys
        )
    
    def _identify_root_causes(self) -> List[RootCause]:
        """Identifies root causes with evidence"""
        return [
            RootCause(
                cause_id="cause_001",
                category="query_performance",
                title="Unindexed Full Table Scan on products.name",
                confidence=94,
                description="New search feature introduced query without supporting index, causing full table scan on 1.2M rows",
                evidence=[
                    "EXPLAIN plan shows 'Seq Scan' on products table (1,234,567 rows)",
                    "Query execution time: 2.3s average (baseline: 45ms for indexed queries)",
                    "Query introduced in deployment v2.3.5 at 14:15 - incident at 14:32",
                    "CPU spike correlates with query execution frequency (1,247 executions)",
                    "No existing index on products.name column"
                ],
                affected_components=[
                    "products table",
                    "Search API endpoint /api/products/search",
                    "Frontend search feature"
                ],
                typical_symptoms=[
                    "High CPU utilization (80%+)",
                    "Slow API response times (2s+)",
                    "Increased connection count",
                    "Buffer cache churn"
                ],
                mitigation_urgency="immediate"
            ),
            RootCause(
                cause_id="cause_002",
                category="connection_exhaustion",
                title="Traffic Spike Amplified Impact",
                confidence=88,
                description="Marketing campaign caused 3x normal traffic, multiplying effect of slow query",
                evidence=[
                    "Traffic increased from 5K req/min to 15K req/min at 14:20",
                    "Connection count jumped from 150 to 487",
                    "Query execution frequency increased proportionally",
                    "Marketing email sent at 14:18 (confirmed by marketing team)"
                ],
                affected_components=[
                    "Application connection pool",
                    "Database connection manager",
                    "Load balancer"
                ],
                typical_symptoms=[
                    "Rapid connection count increase",
                    "Connection pool saturation",
                    "Queue wait times"
                ],
                mitigation_urgency="high"
            )
        ]
    
    def _find_pattern_matches(self) -> List[PatternMatch]:
        """Finds historical pattern matches"""
        return [
            PatternMatch(
                pattern_name="Deployment-Triggered Performance Degradation",
                similarity_score=91,
                historical_occurrences=3,
                avg_resolution_time_minutes=22,
                common_fix="Add missing index + optimize query"
            ),
            PatternMatch(
                pattern_name="Traffic Spike + Inefficient Query",
                similarity_score=86,
                historical_occurrences=5,
                avg_resolution_time_minutes=18,
                common_fix="Scale database + add caching layer"
            )
        ]
    
    def _perform_five_whys_analysis(self) -> FiveWhysAnalysis:
        """Performs Five Whys analysis"""
        return FiveWhysAnalysis(
            why_1="Why did CPU spike to 95%?",
            answer_1="Because search queries were running 1,247 times causing full table scans",
            why_2="Why were queries doing full table scans?",
            answer_2="Because no index exists on products.name for text search",
            why_3="Why was no index created before deployment?",
            answer_3="Because new search feature wasn't tested with production data volume",
            why_4="Why wasn't it tested with production data?",
            answer_4="Because staging database only has 10% of production data",
            why_5="Why doesn't staging have realistic data volume?",
            answer_5="Because data subsetting process excludes large tables to save costs",
            root_cause="Testing process doesn't validate query performance at production scale"
        )


class SimilarIncidentFinder:
    """Finds similar historical incidents"""
    
    def find_similar_incidents(self, incident_id: str) -> SimilarIncidentsData:
        """Finds similar incidents with resolutions"""
        current = CurrentIncident(
            incident_id=incident_id,
            title="Database CPU Spike - 95% Utilization",
            severity=IncidentSeverity.CRITICAL
        )
        
        similar = self._find_similar(incident_id)
        patterns = self._identify_recurrence_patterns()
        
        return SimilarIncidentsData(
            current_incident=current,
            similar_incidents=similar,
            recurrence_patterns=patterns
        )
    
    def _find_similar(self, incident_id: str) -> List[SimilarIncident]:
        """Finds similar incidents"""
        return [
            SimilarIncident(
                incident_id="INC-2024-10-15-003",
                timestamp="2024-10-15 09:23:00",
                title="Database CPU Spike - 92% Utilization",
                similarity_score=94,
                root_cause="Inefficient query with full table scan on products.name after deployment v2.1.2",
                resolution="Added GIN index on products.name using pg_trgm extension",
                resolution_time_minutes=18,
                resolved_by="Sarah Chen (DBA)",
                prevented_recurrence=True,
                shared_symptoms=[
                    "CPU usage spiked to 90%+ during peak hours",
                    "Full table scan on products table (1.2M rows)",
                    "Query execution time: 2.1s average",
                    "Triggered by new deployment with search feature",
                    "Connection count increased 200%+",
                    "Traffic spike from marketing campaign"
                ],
                different_factors=[
                    "v2.1.2 deployment vs current v2.3.5",
                    "Occurred at 9am vs current 2:32pm",
                    "Peak traffic 10K req/min vs current 15K req/min"
                ],
                lessons_learned=[
                    "Always test queries in staging with production data volume",
                    "Create indexes CONCURRENTLY to avoid table locks",
                    "Monitor query execution plans after deployments",
                    "Set up alerts for CPU >80% for 5+ minutes",
                    "Implement query timeout of 5s for user-facing queries"
                ]
            ),
            SimilarIncident(
                incident_id="INC-2024-09-22-007",
                timestamp="2024-09-22 14:45:00",
                title="Connection Pool Exhaustion - 498/500",
                similarity_score=78,
                root_cause="Traffic spike (4x normal) exhausted database connection pool",
                resolution="Increased max_connections to 1000 + deployed PgBouncer",
                resolution_time_minutes=45,
                resolved_by="Mike Rodriguez (SRE)",
                prevented_recurrence=True,
                shared_symptoms=[
                    "Connection count reached 98% of max_connections",
                    "Traffic spike from external event (3x-4x normal)",
                    "Connection wait time increased 100x",
                    "Slow API response times (5s+)"
                ],
                different_factors=[],
                lessons_learned=[
                    "Deploy PgBouncer for connection pooling",
                    "Set up auto-scaling for application servers",
                    "Monitor connection count and set alerts at 80% capacity",
                    "Implement circuit breakers in application code"
                ]
            )
        ]
    
    def _identify_recurrence_patterns(self) -> List[RecurrencePattern]:
        """Identifies recurrence patterns"""
        return [
            RecurrencePattern(
                pattern_name="Post-Deployment Performance Issues",
                occurrences=7,
                frequency="~1 per month",
                avg_resolution_time_minutes=25,
                trend="decreasing",
                last_occurrence="2024-10-15",
                prevention_status="partial",
                prevention_measures=[
                    "Query performance testing added to CI/CD (50% reduction in incidents)",
                    "Database monitoring alerts improved",
                    "Runbooks created for common scenarios"
                ]
            )
        ]


class FixGenerator:
    """Generates fix recommendations"""
    
    def generate_fixes(self, incident_id: str, fix_preferences: Dict[str, Any]) -> GenerateFixData:
        """Generates immediate, short-term, and long-term fixes"""
        fixes = self._generate_fix_recommendations()
        automated = self._identify_automated_fixes(fixes)
        
        return GenerateFixData(
            incident_id=incident_id,
            fixes=fixes,
            automated_fixes=automated
        )
    
    def _generate_fix_recommendations(self) -> List[FixRecommendation]:
        """Generates fix recommendations"""
        return [
            FixRecommendation(
                fix_id="FIX-001",
                fix_type=FixType.IMMEDIATE,
                category="query_optimization",
                title="Add Index on products.name",
                impact="high",
                estimated_resolution_time_minutes=5,
                risk_level=RiskLevel.SAFE,
                sql_commands=[
                    "-- Add index on products.name for text search (concurrent to avoid table lock)",
                    "CREATE INDEX CONCURRENTLY idx_products_name ON products USING GIN (name gin_trgm_ops);",
                    "",
                    "-- Verify index was created",
                    "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'products' AND indexname = 'idx_products_name';",
                    "",
                    "-- Test query performance after index",
                    "EXPLAIN ANALYZE SELECT * FROM products WHERE name ILIKE '%search%';"
                ],
                rollback_plan="DROP INDEX CONCURRENTLY idx_products_name;",
                prerequisites=[
                    "Install pg_trgm extension: CREATE EXTENSION IF NOT EXISTS pg_trgm;",
                    "Ensure sufficient disk space for index (estimate: 150 MB)",
                    "Check for existing index on products.name",
                    "Verify no other CREATE INDEX operations running"
                ],
                validation_steps=[
                    "Run EXPLAIN on slow query - should show 'Index Scan' instead of 'Seq Scan'",
                    "Monitor query execution time - target: <100ms (current: 2.3s)",
                    "Check CPU usage - should drop from 95% to <50%",
                    "Verify no lock timeouts during index creation"
                ]
            ),
            FixRecommendation(
                fix_id="FIX-002",
                fix_type=FixType.SHORT_TERM,
                category="query_optimization",
                title="Add Query Result Caching",
                impact="medium",
                estimated_resolution_time_minutes=30,
                risk_level=RiskLevel.MODERATE,
                sql_commands=[],
                rollback_plan="Disable caching layer, direct database queries",
                prerequisites=[
                    "Redis cluster deployed and accessible",
                    "Application code updated with caching logic",
                    "Cache invalidation strategy defined"
                ],
                validation_steps=[
                    "Verify cache hit rate >70% for search queries",
                    "Monitor database query count - should decrease 70%",
                    "Test cache invalidation when products updated",
                    "Verify stale data acceptable (5min TTL)"
                ]
            ),
            FixRecommendation(
                fix_id="FIX-003",
                fix_type=FixType.LONG_TERM,
                category="architecture",
                title="Migrate to Elasticsearch for Full-Text Search",
                impact="high",
                estimated_resolution_time_minutes=2880,
                risk_level=RiskLevel.MODERATE,
                sql_commands=[],
                rollback_plan="Maintain PostgreSQL as fallback, gradual rollback",
                prerequisites=[
                    "Elasticsearch cluster provisioned",
                    "Data sync pipeline from PostgreSQL to Elasticsearch",
                    "Search API refactored to use Elasticsearch",
                    "Load testing completed"
                ],
                validation_steps=[
                    "Search latency <50ms (10x improvement)",
                    "Handle 100K+ searches/min (10x current capacity)",
                    "Zero downtime migration verified",
                    "Fallback to PostgreSQL tested"
                ]
            )
        ]
    
    def _identify_automated_fixes(self, fixes: List[FixRecommendation]) -> List[AutomatedFix]:
        """Identifies fixes that can be automated"""
        return [
            AutomatedFix(
                fix_id="FIX-001",
                name="Auto-Create Index",
                description="Automatically create GIN index on products.name",
                can_automate=True,
                automation_risk="low",
                estimated_duration_seconds=300,
                approval_required=False
            )
        ]


class PreventionChecklistGenerator:
    """Generates prevention checklists"""
    
    def generate_checklist(self, incident_id: str) -> PreventionChecklistData:
        """Generates prevention checklist"""
        checklist = self._create_checklist()
        summary = self._calculate_summary(checklist)
        quick_wins = self._identify_quick_wins(checklist)
        
        return PreventionChecklistData(
            incident_id=incident_id,
            prevention_checklist=checklist,
            summary=summary,
            quick_wins=quick_wins
        )
    
    def _create_checklist(self) -> List[ChecklistCategory]:
        """Creates prevention checklist"""
        return [
            ChecklistCategory(
                category="Testing",
                priority="high",
                items=[
                    ChecklistItem(
                        task="Test all queries with production-scale data (1M+ rows)",
                        status="not_implemented",
                        estimated_effort_hours=8,
                        impact="Prevent 80% of query performance incidents"
                    ),
                    ChecklistItem(
                        task="Add query performance tests to CI/CD pipeline",
                        status="not_implemented",
                        estimated_effort_hours=16,
                        impact="Automated detection before deployment"
                    ),
                    ChecklistItem(
                        task="Run EXPLAIN ANALYZE on all new queries before merging",
                        status="not_implemented",
                        estimated_effort_hours=2,
                        impact="Catch missing indexes early"
                    )
                ]
            ),
            ChecklistCategory(
                category="Monitoring",
                priority="high",
                items=[
                    ChecklistItem(
                        task="Set up alert: CPU >80% for >5 minutes",
                        status="implemented",
                        estimated_effort_hours=0,
                        impact="Early warning system"
                    ),
                    ChecklistItem(
                        task="Set up alert: Slow query count >10 in 1 minute",
                        status="not_implemented",
                        estimated_effort_hours=2,
                        impact="Detect query performance degradation"
                    ),
                    ChecklistItem(
                        task="Track query execution plans after each deployment",
                        status="not_implemented",
                        estimated_effort_hours=8,
                        impact="Detect plan regressions automatically"
                    )
                ]
            ),
            ChecklistCategory(
                category="Deployment",
                priority="medium",
                items=[
                    ChecklistItem(
                        task="Implement gradual rollout (10% → 50% → 100%)",
                        status="not_implemented",
                        estimated_effort_hours=24,
                        impact="Limit blast radius of performance issues"
                    ),
                    ChecklistItem(
                        task="Add database schema review to deployment checklist",
                        status="not_implemented",
                        estimated_effort_hours=1,
                        impact="Catch missing indexes before production"
                    ),
                    ChecklistItem(
                        task="Require DBA approval for queries touching >100K rows",
                        status="not_implemented",
                        estimated_effort_hours=4,
                        impact="Expert review for high-impact queries"
                    )
                ]
            ),
            ChecklistCategory(
                category="Architecture",
                priority="low",
                items=[
                    ChecklistItem(
                        task="Implement read replicas for search queries",
                        status="not_implemented",
                        estimated_effort_hours=40,
                        impact="Isolate search load from transactional queries"
                    ),
                    ChecklistItem(
                        task="Evaluate Elasticsearch for full-text search",
                        status="not_implemented",
                        estimated_effort_hours=80,
                        impact="10x search performance improvement"
                    )
                ]
            )
        ]
    
    def _calculate_summary(self, checklist: List[ChecklistCategory]) -> ChecklistSummary:
        """Calculates checklist summary"""
        all_items = [item for category in checklist for item in category.items]
        
        implemented = sum(1 for item in all_items if item.status == "implemented")
        not_implemented = len(all_items) - implemented
        
        high_priority = sum(1 for cat in checklist if cat.priority == "high" for _ in cat.items)
        medium_priority = sum(1 for cat in checklist if cat.priority == "medium" for _ in cat.items)
        low_priority = sum(1 for cat in checklist if cat.priority == "low" for _ in cat.items)
        
        total_effort = sum(item.estimated_effort_hours for item in all_items)
        
        return ChecklistSummary(
            total_items=len(all_items),
            implemented=implemented,
            not_implemented=not_implemented,
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
            total_estimated_effort_hours=total_effort
        )
    
    def _identify_quick_wins(self, checklist: List[ChecklistCategory]) -> List[QuickWin]:
        """Identifies quick wins"""
        return [
            QuickWin(
                task="Set up alert: Slow query count >10 in 1 minute",
                effort_hours=2,
                impact="high",
                priority="Implement this week"
            ),
            QuickWin(
                task="Run EXPLAIN ANALYZE on all new queries before merging",
                effort_hours=2,
                impact="high",
                priority="Implement this week"
            ),
            QuickWin(
                task="Add database schema review to deployment checklist",
                effort_hours=1,
                impact="medium",
                priority="Implement this week"
            )
        ]
