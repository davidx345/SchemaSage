"""
Migration rollback planner service.
Creates detailed rollback plans for migration operations.
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from models.rollback_models import (
    RollbackComplexity, RollbackRisk, DataRecoveryMethod, RollbackPhase,
    MigrationState, RollbackStep, DataRecoveryPlan, RollbackValidation,
    RollbackRiskAssessment, RollbackPrerequisite, RollbackResourceRequirement,
    RollbackTimeline, RollbackSummary
)


class RollbackPlanner:
    """
    Service for creating migration rollback plans.
    Generates comprehensive rollback strategies with risk assessment.
    """
    
    def __init__(self):
        """Initialize the rollback planner"""
        pass
        
    def generate_rollback_plan(
        self,
        migration_id: str,
        migration_state: MigrationState,
        source_db_type: str,
        target_db_type: str,
        include_data_recovery: bool = True,
        max_downtime_minutes: Optional[int] = None,
        preserve_target_changes: bool = False
    ) -> Tuple[RollbackSummary, RollbackRiskAssessment, List[RollbackPrerequisite],
               List[RollbackStep], List[RollbackTimeline], Optional[DataRecoveryPlan],
               List[RollbackValidation], RollbackResourceRequirement, List[str], List[str], List[str]]:
        """
        Generate comprehensive rollback plan for migration.
        
        Args:
            migration_id: Migration identifier
            migration_state: Current migration state
            source_db_type: Source database type
            target_db_type: Target database type
            include_data_recovery: Include data recovery steps
            max_downtime_minutes: Maximum acceptable downtime
            preserve_target_changes: Preserve changes made in target
            
        Returns:
            Tuple of rollback plan components
        """
        # Assess complexity and risk
        complexity = self._assess_complexity(migration_state)
        risk_assessment = self._assess_risks(migration_state, preserve_target_changes)
        
        # Generate prerequisites
        prerequisites = self._generate_prerequisites(migration_state)
        
        # Generate rollback steps
        steps = self._generate_rollback_steps(
            migration_state, complexity, preserve_target_changes
        )
        
        # Generate timeline
        timeline = self._generate_timeline(steps)
        
        # Generate data recovery plan
        data_recovery = None
        if include_data_recovery and migration_state.has_backup:
            data_recovery = self._generate_data_recovery_plan(migration_state)
            
        # Generate validation checks
        validations = self._generate_validations(migration_state)
        
        # Calculate resource requirements
        resources = self._calculate_resources(migration_state, steps)
        
        # Generate summary
        total_duration = sum(step.estimated_duration_minutes for step in steps)
        downtime = self._estimate_downtime(steps)
        
        can_rollback = self._can_rollback(risk_assessment, max_downtime_minutes, downtime)
        
        summary = RollbackSummary(
            migration_id=migration_id,
            plan_created_at=datetime.now(),
            complexity=complexity,
            estimated_total_duration_minutes=total_duration,
            estimated_downtime_minutes=downtime,
            total_steps=len(steps),
            critical_steps=sum(1 for s in steps if s.risk_level in [RollbackRisk.HIGH, RollbackRisk.CRITICAL]),
            can_rollback=can_rollback,
            recommendation=self._generate_rollback_recommendation(
                can_rollback, complexity, downtime
            )
        )
        
        # Generate warnings, recommendations, and emergency contacts
        warnings = self._generate_warnings(risk_assessment, steps, downtime)
        recommendations = self._generate_recommendations(complexity, risk_assessment)
        emergency_contacts = self._generate_emergency_contacts()
        
        return (summary, risk_assessment, prerequisites, steps, timeline,
                data_recovery, validations, resources, warnings, recommendations,
                emergency_contacts)
                
    def _assess_complexity(self, state: MigrationState) -> RollbackComplexity:
        """Assess rollback complexity"""
        # Calculate complexity score
        score = 0
        
        # Data volume factor
        if state.data_migrated_gb > 1000:
            score += 3
        elif state.data_migrated_gb > 100:
            score += 2
        elif state.data_migrated_gb > 10:
            score += 1
            
        # Table count factor
        if len(state.tables_migrated) > 50:
            score += 2
        elif len(state.tables_migrated) > 20:
            score += 1
            
        # Schema changes factor
        if len(state.schema_changes_applied) > 20:
            score += 2
        elif len(state.schema_changes_applied) > 10:
            score += 1
            
        # Backup availability
        if not state.has_backup:
            score += 3
            
        # Map score to complexity
        if score >= 8:
            return RollbackComplexity.VERY_COMPLEX
        elif score >= 5:
            return RollbackComplexity.COMPLEX
        elif score >= 3:
            return RollbackComplexity.MODERATE
        else:
            return RollbackComplexity.SIMPLE
            
    def _assess_risks(
        self,
        state: MigrationState,
        preserve_target_changes: bool
    ) -> RollbackRiskAssessment:
        """Assess rollback risks"""
        risk_factors = []
        mitigation_strategies = []
        irreversible_changes = []
        
        # Data loss risk
        if not state.has_backup:
            data_loss_risk = RollbackRisk.CRITICAL
            risk_factors.append("No backup available - data loss risk is critical")
            mitigation_strategies.append("Create immediate backup before proceeding")
        elif state.backup_timestamp and (datetime.now() - state.backup_timestamp).days > 1:
            data_loss_risk = RollbackRisk.MEDIUM
            risk_factors.append("Backup is over 24 hours old")
            mitigation_strategies.append("Create fresh backup to minimize data loss")
        else:
            data_loss_risk = RollbackRisk.LOW
            
        # Downtime risk
        if state.data_migrated_gb > 500:
            downtime_risk = RollbackRisk.HIGH
            risk_factors.append("Large data volume increases rollback time")
            mitigation_strategies.append("Plan rollback during maintenance window")
        else:
            downtime_risk = RollbackRisk.MEDIUM
            
        # Complexity risk
        if len(state.schema_changes_applied) > 20:
            complexity_risk = RollbackRisk.HIGH
            risk_factors.append("Many schema changes complicate rollback")
        else:
            complexity_risk = RollbackRisk.MEDIUM
            
        # Check for irreversible changes
        if "DROP" in str(state.schema_changes_applied):
            irreversible_changes.append("Tables dropped - data cannot be recovered without backup")
            
        # Overall risk
        risk_scores = {
            RollbackRisk.LOW: 1,
            RollbackRisk.MEDIUM: 2,
            RollbackRisk.HIGH: 3,
            RollbackRisk.CRITICAL: 4
        }
        avg_risk_score = (
            risk_scores[data_loss_risk] +
            risk_scores[downtime_risk] +
            risk_scores[complexity_risk]
        ) / 3
        
        if avg_risk_score >= 3.5:
            overall_risk = RollbackRisk.CRITICAL
        elif avg_risk_score >= 2.5:
            overall_risk = RollbackRisk.HIGH
        elif avg_risk_score >= 1.5:
            overall_risk = RollbackRisk.MEDIUM
        else:
            overall_risk = RollbackRisk.LOW
            
        return RollbackRiskAssessment(
            overall_risk=overall_risk,
            data_loss_risk=data_loss_risk,
            downtime_risk=downtime_risk,
            complexity_risk=complexity_risk,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            irreversible_changes=irreversible_changes
        )
        
    def _generate_prerequisites(self, state: MigrationState) -> List[RollbackPrerequisite]:
        """Generate rollback prerequisites"""
        prerequisites = []
        
        # Backup verification
        prerequisites.append(RollbackPrerequisite(
            requirement="Valid backup available",
            description=f"Verify backup from {state.backup_timestamp} is accessible and complete",
            critical=True,
            validation_command="pg_restore --list backup_file.dump | head -20"
        ))
        
        # Maintenance window
        prerequisites.append(RollbackPrerequisite(
            requirement="Maintenance window scheduled",
            description="Ensure sufficient downtime window for rollback operation",
            critical=True
        ))
        
        # Access credentials
        prerequisites.append(RollbackPrerequisite(
            requirement="Database administrator access",
            description="Superuser credentials for both source and target databases",
            critical=True
        ))
        
        # Communication plan
        prerequisites.append(RollbackPrerequisite(
            requirement="Stakeholder notification",
            description="Notify all stakeholders of planned rollback",
            critical=True
        ))
        
        return prerequisites
        
    def _generate_rollback_steps(
        self,
        state: MigrationState,
        complexity: RollbackComplexity,
        preserve_target: bool
    ) -> List[RollbackStep]:
        """Generate ordered rollback steps"""
        steps = []
        step_num = 1
        
        # Phase 1: Preparation
        steps.append(RollbackStep(
            step_number=step_num,
            phase=RollbackPhase.PREPARATION,
            action="Create pre-rollback backup",
            description="Take snapshot of current state before starting rollback",
            estimated_duration_minutes=15,
            risk_level=RollbackRisk.LOW,
            reversible=True,
            validation_query="SELECT pg_database_size(current_database())"
        ))
        step_num += 1
        
        # Phase 2: Traffic redirect
        steps.append(RollbackStep(
            step_number=step_num,
            phase=RollbackPhase.TRAFFIC_REDIRECT,
            action="Stop application traffic",
            description="Stop all application connections to target database",
            estimated_duration_minutes=5,
            risk_level=RollbackRisk.MEDIUM,
            reversible=True
        ))
        step_num += 1
        
        # Phase 3: Data validation
        steps.append(RollbackStep(
            step_number=step_num,
            phase=RollbackPhase.DATA_VALIDATION,
            action="Validate source database",
            description="Verify source database is still available and accessible",
            sql_commands=["SELECT COUNT(*) FROM pg_database WHERE datname = 'source_db'"],
            estimated_duration_minutes=5,
            risk_level=RollbackRisk.LOW,
            reversible=True,
            validation_query="SELECT version()",
            dependencies=[1, 2]
        ))
        step_num += 1
        
        # Phase 4: Schema rollback
        for change in state.schema_changes_applied[:5]:  # Limit to first 5 for brevity
            steps.append(RollbackStep(
                step_number=step_num,
                phase=RollbackPhase.SCHEMA_ROLLBACK,
                action=f"Revert schema change: {change}",
                description=f"Reverse schema modification: {change}",
                sql_commands=[f"-- Reverse: {change}"],
                estimated_duration_minutes=2,
                risk_level=RollbackRisk.MEDIUM,
                reversible=False,
                dependencies=[3]
            ))
            step_num += 1
            
        # Phase 5: Data rollback
        if state.has_backup:
            steps.append(RollbackStep(
                step_number=step_num,
                phase=RollbackPhase.DATA_ROLLBACK,
                action="Restore data from backup",
                description=f"Restore {state.data_migrated_gb}GB of data from backup",
                estimated_duration_minutes=int(state.data_migrated_gb * 2),  # 2 min per GB
                risk_level=RollbackRisk.HIGH,
                reversible=False,
                warning="This operation cannot be undone once started"
            ))
            step_num += 1
            
        # Phase 6: Verification
        steps.append(RollbackStep(
            step_number=step_num,
            phase=RollbackPhase.VERIFICATION,
            action="Verify data integrity",
            description="Run integrity checks on restored data",
            estimated_duration_minutes=10,
            risk_level=RollbackRisk.LOW,
            reversible=True,
            validation_query="SELECT COUNT(*) FROM information_schema.tables"
        ))
        step_num += 1
        
        # Phase 7: Cleanup
        steps.append(RollbackStep(
            step_number=step_num,
            phase=RollbackPhase.CLEANUP,
            action="Clean up migration artifacts",
            description="Remove temporary tables and migration tracking data",
            estimated_duration_minutes=5,
            risk_level=RollbackRisk.LOW,
            reversible=True
        ))
        step_num += 1
        
        # Phase 8: Completion
        steps.append(RollbackStep(
            step_number=step_num,
            phase=RollbackPhase.COMPLETION,
            action="Resume application traffic",
            description="Redirect application to source database and resume operations",
            estimated_duration_minutes=5,
            risk_level=RollbackRisk.MEDIUM,
            reversible=True
        ))
        
        return steps
        
    def _generate_timeline(self, steps: List[RollbackStep]) -> List[RollbackTimeline]:
        """Generate rollback timeline"""
        timeline = []
        current_offset = 0
        
        phases = {}
        for step in steps:
            if step.phase not in phases:
                phases[step.phase] = []
            phases[step.phase].append(step)
            
        for phase in RollbackPhase:
            if phase in phases:
                phase_steps = phases[phase]
                duration = sum(s.estimated_duration_minutes for s in phase_steps)
                critical_path = any(s.risk_level in [RollbackRisk.HIGH, RollbackRisk.CRITICAL] 
                                   for s in phase_steps)
                
                timeline.append(RollbackTimeline(
                    phase=phase,
                    start_offset_minutes=current_offset,
                    duration_minutes=duration,
                    critical_path=critical_path,
                    description=f"{len(phase_steps)} steps in {phase.value} phase"
                ))
                
                current_offset += duration
                
        return timeline
        
    def _generate_data_recovery_plan(self, state: MigrationState) -> DataRecoveryPlan:
        """Generate data recovery plan"""
        return DataRecoveryPlan(
            method=DataRecoveryMethod.BACKUP_RESTORE,
            source=f"Backup from {state.backup_timestamp}",
            estimated_duration_minutes=int(state.data_migrated_gb * 2),
            data_to_recover_gb=state.data_migrated_gb,
            recovery_steps=[
                "Stop all connections to target database",
                "Verify backup file integrity",
                "Restore database schema from backup",
                "Restore data from backup in parallel streams",
                "Rebuild indexes and constraints",
                "Verify data integrity with checksums"
            ],
            validation_checks=[
                "Compare row counts between backup and restored database",
                "Verify foreign key constraints",
                "Check for orphaned records"
            ],
            risk_factors=[
                "Backup may be incomplete if taken during active migration",
                "Large data volume increases restoration time"
            ]
        )
        
    def _generate_validations(self, state: MigrationState) -> List[RollbackValidation]:
        """Generate validation checks"""
        validations = []
        
        for table in state.tables_migrated[:5]:  # First 5 tables
            validations.append(RollbackValidation(
                check_name=f"Verify {table} row count",
                query=f"SELECT COUNT(*) FROM {table}",
                expected_result="Matches pre-migration count",
                critical=True,
                description=f"Ensure all rows in {table} are restored"
            ))
            
        return validations
        
    def _calculate_resources(
        self,
        state: MigrationState,
        steps: List[RollbackStep]
    ) -> RollbackResourceRequirement:
        """Calculate required resources"""
        return RollbackResourceRequirement(
            storage_required_gb=state.data_migrated_gb * 1.5,  # 1.5x for temp space
            memory_required_gb=min(64.0, state.data_migrated_gb * 0.1),
            cpu_cores=8,
            network_bandwidth_mbps=1000.0,
            personnel_required=2,
            specialist_skills=["Database Administrator", "Migration Engineer"]
        )
        
    def _estimate_downtime(self, steps: List[RollbackStep]) -> int:
        """Estimate total downtime"""
        # Downtime = traffic redirect through completion
        downtime_steps = [s for s in steps if s.phase in [
            RollbackPhase.TRAFFIC_REDIRECT,
            RollbackPhase.DATA_VALIDATION,
            RollbackPhase.SCHEMA_ROLLBACK,
            RollbackPhase.DATA_ROLLBACK,
            RollbackPhase.VERIFICATION,
            RollbackPhase.COMPLETION
        ]]
        return sum(s.estimated_duration_minutes for s in downtime_steps)
        
    def _can_rollback(
        self,
        risk_assessment: RollbackRiskAssessment,
        max_downtime: Optional[int],
        estimated_downtime: int
    ) -> bool:
        """Determine if rollback is feasible"""
        # Cannot rollback if risk is critical
        if risk_assessment.overall_risk == RollbackRisk.CRITICAL:
            return False
            
        # Cannot rollback if exceeds max downtime
        if max_downtime and estimated_downtime > max_downtime:
            return False
            
        # Can rollback otherwise
        return True
        
    def _generate_rollback_recommendation(
        self,
        can_rollback: bool,
        complexity: RollbackComplexity,
        downtime: int
    ) -> str:
        """Generate rollback recommendation"""
        if not can_rollback:
            return "Rollback not recommended due to high risk or downtime constraints"
        elif complexity == RollbackComplexity.SIMPLE:
            return f"Rollback is straightforward. Estimated downtime: {downtime} minutes"
        elif complexity == RollbackComplexity.MODERATE:
            return f"Rollback is moderately complex. Plan for {downtime} minutes downtime"
        else:
            return f"Rollback is complex. Requires careful planning. Downtime: {downtime} minutes"
            
    def _generate_warnings(
        self,
        risk_assessment: RollbackRiskAssessment,
        steps: List[RollbackStep],
        downtime: int
    ) -> List[str]:
        """Generate warnings"""
        warnings = []
        
        if risk_assessment.overall_risk in [RollbackRisk.HIGH, RollbackRisk.CRITICAL]:
            warnings.append(f"⚠️ Overall rollback risk is {risk_assessment.overall_risk.value}")
            
        irreversible_steps = [s for s in steps if not s.reversible]
        if irreversible_steps:
            warnings.append(f"⚠️ {len(irreversible_steps)} steps cannot be reversed once executed")
            
        if downtime > 120:
            warnings.append(f"⚠️ Estimated downtime of {downtime} minutes may impact business")
            
        return warnings
        
    def _generate_recommendations(
        self,
        complexity: RollbackComplexity,
        risk_assessment: RollbackRiskAssessment
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        recommendations.append("Test rollback procedure in staging environment first")
        recommendations.append("Have database expert on standby during rollback")
        
        if complexity in [RollbackComplexity.COMPLEX, RollbackComplexity.VERY_COMPLEX]:
            recommendations.append("Break rollback into smaller phases if possible")
            
        if risk_assessment.data_loss_risk in [RollbackRisk.HIGH, RollbackRisk.CRITICAL]:
            recommendations.append("Create additional backup before starting rollback")
            
        return recommendations
        
    def _generate_emergency_contacts(self) -> List[str]:
        """Generate emergency contact information"""
        return [
            "Database Team Lead: db-team@example.com",
            "Migration Engineer: migration-team@example.com",
            "24/7 Support: +1-555-0100"
        ]


def generate_rollback_plan(
    migration_id: str,
    migration_state: MigrationState,
    source_db_type: str,
    target_db_type: str,
    include_data_recovery: bool = True,
    max_downtime_minutes: Optional[int] = None,
    preserve_target_changes: bool = False
) -> Tuple:
    """Generate rollback plan for migration"""
    planner = RollbackPlanner()
    return planner.generate_rollback_plan(
        migration_id, migration_state, source_db_type, target_db_type,
        include_data_recovery, max_downtime_minutes, preserve_target_changes
    )
