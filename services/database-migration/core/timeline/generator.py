"""
Migration Timeline Generator

Generates detailed migration timeline with phases, resources, and risks.
"""

import logging
from typing import List, Tuple
from models.timeline_models import (
    TimelineRequest, MigrationPhase, ResourceRequirement, RiskItem,
    TimelineSummary, MigrationComplexity, RiskLevel, PhaseStatus
)

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """Generate migration timeline based on project parameters"""
    
    def __init__(self):
        self.phases: List[MigrationPhase] = []
        self.all_resources: List[ResourceRequirement] = []
        self.all_risks: List[RiskItem] = []
        
    def generate_timeline(self, request: TimelineRequest) -> Tuple[TimelineSummary, List[MigrationPhase], List[ResourceRequirement], List[RiskItem], List[str]]:
        """
        Generate complete migration timeline
        
        Args:
            request: Timeline request parameters
            
        Returns:
            Tuple of (summary, phases, resources, risks, recommendations)
        """
        # Calculate complexity if not provided
        complexity = request.complexity or self._calculate_complexity(request)
        
        # Generate phases
        self.phases = self._generate_phases(request, complexity)
        
        # Aggregate resources and risks
        self.all_resources = self._aggregate_resources()
        self.all_risks = self._aggregate_risks()
        
        # Generate summary
        summary = self._generate_summary(complexity)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(request, complexity)
        
        return summary, self.phases, self.all_resources, self.all_risks, recommendations
    
    def _calculate_complexity(self, request: TimelineRequest) -> MigrationComplexity:
        """Calculate migration complexity based on parameters"""
        complexity_score = 0
        
        # Data volume factor (0-30 points)
        if request.data_volume_gb < 10:
            complexity_score += 5
        elif request.data_volume_gb < 100:
            complexity_score += 10
        elif request.data_volume_gb < 1000:
            complexity_score += 20
        else:
            complexity_score += 30
        
        # Table count factor (0-20 points)
        if request.num_tables < 50:
            complexity_score += 5
        elif request.num_tables < 200:
            complexity_score += 10
        elif request.num_tables < 500:
            complexity_score += 15
        else:
            complexity_score += 20
        
        # Stored procedures factor (0-20 points)
        if request.num_stored_procedures > 100:
            complexity_score += 20
        elif request.num_stored_procedures > 50:
            complexity_score += 15
        elif request.num_stored_procedures > 10:
            complexity_score += 10
        elif request.num_stored_procedures > 0:
            complexity_score += 5
        
        # Views and triggers (0-15 points)
        object_count = request.num_views + request.num_triggers
        if object_count > 50:
            complexity_score += 15
        elif object_count > 20:
            complexity_score += 10
        elif object_count > 5:
            complexity_score += 5
        
        # Special features (0-15 points)
        if request.has_replication:
            complexity_score += 8
        if request.has_encryption:
            complexity_score += 7
        
        # Determine complexity level
        if complexity_score < 25:
            return MigrationComplexity.SIMPLE
        elif complexity_score < 50:
            return MigrationComplexity.MODERATE
        elif complexity_score < 75:
            return MigrationComplexity.COMPLEX
        else:
            return MigrationComplexity.VERY_COMPLEX
    
    def _generate_phases(self, request: TimelineRequest, complexity: MigrationComplexity) -> List[MigrationPhase]:
        """Generate migration phases"""
        phases = []
        
        # Phase 1: Assessment and Planning
        phases.append(MigrationPhase(
            phase_number=1,
            name="Assessment and Planning",
            description="Analyze source database, identify dependencies, and create detailed migration plan",
            duration_days=self._calculate_phase_duration(complexity, 3, 5, 7, 10),
            tasks=[
                "Analyze source database schema and data",
                "Identify all dependencies and relationships",
                "Document stored procedures, triggers, and views",
                "Create detailed migration strategy",
                "Define success criteria and rollback plan"
            ],
            dependencies=[],
            resource_requirements=[
                ResourceRequirement(
                    category="Personnel",
                    requirement="Database architect and 1-2 senior DBAs",
                    is_critical=True
                ),
                ResourceRequirement(
                    category="Tools",
                    requirement="Schema analysis and documentation tools",
                    estimated_cost=500.0,
                    is_critical=False
                )
            ],
            risks=[
                RiskItem(
                    risk_type="incomplete_analysis",
                    level=RiskLevel.HIGH,
                    description="Missing critical dependencies or objects",
                    mitigation="Conduct thorough automated and manual analysis",
                    probability=0.3
                )
            ]
        ))
        
        # Phase 2: Environment Setup
        phases.append(MigrationPhase(
            phase_number=2,
            name="Environment Setup",
            description="Provision target infrastructure and configure migration tools",
            duration_days=self._calculate_phase_duration(complexity, 2, 3, 5, 7),
            tasks=[
                "Provision target database infrastructure",
                "Configure network connectivity and security",
                "Set up migration tools and data transfer mechanisms",
                "Create staging environment for testing",
                "Configure monitoring and alerting"
            ],
            dependencies=[1],
            resource_requirements=[
                ResourceRequirement(
                    category="Infrastructure",
                    requirement=f"Target {request.target_db_type.value} database instance",
                    estimated_cost=1000.0,
                    is_critical=True
                ),
                ResourceRequirement(
                    category="Network",
                    requirement="Secure connection between source and target",
                    estimated_cost=200.0,
                    is_critical=True
                )
            ],
            risks=[
                RiskItem(
                    risk_type="connectivity",
                    level=RiskLevel.MEDIUM,
                    description="Network connectivity issues between environments",
                    mitigation="Test connectivity early and have backup connection methods",
                    probability=0.2
                )
            ]
        ))
        
        # Phase 3: Schema Migration
        phases.append(MigrationPhase(
            phase_number=3,
            name="Schema Migration",
            description="Migrate database schema to target database",
            duration_days=self._calculate_phase_duration(complexity, 3, 5, 8, 12),
            tasks=[
                "Convert and migrate table schemas",
                "Recreate indexes and constraints",
                "Migrate views and materialized views",
                "Convert stored procedures and functions",
                "Migrate triggers",
                "Validate schema integrity"
            ],
            dependencies=[2],
            resource_requirements=[
                ResourceRequirement(
                    category="Personnel",
                    requirement="2-3 database developers with expertise in both platforms",
                    is_critical=True
                )
            ],
            risks=[
                RiskItem(
                    risk_type="compatibility",
                    level=RiskLevel.HIGH,
                    description="Incompatible schema features or data types",
                    mitigation="Use automated conversion tools with manual review",
                    probability=0.4
                ),
                RiskItem(
                    risk_type="data_type_mismatch",
                    level=RiskLevel.MEDIUM,
                    description="Data type conversion issues",
                    mitigation="Test all data type mappings thoroughly",
                    probability=0.3
                )
            ]
        ))
        
        # Phase 4: Data Migration
        phases.append(MigrationPhase(
            phase_number=4,
            name="Data Migration",
            description="Transfer data from source to target database",
            duration_days=self._calculate_data_migration_duration(request, complexity),
            tasks=[
                "Plan data migration batches and order",
                "Perform initial data load",
                "Validate data integrity and completeness",
                "Handle incremental data sync if needed",
                "Resolve data quality issues"
            ],
            dependencies=[3],
            resource_requirements=[
                ResourceRequirement(
                    category="Compute",
                    requirement="High-performance migration server",
                    estimated_cost=500.0,
                    is_critical=True
                ),
                ResourceRequirement(
                    category="Storage",
                    requirement=f"Staging storage for {request.data_volume_gb}GB data",
                    estimated_cost=request.data_volume_gb * 0.1,
                    is_critical=True
                )
            ],
            risks=[
                RiskItem(
                    risk_type="data_loss",
                    level=RiskLevel.CRITICAL,
                    description="Risk of data loss during transfer",
                    mitigation="Implement checksums and validation at every step",
                    probability=0.1
                ),
                RiskItem(
                    risk_type="performance",
                    level=RiskLevel.MEDIUM,
                    description="Slow data transfer impacting timeline",
                    mitigation="Optimize batch sizes and use parallel transfers",
                    probability=0.4
                )
            ]
        ))
        
        # Phase 5: Testing and Validation
        phases.append(MigrationPhase(
            phase_number=5,
            name="Testing and Validation",
            description="Comprehensive testing of migrated database",
            duration_days=self._calculate_phase_duration(complexity, 5, 7, 10, 14),
            tasks=[
                "Execute functional tests",
                "Perform data validation and reconciliation",
                "Run performance benchmarks",
                "Test application integration",
                "Conduct user acceptance testing",
                "Validate backup and restore procedures"
            ],
            dependencies=[4],
            resource_requirements=[
                ResourceRequirement(
                    category="Personnel",
                    requirement="QA team and application developers",
                    is_critical=True
                ),
                ResourceRequirement(
                    category="Tools",
                    requirement="Testing and data validation tools",
                    estimated_cost=1000.0,
                    is_critical=False
                )
            ],
            risks=[
                RiskItem(
                    risk_type="insufficient_testing",
                    level=RiskLevel.HIGH,
                    description="Missing critical test scenarios",
                    mitigation="Create comprehensive test plan covering all use cases",
                    probability=0.3
                )
            ]
        ))
        
        # Phase 6: Cutover and Go-Live
        phases.append(MigrationPhase(
            phase_number=6,
            name="Cutover and Go-Live",
            description="Final cutover to production",
            duration_days=self._calculate_phase_duration(complexity, 1, 2, 3, 4),
            tasks=[
                "Execute final data sync",
                "Switch application connections to target database",
                "Monitor system performance and errors",
                "Execute rollback if critical issues arise",
                "Confirm successful cutover"
            ],
            dependencies=[5],
            resource_requirements=[
                ResourceRequirement(
                    category="Personnel",
                    requirement="Full team on-call for cutover window",
                    is_critical=True
                )
            ],
            risks=[
                RiskItem(
                    risk_type="downtime",
                    level=RiskLevel.CRITICAL,
                    description="Extended downtime during cutover",
                    mitigation="Practice cutover procedure and minimize sync window",
                    probability=0.2
                ),
                RiskItem(
                    risk_type="rollback",
                    level=RiskLevel.HIGH,
                    description="Need to rollback after cutover",
                    mitigation="Have tested rollback plan ready",
                    probability=0.15
                )
            ]
        ))
        
        # Phase 7: Post-Migration Support
        phases.append(MigrationPhase(
            phase_number=7,
            name="Post-Migration Support",
            description="Monitor and optimize after go-live",
            duration_days=self._calculate_phase_duration(complexity, 5, 7, 10, 14),
            tasks=[
                "Monitor performance and stability",
                "Optimize queries and indexes",
                "Resolve post-migration issues",
                "Fine-tune configuration",
                "Decommission old infrastructure"
            ],
            dependencies=[6],
            resource_requirements=[
                ResourceRequirement(
                    category="Personnel",
                    requirement="Support team for post-migration period",
                    is_critical=True
                )
            ],
            risks=[
                RiskItem(
                    risk_type="performance_degradation",
                    level=RiskLevel.MEDIUM,
                    description="Performance issues in production",
                    mitigation="Continuous monitoring and rapid response",
                    probability=0.3
                )
            ]
        ))
        
        return phases
    
    def _calculate_phase_duration(self, complexity: MigrationComplexity, simple: float, moderate: float, complex: float, very_complex: float) -> float:
        """Calculate phase duration based on complexity"""
        if complexity == MigrationComplexity.SIMPLE:
            return simple
        elif complexity == MigrationComplexity.MODERATE:
            return moderate
        elif complexity == MigrationComplexity.COMPLEX:
            return complex
        else:
            return very_complex
    
    def _calculate_data_migration_duration(self, request: TimelineRequest, complexity: MigrationComplexity) -> float:
        """Calculate data migration duration based on volume and complexity"""
        # Base duration from data volume (1 day per 100GB)
        base_days = max(1.0, request.data_volume_gb / 100.0)
        
        # Complexity multiplier
        complexity_multipliers = {
            MigrationComplexity.SIMPLE: 1.0,
            MigrationComplexity.MODERATE: 1.5,
            MigrationComplexity.COMPLEX: 2.0,
            MigrationComplexity.VERY_COMPLEX: 2.5
        }
        
        return round(base_days * complexity_multipliers[complexity], 1)
    
    def _aggregate_resources(self) -> List[ResourceRequirement]:
        """Aggregate all resource requirements across phases"""
        resources = []
        for phase in self.phases:
            resources.extend(phase.resource_requirements)
        return resources
    
    def _aggregate_risks(self) -> List[RiskItem]:
        """Aggregate all risks across phases"""
        risks = []
        for phase in self.phases:
            risks.extend(phase.risks)
        return risks
    
    def _generate_summary(self, complexity: MigrationComplexity) -> TimelineSummary:
        """Generate timeline summary"""
        total_duration = sum(phase.duration_days for phase in self.phases)
        
        # Count risks by level
        critical_risks = sum(1 for risk in self.all_risks if risk.level == RiskLevel.CRITICAL)
        high_risks = sum(1 for risk in self.all_risks if risk.level == RiskLevel.HIGH)
        
        # Determine overall risk
        if critical_risks > 2:
            overall_risk = RiskLevel.CRITICAL
        elif critical_risks > 0 or high_risks > 3:
            overall_risk = RiskLevel.HIGH
        elif high_risks > 0:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        # Recommend team size based on complexity
        team_size_map = {
            MigrationComplexity.SIMPLE: 3,
            MigrationComplexity.MODERATE: 5,
            MigrationComplexity.COMPLEX: 7,
            MigrationComplexity.VERY_COMPLEX: 10
        }
        
        return TimelineSummary(
            total_phases=len(self.phases),
            total_duration_days=round(total_duration, 1),
            total_duration_weeks=round(total_duration / 7, 1),
            complexity_level=complexity,
            overall_risk_level=overall_risk,
            critical_risks_count=critical_risks,
            high_risks_count=high_risks,
            recommended_team_size=team_size_map[complexity]
        )
    
    def _generate_recommendations(self, request: TimelineRequest, complexity: MigrationComplexity) -> List[str]:
        """Generate general recommendations"""
        recommendations = []
        
        recommendations.append("Conduct a proof-of-concept migration with representative data subset")
        recommendations.append("Establish clear communication channels and escalation paths")
        recommendations.append("Document all decisions and changes throughout the process")
        
        if request.data_volume_gb > 1000:
            recommendations.append("Consider incremental migration strategy to minimize downtime")
        
        if request.num_stored_procedures > 50:
            recommendations.append("Prioritize stored procedure testing as high complexity area")
        
        if request.has_replication:
            recommendations.append("Plan for replication reconfiguration in target environment")
        
        if complexity in [MigrationComplexity.COMPLEX, MigrationComplexity.VERY_COMPLEX]:
            recommendations.append("Engage vendor or expert consultants for complex scenarios")
            recommendations.append("Allow buffer time (20-30%) for unexpected issues")
        
        recommendations.append("Implement comprehensive monitoring from day one")
        recommendations.append("Schedule regular checkpoints and status reviews")
        
        return recommendations


def generate_timeline(request: TimelineRequest) -> Tuple[TimelineSummary, List[MigrationPhase], List[ResourceRequirement], List[RiskItem], List[str]]:
    """
    Convenience function to generate migration timeline
    
    Args:
        request: Timeline request parameters
        
    Returns:
        Tuple of (summary, phases, resources, risks, recommendations)
    """
    generator = TimelineGenerator()
    return generator.generate_timeline(request)
