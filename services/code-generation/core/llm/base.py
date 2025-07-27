"""
Base LLM Interface and Abstract Classes
Provides unified interface for all LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI_GPT4 = "openai_gpt4"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    META_LLAMA = "meta_llama"
    GOOGLE_GEMINI = "google_gemini"
    LOCAL_MODEL = "local_model"

class TaskType(Enum):
    """Types of tasks for LLM routing"""
    SCHEMA_GENERATION = "schema_generation"
    CODE_REVIEW = "code_review"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    CRITIQUE = "critique"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"

@dataclass
class LLMRequest:
    """Request object for LLM operations"""
    prompt: str
    task_type: TaskType
    complexity: TaskComplexity
    context: Dict[str, Any] = field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LLMResponse:
    """Response object from LLM operations"""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    cost: float
    latency_ms: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ModelCapabilities:
    """Model capabilities and limits"""
    max_tokens: int
    context_window: int
    supports_streaming: bool
    supports_functions: bool
    cost_per_1k_tokens: float
    task_strengths: List[TaskType]
    availability_score: float
    latency_score: float

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = self._get_provider_type()
        self.capabilities = self._get_capabilities()
        self.is_available = False
        self._initialize()
    
    @abstractmethod
    def _get_provider_type(self) -> LLMProvider:
        """Get the provider type"""
        pass
    
    @abstractmethod
    def _get_capabilities(self) -> ModelCapabilities:
        """Get model capabilities"""
        pass
    
    @abstractmethod
    def _initialize(self):
        """Initialize the provider"""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response for a request"""
        pass
    
    @abstractmethod
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate response for a request"""
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is healthy"""
        try:
            test_request = LLMRequest(
                prompt="Health check",
                task_type=TaskType.DOCUMENTATION,
                complexity=TaskComplexity.SIMPLE,
                max_tokens=10
            )
            response = await self.generate(test_request)
            return response.content is not None
        except Exception:
            return False
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token usage"""
        return (tokens / 1000) * self.capabilities.cost_per_1k_tokens
    
    def get_task_score(self, task_type: TaskType, complexity: TaskComplexity) -> float:
        """Get suitability score for a task"""
        base_score = 1.0 if task_type in self.capabilities.task_strengths else 0.5
        
        # Adjust for complexity
        complexity_multiplier = {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MEDIUM: 0.9,
            TaskComplexity.COMPLEX: 0.8,
            TaskComplexity.ENTERPRISE: 0.7
        }
        
        return base_score * complexity_multiplier.get(complexity, 0.5)

class LLMError(Exception):
    """Base exception for LLM operations"""
    def __init__(self, message: str, provider: LLMProvider = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.provider = provider
        self.details = details or {}

class RateLimitError(LLMError):
    """Rate limit exceeded"""
    pass

class QuotaExceededError(LLMError):
    """Quota exceeded"""
    pass

class ModelUnavailableError(LLMError):
    """Model is unavailable"""
    pass

class InvalidRequestError(LLMError):
    """Invalid request format"""
    pass
