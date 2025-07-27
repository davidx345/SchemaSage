"""
Anthropic Claude Provider Implementation
"""
import anthropic
from typing import Dict, Any, AsyncGenerator
import logging
from datetime import datetime

from .base import (
    BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse, 
    ModelCapabilities, TaskType, TaskComplexity,
    LLMError, RateLimitError, QuotaExceededError, ModelUnavailableError
)

logger = logging.getLogger(__name__)

class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.model = config.get("model", "claude-3-opus-20240229")
        super().__init__(config)
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC_CLAUDE
    
    def _get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            max_tokens=4096,
            context_window=200000,
            supports_streaming=True,
            supports_functions=False,
            cost_per_1k_tokens=0.015,
            task_strengths=[
                TaskType.CODE_REVIEW,
                TaskType.OPTIMIZATION,
                TaskType.CRITIQUE,
                TaskType.DOCUMENTATION
            ],
            availability_score=0.92,
            latency_score=0.75
        )
    
    def _initialize(self):
        """Initialize Anthropic client"""
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.is_available = True
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic API"""
        start_time = datetime.now()
        
        try:
            # Prepare prompt with context
            full_prompt = request.prompt
            if request.context:
                full_prompt = f"Context: {request.context}\n\n{request.prompt}"
            
            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=request.max_tokens or self.capabilities.max_tokens,
                temperature=request.temperature,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            # Extract response data
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Calculate metrics
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            cost = self.estimate_cost(tokens_used)
            confidence = self._calculate_confidence(response, request)
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=self.model,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                confidence=confidence,
                metadata={
                    "stop_reason": response.stop_reason,
                    "model_version": response.model
                }
            )
            
        except anthropic.RateLimitError as e:
            raise RateLimitError(f"Claude rate limit exceeded: {str(e)}", self.provider)
        except anthropic.APIError as e:
            raise ModelUnavailableError(f"Claude API error: {str(e)}", self.provider)
        except Exception as e:
            raise LLMError(f"Claude generation failed: {str(e)}", self.provider)
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate response using Anthropic API"""
        try:
            # Prepare prompt with context
            full_prompt = request.prompt
            if request.context:
                full_prompt = f"Context: {request.context}\n\n{request.prompt}"
            
            # Make streaming API call
            stream = await self.client.messages.create(
                model=self.model,
                max_tokens=request.max_tokens or self.capabilities.max_tokens,
                temperature=request.temperature,
                messages=[{"role": "user", "content": full_prompt}],
                stream=True
            )
            
            async for chunk in stream:
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    yield chunk.delta.text
                    
        except anthropic.RateLimitError as e:
            raise RateLimitError(f"Claude rate limit exceeded: {str(e)}", self.provider)
        except Exception as e:
            raise LLMError(f"Claude streaming failed: {str(e)}", self.provider)
    
    def _calculate_confidence(self, response: Any, request: LLMRequest) -> float:
        """Calculate confidence score based on response"""
        base_confidence = 0.85
        
        # Adjust based on stop reason
        stop_reason = response.stop_reason
        if stop_reason == "end_turn":
            confidence_adjustment = 0.0
        elif stop_reason == "max_tokens":
            confidence_adjustment = -0.1
        else:
            confidence_adjustment = -0.2
        
        # Adjust based on task complexity
        complexity_adjustment = {
            TaskComplexity.SIMPLE: 0.1,
            TaskComplexity.MEDIUM: 0.0,
            TaskComplexity.COMPLEX: -0.05,
            TaskComplexity.ENTERPRISE: -0.1
        }.get(request.complexity, 0.0)
        
        return max(0.1, min(1.0, base_confidence + confidence_adjustment + complexity_adjustment))
