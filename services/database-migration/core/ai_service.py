"""
AI Features Service - Modularized
Phase 4: Natural Language Processing & Intelligent Optimization
"""

# Import all AI services from modular structure
from .ai.natural_language_processor import NaturalLanguageProcessor
from .ai.intelligent_optimizer import IntelligentOptimizer  
from .ai.documentation_generator import DocumentationGenerator

# Export classes for backward compatibility
__all__ = [
    'NaturalLanguageProcessor',
    'IntelligentOptimizer',
    'DocumentationGenerator'
]
