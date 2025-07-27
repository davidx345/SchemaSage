"""
Core module for code generation service
"""

from .code_generator import CodeGenerator
from .advanced_patterns import (
    PatternMatcher,
    AdvancedPatternEngine,
    TemplateEngine,
    IntelligentCodeGenerator
)

# Import modular components
from . import deployment
from . import ml
from . import monitoring

__all__ = [
    'CodeGenerator', 
    'PatternMatcher', 
    'AdvancedPatternEngine', 
    'TemplateEngine', 
    'IntelligentCodeGenerator',
    'deployment',
    'ml',
    'monitoring'
]
