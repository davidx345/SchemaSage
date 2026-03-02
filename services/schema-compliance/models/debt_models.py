"""
Schema Debt Tracker models for Phase 2.3 features.
Includes models for antipattern detection, technical debt calculation, and prioritization.
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

# --- Enums ---

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    MONGODB = "mongodb"

class AntipatternType(str, Enum):
    MISSING_INDEX = "missing_index"
    NO_FOREIGN_KEY = "no_foreign_key"
    DENORMALIZATION = "denormalization"
    POOR_NAMING = "poor_naming"
    NO_PRIMARY_KEY = "no_primary_key"
    WIDE_TABLE = "wide_table"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    UNNECESSARY_NULLABLE = "unnecessary_nullable"
    MAGIC_VALUES = "magic_values"
    MISSING_TIMESTAMP = "missing_timestamp"

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Priority(str, Enum):
    P0_URGENT = "P0"
    P1_HIGH = "P1"
    P2_MEDIUM = "P2"
    P3_LOW = "P3"

# --- Antipattern Detection Models ---

class AntipatternDetectionRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    schema_name: Optional[str] = None
    include_recommendations: bool = True

class Antipattern(BaseModel):
    antipattern_id: str
    type: AntipatternType
    severity: Severity
    table: str
    column: Optional[str] = None
    description: str
    impact: str
    technical_debt_hours: float
    estimated_cost: float
    recommendation: str
    auto_fix_available: bool
    auto_fix_sql: Optional[str] = None

class AntipatternSummary(BaseModel):
    total_antipatterns: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_debt_hours: float
    total_cost: float
    most_common_antipattern: str

class AntipatternDetectionData(BaseModel):
    antipatterns: List[Antipattern]
    summary: AntipatternSummary
    affected_tables: List[str]
    auto_fix_sql: List[str]

class AntipatternDetectionResponse(BaseModel):
    success: bool
    data: AntipatternDetectionData

# --- Technical Debt Calculator Models ---

class TechnicalDebtRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    schema_name: Optional[str] = None
    team_size: int = Field(default=5, ge=1)
    hourly_rate: float = Field(default=75.0, ge=0)

class DebtItem(BaseModel):
    debt_id: str
    category: str
    description: str
    severity: Severity
    affected_entities: List[str]
    effort_hours: float
    cost: float
    business_impact: str
    risk_score: int = Field(..., ge=0, le=100)

class DebtByCategory(BaseModel):
    category: str
    count: int
    total_hours: float
    total_cost: float
    percentage: float

class DebtTimeline(BaseModel):
    immediate: Dict[str, float]  # 0-1 week
    short_term: Dict[str, float]  # 1-4 weeks
    medium_term: Dict[str, float]  # 1-3 months
    long_term: Dict[str, float]  # 3+ months

class TechnicalDebtData(BaseModel):
    total_debt_hours: float
    total_debt_cost: float
    debt_items: List[DebtItem]
    debt_by_category: List[DebtByCategory]
    debt_timeline: DebtTimeline
    roi_metrics: Dict[str, Any]
    interest_rate: float  # Debt accumulation rate per month

class TechnicalDebtResponse(BaseModel):
    success: bool
    data: TechnicalDebtData

# --- Debt Prioritization Models ---

class PrioritizationRequest(BaseModel):
    database_type: DatabaseType
    connection_string: str
    schema_name: Optional[str] = None
    business_priorities: List[str] = Field(default=["performance", "reliability", "security"])
    available_hours_per_sprint: int = Field(default=80, ge=1)

class PrioritizedDebtItem(BaseModel):
    debt_id: str
    title: str
    description: str
    antipattern_type: Optional[AntipatternType]
    severity: Severity
    priority: Priority
    effort_hours: float
    cost_savings: float
    roi_score: float
    business_value: int = Field(..., ge=0, le=100)
    technical_risk: int = Field(..., ge=0, le=100)
    dependencies: List[str]
    recommendation: str
    auto_fix_sql: Optional[str] = None

class SprintRecommendation(BaseModel):
    sprint_number: int
    total_hours: float
    total_cost_savings: float
    items: List[PrioritizedDebtItem]
    completion_percentage: float
    expected_improvement: str

class ROIAnalysis(BaseModel):
    total_investment: float
    expected_savings_year_1: float
    expected_savings_year_2: float
    expected_savings_year_3: float
    payback_period_months: float
    roi_percentage: float

class PrioritizationData(BaseModel):
    prioritized_items: List[PrioritizedDebtItem]
    sprint_recommendations: List[SprintRecommendation]
    roi_analysis: ROIAnalysis
    quick_wins: List[PrioritizedDebtItem]  # High ROI, low effort
    critical_path: List[str]  # Must-fix items
    deferred_items: List[PrioritizedDebtItem]

class PrioritizationResponse(BaseModel):
    success: bool
    data: PrioritizationData
