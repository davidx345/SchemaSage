"""
Schema Compatibility Checker

Analyzes schema compatibility between source and target databases.
"""

import logging
import re
from typing import List, Dict, Any, Tuple
from models.compatibility_models import (
    CompatibilityRequest, CompatibilityIssue, MigrationRecommendation,
    CompatibilitySummary, CompatibilityLevel, IssueSeverity, IssueCategory
)

logger = logging.getLogger(__name__)


class CompatibilityChecker:
    """Check schema compatibility between database types"""
    
    # Data type compatibility mappings (source_db -> target_db -> {source_type: (target_type, compatibility_level)})
    TYPE_MAPPINGS = {
        "postgresql": {
            "mysql": {
                "serial": ("int auto_increment", "high"),
                "bigserial": ("bigint auto_increment", "high"),
                "text": ("longtext", "exact"),
                "bytea": ("blob", "high"),
                "boolean": ("tinyint(1)", "high"),
                "json": ("json", "exact"),
                "jsonb": ("json", "medium"),  # MySQL JSON doesn't have binary format
                "uuid": ("char(36)", "medium"),
                "array": (None, "incompatible"),  # MySQL doesn't support arrays
                "hstore": (None, "incompatible"),
            },
            "sqlserver": {
                "serial": ("int identity", "high"),
                "bigserial": ("bigint identity", "high"),
                "text": ("varchar(max)", "high"),
                "bytea": ("varbinary(max)", "high"),
                "boolean": ("bit", "high"),
                "json": ("nvarchar(max)", "medium"),
                "jsonb": ("nvarchar(max)", "medium"),
                "uuid": ("uniqueidentifier", "exact"),
                "array": (None, "incompatible"),
            }
        },
        "mysql": {
            "postgresql": {
                "auto_increment": ("serial", "high"),
                "longtext": ("text", "exact"),
                "mediumtext": ("text", "exact"),
                "blob": ("bytea", "high"),
                "tinyint(1)": ("boolean", "high"),
                "json": ("jsonb", "high"),
                "enum": ("varchar with check constraint", "medium"),
            },
            "sqlserver": {
                "auto_increment": ("identity", "high"),
                "longtext": ("varchar(max)", "high"),
                "blob": ("varbinary(max)", "high"),
                "tinyint(1)": ("bit", "high"),
                "json": ("nvarchar(max)", "medium"),
            }
        },
        "sqlserver": {
            "postgresql": {
                "identity": ("serial", "high"),
                "varchar(max)": ("text", "high"),
                "nvarchar(max)": ("text", "high"),
                "varbinary(max)": ("bytea", "high"),
                "bit": ("boolean", "high"),
                "uniqueidentifier": ("uuid", "exact"),
            },
            "mysql": {
                "identity": ("auto_increment", "high"),
                "varchar(max)": ("longtext", "high"),
                "nvarchar(max)": ("longtext", "high"),
                "varbinary(max)": ("blob", "high"),
                "bit": ("tinyint(1)", "high"),
                "uniqueidentifier": ("char(36)", "medium"),
            }
        }
    }
    
    def __init__(self):
        self.issues: List[CompatibilityIssue] = []
        self.supported_features: List[str] = []
        self.unsupported_features: List[str] = []
        
    def check_compatibility(self, request: CompatibilityRequest) -> Tuple[CompatibilitySummary, List[CompatibilityIssue], List[MigrationRecommendation], List[str], List[str]]:
        """
        Check schema compatibility
        
        Args:
            request: Compatibility check request
            
        Returns:
            Tuple of (summary, issues, recommendations, supported_features, unsupported_features)
        """
        self.issues = []
        self.supported_features = []
        self.unsupported_features = []
        
        # Check schema compatibility
        self._check_schema_objects(request)
        
        # Check stored procedures if requested
        if request.check_stored_procedures:
            self._check_stored_procedures(request)
        
        # Check triggers if requested
        if request.check_triggers:
            self._check_triggers(request)
        
        # Check views if requested
        if request.check_views:
            self._check_views(request)
        
        # Generate summary
        summary = self._generate_summary()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(request, summary)
        
        return summary, self.issues, recommendations, self.supported_features, self.unsupported_features
    
    def _check_schema_objects(self, request: CompatibilityRequest):
        """Check compatibility of schema objects (tables, columns, types)"""
        schema = request.schema
        source_db = request.source_db_type.value
        target_db = request.target_db_type.value
        
        # Check if we have type mappings for this migration path
        if source_db not in self.TYPE_MAPPINGS or target_db not in self.TYPE_MAPPINGS[source_db]:
            self.issues.append(CompatibilityIssue(
                category=IssueCategory.DATA_TYPE,
                severity=IssueSeverity.WARNING,
                object_type="database",
                object_name=f"{source_db} -> {target_db}",
                description=f"Limited compatibility information for {source_db} to {target_db} migration",
                workaround="Manual review of all data types recommended",
                is_blocker=False
            ))
            return
        
        type_mappings = self.TYPE_MAPPINGS[source_db][target_db]
        
        # Check tables
        tables = schema.get("tables", [])
        for table in tables:
            table_name = table.get("name", "unknown")
            columns = table.get("columns", [])
            
            # Check each column
            for column in columns:
                col_name = column.get("name", "unknown")
                data_type = column.get("data_type", "").lower()
                
                # Check data type compatibility
                self._check_data_type_compatibility(
                    table_name, col_name, data_type, type_mappings
                )
            
            # Check indexes
            indexes = table.get("indexes", [])
            if indexes:
                self._check_index_compatibility(table_name, indexes, request)
            
            # Check constraints
            constraints = table.get("constraints", [])
            if constraints:
                self._check_constraint_compatibility(table_name, constraints, request)
    
    def _check_data_type_compatibility(self, table_name: str, column_name: str, data_type: str, type_mappings: Dict):
        """Check individual data type compatibility"""
        # Extract base type (e.g., "varchar(255)" -> "varchar")
        base_type = re.split(r'[\(\[\s]', data_type)[0].lower()
        
        if base_type in type_mappings:
            target_type, compatibility = type_mappings[base_type]
            
            if compatibility == "incompatible" or target_type is None:
                self.issues.append(CompatibilityIssue(
                    category=IssueCategory.DATA_TYPE,
                    severity=IssueSeverity.CRITICAL,
                    object_type="column",
                    object_name=f"{table_name}.{column_name}",
                    description=f"Data type '{data_type}' is not supported in target database",
                    source_definition=data_type,
                    target_equivalent=None,
                    workaround="Redesign column or use alternative approach",
                    is_blocker=True
                ))
                self.unsupported_features.append(f"Data type: {base_type}")
            elif compatibility == "medium":
                self.issues.append(CompatibilityIssue(
                    category=IssueCategory.DATA_TYPE,
                    severity=IssueSeverity.WARNING,
                    object_type="column",
                    object_name=f"{table_name}.{column_name}",
                    description=f"Data type '{data_type}' requires conversion",
                    source_definition=data_type,
                    target_equivalent=target_type,
                    workaround=f"Use {target_type} with careful data validation",
                    is_blocker=False
                ))
                self.supported_features.append(f"Data type: {base_type} (with conversion)")
            else:
                self.supported_features.append(f"Data type: {base_type}")
        else:
            # Unknown type - add warning
            self.issues.append(CompatibilityIssue(
                category=IssueCategory.DATA_TYPE,
                severity=IssueSeverity.WARNING,
                object_type="column",
                object_name=f"{table_name}.{column_name}",
                description=f"Unknown data type '{data_type}' - manual review required",
                source_definition=data_type,
                workaround="Verify type compatibility manually",
                is_blocker=False
            ))
    
    def _check_index_compatibility(self, table_name: str, indexes: List, request: CompatibilityRequest):
        """Check index compatibility"""
        source_db = request.source_db_type.value
        target_db = request.target_db_type.value
        
        # Check for specific index types that may not be supported
        if source_db == "postgresql" and target_db in ["mysql", "sqlserver"]:
            # PostgreSQL has specialized index types
            for index in indexes:
                if "gin" in str(index).lower() or "gist" in str(index).lower():
                    self.issues.append(CompatibilityIssue(
                        category=IssueCategory.INDEX,
                        severity=IssueSeverity.ERROR,
                        object_type="index",
                        object_name=f"{table_name}.{index}",
                        description=f"Specialized PostgreSQL index type not supported in {target_db}",
                        workaround="Use standard B-tree indexes or alternative indexing strategy",
                        is_blocker=False
                    ))
                    self.unsupported_features.append(f"Index type: {index}")
                else:
                    self.supported_features.append(f"Standard index on {table_name}")
    
    def _check_constraint_compatibility(self, table_name: str, constraints: List, request: CompatibilityRequest):
        """Check constraint compatibility"""
        # Most basic constraints (PK, FK, UNIQUE, NOT NULL) are widely supported
        for constraint in constraints:
            if "check" in str(constraint).lower():
                # Check constraints are widely supported but syntax may differ
                self.issues.append(CompatibilityIssue(
                    category=IssueCategory.CONSTRAINT,
                    severity=IssueSeverity.INFO,
                    object_type="constraint",
                    object_name=f"{table_name}.{constraint}",
                    description="Check constraint syntax may need adjustment",
                    workaround="Review and test check constraint expressions",
                    is_blocker=False
                ))
            
            self.supported_features.append(f"Constraint on {table_name}")
    
    def _check_stored_procedures(self, request: CompatibilityRequest):
        """Check stored procedure compatibility"""
        source_db = request.source_db_type.value
        target_db = request.target_db_type.value
        
        # Stored procedures are highly database-specific
        self.issues.append(CompatibilityIssue(
            category=IssueCategory.STORED_PROCEDURE,
            severity=IssueSeverity.CRITICAL,
            object_type="stored_procedure",
            object_name="all",
            description=f"Stored procedures from {source_db} require complete rewrite for {target_db}",
            workaround="Rewrite all stored procedures in target database syntax",
            is_blocker=True
        ))
        self.unsupported_features.append("Stored procedure direct migration")
    
    def _check_triggers(self, request: CompatibilityRequest):
        """Check trigger compatibility"""
        source_db = request.source_db_type.value
        target_db = request.target_db_type.value
        
        # Triggers have similar issues to stored procedures
        self.issues.append(CompatibilityIssue(
            category=IssueCategory.TRIGGER,
            severity=IssueSeverity.ERROR,
            object_type="trigger",
            object_name="all",
            description=f"Triggers from {source_db} require rewrite for {target_db}",
            workaround="Rewrite triggers using target database trigger syntax",
            is_blocker=False
        ))
        self.unsupported_features.append("Trigger direct migration")
    
    def _check_views(self, request: CompatibilityRequest):
        """Check view compatibility"""
        # Views often work if the underlying SQL is compatible
        self.issues.append(CompatibilityIssue(
            category=IssueCategory.VIEW,
            severity=IssueSeverity.WARNING,
            object_type="view",
            object_name="all",
            description="Views may require SQL syntax adjustments",
            workaround="Review and test all view definitions",
            is_blocker=False
        ))
    
    def _generate_summary(self) -> CompatibilitySummary:
        """Generate compatibility summary"""
        # Count issues by severity
        critical = sum(1 for i in self.issues if i.severity == IssueSeverity.CRITICAL)
        errors = sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
        infos = sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)
        blockers = sum(1 for i in self.issues if i.is_blocker)
        
        # Determine overall compatibility
        if critical > 5 or blockers > 3:
            overall = CompatibilityLevel.INCOMPATIBLE
        elif critical > 0 or blockers > 0:
            overall = CompatibilityLevel.PARTIALLY_COMPATIBLE
        elif errors > 5:
            overall = CompatibilityLevel.PARTIALLY_COMPATIBLE
        elif errors > 0 or warnings > 10:
            overall = CompatibilityLevel.MOSTLY_COMPATIBLE
        else:
            overall = CompatibilityLevel.FULLY_COMPATIBLE
        
        # Calculate compatibility percentage
        total_checks = len(self.supported_features) + len(self.unsupported_features)
        if total_checks > 0:
            compatibility_pct = (len(self.supported_features) / total_checks) * 100
        else:
            compatibility_pct = 0.0
        
        return CompatibilitySummary(
            overall_compatibility=overall,
            total_issues=len(self.issues),
            critical_issues=critical,
            error_issues=errors,
            warning_issues=warnings,
            info_issues=infos,
            blockers_count=blockers,
            compatibility_percentage=round(compatibility_pct, 1)
        )
    
    def _generate_recommendations(self, request: CompatibilityRequest, summary: CompatibilitySummary) -> List[MigrationRecommendation]:
        """Generate migration recommendations"""
        recommendations = []
        
        if summary.blockers_count > 0:
            recommendations.append(MigrationRecommendation(
                priority="high",
                title="Resolve Migration Blockers",
                description=f"Address {summary.blockers_count} critical blocking issues before migration",
                effort_estimate=f"{summary.blockers_count * 2} days"
            ))
        
        if summary.critical_issues > 0:
            recommendations.append(MigrationRecommendation(
                priority="high",
                title="Address Critical Compatibility Issues",
                description=f"Resolve {summary.critical_issues} critical compatibility problems",
                effort_estimate=f"{summary.critical_issues} days"
            ))
        
        if "Stored procedure" in str(self.unsupported_features):
            recommendations.append(MigrationRecommendation(
                priority="high",
                title="Rewrite Stored Procedures",
                description="All stored procedures must be rewritten in target database syntax",
                effort_estimate="2-4 weeks"
            ))
        
        if summary.compatibility_percentage < 80:
            recommendations.append(MigrationRecommendation(
                priority="medium",
                title="Schema Redesign Consideration",
                description=f"With {summary.compatibility_percentage}% compatibility, consider schema redesign",
                effort_estimate="1-2 weeks"
            ))
        
        recommendations.append(MigrationRecommendation(
            priority="medium",
            title="Comprehensive Testing",
            description="Perform thorough testing of all migrated schema objects",
            effort_estimate="1 week"
        ))
        
        return recommendations


def check_compatibility(request: CompatibilityRequest) -> Tuple[CompatibilitySummary, List[CompatibilityIssue], List[MigrationRecommendation], List[str], List[str]]:
    """
    Convenience function to check schema compatibility
    
    Args:
        request: Compatibility check request
        
    Returns:
        Tuple of (summary, issues, recommendations, supported_features, unsupported_features)
    """
    checker = CompatibilityChecker()
    return checker.check_compatibility(request)
