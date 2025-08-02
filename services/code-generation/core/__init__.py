"""
Core module for code generation service
"""

from .code_generator import CodeGenerator

# Try to import advanced patterns, but don't fail if dependencies are missing
try:
    from .advanced_patterns import (
        PatternMatcher,
        AdvancedPatternEngine,
        TemplateEngine,
        IntelligentCodeGenerator
    )
    _advanced_available = True
except ImportError as e:
    # Create placeholder classes if advanced patterns can't be imported
    PatternMatcher = None
    AdvancedPatternEngine = None
    TemplateEngine = None
    IntelligentCodeGenerator = None
    _advanced_available = False

# Import modular components only if their dependencies are available
_modules = []

try:
    from . import deployment
    _modules.append('deployment')
except ImportError:
    deployment = None

try:
    from . import ml
    _modules.append('ml')
except ImportError:
    ml = None

try:
    from . import monitoring
    _modules.append('monitoring')
except ImportError:
    monitoring = None

__all__ = ['CodeGenerator']

# Add advanced patterns if available
if _advanced_available:
    __all__.extend([
        'PatternMatcher', 
        'AdvancedPatternEngine', 
        'TemplateEngine', 
        'IntelligentCodeGenerator'
    ])

# Add available modules
__all__.extend(_modules)
