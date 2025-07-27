"""
Impact analysis for schema changes
"""

import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from models.schemas import SchemaResponse, TableInfo, ColumnInfo

from .models import (
    SchemaChange, ImpactAnalysis, ChangeType, ChangeSeverity,
    ComparisonResult
)

logger = logging.getLogger(__name__)


class ImpactAnalyzer:
    """
    Analyzes the impact of schema changes on applications and operations
    """
    
    def __init__(self, application_metadata: Dict[str, Any] = None):
        """
        Initialize impact analyzer
        
        Args:
            application_metadata: Metadata about applications using the schema
        """
        self.application_metadata = application_metadata or {}
        self.query_patterns = self._load_query_patterns()
        self.dependency_map = self._load_dependency_map()
    
    def analyze_changes(
        self, 
        changes: List[SchemaChange],
        schema_before: SchemaResponse = None,
        schema_after: SchemaResponse = None
    ) -> Dict[str, ImpactAnalysis]:
        """
        Analyze impact of schema changes
        
        Args:
            changes: List of schema changes
            schema_before: Schema before changes
            schema_after: Schema after changes
            
        Returns:
            Impact analysis for each affected object
        """
        impact_analyses = {}
        
        # Group changes by affected object
        changes_by_object = self._group_changes_by_object(changes)
        
        for object_name, object_changes in changes_by_object.items():
            analysis = self._analyze_object_impact(
                object_name, object_changes, schema_before, schema_after
            )
            impact_analyses[object_name] = analysis
        
        return impact_analyses
    
    def _group_changes_by_object(
        self, 
        changes: List[SchemaChange]
    ) -> Dict[str, List[SchemaChange]]:
        """Group changes by affected database object"""
        
        grouped = {}
        for change in changes:
            key = change.table_name or change.object_name
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(change)
        
        return grouped
    
    def _analyze_object_impact(
        self,
        object_name: str,
        changes: List[SchemaChange],
        schema_before: SchemaResponse = None,
        schema_after: SchemaResponse = None
    ) -> ImpactAnalysis:
        """Analyze impact for a specific database object"""
        
        analysis = ImpactAnalysis()
        
        # Analyze each change
        for change in changes:
            self._analyze_single_change(change, analysis)
        
        # Analyze query impact
        analysis.affected_queries = self._find_affected_queries(object_name, changes)
        
        # Analyze breaking changes
        analysis.breaking_changes = self._identify_breaking_changes(changes)
        
        # Determine if migration is required
        analysis.migration_required = self._requires_migration(changes)
        
        # Estimate downtime
        analysis.estimated_downtime = self._estimate_downtime(changes)
        
        # Assess rollback difficulty
        analysis.rollback_difficulty = self._assess_rollback_difficulty(changes)
        
        # Find dependencies
        analysis.dependencies = self._find_dependencies(object_name)
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(changes, analysis)
        
        return analysis
    
    def _analyze_single_change(self, change: SchemaChange, analysis: ImpactAnalysis):
        """Analyze impact of a single change"""
        
        change_type = change.change_type
        
        if change_type == ChangeType.TABLE_REMOVED:
            analysis.breaking_changes.append(
                f"Table '{change.table_name}' removed - all dependent queries will fail"
            )
            analysis.migration_required = True
            
        elif change_type == ChangeType.COLUMN_REMOVED:
            analysis.breaking_changes.append(
                f"Column '{change.column_name}' removed from '{change.table_name}'"
            )
            analysis.migration_required = True
            
        elif change_type == ChangeType.COLUMN_MODIFIED:
            self._analyze_column_modification(change, analysis)
            
        elif change_type == ChangeType.PRIMARY_KEY_REMOVED:
            analysis.breaking_changes.append(
                f"Primary key removed from '{change.table_name}'"
            )
            analysis.migration_required = True
            
        elif change_type == ChangeType.FOREIGN_KEY_REMOVED:
            analysis.breaking_changes.append(
                f"Foreign key constraint removed: {change.object_name}"
            )
    
    def _analyze_column_modification(self, change: SchemaChange, analysis: ImpactAnalysis):
        """Analyze column modification impact"""
        
        details = change.details
        old_value = change.old_value
        new_value = change.new_value
        
        if isinstance(details, dict) and 'property' in details:
            property_name = details['property']
            
            if property_name == 'type':
                if not self._are_types_compatible(old_value, new_value):
                    analysis.breaking_changes.append(
                        f"Incompatible type change in '{change.table_name}.{change.column_name}': {old_value} -> {new_value}"
                    )
                    analysis.migration_required = True
            
            elif property_name == 'nullable':
                if old_value and not new_value:  # Making non-nullable
                    analysis.breaking_changes.append(
                        f"Column '{change.table_name}.{change.column_name}' made non-nullable"
                    )
                    analysis.migration_required = True
    
    def _find_affected_queries(self, object_name: str, changes: List[SchemaChange]) -> List[str]:
        """Find queries affected by changes"""
        
        affected_queries = []
        
        # This would typically analyze stored procedures, views, application queries, etc.
        # For now, provide example patterns
        
        for change in changes:
            if change.change_type == ChangeType.TABLE_REMOVED:
                affected_queries.extend([
                    f"SELECT * FROM {change.table_name}",
                    f"INSERT INTO {change.table_name}",
                    f"UPDATE {change.table_name}",
                    f"DELETE FROM {change.table_name}"
                ])
            
            elif change.change_type == ChangeType.COLUMN_REMOVED:
                affected_queries.extend([
                    f"SELECT {change.column_name} FROM {change.table_name}",
                    f"INSERT INTO {change.table_name} ({change.column_name})",
                    f"UPDATE {change.table_name} SET {change.column_name}",
                    f"WHERE {change.column_name}"
                ])
        
        return affected_queries
    
    def _identify_breaking_changes(self, changes: List[SchemaChange]) -> List[str]:
        """Identify breaking changes"""
        
        breaking_changes = []
        breaking_change_types = {
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.PRIMARY_KEY_REMOVED,
            ChangeType.FOREIGN_KEY_REMOVED
        }
        
        for change in changes:
            if change.change_type in breaking_change_types:
                breaking_changes.append(
                    f"{change.change_type.value}: {change.object_name}"
                )
        
        return breaking_changes
    
    def _requires_migration(self, changes: List[SchemaChange]) -> bool:
        """Determine if changes require data migration"""
        
        migration_required_types = {
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.COLUMN_MODIFIED,
            ChangeType.PRIMARY_KEY_REMOVED,
            ChangeType.PRIMARY_KEY_ADDED
        }
        
        return any(change.change_type in migration_required_types for change in changes)
    
    def _estimate_downtime(self, changes: List[SchemaChange]) -> Optional[str]:
        """Estimate downtime required for changes"""
        
        # Simple heuristic based on change types and complexity
        high_impact_changes = sum(1 for change in changes if change.severity in [ChangeSeverity.HIGH, ChangeSeverity.CRITICAL])
        total_changes = len(changes)
        
        if high_impact_changes == 0:
            return "< 5 minutes"
        elif high_impact_changes <= 2:
            return "5-15 minutes"
        elif high_impact_changes <= 5:
            return "15-30 minutes"
        else:
            return "30+ minutes"
    
    def _assess_rollback_difficulty(self, changes: List[SchemaChange]) -> str:
        """Assess difficulty of rolling back changes"""
        
        # Check for irreversible changes
        irreversible_types = {
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.CONSTRAINT_REMOVED
        }
        
        data_loss_types = {
            ChangeType.COLUMN_MODIFIED  # Type changes may cause data loss
        }
        
        if any(change.change_type in irreversible_types for change in changes):
            return "high"
        elif any(change.change_type in data_loss_types for change in changes):
            return "medium"
        else:
            return "low"
    
    def _find_dependencies(self, object_name: str) -> List[str]:
        """Find dependencies for the given object"""
        
        dependencies = []
        
        # Check dependency map
        if object_name in self.dependency_map:
            dependencies.extend(self.dependency_map[object_name])
        
        # Add common dependencies based on object type
        if '.' not in object_name:  # Table name
            dependencies.extend([
                f"Views referencing {object_name}",
                f"Stored procedures using {object_name}",
                f"Foreign key constraints to {object_name}",
                f"Application models for {object_name}"
            ])
        
        return dependencies
    
    def _generate_recommendations(
        self, 
        changes: List[SchemaChange], 
        analysis: ImpactAnalysis
    ) -> List[str]:
        """Generate recommendations for handling changes"""
        
        recommendations = []
        
        if analysis.breaking_changes:
            recommendations.append("Review all breaking changes before deployment")
            recommendations.append("Update application code to handle schema changes")
            recommendations.append("Create database migration scripts")
        
        if analysis.migration_required:
            recommendations.append("Plan data migration strategy")
            recommendations.append("Test migration on copy of production data")
            recommendations.append("Prepare rollback procedures")
        
        if analysis.rollback_difficulty == "high":
            recommendations.append("Create full database backup before changes")
            recommendations.append("Consider blue-green deployment strategy")
        
        # Add specific recommendations based on change types
        critical_changes = [c for c in changes if c.severity == ChangeSeverity.CRITICAL]
        if critical_changes:
            recommendations.append("Schedule changes during maintenance window")
            recommendations.append("Notify all stakeholders before deployment")
        
        return recommendations
    
    def _are_types_compatible(self, old_type: str, new_type: str) -> bool:
        """Check if type change is compatible"""
        
        # Define compatible type conversions
        compatible_conversions = {
            ('INTEGER', 'BIGINT'),
            ('INTEGER', 'DECIMAL'),
            ('VARCHAR', 'TEXT'),
            ('CHAR', 'VARCHAR'),
            ('DATE', 'DATETIME'),
            ('TIME', 'DATETIME')
        }
        
        return (old_type, new_type) in compatible_conversions
    
    def _load_query_patterns(self) -> List[Dict[str, Any]]:
        """Load common query patterns for impact analysis"""
        
        # This would typically load from configuration or analyze actual queries
        return [
            {
                'pattern': 'SELECT * FROM {table}',
                'impact': 'high',
                'description': 'Select all columns'
            },
            {
                'pattern': 'INSERT INTO {table}',
                'impact': 'high',
                'description': 'Insert statements'
            },
            {
                'pattern': 'UPDATE {table} SET {column}',
                'impact': 'medium',
                'description': 'Update statements'
            }
        ]
    
    def _load_dependency_map(self) -> Dict[str, List[str]]:
        """Load dependency mapping"""
        
        # This would typically be loaded from configuration or discovered automatically
        return {}
    
    def generate_impact_report(
        self, 
        changes: List[SchemaChange],
        impact_analyses: Dict[str, ImpactAnalysis]
    ) -> Dict[str, Any]:
        """Generate comprehensive impact report"""
        
        # Overall statistics
        total_changes = len(changes)
        breaking_changes_count = sum(len(analysis.breaking_changes) for analysis in impact_analyses.values())
        migration_required_count = sum(1 for analysis in impact_analyses.values() if analysis.migration_required)
        
        # Severity breakdown
        severity_breakdown = {}
        for severity in ChangeSeverity:
            severity_breakdown[severity.value] = sum(1 for change in changes if change.severity == severity)
        
        # Risk assessment
        risk_level = self._assess_overall_risk(changes, impact_analyses)
        
        # Recommendations
        overall_recommendations = self._generate_overall_recommendations(changes, impact_analyses)
        
        return {
            'summary': {
                'total_changes': total_changes,
                'breaking_changes': breaking_changes_count,
                'migration_required': migration_required_count,
                'severity_breakdown': severity_breakdown,
                'risk_level': risk_level
            },
            'impact_analyses': {
                object_name: analysis.to_dict() 
                for object_name, analysis in impact_analyses.items()
            },
            'recommendations': overall_recommendations,
            'generated_at': datetime.now().isoformat()
        }
    
    def _assess_overall_risk(
        self, 
        changes: List[SchemaChange],
        impact_analyses: Dict[str, ImpactAnalysis]
    ) -> str:
        """Assess overall risk level"""
        
        critical_count = sum(1 for change in changes if change.severity == ChangeSeverity.CRITICAL)
        high_count = sum(1 for change in changes if change.severity == ChangeSeverity.HIGH)
        breaking_changes = sum(len(analysis.breaking_changes) for analysis in impact_analyses.values())
        
        if critical_count > 0 or breaking_changes > 3:
            return "critical"
        elif high_count > 2 or breaking_changes > 0:
            return "high"
        elif high_count > 0:
            return "medium"
        else:
            return "low"
    
    def _generate_overall_recommendations(
        self,
        changes: List[SchemaChange],
        impact_analyses: Dict[str, ImpactAnalysis]
    ) -> List[str]:
        """Generate overall recommendations"""
        
        recommendations = set()
        
        # Collect all recommendations from individual analyses
        for analysis in impact_analyses.values():
            recommendations.update(analysis.recommendations)
        
        # Add overall recommendations
        if any(analysis.migration_required for analysis in impact_analyses.values()):
            recommendations.add("Coordinate all migrations as a single deployment")
            recommendations.add("Test complete migration process in staging environment")
        
        risk_level = self._assess_overall_risk(changes, impact_analyses)
        if risk_level in ['high', 'critical']:
            recommendations.add("Conduct thorough impact assessment before deployment")
            recommendations.add("Have rollback plan ready")
            recommendations.add("Consider phased deployment approach")
        
        return sorted(list(recommendations))
