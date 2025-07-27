"""
Base classes and types for AI schema critic system
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class CritiqueCategory(Enum):
    """Categories of schema critique"""
    PERFORMANCE = "performance"
    NORMALIZATION = "normalization"
    INDEXING = "indexing"
    RELATIONSHIPS = "relationships"
    NAMING_CONVENTIONS = "naming_conventions"
    DATA_TYPES = "data_types"
    CONSTRAINTS = "constraints"
    SECURITY = "security"
    SCALABILITY = "scalability"
    BEST_PRACTICES = "best_practices"

class SeverityLevel(Enum):
    """Severity levels for critiques"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SchemaCritique:
    """Individual schema critique"""
    id: str
    category: CritiqueCategory
    severity: SeverityLevel
    title: str
    description: str
    recommendation: str
    affected_tables: List[str]
    affected_columns: List[str]
    confidence: float
    impact_score: float
    fix_complexity: str  # easy, medium, hard
    estimated_effort: str  # time estimate
    references: List[str]  # Documentation links
    code_examples: List[str]
    created_at: datetime

@dataclass
class SchemaAnalysisReport:
    """Complete schema analysis report"""
    schema_id: str
    analysis_id: str
    overall_score: float
    grade: str  # A+, A, B, C, D, F
    critiques: List[SchemaCritique]
    strengths: List[str]
    summary: str
    recommendations_count: Dict[SeverityLevel, int]
    category_scores: Dict[CritiqueCategory, float]
    analyzed_at: datetime
    analysis_duration: float
    total_tables: int
    total_columns: int
    total_relationships: int
