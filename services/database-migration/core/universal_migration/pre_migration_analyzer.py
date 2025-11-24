"""
Pre-Migration Analyzer Core Logic.
Analyzes migration risks, breaking changes, and dependencies.
"""
from typing import List, Dict, Any
from models.universal_migration_models import (
    PreAnalysisData, BreakingChange, PerformanceImpact, Dependency, RiskLevel
)


class PreMigrationAnalyzer:
    """
    Analyzes migration risks and breaking changes before execution.
    """
    
    def analyze_migration(self, source_type: str, target_type: str, migration_plan_id: str) -> PreAnalysisData:
        """Analyzes migration for breaking changes and risks."""
        # Detect breaking changes
        breaking_changes = self._detect_breaking_changes(source_type, target_type)
        
        # Analyze performance impact
        performance_impact = self._analyze_performance_impact(source_type, target_type)
        
        # Identify dependencies
        dependencies = self._identify_dependencies(source_type, target_type)
        
        # Calculate overall risk
        overall_risk = self._calculate_overall_risk(breaking_changes, performance_impact)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(breaking_changes, performance_impact, dependencies)
        
        # Estimate downtime
        estimated_downtime = self._estimate_downtime(breaking_changes, performance_impact)
        
        return PreAnalysisData(
            breaking_changes=breaking_changes,
            performance_impact=performance_impact,
            dependencies=dependencies,
            overall_risk_level=overall_risk,
            recommendations=recommendations,
            estimated_downtime_minutes=estimated_downtime
        )
    
    def _detect_breaking_changes(self, source_type: str, target_type: str) -> List[BreakingChange]:
        """Detects breaking changes in migration."""
        changes = []
        
        if source_type == "postgresql" and target_type == "mongodb":
            # PostgreSQL to MongoDB has significant breaking changes
            changes.append(BreakingChange(
                severity=RiskLevel.HIGH,
                category="Schema Model",
                description="Relational tables will be converted to document collections",
                affected_objects=["users", "orders", "products", "order_items"],
                migration_strategy="Convert tables to collections with embedded documents for one-to-many relationships",
                estimated_effort_hours=8
            ))
            
            changes.append(BreakingChange(
                severity=RiskLevel.HIGH,
                category="Relationships",
                description="Foreign key constraints not supported in MongoDB",
                affected_objects=["orders.user_id", "order_items.order_id", "order_items.product_id"],
                migration_strategy="Replace with manual reference checking in application code or use $lookup for joins",
                estimated_effort_hours=12
            ))
            
            changes.append(BreakingChange(
                severity=RiskLevel.MEDIUM,
                category="Transactions",
                description="ACID transactions have different semantics in MongoDB",
                affected_objects=["payment_processing", "order_fulfillment"],
                migration_strategy="Use MongoDB multi-document transactions with session management",
                estimated_effort_hours=6
            ))
            
            changes.append(BreakingChange(
                severity=RiskLevel.MEDIUM,
                category="Query Language",
                description="SQL queries must be rewritten to MongoDB Query API",
                affected_objects=["All SELECT/JOIN/UPDATE statements"],
                migration_strategy="Convert SQL to MongoDB aggregation pipeline or find() operations",
                estimated_effort_hours=20
            ))
        
        elif source_type == "mysql" and target_type == "postgresql":
            # MySQL to PostgreSQL has moderate breaking changes
            changes.append(BreakingChange(
                severity=RiskLevel.MEDIUM,
                category="Data Types",
                description="Some MySQL data types have different equivalents in PostgreSQL",
                affected_objects=["DATETIME columns", "ENUM types", "TINYINT columns"],
                migration_strategy="Map DATETIME to TIMESTAMP, ENUM to VARCHAR with CHECK constraint, TINYINT to SMALLINT",
                estimated_effort_hours=4
            ))
            
            changes.append(BreakingChange(
                severity=RiskLevel.LOW,
                category="Auto-Increment",
                description="AUTO_INCREMENT syntax differs from PostgreSQL SERIAL",
                affected_objects=["id columns"],
                migration_strategy="Convert AUTO_INCREMENT to SERIAL or IDENTITY columns",
                estimated_effort_hours=2
            ))
        
        return changes
    
    def _analyze_performance_impact(self, source_type: str, target_type: str) -> List[PerformanceImpact]:
        """Analyzes performance impact of migration."""
        impacts = []
        
        if source_type == "postgresql" and target_type == "mongodb":
            impacts.append(PerformanceImpact(
                area="Query Performance",
                impact_type="varies",
                magnitude="medium",
                description="JOIN queries will be slower (replaced with $lookup), but document reads will be faster",
                recommendations=[
                    "Denormalize frequently accessed data",
                    "Create compound indexes for common query patterns",
                    "Use projection to limit returned fields"
                ]
            ))
            
            impacts.append(PerformanceImpact(
                area="Write Performance",
                impact_type="improvement",
                magnitude="high",
                description="Write operations typically faster in MongoDB due to flexible schema",
                recommendations=[
                    "Use bulk write operations for batch inserts",
                    "Configure write concern based on durability requirements"
                ]
            ))
        
        elif source_type == "mysql" and target_type == "postgresql":
            impacts.append(PerformanceImpact(
                area="Full-Text Search",
                impact_type="improvement",
                magnitude="medium",
                description="PostgreSQL full-text search is more powerful than MySQL FULLTEXT",
                recommendations=[
                    "Migrate FULLTEXT indexes to PostgreSQL tsvector",
                    "Consider using GIN indexes for text search"
                ]
            ))
        
        return impacts
    
    def _identify_dependencies(self, source_type: str, target_type: str) -> List[Dependency]:
        """Identifies migration dependencies."""
        dependencies = []
        
        dependencies.append(Dependency(
            name="Application Code",
            current_version="N/A",
            required_version="N/A",
            upgrade_required=True,
            estimated_complexity=RiskLevel.HIGH,
            notes="Database client libraries and query logic must be updated"
        ))
        
        if target_type == "mongodb":
            dependencies.append(Dependency(
                name="MongoDB Driver",
                current_version="N/A",
                required_version=">=4.0.0",
                upgrade_required=True,
                estimated_complexity=RiskLevel.MEDIUM,
                notes="Install and configure MongoDB driver for your application language"
            ))
        
        if target_type == "postgresql":
            dependencies.append(Dependency(
                name="PostgreSQL Client",
                current_version="N/A",
                required_version=">=12.0",
                upgrade_required=True,
                estimated_complexity=RiskLevel.LOW,
                notes="Update database connection libraries to support PostgreSQL"
            ))
        
        return dependencies
    
    def _calculate_overall_risk(self, breaking_changes: List[BreakingChange], performance_impact: List[PerformanceImpact]) -> RiskLevel:
        """Calculates overall migration risk level."""
        if not breaking_changes:
            return RiskLevel.LOW
        
        high_risk_count = sum(1 for bc in breaking_changes if bc.severity == RiskLevel.HIGH)
        medium_risk_count = sum(1 for bc in breaking_changes if bc.severity == RiskLevel.MEDIUM)
        
        if high_risk_count >= 2:
            return RiskLevel.HIGH
        elif high_risk_count == 1 or medium_risk_count >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendations(self, breaking_changes: List[BreakingChange], performance_impact: List[PerformanceImpact], dependencies: List[Dependency]) -> List[str]:
        """Generates migration recommendations."""
        recommendations = []
        
        if breaking_changes:
            recommendations.append("Perform thorough testing in staging environment before production migration")
            recommendations.append("Create comprehensive rollback plan with data backups")
        
        high_risk_changes = [bc for bc in breaking_changes if bc.severity == RiskLevel.HIGH]
        if high_risk_changes:
            recommendations.append("Consider phased migration approach for high-risk changes")
            recommendations.append("Update application code to handle both old and new database schemas during transition")
        
        if any(dep.upgrade_required for dep in dependencies):
            recommendations.append("Update all dependent libraries and frameworks before migration")
        
        recommendations.append("Monitor query performance closely after migration")
        recommendations.append("Plan for extended maintenance window to handle unexpected issues")
        
        return recommendations
    
    def _estimate_downtime(self, breaking_changes: List[BreakingChange], performance_impact: List[PerformanceImpact]) -> int:
        """Estimates migration downtime in minutes."""
        base_downtime = 60  # Base 1 hour for migration execution
        
        # Add time for breaking changes
        for bc in breaking_changes:
            if bc.severity == RiskLevel.HIGH:
                base_downtime += 30
            elif bc.severity == RiskLevel.MEDIUM:
                base_downtime += 15
        
        # Add buffer for testing and verification
        base_downtime += 30
        
        return base_downtime
