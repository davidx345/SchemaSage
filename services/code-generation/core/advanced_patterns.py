"""
Advanced Pattern Matching and Intelligent Code Generation
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from models.schemas import SchemaResponse, CodeGenFormat
from .code_generator import CodeGenerator, CodeGenerationResult

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Represents a code generation pattern"""
    name: str
    description: str
    template: str
    conditions: Dict[str, Any]


class PatternMatcher:
    """Matches database patterns to code generation templates"""
    
    def __init__(self):
        self.patterns: List[Pattern] = []
        logger.info("PatternMatcher initialized")
    
    def match_patterns(self, schema: SchemaResponse) -> List[Pattern]:
        """Match schema to available patterns"""
        matched = []
        for pattern in self.patterns:
            if self._matches_conditions(schema, pattern.conditions):
                matched.append(pattern)
        return matched
    
    def _matches_conditions(self, schema: SchemaResponse, conditions: Dict[str, Any]) -> bool:
        """Check if schema matches pattern conditions"""
        # Simple condition matching - can be extended
        if "min_tables" in conditions:
            if len(schema.tables) < conditions["min_tables"]:
                return False
        
        if "has_relationships" in conditions:
            has_rels = bool(schema.relationships)
            if has_rels != conditions["has_relationships"]:
                return False
                
        return True


class AdvancedPatternEngine:
    """Advanced pattern matching engine for code generation"""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.template_cache: Dict[str, Any] = {}
        logger.info("AdvancedPatternEngine initialized")
    
    def analyze_schema_patterns(self, schema: SchemaResponse) -> Dict[str, Any]:
        """Analyze schema for advanced patterns"""
        patterns = self.pattern_matcher.match_patterns(schema)
        
        analysis = {
            "matched_patterns": [p.name for p in patterns],
            "complexity_score": self._calculate_complexity(schema),
            "recommendations": self._generate_recommendations(schema, patterns)
        }
        
        return analysis
    
    def _calculate_complexity(self, schema: SchemaResponse) -> float:
        """Calculate schema complexity score"""
        table_count = len(schema.tables)
        total_columns = sum(len(table.columns) for table in schema.tables)
        relationship_count = len(schema.relationships) if schema.relationships else 0
        
        # Simple complexity calculation
        complexity = (table_count * 0.3) + (total_columns * 0.1) + (relationship_count * 0.6)
        return min(complexity / 10.0, 1.0)  # Normalize to 0-1
    
    def _generate_recommendations(self, schema: SchemaResponse, patterns: List[Pattern]) -> List[str]:
        """Generate code generation recommendations"""
        recommendations = []
        
        if len(schema.tables) > 10:
            recommendations.append("Consider using modular code generation for large schemas")
        
        if schema.relationships and len(schema.relationships) > 5:
            recommendations.append("Include relationship mapping in generated code")
        
        if patterns:
            recommendations.append(f"Apply {len(patterns)} matched patterns for optimal code structure")
        
        return recommendations


class TemplateEngine:
    """Enhanced template engine with intelligent features"""
    
    def __init__(self):
        self.advanced_patterns = AdvancedPatternEngine()
        logger.info("TemplateEngine initialized")
    
    def enhance_template_context(self, schema: SchemaResponse, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance template context with intelligent analysis"""
        pattern_analysis = self.advanced_patterns.analyze_schema_patterns(schema)
        
        enhanced_context = context.copy()
        enhanced_context.update({
            "pattern_analysis": pattern_analysis,
            "intelligent_features": True,
            "auto_optimizations": self._get_optimizations(schema)
        })
        
        return enhanced_context
    
    def _get_optimizations(self, schema: SchemaResponse) -> List[str]:
        """Get recommended optimizations for the schema"""
        optimizations = []
        
        # Check for common optimization opportunities
        for table in schema.tables:
            if len(table.columns) > 20:
                optimizations.append(f"Consider normalizing large table: {table.name}")
            
            pk_columns = [col for col in table.columns if col.is_primary_key]
            if not pk_columns:
                optimizations.append(f"Add primary key to table: {table.name}")
        
        return optimizations


class IntelligentCodeGenerator(CodeGenerator):
    """AI-enhanced code generator with intelligent pattern matching"""
    
    def __init__(self):
        super().__init__()
        self.template_engine = TemplateEngine()
        logger.info("IntelligentCodeGenerator initialized")
    
    async def generate_code(
        self,
        schema: SchemaResponse,
        format: CodeGenFormat,
        options: Optional[Dict[str, Any]] = None
    ) -> CodeGenerationResult:
        """
        Generate code with intelligent enhancements
        """
        logger.info(f"Generating intelligent {format.value} code")
        
        # Use base generator but enhance the context
        try:
            # Get template for format
            template_name = self.format_templates.get(format)
            if not template_name:
                from .etl_code_generator.base import CodeGenerationError
                raise CodeGenerationError(f"Unsupported format: {format.value}")
            
            # Load template
            template = self.env.get_template(template_name)
            
            # Prepare enhanced template context
            base_context = self._prepare_template_context(schema, options or {})
            enhanced_context = self.template_engine.enhance_template_context(schema, base_context)
            
            # Generate code
            code = await self._render_template(template, enhanced_context)
            
            # Enhanced metadata
            metadata = {
                "format": format.value,
                "table_count": len(schema.tables),
                "column_count": sum(len(table.columns) for table in schema.tables),
                "relationship_count": len(schema.relationships) if schema.relationships else 0,
                "template_used": template_name,
                "generation_options": options or {},
                "schema_version": schema.metadata.version if schema.metadata else "1.0",
                "intelligent_features": True,
                "pattern_analysis": enhanced_context.get("pattern_analysis", {}),
                "optimizations": enhanced_context.get("auto_optimizations", [])
            }
            
            result = CodeGenerationResult(
                code=code,
                metadata=metadata,
                format=format,
                generated_at=self._get_current_time()
            )
            
            logger.info(f"Successfully generated intelligent {len(code)} characters of {format.value} code")
            return result
            
        except Exception as e:
            from .etl_code_generator.base import CodeGenerationError
            logger.error(f"Intelligent code generation failed: {e}")
            raise CodeGenerationError(f"Intelligent code generation failed: {str(e)}") from e
    
    def _get_current_time(self):
        """Get current time - separated for easier testing"""
        from datetime import datetime
        return datetime.now()


# Export all classes
__all__ = [
    'Pattern',
    'PatternMatcher', 
    'AdvancedPatternEngine', 
    'TemplateEngine', 
    'IntelligentCodeGenerator'
]
