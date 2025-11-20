"""
Index recommendation engine.
Analyzes workloads and recommends optimal indexes.
"""
from typing import List, Dict, Tuple
from collections import defaultdict

from models.index_models import (
    IndexType, WorkloadPattern, IndexImpact,
    ColumnUsage, TableWorkload, IndexRecommendation, CoveringIndexRecommendation,
    RedundantIndex, MissingIndexPattern, IndexMaintenanceRecommendation,
    WorkloadAnalysis, IndexStatistics
)


class IndexRecommendationEngine:
    """
    Engine for analyzing workloads and recommending indexes.
    """
    
    def __init__(self):
        """Initialize the index recommendation engine"""
        pass
        
    def recommend_indexes(
        self,
        database_engine: str,
        table_workloads: List[TableWorkload],
        existing_indexes: List[Dict],
        workload_patterns: List[WorkloadPattern],
        min_improvement_threshold: float = 10.0,
        max_recommendations: int = 10,
        optimization_goal: str = "balanced"
    ) -> Tuple[List[IndexRecommendation], List[CoveringIndexRecommendation],
               List[RedundantIndex], List[MissingIndexPattern],
               List[IndexMaintenanceRecommendation], WorkloadAnalysis,
               IndexStatistics, List[str]]:
        """
        Analyze workload and generate index recommendations.
        """
        # Analyze workload patterns
        workload_analysis = self._analyze_workload(table_workloads, workload_patterns)
        
        # Generate index recommendations
        recommendations = self._generate_recommendations(
            database_engine, table_workloads, existing_indexes,
            optimization_goal, min_improvement_threshold
        )
        
        # Limit recommendations
        recommendations = recommendations[:max_recommendations]
        
        # Identify covering index opportunities
        covering_indexes = self._identify_covering_indexes(
            table_workloads, recommendations, database_engine
        )
        
        # Detect redundant indexes
        redundant = self._detect_redundant_indexes(existing_indexes, recommendations)
        
        # Find missing index patterns
        missing_patterns = self._find_missing_patterns(table_workloads, existing_indexes)
        
        # Generate maintenance recommendations
        maintenance = self._generate_maintenance_recommendations(existing_indexes)
        
        # Calculate statistics
        statistics = self._calculate_statistics(
            recommendations, redundant, existing_indexes, table_workloads
        )
        
        # Generate warnings
        warnings = self._generate_warnings(recommendations, redundant, workload_analysis)
        
        return (recommendations, covering_indexes, redundant, missing_patterns,
                maintenance, workload_analysis, statistics, warnings)
                
    def _analyze_workload(
        self,
        table_workloads: List[TableWorkload],
        patterns: List[WorkloadPattern]
    ) -> WorkloadAnalysis:
        """Analyze workload characteristics"""
        total_queries = sum(tw.queries_per_second for tw in table_workloads)
        
        # Categorize queries
        read_heavy = WorkloadPattern.READ_HEAVY in patterns
        write_heavy = WorkloadPattern.WRITE_HEAVY in patterns
        analytical = WorkloadPattern.ANALYTICAL in patterns
        
        # Calculate column usage
        all_columns = {}
        for tw in table_workloads:
            for col_name, usage in tw.column_usage.items():
                if col_name not in all_columns:
                    all_columns[col_name] = usage
                else:
                    # Merge usage statistics
                    all_columns[col_name].in_where_clause_count += usage.in_where_clause_count
                    all_columns[col_name].in_join_count += usage.in_join_count
                    all_columns[col_name].in_order_by_count += usage.in_order_by_count
                    all_columns[col_name].in_group_by_count += usage.in_group_by_count
                    
        # Find most accessed columns
        most_accessed = sorted(
            all_columns.items(),
            key=lambda x: (x[1].in_where_clause_count + x[1].in_join_count),
            reverse=True
        )[:5]
        
        # Identify index candidates
        candidates = []
        for col_name, usage in most_accessed:
            if usage.in_where_clause_count > 0 or usage.in_join_count > 0:
                candidates.append(col_name)
                
        return WorkloadAnalysis(
            total_queries_per_second=round(total_queries, 2),
            read_write_ratio=3.0 if read_heavy else (0.5 if write_heavy else 1.5),
            most_accessed_columns=[col for col, _ in most_accessed],
            index_candidates=candidates,
            workload_patterns=patterns
        )
        
    def _generate_recommendations(
        self,
        engine: str,
        table_workloads: List[TableWorkload],
        existing: List[Dict],
        goal: str,
        min_improvement: float
    ) -> List[IndexRecommendation]:
        """Generate index recommendations"""
        recommendations = []
        existing_indexes_set = {(idx.get('table'), tuple(idx.get('columns', [])))
                               for idx in existing}
        
        for workload in table_workloads:
            # Get high-usage columns
            sorted_cols = sorted(
                workload.column_usage.items(),
                key=lambda x: x[1].in_where_clause_count + x[1].in_join_count * 2,
                reverse=True
            )
            
            # Recommend indexes for top columns
            for col_name, usage in sorted_cols[:3]:
                # Skip if index exists
                if (workload.table_name, (col_name,)) in existing_indexes_set:
                    continue
                    
                # Calculate expected improvement
                total_usage = (usage.in_where_clause_count + usage.in_join_count * 2 +
                              usage.in_order_by_count + usage.in_group_by_count)
                              
                if total_usage == 0:
                    continue
                    
                # Estimate improvement based on selectivity
                read_improvement = min(90, usage.selectivity * 0.8)
                write_overhead = 5.0 if goal == "read_performance" else 10.0
                
                # Determine impact
                if read_improvement > 50:
                    impact = IndexImpact.HIGH
                elif read_improvement > 25:
                    impact = IndexImpact.MEDIUM
                else:
                    impact = IndexImpact.LOW
                    
                if read_improvement < min_improvement:
                    continue
                    
                # Determine index type
                index_type = self._determine_index_type(engine, usage)
                
                # Estimate size
                estimated_size = workload.estimated_row_count * 0.01  # 10KB per 1000 rows
                
                recommendations.append(IndexRecommendation(
                    table_name=workload.table_name,
                    columns=[col_name],
                    index_type=index_type,
                    rationale=f"Column used in {total_usage} query operations",
                    estimated_size_mb=round(estimated_size, 2),
                    estimated_read_improvement_percent=round(read_improvement, 1),
                    estimated_write_overhead_percent=round(write_overhead, 1),
                    impact=impact,
                    creation_sql=f"CREATE INDEX idx_{workload.table_name}_{col_name} ON {workload.table_name}({col_name});"
                ))
                
        return recommendations
        
    def _determine_index_type(self, engine: str, usage: ColumnUsage) -> IndexType:
        """Determine optimal index type"""
        # Simple heuristic based on usage patterns
        if usage.in_where_clause_count > usage.in_join_count:
            if "postgres" in engine.lower():
                return IndexType.BTREE
            elif "mysql" in engine.lower():
                return IndexType.BTREE
            else:
                return IndexType.BTREE
        else:
            return IndexType.BTREE
            
    def _identify_covering_indexes(
        self,
        workloads: List[TableWorkload],
        recommendations: List[IndexRecommendation],
        engine: str
    ) -> List[CoveringIndexRecommendation]:
        """Identify covering index opportunities"""
        covering = []
        
        for workload in workloads:
            # Find columns frequently accessed together
            high_usage_cols = [
                col for col, usage in workload.column_usage.items()
                if (usage.in_where_clause_count + usage.in_join_count) > 5
            ]
            
            if len(high_usage_cols) >= 2:
                key_cols = high_usage_cols[:2]
                included_cols = high_usage_cols[2:4] if len(high_usage_cols) > 2 else []
                
                estimated_improvement = 30.0 + len(included_cols) * 10
                
                covering.append(CoveringIndexRecommendation(
                    table_name=workload.table_name,
                    key_columns=key_cols,
                    included_columns=included_cols,
                    queries_covered=workload.queries_per_second * 0.3,
                    estimated_improvement_percent=round(estimated_improvement, 1),
                    creation_sql=self._generate_covering_index_sql(
                        workload.table_name, key_cols, included_cols, engine
                    )
                ))
                
        return covering
        
    def _generate_covering_index_sql(
        self,
        table: str,
        key_cols: List[str],
        included: List[str],
        engine: str
    ) -> str:
        """Generate covering index SQL"""
        idx_name = f"idx_{table}_covering"
        key_part = ", ".join(key_cols)
        
        if "sqlserver" in engine.lower() and included:
            include_part = ", ".join(included)
            return f"CREATE INDEX {idx_name} ON {table}({key_part}) INCLUDE ({include_part});"
        else:
            all_cols = key_cols + included
            return f"CREATE INDEX {idx_name} ON {table}({', '.join(all_cols)});"
            
    def _detect_redundant_indexes(
        self,
        existing: List[Dict],
        recommendations: List[IndexRecommendation]
    ) -> List[RedundantIndex]:
        """Detect redundant indexes"""
        redundant = []
        
        for i, idx1 in enumerate(existing):
            cols1 = set(idx1.get('columns', []))
            
            for idx2 in existing[i+1:]:
                cols2 = set(idx2.get('columns', []))
                
                # Check if one is subset of another
                if cols1.issubset(cols2) or cols2.issubset(cols1):
                    space_saved = idx1.get('size_mb', 10)
                    
                    redundant.append(RedundantIndex(
                        index_name=idx1.get('name', 'unknown'),
                        table_name=idx1.get('table', 'unknown'),
                        columns=list(cols1),
                        overlaps_with=idx2.get('name', 'unknown'),
                        space_saved_mb=round(space_saved, 2),
                        recommendation="Consider dropping this index"
                    ))
                    break
                    
        return redundant
        
    def _find_missing_patterns(
        self,
        workloads: List[TableWorkload],
        existing: List[Dict]
    ) -> List[MissingIndexPattern]:
        """Find common missing index patterns"""
        patterns = []
        existing_set = {(idx.get('table'), tuple(idx.get('columns', [])))
                       for idx in existing}
        
        for workload in workloads:
            # Pattern: High WHERE clause usage without index
            for col, usage in workload.column_usage.items():
                if usage.in_where_clause_count > 10:
                    if (workload.table_name, (col,)) not in existing_set:
                        patterns.append(MissingIndexPattern(
                            pattern_type="High WHERE clause usage",
                            affected_tables=[workload.table_name],
                            suggested_columns=[col],
                            frequency=usage.in_where_clause_count,
                            impact_description=f"Column '{col}' frequently used in WHERE but not indexed"
                        ))
                        
        return patterns
        
    def _generate_maintenance_recommendations(
        self,
        existing: List[Dict]
    ) -> List[IndexMaintenanceRecommendation]:
        """Generate index maintenance recommendations"""
        maintenance = []
        
        for idx in existing:
            # Simulate fragmentation check
            fragmentation = idx.get('fragmentation_percent', 15.0)
            
            if fragmentation > 30:
                maintenance.append(IndexMaintenanceRecommendation(
                    index_name=idx.get('name', 'unknown'),
                    table_name=idx.get('table', 'unknown'),
                    maintenance_action="REBUILD",
                    fragmentation_percent=fragmentation,
                    estimated_improvement="Restore index efficiency",
                    maintenance_sql=f"ALTER INDEX {idx.get('name')} ON {idx.get('table')} REBUILD;"
                ))
            elif fragmentation > 10:
                maintenance.append(IndexMaintenanceRecommendation(
                    index_name=idx.get('name', 'unknown'),
                    table_name=idx.get('table', 'unknown'),
                    maintenance_action="REORGANIZE",
                    fragmentation_percent=fragmentation,
                    estimated_improvement="Improve index performance",
                    maintenance_sql=f"ALTER INDEX {idx.get('name')} ON {idx.get('table')} REORGANIZE;"
                ))
                
        return maintenance
        
    def _calculate_statistics(
        self,
        recommendations: List[IndexRecommendation],
        redundant: List[RedundantIndex],
        existing: List[Dict],
        workloads: List[TableWorkload]
    ) -> IndexStatistics:
        """Calculate index statistics"""
        total_indexes = len(existing) + len(recommendations)
        total_space = sum(idx.get('size_mb', 10) for idx in existing)
        total_space += sum(rec.estimated_size_mb for rec in recommendations)
        
        space_saved = sum(red.space_saved_mb for red in redundant)
        
        # Estimate performance improvement
        avg_improvement = sum(rec.estimated_read_improvement_percent
                             for rec in recommendations) / max(1, len(recommendations))
        
        tables_analyzed = len(set(wl.table_name for wl in workloads))
        
        return IndexStatistics(
            total_indexes_recommended=len(recommendations),
            total_existing_indexes=len(existing),
            redundant_indexes_found=len(redundant),
            estimated_total_space_mb=round(total_space, 2),
            estimated_space_saved_mb=round(space_saved, 2),
            estimated_performance_improvement_percent=round(avg_improvement, 1),
            tables_analyzed=tables_analyzed
        )
        
    def _generate_warnings(
        self,
        recommendations: List[IndexRecommendation],
        redundant: List[RedundantIndex],
        analysis: WorkloadAnalysis
    ) -> List[str]:
        """Generate warnings"""
        warnings = []
        
        if len(recommendations) > 15:
            warnings.append(f"Large number of index recommendations ({len(recommendations)}) - prioritize by impact")
            
        if len(redundant) > 5:
            warnings.append(f"Many redundant indexes detected ({len(redundant)}) - consider cleanup")
            
        if analysis.read_write_ratio < 1.0:
            warnings.append("Write-heavy workload - be cautious with index additions to avoid write overhead")
            
        return warnings


def recommend_indexes_for_workload(
    database_engine: str,
    table_workloads: List[TableWorkload],
    existing_indexes: List[Dict],
    workload_patterns: List[WorkloadPattern],
    min_improvement_threshold: float = 10.0,
    max_recommendations: int = 10,
    optimization_goal: str = "balanced"
) -> Tuple:
    """Generate index recommendations for workload"""
    engine = IndexRecommendationEngine()
    return engine.recommend_indexes(
        database_engine, table_workloads, existing_indexes,
        workload_patterns, min_improvement_threshold,
        max_recommendations, optimization_goal
    )
