"""
ROI Calculator and Debt Prioritizer Core Logic.
Calculates technical debt costs and prioritizes fixes by ROI.
"""
from typing import List, Dict, Any
from uuid import uuid4
from models.debt_models import (
    TechnicalDebtData, DebtItem, DebtByCategory, DebtTimeline,
    PrioritizationData, PrioritizedDebtItem, SprintRecommendation, ROIAnalysis,
    Severity, Priority, AntipatternType, DatabaseType
)

class ROICalculator:
    """
    Calculates technical debt and prioritizes fixes by ROI.
    """
    
    def calculate_debt(
        self,
        db_type: DatabaseType,
        connection_string: str,
        schema_name: str = None,
        team_size: int = 5,
        hourly_rate: float = 75.0
    ) -> TechnicalDebtData:
        """
        Calculates total technical debt with cost breakdown.
        """
        debt_items = self._identify_debt_items(hourly_rate)
        debt_by_category = self._categorize_debt(debt_items)
        debt_timeline = self._create_timeline(debt_items)
        roi_metrics = self._calculate_roi_metrics(debt_items, team_size)
        interest_rate = self._calculate_interest_rate(debt_items)
        
        total_hours = sum(item.effort_hours for item in debt_items)
        total_cost = sum(item.cost for item in debt_items)
        
        return TechnicalDebtData(
            total_debt_hours=total_hours,
            total_debt_cost=total_cost,
            debt_items=debt_items,
            debt_by_category=debt_by_category,
            debt_timeline=debt_timeline,
            roi_metrics=roi_metrics,
            interest_rate=interest_rate
        )
    
    def prioritize(
        self,
        db_type: DatabaseType,
        connection_string: str,
        schema_name: str = None,
        business_priorities: List[str] = None,
        available_hours_per_sprint: int = 80
    ) -> PrioritizationData:
        """
        Prioritizes technical debt fixes by ROI and business value.
        """
        if business_priorities is None:
            business_priorities = ["performance", "reliability", "security"]
        
        prioritized_items = self._prioritize_items(business_priorities)
        sprint_recommendations = self._plan_sprints(prioritized_items, available_hours_per_sprint)
        roi_analysis = self._analyze_roi(prioritized_items)
        quick_wins = self._identify_quick_wins(prioritized_items)
        critical_path = self._identify_critical_path(prioritized_items)
        deferred_items = self._identify_deferred_items(prioritized_items)
        
        return PrioritizationData(
            prioritized_items=prioritized_items,
            sprint_recommendations=sprint_recommendations,
            roi_analysis=roi_analysis,
            quick_wins=quick_wins,
            critical_path=critical_path,
            deferred_items=deferred_items
        )
    
    def _identify_debt_items(self, hourly_rate: float) -> List[DebtItem]:
        """Simulates identifying technical debt items."""
        items = []
        
        # Performance Debt
        items.append(DebtItem(
            debt_id=f"debt_{str(uuid4())[:8]}",
            category="performance",
            description="Missing indexes causing 2.5s average query time",
            severity=Severity.HIGH,
            affected_entities=["users", "orders", "products"],
            effort_hours=12.0,
            cost=12.0 * hourly_rate,
            business_impact="Poor user experience, 25% cart abandonment rate",
            risk_score=85
        ))
        
        # Data Integrity Debt
        items.append(DebtItem(
            debt_id=f"debt_{str(uuid4())[:8]}",
            category="data_integrity",
            description="Missing foreign key constraints on 8 tables",
            severity=Severity.CRITICAL,
            affected_entities=["orders", "order_items", "payments", "invoices"],
            effort_hours=16.0,
            cost=16.0 * hourly_rate,
            business_impact="Data inconsistency causing billing errors ($15K/month)",
            risk_score=95
        ))
        
        # Schema Design Debt
        items.append(DebtItem(
            debt_id=f"debt_{str(uuid4())[:8]}",
            category="schema_design",
            description="Denormalized tables causing update anomalies",
            severity=Severity.MEDIUM,
            affected_entities=["order_items", "cart_items"],
            effort_hours=24.0,
            cost=24.0 * hourly_rate,
            business_impact="Incorrect pricing shown in 3% of orders",
            risk_score=65
        ))
        
        # Maintainability Debt
        items.append(DebtItem(
            debt_id=f"debt_{str(uuid4())[:8]}",
            category="maintainability",
            description="Poor naming conventions across 15 tables",
            severity=Severity.LOW,
            affected_entities=["tbl_usr_data", "usr_prefs", "sys_config"],
            effort_hours=8.0,
            cost=8.0 * hourly_rate,
            business_impact="Developer confusion, 20% slower feature development",
            risk_score=35
        ))
        
        # Security Debt
        items.append(DebtItem(
            debt_id=f"debt_{str(uuid4())[:8]}",
            category="security",
            description="Sensitive data not encrypted at rest",
            severity=Severity.CRITICAL,
            affected_entities=["users", "payment_methods"],
            effort_hours=20.0,
            cost=20.0 * hourly_rate,
            business_impact="GDPR compliance risk, potential fines",
            risk_score=90
        ))
        
        # Scalability Debt
        items.append(DebtItem(
            debt_id=f"debt_{str(uuid4())[:8]}",
            category="scalability",
            description="Wide tables (85+ columns) causing I/O bottlenecks",
            severity=Severity.MEDIUM,
            affected_entities=["user_profiles"],
            effort_hours=32.0,
            cost=32.0 * hourly_rate,
            business_impact="Cannot scale beyond 500K users",
            risk_score=70
        ))
        
        return items
    
    def _categorize_debt(self, debt_items: List[DebtItem]) -> List[DebtByCategory]:
        """Groups debt by category."""
        categories = {}
        total_hours = sum(item.effort_hours for item in debt_items)
        
        for item in debt_items:
            if item.category not in categories:
                categories[item.category] = {
                    "count": 0,
                    "hours": 0.0,
                    "cost": 0.0
                }
            
            categories[item.category]["count"] += 1
            categories[item.category]["hours"] += item.effort_hours
            categories[item.category]["cost"] += item.cost
        
        result = []
        for cat, data in categories.items():
            result.append(DebtByCategory(
                category=cat,
                count=data["count"],
                total_hours=data["hours"],
                total_cost=data["cost"],
                percentage=round((data["hours"] / total_hours) * 100, 2) if total_hours > 0 else 0
            ))
        
        return sorted(result, key=lambda x: x.total_hours, reverse=True)
    
    def _create_timeline(self, debt_items: List[DebtItem]) -> DebtTimeline:
        """Creates timeline for debt repayment."""
        immediate = {"hours": 0, "cost": 0}
        short_term = {"hours": 0, "cost": 0}
        medium_term = {"hours": 0, "cost": 0}
        long_term = {"hours": 0, "cost": 0}
        
        for item in debt_items:
            if item.severity == Severity.CRITICAL:
                immediate["hours"] += item.effort_hours
                immediate["cost"] += item.cost
            elif item.severity == Severity.HIGH:
                short_term["hours"] += item.effort_hours
                short_term["cost"] += item.cost
            elif item.severity == Severity.MEDIUM:
                medium_term["hours"] += item.effort_hours
                medium_term["cost"] += item.cost
            else:
                long_term["hours"] += item.effort_hours
                long_term["cost"] += item.cost
        
        return DebtTimeline(
            immediate=immediate,
            short_term=short_term,
            medium_term=medium_term,
            long_term=long_term
        )
    
    def _calculate_roi_metrics(self, debt_items: List[DebtItem], team_size: int) -> Dict[str, Any]:
        """Calculates ROI metrics."""
        total_cost = sum(item.cost for item in debt_items)
        
        # Estimate savings from fixing debt (performance improvements, reduced errors, etc.)
        estimated_annual_savings = total_cost * 2.5  # Typical 2.5x return
        
        return {
            "total_investment": total_cost,
            "estimated_annual_savings": round(estimated_annual_savings, 2),
            "payback_period_months": round((total_cost / estimated_annual_savings) * 12, 1) if estimated_annual_savings > 0 else 0,
            "team_capacity_impact_weeks": round(sum(item.effort_hours for item in debt_items) / (team_size * 40), 1)
        }
    
    def _calculate_interest_rate(self, debt_items: List[DebtItem]) -> float:
        """Calculates monthly debt accumulation rate."""
        # Technical debt typically grows 10-15% per quarter if not addressed
        high_severity_ratio = len([i for i in debt_items if i.severity in [Severity.CRITICAL, Severity.HIGH]]) / len(debt_items)
        base_rate = 0.12  # 12% annual
        return round(base_rate * (1 + high_severity_ratio), 3)
    
    def _prioritize_items(self, business_priorities: List[str]) -> List[PrioritizedDebtItem]:
        """Prioritizes debt items by ROI and business value."""
        items = []
        
        # Critical: Data Integrity
        items.append(PrioritizedDebtItem(
            debt_id=f"pdebt_{str(uuid4())[:8]}",
            title="Add Missing Foreign Keys",
            description="Implement FK constraints on 8 tables to prevent orphaned records",
            antipattern_type=AntipatternType.NO_FOREIGN_KEY,
            severity=Severity.CRITICAL,
            priority=Priority.P0_URGENT,
            effort_hours=16.0,
            cost_savings=15000.0,  # Monthly billing error prevention
            roi_score=937.5,  # (15000 / 16)
            business_value=95,
            technical_risk=90,
            dependencies=[],
            recommendation="Add FK constraints with ON DELETE CASCADE where appropriate",
            auto_fix_sql="ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id);"
        ))
        
        # High: Performance
        items.append(PrioritizedDebtItem(
            debt_id=f"pdebt_{str(uuid4())[:8]}",
            title="Create Missing Indexes",
            description="Add indexes on frequently queried columns (email, user_id, created_at)",
            antipattern_type=AntipatternType.MISSING_INDEX,
            severity=Severity.HIGH,
            priority=Priority.P1_HIGH,
            effort_hours=12.0,
            cost_savings=8000.0,  # Reduced infrastructure costs + improved conversion
            roi_score=666.7,
            business_value=85,
            technical_risk=70,
            dependencies=[],
            recommendation="Analyze slow query log and add indexes on high-cardinality columns",
            auto_fix_sql="CREATE INDEX idx_users_email ON users(email); CREATE INDEX idx_orders_user_id ON orders(user_id);"
        ))
        
        # Critical: Security
        items.append(PrioritizedDebtItem(
            debt_id=f"pdebt_{str(uuid4())[:8]}",
            title="Encrypt Sensitive Data",
            description="Implement column-level encryption for PII and payment data",
            antipattern_type=None,
            severity=Severity.CRITICAL,
            priority=Priority.P0_URGENT,
            effort_hours=20.0,
            cost_savings=50000.0,  # Avoided GDPR fines
            roi_score=2500.0,
            business_value=90,
            technical_risk=85,
            dependencies=[],
            recommendation="Use pgcrypto or application-level encryption with key rotation",
            auto_fix_sql="CREATE EXTENSION IF NOT EXISTS pgcrypto; ALTER TABLE users ADD COLUMN ssn_encrypted bytea;"
        ))
        
        # Medium: Schema Design
        items.append(PrioritizedDebtItem(
            debt_id=f"pdebt_{str(uuid4())[:8]}",
            title="Normalize Denormalized Tables",
            description="Split order_items to remove product detail duplication",
            antipattern_type=AntipatternType.DENORMALIZATION,
            severity=Severity.MEDIUM,
            priority=Priority.P2_MEDIUM,
            effort_hours=24.0,
            cost_savings=3000.0,
            roi_score=125.0,
            business_value=60,
            technical_risk=65,
            dependencies=["Add Missing Foreign Keys"],
            recommendation="Create proper relationships and migrate duplicated data",
            auto_fix_sql=None
        ))
        
        # Low: Naming
        items.append(PrioritizedDebtItem(
            debt_id=f"pdebt_{str(uuid4())[:8]}",
            title="Standardize Naming Conventions",
            description="Rename 15 tables and 50+ columns to follow standards",
            antipattern_type=AntipatternType.POOR_NAMING,
            severity=Severity.LOW,
            priority=Priority.P3_LOW,
            effort_hours=8.0,
            cost_savings=1200.0,  # Faster development
            roi_score=150.0,
            business_value=30,
            technical_risk=25,
            dependencies=[],
            recommendation="Create and enforce naming convention guide",
            auto_fix_sql="ALTER TABLE tbl_usr_data RENAME TO user_data;"
        ))
        
        # Sort by priority then ROI
        priority_order = {Priority.P0_URGENT: 0, Priority.P1_HIGH: 1, Priority.P2_MEDIUM: 2, Priority.P3_LOW: 3}
        return sorted(items, key=lambda x: (priority_order[x.priority], -x.roi_score))
    
    def _plan_sprints(self, items: List[PrioritizedDebtItem], hours_per_sprint: int) -> List[SprintRecommendation]:
        """Plans sprint allocations."""
        sprints = []
        current_sprint = []
        current_hours = 0
        sprint_num = 1
        
        for item in items:
            if current_hours + item.effort_hours <= hours_per_sprint:
                current_sprint.append(item)
                current_hours += item.effort_hours
            else:
                if current_sprint:
                    sprints.append(self._create_sprint_recommendation(sprint_num, current_sprint))
                    sprint_num += 1
                current_sprint = [item]
                current_hours = item.effort_hours
        
        if current_sprint:
            sprints.append(self._create_sprint_recommendation(sprint_num, current_sprint))
        
        return sprints[:4]  # Limit to 4 sprints
    
    def _create_sprint_recommendation(self, sprint_num: int, items: List[PrioritizedDebtItem]) -> SprintRecommendation:
        """Creates sprint recommendation."""
        total_hours = sum(item.effort_hours for item in items)
        total_savings = sum(item.cost_savings for item in items)
        
        return SprintRecommendation(
            sprint_number=sprint_num,
            total_hours=total_hours,
            total_cost_savings=total_savings,
            items=items,
            completion_percentage=round((sprint_num / 4) * 100, 1),
            expected_improvement=f"Sprint {sprint_num}: {len(items)} items, ${total_savings:,.0f} annual savings"
        )
    
    def _analyze_roi(self, items: List[PrioritizedDebtItem]) -> ROIAnalysis:
        """Analyzes ROI over 3 years."""
        total_investment = sum(item.effort_hours * 75 for item in items)  # Assuming $75/hr
        year_1_savings = sum(item.cost_savings for item in items)
        
        # Assume 10% improvement each year
        year_2_savings = year_1_savings * 1.10
        year_3_savings = year_2_savings * 1.10
        
        total_savings = year_1_savings + year_2_savings + year_3_savings
        roi_percentage = ((total_savings - total_investment) / total_investment) * 100 if total_investment > 0 else 0
        payback_months = (total_investment / year_1_savings) * 12 if year_1_savings > 0 else 0
        
        return ROIAnalysis(
            total_investment=round(total_investment, 2),
            expected_savings_year_1=round(year_1_savings, 2),
            expected_savings_year_2=round(year_2_savings, 2),
            expected_savings_year_3=round(year_3_savings, 2),
            payback_period_months=round(payback_months, 1),
            roi_percentage=round(roi_percentage, 1)
        )
    
    def _identify_quick_wins(self, items: List[PrioritizedDebtItem]) -> List[PrioritizedDebtItem]:
        """Identifies high ROI, low effort items."""
        return [item for item in items if item.roi_score > 500 and item.effort_hours <= 12][:3]
    
    def _identify_critical_path(self, items: List[PrioritizedDebtItem]) -> List[str]:
        """Identifies must-fix items."""
        return [item.title for item in items if item.priority == Priority.P0_URGENT]
    
    def _identify_deferred_items(self, items: List[PrioritizedDebtItem]) -> List[PrioritizedDebtItem]:
        """Identifies items that can be deferred."""
        return [item for item in items if item.priority == Priority.P3_LOW]
