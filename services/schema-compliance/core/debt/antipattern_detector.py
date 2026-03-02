"""
Antipattern Detector Core Logic.
Detects common database schema antipatterns.
"""
from typing import List, Dict, Any
from uuid import uuid4
from models.debt_models import (
    AntipatternDetectionData, Antipattern, AntipatternSummary,
    AntipatternType, Severity, DatabaseType
)

class AntipatternDetector:
    """
    Detects schema antipatterns and technical debt.
    """
    
    def __init__(self):
        self.severity_cost_multiplier = {
            Severity.CRITICAL: 40.0,
            Severity.HIGH: 20.0,
            Severity.MEDIUM: 10.0,
            Severity.LOW: 5.0
        }
    
    def detect(
        self, 
        db_type: DatabaseType, 
        connection_string: str,
        schema_name: str = None,
        include_recommendations: bool = True
    ) -> AntipatternDetectionData:
        """
        Scans database schema for antipatterns.
        """
        # In production, this would query information_schema and system catalogs
        antipatterns = self._scan_for_antipatterns(include_recommendations)
        summary = self._generate_summary(antipatterns)
        affected_tables = self._get_affected_tables(antipatterns)
        auto_fix_sql = self._generate_auto_fix_sql(antipatterns)
        
        return AntipatternDetectionData(
            antipatterns=antipatterns,
            summary=summary,
            affected_tables=affected_tables,
            auto_fix_sql=auto_fix_sql
        )
    
    def _scan_for_antipatterns(self, include_recommendations: bool) -> List[Antipattern]:
        """Simulates scanning for antipatterns."""
        antipatterns = []
        
        # Missing Index Antipattern
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.MISSING_INDEX,
            severity=Severity.HIGH,
            table="users",
            column="email",
            description="Frequently queried column 'email' lacks index",
            impact="90% of queries on this table perform full table scan (avg 2.5s)",
            technical_debt_hours=4.0,
            estimated_cost=300.0,
            recommendation="CREATE INDEX idx_users_email ON users(email)" if include_recommendations else "",
            auto_fix_available=True,
            auto_fix_sql="CREATE INDEX idx_users_email ON users(email);"
        ))
        
        # Missing Foreign Key
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.NO_FOREIGN_KEY,
            severity=Severity.CRITICAL,
            table="orders",
            column="user_id",
            description="Column 'user_id' references 'users' but has no foreign key constraint",
            impact="Data integrity at risk - orphaned records possible",
            technical_debt_hours=8.0,
            estimated_cost=600.0,
            recommendation="Add foreign key constraint with CASCADE rules" if include_recommendations else "",
            auto_fix_available=True,
            auto_fix_sql="ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;"
        ))
        
        # Denormalization
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.DENORMALIZATION,
            severity=Severity.MEDIUM,
            table="order_items",
            column="product_name,product_price",
            description="Product details duplicated in order_items instead of referencing products table",
            impact="Data inconsistency: 15% of records have outdated prices",
            technical_debt_hours=16.0,
            estimated_cost=1200.0,
            recommendation="Normalize by removing duplicate columns and using proper foreign keys" if include_recommendations else "",
            auto_fix_available=False,
            auto_fix_sql=None
        ))
        
        # Poor Naming
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.POOR_NAMING,
            severity=Severity.LOW,
            table="tbl_usr_data",
            column=None,
            description="Table uses poor naming convention: abbreviated, prefixed with 'tbl_'",
            impact="Reduced code maintainability and developer confusion",
            technical_debt_hours=2.0,
            estimated_cost=150.0,
            recommendation="Rename to 'user_data' following naming standards" if include_recommendations else "",
            auto_fix_available=True,
            auto_fix_sql="ALTER TABLE tbl_usr_data RENAME TO user_data;"
        ))
        
        # Missing Primary Key
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.NO_PRIMARY_KEY,
            severity=Severity.CRITICAL,
            table="session_logs",
            column=None,
            description="Table has no primary key defined",
            impact="Cannot ensure row uniqueness, replication issues",
            technical_debt_hours=6.0,
            estimated_cost=450.0,
            recommendation="Add surrogate key (id) or composite primary key" if include_recommendations else "",
            auto_fix_available=True,
            auto_fix_sql="ALTER TABLE session_logs ADD COLUMN id SERIAL PRIMARY KEY;"
        ))
        
        # Wide Table
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.WIDE_TABLE,
            severity=Severity.MEDIUM,
            table="user_profiles",
            column=None,
            description="Table has 85 columns, most rarely used together",
            impact="Poor cache utilization, increased I/O costs",
            technical_debt_hours=24.0,
            estimated_cost=1800.0,
            recommendation="Split into multiple related tables (user_profiles, user_preferences, user_metadata)" if include_recommendations else "",
            auto_fix_available=False,
            auto_fix_sql=None
        ))
        
        # Unnecessary Nullable
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.UNNECESSARY_NULLABLE,
            severity=Severity.MEDIUM,
            table="products",
            column="price",
            description="Critical column 'price' allows NULL values",
            impact="3% of records have NULL price causing business logic errors",
            technical_debt_hours=4.0,
            estimated_cost=300.0,
            recommendation="Add NOT NULL constraint after data cleanup" if include_recommendations else "",
            auto_fix_available=True,
            auto_fix_sql="UPDATE products SET price = 0.00 WHERE price IS NULL; ALTER TABLE products ALTER COLUMN price SET NOT NULL;"
        ))
        
        # Missing Timestamps
        antipatterns.append(Antipattern(
            antipattern_id=f"ap_{str(uuid4())[:8]}",
            type=AntipatternType.MISSING_TIMESTAMP,
            severity=Severity.HIGH,
            table="transactions",
            column=None,
            description="Critical table lacks created_at/updated_at timestamps",
            impact="Cannot track data lineage or audit changes",
            technical_debt_hours=3.0,
            estimated_cost=225.0,
            recommendation="Add created_at and updated_at columns with defaults" if include_recommendations else "",
            auto_fix_available=True,
            auto_fix_sql="ALTER TABLE transactions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
        ))
        
        return antipatterns
    
    def _generate_summary(self, antipatterns: List[Antipattern]) -> AntipatternSummary:
        """Generates summary statistics."""
        severity_counts = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0
        }
        
        for ap in antipatterns:
            severity_counts[ap.severity] += 1
        
        # Find most common antipattern
        type_counts = {}
        for ap in antipatterns:
            type_counts[ap.type.value] = type_counts.get(ap.type.value, 0) + 1
        
        most_common = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "none"
        
        total_debt = sum(ap.technical_debt_hours for ap in antipatterns)
        total_cost = sum(ap.estimated_cost for ap in antipatterns)
        
        return AntipatternSummary(
            total_antipatterns=len(antipatterns),
            critical_count=severity_counts[Severity.CRITICAL],
            high_count=severity_counts[Severity.HIGH],
            medium_count=severity_counts[Severity.MEDIUM],
            low_count=severity_counts[Severity.LOW],
            total_debt_hours=total_debt,
            total_cost=total_cost,
            most_common_antipattern=most_common
        )
    
    def _get_affected_tables(self, antipatterns: List[Antipattern]) -> List[str]:
        """Extracts unique list of affected tables."""
        tables = set()
        for ap in antipatterns:
            tables.add(ap.table)
        return sorted(list(tables))
    
    def _generate_auto_fix_sql(self, antipatterns: List[Antipattern]) -> List[str]:
        """Generates auto-fix SQL statements."""
        sql = ["-- Auto-generated fixes for schema antipatterns", ""]
        
        for ap in antipatterns:
            if ap.auto_fix_available and ap.auto_fix_sql:
                sql.append(f"-- Fix: {ap.description}")
                sql.append(ap.auto_fix_sql)
                sql.append("")
        
        return sql
