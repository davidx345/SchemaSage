"""
Cloud Migration Assessment and Planning Module

Handles cloud readiness assessment, migration planning, and cost optimization.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MigrationComplexity(Enum):
    """Migration complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class MigrationStrategy(Enum):
    """Migration strategy types"""
    LIFT_AND_SHIFT = "lift_and_shift"
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    HYBRID = "hybrid"


@dataclass
class CloudReadinessScore:
    """Cloud readiness assessment score"""
    overall_score: float  # 0-100
    dimensions: Dict[str, float]
    blockers: List[str]
    recommendations: List[str]
    risk_level: str


@dataclass
class MigrationPlan:
    """Comprehensive migration plan"""
    migration_id: str
    source_system: Dict[str, Any]
    target_cloud: str
    strategy: MigrationStrategy
    complexity: MigrationComplexity
    estimated_duration: timedelta
    estimated_cost: float
    phases: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    rollback_plan: Dict[str, Any]
    success_criteria: List[str]


class CloudAssessmentEngine:
    """Engine for assessing cloud migration readiness"""
    
    def __init__(self):
        self.assessment_criteria = {
            'technical_compatibility': {
                'weight': 0.25,
                'factors': ['database_version', 'feature_compatibility', 'extensions_used', 'data_types']
            },
            'data_complexity': {
                'weight': 0.20,
                'factors': ['data_volume', 'schema_complexity', 'relationships', 'stored_procedures']
            },
            'performance_requirements': {
                'weight': 0.20,
                'factors': ['throughput', 'latency_sensitivity', 'concurrent_users', 'query_complexity']
            },
            'security_compliance': {
                'weight': 0.15,
                'factors': ['data_classification', 'compliance_requirements', 'encryption_needs', 'access_patterns']
            },
            'operational_readiness': {
                'weight': 0.10,
                'factors': ['team_skills', 'monitoring_setup', 'backup_strategy', 'disaster_recovery']
            },
            'business_impact': {
                'weight': 0.10,
                'factors': ['downtime_tolerance', 'critical_operations', 'integration_dependencies', 'user_impact']
            }
        }
    
    async def assess_cloud_readiness(self, source_schema: Dict[str, Any], requirements: Dict[str, Any]) -> CloudReadinessScore:
        """Perform comprehensive cloud readiness assessment"""
        try:
            dimension_scores = {}
            all_blockers = []
            all_recommendations = []
            
            # Assess each dimension
            for dimension, config in self.assessment_criteria.items():
                score, blockers, recommendations = await self._assess_dimension(
                    dimension, source_schema, requirements
                )
                dimension_scores[dimension] = score
                all_blockers.extend(blockers)
                all_recommendations.extend(recommendations)
            
            # Calculate weighted overall score
            overall_score = sum(
                score * config['weight'] 
                for (dimension, score), config in zip(dimension_scores.items(), self.assessment_criteria.values())
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_score, all_blockers)
            
            return CloudReadinessScore(
                overall_score=overall_score,
                dimensions=dimension_scores,
                blockers=all_blockers,
                recommendations=all_recommendations,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Cloud readiness assessment failed: {e}")
            return CloudReadinessScore(0.0, {}, [f"Assessment failed: {str(e)}"], [], "high")
    
    async def _assess_dimension(self, dimension: str, schema: Dict[str, Any], requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Assess a specific dimension"""
        score = 0.0
        blockers = []
        recommendations = []
        
        if dimension == 'technical_compatibility':
            score, blockers, recommendations = await self._assess_technical_compatibility(schema, requirements)
        elif dimension == 'data_complexity':
            score, blockers, recommendations = await self._assess_data_complexity(schema, requirements)
        elif dimension == 'performance_requirements':
            score, blockers, recommendations = await self._assess_performance_requirements(schema, requirements)
        elif dimension == 'security_compliance':
            score, blockers, recommendations = await self._assess_security_compliance(schema, requirements)
        elif dimension == 'operational_readiness':
            score, blockers, recommendations = await self._assess_operational_readiness(schema, requirements)
        elif dimension == 'business_impact':
            score, blockers, recommendations = await self._assess_business_impact(schema, requirements)
        
        return score, blockers, recommendations
    
    async def _assess_technical_compatibility(self, schema: Dict[str, Any], requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Assess technical compatibility for cloud migration"""
        score = 85.0  # Base score
        blockers = []
        recommendations = []
        
        # Check database version compatibility
        db_type = schema.get('database_type', '').lower()
        db_version = schema.get('database_version', '')
        
        if db_type == 'postgresql':
            if db_version and float(db_version.split('.')[0]) < 11:
                score -= 20
                recommendations.append("Consider upgrading PostgreSQL to version 11+ for better cloud compatibility")
        elif db_type == 'mysql':
            if db_version and float(db_version.split('.')[0]) < 8:
                score -= 15
                recommendations.append("Consider upgrading MySQL to version 8.0+ for cloud optimization")
        
        # Check for unsupported features
        unsupported_features = schema.get('unsupported_features', [])
        if unsupported_features:
            score -= len(unsupported_features) * 5
            blockers.extend([f"Unsupported feature: {feature}" for feature in unsupported_features])
        
        # Check extensions
        extensions = schema.get('extensions', [])
        cloud_incompatible_extensions = ['plpythonu', 'plperlu', 'file_fdw']
        for ext in extensions:
            if ext in cloud_incompatible_extensions:
                score -= 10
                blockers.append(f"Extension {ext} not available in managed cloud services")
        
        return max(0, score), blockers, recommendations
    
    async def _assess_data_complexity(self, schema: Dict[str, Any], requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Assess data complexity for migration"""
        score = 90.0
        blockers = []
        recommendations = []
        
        # Data volume assessment
        estimated_size_gb = schema.get('estimated_size_gb', 0)
        if estimated_size_gb > 1000:  # 1TB+
            score -= 15
            recommendations.append("Large dataset migration requires careful planning and potentially parallel transfer")
        elif estimated_size_gb > 100:  # 100GB+
            score -= 5
            recommendations.append("Consider migration during off-peak hours")
        
        # Schema complexity
        table_count = len(schema.get('tables', []))
        if table_count > 500:
            score -= 20
            recommendations.append("Complex schema with many tables - consider modular migration approach")
        elif table_count > 100:
            score -= 10
            recommendations.append("Moderate schema complexity - plan for extended migration window")
        
        # Relationships and constraints
        foreign_keys = sum(len(table.get('foreign_keys', [])) for table in schema.get('tables', []))
        if foreign_keys > 100:
            score -= 15
            recommendations.append("Many foreign key relationships - ensure referential integrity during migration")
        
        # Stored procedures and functions
        procedures = schema.get('stored_procedures', [])
        functions = schema.get('functions', [])
        if len(procedures) + len(functions) > 50:
            score -= 10
            recommendations.append("Many stored procedures/functions may require refactoring for cloud compatibility")
        
        return max(0, score), blockers, recommendations
    
    async def _assess_performance_requirements(self, schema: Dict[str, Any], requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Assess performance requirements"""
        score = 80.0
        blockers = []
        recommendations = []
        
        # Throughput requirements
        required_tps = requirements.get('transactions_per_second', 0)
        if required_tps > 10000:
            score -= 20
            recommendations.append("High throughput requirements - consider high-performance instance types")
        elif required_tps > 1000:
            score -= 10
            recommendations.append("Moderate throughput requirements - ensure adequate IOPS provisioning")
        
        # Latency requirements
        max_latency_ms = requirements.get('max_latency_ms', 1000)
        if max_latency_ms < 10:
            score -= 25
            blockers.append("Ultra-low latency requirements may not be achievable in cloud")
        elif max_latency_ms < 50:
            score -= 15
            recommendations.append("Low latency requirements - consider placement groups and dedicated instances")
        
        # Concurrent users
        concurrent_users = requirements.get('concurrent_users', 0)
        if concurrent_users > 1000:
            score -= 10
            recommendations.append("High concurrency - ensure connection pooling and read replicas")
        
        return max(0, score), blockers, recommendations
    
    async def _assess_security_compliance(self, schema: Dict[str, Any], requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Assess security and compliance requirements"""
        score = 85.0
        blockers = []
        recommendations = []
        
        # Compliance requirements
        compliance_needs = requirements.get('compliance', [])
        if 'PCI-DSS' in compliance_needs:
            recommendations.append("PCI-DSS compliance requires dedicated instances and additional security controls")
        if 'HIPAA' in compliance_needs:
            recommendations.append("HIPAA compliance requires encryption at rest and in transit")
        if 'SOX' in compliance_needs:
            recommendations.append("SOX compliance requires detailed audit logging and access controls")
        
        # Data classification
        sensitive_data = schema.get('sensitive_data_detected', [])
        if sensitive_data:
            recommendations.append("Sensitive data detected - ensure encryption and access controls are configured")
        
        # Encryption requirements
        encryption_required = requirements.get('encryption_required', False)
        if encryption_required:
            recommendations.append("Enable encryption at rest and in transit for all data")
        
        return score, blockers, recommendations
    
    async def _assess_operational_readiness(self, schema: Dict[str, Any], requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Assess operational readiness"""
        score = 70.0
        blockers = []
        recommendations = []
        
        # Team skills
        cloud_experience = requirements.get('team_cloud_experience', 'none')
        if cloud_experience == 'none':
            score -= 30
            recommendations.append("Team training on cloud database management recommended")
        elif cloud_experience == 'basic':
            score -= 15
            recommendations.append("Additional cloud database training would be beneficial")
        
        # Monitoring setup
        current_monitoring = requirements.get('current_monitoring', [])
        if not current_monitoring:
            score -= 20
            recommendations.append("Implement comprehensive monitoring and alerting")
        
        # Backup strategy
        backup_strategy = requirements.get('backup_strategy', 'none')
        if backup_strategy == 'none':
            score -= 25
            blockers.append("No backup strategy defined - critical for cloud migration")
        
        return max(0, score), blockers, recommendations
    
    async def _assess_business_impact(self, schema: Dict[str, Any], requirements: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
        """Assess business impact"""
        score = 75.0
        blockers = []
        recommendations = []
        
        # Downtime tolerance
        max_downtime_hours = requirements.get('max_downtime_hours', 24)
        if max_downtime_hours < 1:
            score -= 25
            recommendations.append("Near-zero downtime requirement - consider blue/green deployment")
        elif max_downtime_hours < 4:
            score -= 15
            recommendations.append("Low downtime tolerance - plan for minimal downtime migration")
        
        # Critical operations
        is_critical = requirements.get('is_critical_system', False)
        if is_critical:
            score -= 10
            recommendations.append("Critical system - ensure comprehensive testing and rollback plan")
        
        # Integration dependencies
        integration_count = len(requirements.get('integrations', []))
        if integration_count > 10:
            score -= 15
            recommendations.append("Many integrations - coordinate migration with dependent systems")
        
        return max(0, score), blockers, recommendations
    
    def _determine_risk_level(self, overall_score: float, blockers: List[str]) -> str:
        """Determine risk level based on score and blockers"""
        if blockers:
            return "high"
        elif overall_score >= 80:
            return "low"
        elif overall_score >= 60:
            return "medium"
        else:
            return "high"


class CloudMigrationPlanner:
    """Plans cloud migration strategies and generates execution plans"""
    
    def __init__(self):
        self.strategy_templates = {
            MigrationStrategy.LIFT_AND_SHIFT: {
                'description': 'Move existing database to cloud with minimal changes',
                'complexity': MigrationComplexity.SIMPLE,
                'duration_multiplier': 1.0,
                'cost_multiplier': 1.0,
                'risk_level': 'low'
            },
            MigrationStrategy.REPLATFORM: {
                'description': 'Migrate to cloud-native database service with optimization',
                'complexity': MigrationComplexity.MODERATE,
                'duration_multiplier': 1.5,
                'cost_multiplier': 1.2,
                'risk_level': 'medium'
            },
            MigrationStrategy.REFACTOR: {
                'description': 'Redesign for cloud-native architecture',
                'complexity': MigrationComplexity.COMPLEX,
                'duration_multiplier': 3.0,
                'cost_multiplier': 2.0,
                'risk_level': 'high'
            },
            MigrationStrategy.HYBRID: {
                'description': 'Gradual migration with hybrid cloud approach',
                'complexity': MigrationComplexity.COMPLEX,
                'duration_multiplier': 2.5,
                'cost_multiplier': 1.8,
                'risk_level': 'medium'
            }
        }
    
    async def create_migration_plan(
        self, 
        readiness_score: CloudReadinessScore,
        source_schema: Dict[str, Any],
        target_cloud: str,
        requirements: Dict[str, Any]
    ) -> MigrationPlan:
        """Create comprehensive migration plan"""
        try:
            # Determine optimal strategy
            strategy = await self._select_migration_strategy(readiness_score, requirements)
            
            # Calculate complexity
            complexity = await self._determine_complexity(source_schema, strategy, requirements)
            
            # Estimate duration and cost
            duration = await self._estimate_duration(source_schema, strategy, complexity)
            cost = await self._estimate_migration_cost(source_schema, strategy, target_cloud)
            
            # Generate migration phases
            phases = await self._generate_migration_phases(source_schema, strategy, requirements)
            
            # Identify risks
            risks = await self._identify_migration_risks(readiness_score, strategy, requirements)
            
            # Create rollback plan
            rollback_plan = await self._create_rollback_plan(source_schema, strategy)
            
            # Define success criteria
            success_criteria = await self._define_success_criteria(requirements)
            
            migration_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return MigrationPlan(
                migration_id=migration_id,
                source_system=source_schema,
                target_cloud=target_cloud,
                strategy=strategy,
                complexity=complexity,
                estimated_duration=duration,
                estimated_cost=cost,
                phases=phases,
                risks=risks,
                rollback_plan=rollback_plan,
                success_criteria=success_criteria
            )
            
        except Exception as e:
            logger.error(f"Migration planning failed: {e}")
            raise
    
    async def _select_migration_strategy(self, readiness_score: CloudReadinessScore, requirements: Dict[str, Any]) -> MigrationStrategy:
        """Select optimal migration strategy"""
        # Simple heuristics - can be enhanced with ML
        if readiness_score.risk_level == "high" or readiness_score.overall_score < 50:
            return MigrationStrategy.LIFT_AND_SHIFT
        
        modernization_required = requirements.get('modernization_required', False)
        if modernization_required:
            return MigrationStrategy.REFACTOR
        
        cloud_native_features = requirements.get('use_cloud_native_features', False)
        if cloud_native_features:
            return MigrationStrategy.REPLATFORM
        
        # Default to replatform for good balance
        return MigrationStrategy.REPLATFORM
    
    async def _determine_complexity(self, schema: Dict[str, Any], strategy: MigrationStrategy, requirements: Dict[str, Any]) -> MigrationComplexity:
        """Determine migration complexity"""
        base_complexity = self.strategy_templates[strategy]['complexity']
        
        # Adjust based on schema characteristics
        table_count = len(schema.get('tables', []))
        data_size_gb = schema.get('estimated_size_gb', 0)
        
        complexity_score = 0
        if table_count > 100:
            complexity_score += 1
        if data_size_gb > 500:
            complexity_score += 1
        if len(schema.get('stored_procedures', [])) > 20:
            complexity_score += 1
        if requirements.get('zero_downtime', False):
            complexity_score += 1
        
        if complexity_score >= 3:
            return MigrationComplexity.VERY_COMPLEX
        elif complexity_score >= 2:
            return MigrationComplexity.COMPLEX
        elif complexity_score >= 1:
            return MigrationComplexity.MODERATE
        else:
            return MigrationComplexity.SIMPLE
    
    async def _estimate_duration(self, schema: Dict[str, Any], strategy: MigrationStrategy, complexity: MigrationComplexity) -> timedelta:
        """Estimate migration duration"""
        base_days = {
            MigrationComplexity.SIMPLE: 3,
            MigrationComplexity.MODERATE: 7,
            MigrationComplexity.COMPLEX: 14,
            MigrationComplexity.VERY_COMPLEX: 30
        }
        
        duration_days = base_days[complexity]
        duration_days *= self.strategy_templates[strategy]['duration_multiplier']
        
        # Adjust for data size
        data_size_gb = schema.get('estimated_size_gb', 0)
        if data_size_gb > 1000:  # 1TB+
            duration_days *= 1.5
        elif data_size_gb > 100:  # 100GB+
            duration_days *= 1.2
        
        return timedelta(days=int(duration_days))
    
    async def _estimate_migration_cost(self, schema: Dict[str, Any], strategy: MigrationStrategy, target_cloud: str) -> float:
        """Estimate migration project cost"""
        base_cost = {
            MigrationComplexity.SIMPLE: 5000,
            MigrationComplexity.MODERATE: 15000,
            MigrationComplexity.COMPLEX: 35000,
            MigrationComplexity.VERY_COMPLEX: 75000
        }
        
        # This is a simplified calculation - real implementation would be more sophisticated
        table_count = len(schema.get('tables', []))
        cost = base_cost.get(MigrationComplexity.MODERATE, 15000)  # Default
        
        cost *= self.strategy_templates[strategy]['cost_multiplier']
        
        # Adjust for schema size
        if table_count > 200:
            cost *= 1.5
        elif table_count > 50:
            cost *= 1.2
        
        return cost
    
    async def _generate_migration_phases(self, schema: Dict[str, Any], strategy: MigrationStrategy, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate migration execution phases"""
        base_phases = [
            {
                'phase': 1,
                'name': 'Pre-migration Assessment',
                'description': 'Final assessment and preparation',
                'duration_days': 2,
                'tasks': [
                    'Validate source system connectivity',
                    'Verify target cloud environment setup',
                    'Confirm backup and rollback procedures',
                    'Run final compatibility checks'
                ]
            },
            {
                'phase': 2,
                'name': 'Schema Migration',
                'description': 'Migrate database schema to target',
                'duration_days': 1,
                'tasks': [
                    'Create target database instance',
                    'Migrate schema structure',
                    'Create indexes and constraints',
                    'Validate schema consistency'
                ]
            },
            {
                'phase': 3,
                'name': 'Data Migration',
                'description': 'Transfer data to target system',
                'duration_days': 3,
                'tasks': [
                    'Initial data load',
                    'Incremental data sync',
                    'Data validation and verification',
                    'Performance testing'
                ]
            },
            {
                'phase': 4,
                'name': 'Application Cutover',
                'description': 'Switch applications to new database',
                'duration_days': 1,
                'tasks': [
                    'Update application configurations',
                    'Perform final data sync',
                    'Switch traffic to new database',
                    'Monitor system stability'
                ]
            },
            {
                'phase': 5,
                'name': 'Post-migration Optimization',
                'description': 'Optimize and finalize migration',
                'duration_days': 2,
                'tasks': [
                    'Performance tuning',
                    'Security configuration',
                    'Monitoring setup',
                    'Documentation and training'
                ]
            }
        ]
        
        # Adjust phases based on strategy
        if strategy == MigrationStrategy.REFACTOR:
            base_phases.insert(2, {
                'phase': 2.5,
                'name': 'Application Refactoring',
                'description': 'Modify applications for cloud-native features',
                'duration_days': 5,
                'tasks': [
                    'Refactor application code',
                    'Implement cloud-native patterns',
                    'Update database access patterns',
                    'Test refactored applications'
                ]
            })
        
        return base_phases
    
    async def _identify_migration_risks(self, readiness_score: CloudReadinessScore, strategy: MigrationStrategy, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify migration risks"""
        risks = []
        
        # Add risks based on readiness score
        for blocker in readiness_score.blockers:
            risks.append({
                'type': 'compatibility',
                'severity': 'high',
                'description': blocker,
                'mitigation': 'Address compatibility issue before migration'
            })
        
        # Add strategy-specific risks
        if strategy == MigrationStrategy.REFACTOR:
            risks.append({
                'type': 'complexity',
                'severity': 'medium',
                'description': 'Application refactoring may introduce bugs',
                'mitigation': 'Extensive testing and gradual rollout'
            })
        
        # Add data-related risks
        data_size = requirements.get('estimated_size_gb', 0)
        if data_size > 1000:
            risks.append({
                'type': 'data_transfer',
                'severity': 'medium',
                'description': 'Large data transfer may take longer than expected',
                'mitigation': 'Use parallel transfer and incremental sync'
            })
        
        return risks
    
    async def _create_rollback_plan(self, schema: Dict[str, Any], strategy: MigrationStrategy) -> Dict[str, Any]:
        """Create rollback plan"""
        return {
            'triggers': [
                'Performance degradation > 50%',
                'Data integrity issues detected',
                'Critical application failures',
                'Unacceptable downtime duration'
            ],
            'steps': [
                'Stop application traffic to new database',
                'Activate backup database connection',
                'Verify data consistency',
                'Resume normal operations',
                'Investigate and document issues'
            ],
            'estimated_rollback_time': '2 hours',
            'data_recovery_time': '4 hours',
            'backup_retention': '30 days'
        }
    
    async def _define_success_criteria(self, requirements: Dict[str, Any]) -> List[str]:
        """Define success criteria for migration"""
        criteria = [
            'All data successfully migrated with 100% integrity',
            'Application connectivity restored within SLA',
            'Performance meets or exceeds baseline metrics',
            'All critical business functions operational',
            'Security and compliance requirements satisfied'
        ]
        
        # Add specific criteria based on requirements
        if requirements.get('performance_improvement_target'):
            criteria.append(f"Performance improvement of {requirements['performance_improvement_target']}% achieved")
        
        if requirements.get('cost_reduction_target'):
            criteria.append(f"Cost reduction of {requirements['cost_reduction_target']}% achieved")
        
        return criteria


# Global instances
assessment_engine = CloudAssessmentEngine()
migration_planner = CloudMigrationPlanner()
