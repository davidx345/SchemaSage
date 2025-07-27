"""
Schema critic module initialization and main critic class
"""
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from models.schemas import SchemaResponse
from .base import SchemaCritique, SchemaAnalysisReport, CritiqueCategory, SeverityLevel
from .performance_analyzer import PerformanceAnalyzer
from .normalization_analyzer import NormalizationAnalyzer

logger = logging.getLogger(__name__)

class AISchemacritic:
    """AI-powered schema critique and analysis system"""
    
    def __init__(self):
        self.performance_analyzer = PerformanceAnalyzer()
        self.normalization_analyzer = NormalizationAnalyzer()
        
        # Scoring weights for different categories
        self.category_weights = {
            CritiqueCategory.PERFORMANCE: 0.25,
            CritiqueCategory.NORMALIZATION: 0.20,
            CritiqueCategory.INDEXING: 0.15,
            CritiqueCategory.RELATIONSHIPS: 0.15,
            CritiqueCategory.NAMING_CONVENTIONS: 0.10,
            CritiqueCategory.DATA_TYPES: 0.10,
            CritiqueCategory.CONSTRAINTS: 0.05
        }
    
    async def analyze_schema(
        self, 
        schema: SchemaResponse,
        context: Optional[Dict[str, Any]] = None
    ) -> SchemaAnalysisReport:
        """Perform comprehensive schema analysis"""
        start_time = time.time()
        
        try:
            critiques = []
            
            # Performance analysis
            perf_critiques = await self.performance_analyzer.analyze_performance(schema, context)
            critiques.extend(perf_critiques)
            
            # Normalization analysis
            norm_critiques = await self.normalization_analyzer.analyze_normalization(schema)
            critiques.extend(norm_critiques)
            
            # Naming conventions analysis
            naming_critiques = await self.normalization_analyzer.analyze_naming_conventions(schema)
            critiques.extend(naming_critiques)
            
            # Data types analysis
            datatype_critiques = await self.normalization_analyzer.analyze_data_types(schema)
            critiques.extend(datatype_critiques)
            
            # Calculate overall score and grade
            overall_score = self._calculate_overall_score(critiques)
            grade = self._calculate_grade(overall_score)
            
            # Generate summary
            summary = self._generate_summary(critiques, overall_score)
            
            # Count recommendations by severity
            recommendations_count = self._count_recommendations_by_severity(critiques)
            
            # Calculate category scores
            category_scores = self._calculate_category_scores(critiques)
            
            # Identify strengths
            strengths = self._identify_strengths(schema, critiques)
            
            analysis_duration = time.time() - start_time
            
            return SchemaAnalysisReport(
                schema_id=getattr(schema, 'id', 'unknown'),
                analysis_id=f"analysis_{int(time.time())}",
                overall_score=overall_score,
                grade=grade,
                critiques=critiques,
                strengths=strengths,
                summary=summary,
                recommendations_count=recommendations_count,
                category_scores=category_scores,
                analyzed_at=datetime.now(),
                analysis_duration=analysis_duration,
                total_tables=len(schema.tables),
                total_columns=sum(len(table.columns) for table in schema.tables),
                total_relationships=len(schema.relationships)
            )
        
        except Exception as e:
            logger.error(f"Error in schema analysis: {e}")
            raise
    
    def _calculate_overall_score(self, critiques: List[SchemaCritique]) -> float:
        """Calculate overall schema quality score (0-100)"""
        if not critiques:
            return 100.0
        
        # Start with perfect score
        score = 100.0
        
        # Deduct points based on severity
        severity_penalties = {
            SeverityLevel.INFO: 0,
            SeverityLevel.LOW: 2,
            SeverityLevel.MEDIUM: 5,
            SeverityLevel.HIGH: 10,
            SeverityLevel.CRITICAL: 20
        }
        
        for critique in critiques:
            penalty = severity_penalties.get(critique.severity, 0)
            # Apply category weight
            weighted_penalty = penalty * self.category_weights.get(critique.category, 0.1)
            score -= weighted_penalty
        
        return max(0.0, min(100.0, score))
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def _generate_summary(self, critiques: List[SchemaCritique], score: float) -> str:
        """Generate analysis summary"""
        if score >= 90:
            summary = "Excellent schema design with minimal issues."
        elif score >= 80:
            summary = "Good schema design with some areas for improvement."
        elif score >= 70:
            summary = "Average schema design with several recommendations."
        elif score >= 60:
            summary = "Below average schema design requiring attention."
        else:
            summary = "Poor schema design needing significant improvements."
        
        if critiques:
            high_severity = len([c for c in critiques if c.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]])
            if high_severity > 0:
                summary += f" {high_severity} high-priority issues identified."
        
        return summary
    
    def _count_recommendations_by_severity(self, critiques: List[SchemaCritique]) -> Dict[SeverityLevel, int]:
        """Count recommendations by severity level"""
        counts = {severity: 0 for severity in SeverityLevel}
        
        for critique in critiques:
            counts[critique.severity] += 1
        
        return counts
    
    def _calculate_category_scores(self, critiques: List[SchemaCritique]) -> Dict[CritiqueCategory, float]:
        """Calculate scores for each category"""
        category_scores = {}
        
        # Group critiques by category
        category_critiques = {}
        for critique in critiques:
            if critique.category not in category_critiques:
                category_critiques[critique.category] = []
            category_critiques[critique.category].append(critique)
        
        # Calculate score for each category
        for category in CritiqueCategory:
            if category in category_critiques:
                category_issues = category_critiques[category]
                # Start with 100 and deduct based on severity
                score = 100.0
                for critique in category_issues:
                    if critique.severity == SeverityLevel.CRITICAL:
                        score -= 30
                    elif critique.severity == SeverityLevel.HIGH:
                        score -= 20
                    elif critique.severity == SeverityLevel.MEDIUM:
                        score -= 10
                    elif critique.severity == SeverityLevel.LOW:
                        score -= 5
                
                category_scores[category] = max(0.0, score)
            else:
                category_scores[category] = 100.0
        
        return category_scores
    
    def _identify_strengths(self, schema: SchemaResponse, critiques: List[SchemaCritique]) -> List[str]:
        """Identify schema strengths"""
        strengths = []
        
        # Check for good practices
        
        # Primary keys
        tables_with_pk = sum(1 for table in schema.tables 
                           if any(getattr(col, 'primary_key', False) for col in table.columns))
        if tables_with_pk == len(schema.tables):
            strengths.append("All tables have primary keys")
        elif tables_with_pk > len(schema.tables) * 0.8:
            strengths.append("Most tables have primary keys")
        
        # Relationships
        if schema.relationships:
            strengths.append(f"Well-defined relationships ({len(schema.relationships)} relationships)")
        
        # Naming consistency (if no naming critique)
        naming_issues = [c for c in critiques if c.category == CritiqueCategory.NAMING_CONVENTIONS]
        if not naming_issues:
            strengths.append("Consistent naming conventions")
        
        # Performance (if few performance issues)
        perf_issues = [c for c in critiques if c.category == CritiqueCategory.PERFORMANCE]
        if len(perf_issues) <= 1:
            strengths.append("Good performance characteristics")
        
        # Normalization (if few normalization issues)
        norm_issues = [c for c in critiques if c.category == CritiqueCategory.NORMALIZATION]
        if len(norm_issues) <= 1:
            strengths.append("Well-normalized structure")
        
        # Table count
        if 5 <= len(schema.tables) <= 50:
            strengths.append("Appropriate number of tables")
        
        return strengths

__all__ = [
    'CritiqueCategory',
    'SeverityLevel',
    'SchemaCritique',
    'SchemaAnalysisReport',
    'PerformanceAnalyzer',
    'NormalizationAnalyzer',
    'AISchemacritic'
]
