"""
Schema diff visualization service.
Compares schemas and generates detailed difference reports with migration actions.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime

from models.diff_models import (
    DiffType, ChangeType, ImpactLevel, VisualizationFormat,
    SchemaDefinition, ColumnDiff, TableDiff, IndexDiff, ConstraintDiff,
    ViewDiff, MigrationAction, DiffStatistics, DiffSummary
)


class SchemaDiffVisualizer:
    """
    Service for comparing schemas and visualizing differences.
    Generates detailed diff reports and migration action plans.
    """
    
    def __init__(self):
        """Initialize the schema diff visualizer"""
        pass
        
    def compare_schemas(
        self,
        source_schema: SchemaDefinition,
        target_schema: SchemaDefinition,
        output_format: VisualizationFormat = VisualizationFormat.JSON,
        show_unchanged: bool = False,
        detail_level: int = 2,
        compare_data_types: bool = True,
        compare_constraints: bool = True,
        compare_indexes: bool = True
    ) -> Tuple[DiffSummary, DiffStatistics, List[TableDiff], List[IndexDiff],
               List[ConstraintDiff], List[ViewDiff], List[MigrationAction],
               Dict[str, Any], List[str], List[str]]:
        """
        Compare two schemas and generate detailed difference report.
        
        Args:
            source_schema: Source schema definition
            target_schema: Target schema definition
            output_format: Desired output format
            show_unchanged: Include unchanged elements
            detail_level: Level of detail (1-3)
            compare_data_types: Compare data type differences
            compare_constraints: Compare constraint differences
            compare_indexes: Compare index differences
            
        Returns:
            Tuple of diff components
        """
        # Compare tables
        table_diffs = self._compare_tables(
            source_schema.tables,
            target_schema.tables,
            show_unchanged,
            compare_data_types
        )
        
        # Compare indexes
        index_diffs = []
        if compare_indexes and source_schema.indexes and target_schema.indexes:
            index_diffs = self._compare_indexes(
                source_schema.indexes,
                target_schema.indexes
            )
            
        # Compare constraints
        constraint_diffs = []
        if compare_constraints and source_schema.constraints and target_schema.constraints:
            constraint_diffs = self._compare_constraints(
                source_schema.constraints,
                target_schema.constraints
            )
            
        # Compare views
        view_diffs = []
        if source_schema.views and target_schema.views:
            view_diffs = self._compare_views(
                source_schema.views,
                target_schema.views
            )
            
        # Generate statistics
        statistics = self._generate_statistics(
            source_schema, target_schema, table_diffs,
            index_diffs, constraint_diffs, view_diffs
        )
        
        # Generate migration actions
        migration_actions = self._generate_migration_actions(
            table_diffs, index_diffs, constraint_diffs, view_diffs
        )
        
        # Calculate compatibility
        summary = self._generate_summary(statistics, migration_actions)
        
        # Generate visualization data
        visualization_data = self._generate_visualization_data(
            output_format, table_diffs, index_diffs, constraint_diffs, view_diffs
        )
        
        # Generate warnings and recommendations
        warnings = self._generate_warnings(statistics, migration_actions)
        recommendations = self._generate_recommendations(
            statistics, migration_actions, summary.compatibility_score
        )
        
        return (summary, statistics, table_diffs, index_diffs, constraint_diffs,
                view_diffs, migration_actions, visualization_data, warnings, recommendations)
                
    def _compare_tables(
        self,
        source_tables: Dict[str, Dict[str, Any]],
        target_tables: Dict[str, Dict[str, Any]],
        show_unchanged: bool,
        compare_data_types: bool
    ) -> List[TableDiff]:
        """Compare tables between source and target"""
        table_diffs = []
        
        source_table_names = set(source_tables.keys())
        target_table_names = set(target_tables.keys())
        
        # Tables only in source (removed)
        for table_name in source_table_names - target_table_names:
            table_diffs.append(TableDiff(
                table_name=table_name,
                diff_type=DiffType.REMOVED,
                column_diffs=[],
                impact_level=ImpactLevel.HIGH,
                migration_complexity="High - table needs to be dropped or archived"
            ))
            
        # Tables only in target (added)
        for table_name in target_table_names - source_table_names:
            table_diffs.append(TableDiff(
                table_name=table_name,
                diff_type=DiffType.ADDED,
                column_diffs=[],
                impact_level=ImpactLevel.MEDIUM,
                migration_complexity="Medium - new table needs to be created"
            ))
            
        # Tables in both (check for modifications)
        for table_name in source_table_names & target_table_names:
            column_diffs = self._compare_columns(
                source_tables[table_name].get("columns", {}),
                target_tables[table_name].get("columns", {}),
                compare_data_types
            )
            
            if column_diffs or show_unchanged:
                diff_type = DiffType.MODIFIED if column_diffs else DiffType.UNCHANGED
                impact = self._calculate_table_impact(column_diffs)
                complexity = self._assess_migration_complexity(column_diffs)
                
                table_diffs.append(TableDiff(
                    table_name=table_name,
                    diff_type=diff_type,
                    column_diffs=column_diffs,
                    impact_level=impact,
                    migration_complexity=complexity
                ))
                
        return table_diffs
        
    def _compare_columns(
        self,
        source_columns: Dict[str, Any],
        target_columns: Dict[str, Any],
        compare_data_types: bool
    ) -> List[ColumnDiff]:
        """Compare columns between source and target tables"""
        column_diffs = []
        
        source_col_names = set(source_columns.keys())
        target_col_names = set(target_columns.keys())
        
        # Columns removed
        for col_name in source_col_names - target_col_names:
            column_diffs.append(ColumnDiff(
                column_name=col_name,
                diff_type=DiffType.REMOVED,
                source_definition=source_columns[col_name],
                changes=["Column removed from target schema"]
            ))
            
        # Columns added
        for col_name in target_col_names - source_col_names:
            column_diffs.append(ColumnDiff(
                column_name=col_name,
                diff_type=DiffType.ADDED,
                target_definition=target_columns[col_name],
                changes=["New column added in target schema"]
            ))
            
        # Columns in both
        if compare_data_types:
            for col_name in source_col_names & target_col_names:
                source_def = source_columns[col_name]
                target_def = target_columns[col_name]
                changes = self._detect_column_changes(source_def, target_def)
                
                if changes:
                    column_diffs.append(ColumnDiff(
                        column_name=col_name,
                        diff_type=DiffType.MODIFIED,
                        source_definition=source_def,
                        target_definition=target_def,
                        changes=changes
                    ))
                    
        return column_diffs
        
    def _detect_column_changes(self, source_def: Any, target_def: Any) -> List[str]:
        """Detect specific changes in column definition"""
        changes = []
        
        if isinstance(source_def, dict) and isinstance(target_def, dict):
            # Compare data types
            if source_def.get("type") != target_def.get("type"):
                changes.append(
                    f"Data type changed: {source_def.get('type')} → {target_def.get('type')}"
                )
                
            # Compare nullable
            if source_def.get("nullable") != target_def.get("nullable"):
                changes.append(
                    f"Nullable changed: {source_def.get('nullable')} → {target_def.get('nullable')}"
                )
                
            # Compare default values
            if source_def.get("default") != target_def.get("default"):
                changes.append(
                    f"Default value changed: {source_def.get('default')} → {target_def.get('default')}"
                )
                
        return changes
        
    def _compare_indexes(
        self,
        source_indexes: Dict[str, List[str]],
        target_indexes: Dict[str, List[str]]
    ) -> List[IndexDiff]:
        """Compare indexes between schemas"""
        index_diffs = []
        
        source_idx_names = set(source_indexes.keys())
        target_idx_names = set(target_indexes.keys())
        
        # Indexes removed
        for idx_name in source_idx_names - target_idx_names:
            index_diffs.append(IndexDiff(
                index_name=idx_name,
                table_name="unknown",
                diff_type=DiffType.REMOVED,
                source_columns=source_indexes[idx_name],
                impact_level=ImpactLevel.MEDIUM
            ))
            
        # Indexes added
        for idx_name in target_idx_names - source_idx_names:
            index_diffs.append(IndexDiff(
                index_name=idx_name,
                table_name="unknown",
                diff_type=DiffType.ADDED,
                target_columns=target_indexes[idx_name],
                impact_level=ImpactLevel.LOW
            ))
            
        return index_diffs
        
    def _compare_constraints(
        self,
        source_constraints: Dict[str, List[Dict[str, Any]]],
        target_constraints: Dict[str, List[Dict[str, Any]]]
    ) -> List[ConstraintDiff]:
        """Compare constraints between schemas"""
        constraint_diffs = []
        
        # Simplified comparison - in production would be more detailed
        source_tables = set(source_constraints.keys())
        target_tables = set(target_constraints.keys())
        
        for table in source_tables | target_tables:
            source_cons = source_constraints.get(table, [])
            target_cons = target_constraints.get(table, [])
            
            if len(source_cons) != len(target_cons):
                constraint_diffs.append(ConstraintDiff(
                    constraint_name=f"{table}_constraints",
                    constraint_type="MIXED",
                    table_name=table,
                    diff_type=DiffType.MODIFIED,
                    source_definition=f"{len(source_cons)} constraints",
                    target_definition=f"{len(target_cons)} constraints",
                    impact_level=ImpactLevel.MEDIUM
                ))
                
        return constraint_diffs
        
    def _compare_views(
        self,
        source_views: Dict[str, str],
        target_views: Dict[str, str]
    ) -> List[ViewDiff]:
        """Compare views between schemas"""
        view_diffs = []
        
        source_view_names = set(source_views.keys())
        target_view_names = set(target_views.keys())
        
        # Views removed
        for view_name in source_view_names - target_view_names:
            view_diffs.append(ViewDiff(
                view_name=view_name,
                diff_type=DiffType.REMOVED,
                source_sql=source_views[view_name],
                impact_level=ImpactLevel.MEDIUM
            ))
            
        # Views added
        for view_name in target_view_names - source_view_names:
            view_diffs.append(ViewDiff(
                view_name=view_name,
                diff_type=DiffType.ADDED,
                target_sql=target_views[view_name],
                impact_level=ImpactLevel.LOW
            ))
            
        return view_diffs
        
    def _calculate_table_impact(self, column_diffs: List[ColumnDiff]) -> ImpactLevel:
        """Calculate impact level based on column changes"""
        if not column_diffs:
            return ImpactLevel.NONE
            
        has_removed = any(cd.diff_type == DiffType.REMOVED for cd in column_diffs)
        has_modified = any(cd.diff_type == DiffType.MODIFIED for cd in column_diffs)
        
        if has_removed:
            return ImpactLevel.HIGH
        elif has_modified:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
            
    def _assess_migration_complexity(self, column_diffs: List[ColumnDiff]) -> str:
        """Assess migration complexity based on changes"""
        if not column_diffs:
            return "Low - no structural changes required"
            
        removed_count = sum(1 for cd in column_diffs if cd.diff_type == DiffType.REMOVED)
        modified_count = sum(1 for cd in column_diffs if cd.diff_type == DiffType.MODIFIED)
        
        if removed_count > 0:
            return f"High - {removed_count} columns removed, data migration required"
        elif modified_count > 3:
            return f"Medium-High - {modified_count} columns modified"
        elif modified_count > 0:
            return f"Medium - {modified_count} columns modified"
        else:
            return "Low - only new columns added"
            
    def _generate_statistics(
        self,
        source_schema: SchemaDefinition,
        target_schema: SchemaDefinition,
        table_diffs: List[TableDiff],
        index_diffs: List[IndexDiff],
        constraint_diffs: List[ConstraintDiff],
        view_diffs: List[ViewDiff]
    ) -> DiffStatistics:
        """Generate statistical summary"""
        total_tables = len(source_schema.tables) + len(target_schema.tables)
        tables_added = sum(1 for td in table_diffs if td.diff_type == DiffType.ADDED)
        tables_removed = sum(1 for td in table_diffs if td.diff_type == DiffType.REMOVED)
        tables_modified = sum(1 for td in table_diffs if td.diff_type == DiffType.MODIFIED)
        
        # Count total columns
        total_columns = sum(len(t.get("columns", {})) for t in source_schema.tables.values())
        total_columns += sum(len(t.get("columns", {})) for t in target_schema.tables.values())
        
        columns_added = sum(
            sum(1 for cd in td.column_diffs if cd.diff_type == DiffType.ADDED)
            for td in table_diffs
        )
        columns_removed = sum(
            sum(1 for cd in td.column_diffs if cd.diff_type == DiffType.REMOVED)
            for td in table_diffs
        )
        columns_modified = sum(
            sum(1 for cd in td.column_diffs if cd.diff_type == DiffType.MODIFIED)
            for td in table_diffs
        )
        
        return DiffStatistics(
            total_tables=total_tables,
            tables_added=tables_added,
            tables_removed=tables_removed,
            tables_modified=tables_modified,
            total_columns=total_columns,
            columns_added=columns_added,
            columns_removed=columns_removed,
            columns_modified=columns_modified,
            indexes_changed=len(index_diffs),
            constraints_changed=len(constraint_diffs),
            views_changed=len(view_diffs)
        )
        
    def _generate_migration_actions(
        self,
        table_diffs: List[TableDiff],
        index_diffs: List[IndexDiff],
        constraint_diffs: List[ConstraintDiff],
        view_diffs: List[ViewDiff]
    ) -> List[MigrationAction]:
        """Generate ordered migration actions"""
        actions = []
        order = 1
        
        # Drop views first
        for vd in view_diffs:
            if vd.diff_type == DiffType.REMOVED:
                actions.append(MigrationAction(
                    action_type="DROP",
                    change_type=ChangeType.VIEW,
                    object_name=vd.view_name,
                    sql_statement=f"DROP VIEW IF EXISTS {vd.view_name};",
                    order=order,
                    reversible=True,
                    risk_level=ImpactLevel.LOW
                ))
                order += 1
                
        # Alter/create tables
        for td in table_diffs:
            if td.diff_type == DiffType.ADDED:
                actions.append(MigrationAction(
                    action_type="CREATE",
                    change_type=ChangeType.TABLE,
                    object_name=td.table_name,
                    sql_statement=f"CREATE TABLE {td.table_name} (...);",
                    order=order,
                    reversible=True,
                    risk_level=ImpactLevel.MEDIUM
                ))
                order += 1
                
        return actions
        
    def _generate_summary(
        self,
        statistics: DiffStatistics,
        migration_actions: List[MigrationAction]
    ) -> DiffSummary:
        """Generate diff summary"""
        # Calculate compatibility score
        total_changes = (statistics.tables_added + statistics.tables_removed +
                        statistics.tables_modified + statistics.columns_added +
                        statistics.columns_removed + statistics.columns_modified)
        
        compatibility_score = max(0, 100 - (total_changes * 2))
        
        critical_diffs = sum(
            1 for action in migration_actions
            if action.risk_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
        )
        
        # Estimate migration hours
        migration_hours = len(migration_actions) * 0.5 + total_changes * 0.1
        
        return DiffSummary(
            comparison_timestamp=datetime.now().isoformat(),
            schemas_compatible=compatibility_score > 60,
            compatibility_score=round(compatibility_score, 2),
            critical_differences=critical_diffs,
            migration_estimated_hours=round(migration_hours, 1)
        )
        
    def _generate_visualization_data(
        self,
        output_format: VisualizationFormat,
        table_diffs: List[TableDiff],
        index_diffs: List[IndexDiff],
        constraint_diffs: List[ConstraintDiff],
        view_diffs: List[ViewDiff]
    ) -> Dict[str, Any]:
        """Generate format-specific visualization data"""
        if output_format == VisualizationFormat.GRAPHICAL:
            return {
                "nodes": [{"id": td.table_name, "type": "table"} for td in table_diffs],
                "edges": [],
                "layout": "hierarchical"
            }
        else:
            return {}
            
    def _generate_warnings(
        self,
        statistics: DiffStatistics,
        migration_actions: List[MigrationAction]
    ) -> List[str]:
        """Generate warnings"""
        warnings = []
        
        if statistics.tables_removed > 0:
            warnings.append(
                f"{statistics.tables_removed} tables will be removed - ensure data is backed up"
            )
            
        if statistics.columns_removed > 10:
            warnings.append(
                f"{statistics.columns_removed} columns will be removed - potential data loss"
            )
            
        return warnings
        
    def _generate_recommendations(
        self,
        statistics: DiffStatistics,
        migration_actions: List[MigrationAction],
        compatibility_score: float
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        if compatibility_score < 70:
            recommendations.append(
                "Schemas have significant differences. Consider phased migration approach"
            )
            
        if len(migration_actions) > 50:
            recommendations.append(
                "Large number of migration actions. Use automated migration tools"
            )
            
        recommendations.append("Test migration in staging environment before production")
        
        return recommendations


def compare_schemas(
    source_schema: SchemaDefinition,
    target_schema: SchemaDefinition,
    output_format: VisualizationFormat = VisualizationFormat.JSON,
    show_unchanged: bool = False,
    detail_level: int = 2,
    compare_data_types: bool = True,
    compare_constraints: bool = True,
    compare_indexes: bool = True
) -> Tuple[DiffSummary, DiffStatistics, List[TableDiff], List[IndexDiff],
           List[ConstraintDiff], List[ViewDiff], List[MigrationAction],
           Dict[str, Any], List[str], List[str]]:
    """Compare two schemas and generate diff report"""
    visualizer = SchemaDiffVisualizer()
    return visualizer.compare_schemas(
        source_schema, target_schema, output_format, show_unchanged,
        detail_level, compare_data_types, compare_constraints, compare_indexes
    )
