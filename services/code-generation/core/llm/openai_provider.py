"""
OpenAI GPT-4 Provider Implementation
"""
import openai
import asyncio
from typing import Dict, Any, AsyncGenerator
import logging
from datetime import datetime

from .base import (
    BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse, 
    ModelCapabilities, TaskType, TaskComplexity,
    LLMError, RateLimitError, QuotaExceededError, ModelUnavailableError
)

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT-4 provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4")
        self.organization = config.get("organization")
        super().__init__(config)
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.OPENAI_GPT4
    
    def _get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            max_tokens=4096,
            context_window=8192,
            supports_streaming=True,
            supports_functions=True,
            cost_per_1k_tokens=0.03,
            task_strengths=[
                TaskType.SCHEMA_GENERATION,
                TaskType.CODE_GENERATION,
                TaskType.CRITIQUE,
                TaskType.DOCUMENTATION
            ],
            availability_score=0.95,
            latency_score=0.8
        )
    
    def _initialize(self):
        """Initialize OpenAI client"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        openai.api_key = self.api_key
        if self.organization:
            openai.organization = self.organization
        
        self.is_available = True
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API"""
        start_time = datetime.now()
        
        try:
            # Prepare messages
            messages = [{"role": "user", "content": request.prompt}]
            
            # Add context if provided
            if request.context:
                context_msg = f"Context: {request.context}"
                messages.insert(0, {"role": "system", "content": context_msg})
            
            # Make API call
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                max_tokens=request.max_tokens or self.capabilities.max_tokens,
                temperature=request.temperature,
                stream=False
            )
            
            # Extract response data
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
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
                    "finish_reason": response.choices[0].finish_reason,
                    "model_version": response.model
                }
            )
            
        except openai.error.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}", self.provider)
        except openai.error.InvalidRequestError as e:
            raise LLMError(f"Invalid OpenAI request: {str(e)}", self.provider)
        except openai.error.APIError as e:
            raise ModelUnavailableError(f"OpenAI API error: {str(e)}", self.provider)
        except Exception as e:
            raise LLMError(f"OpenAI generation failed: {str(e)}", self.provider)
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate response using OpenAI API"""
        try:
            # Prepare messages
            messages = [{"role": "user", "content": request.prompt}]
            
            if request.context:
                context_msg = f"Context: {request.context}"
                messages.insert(0, {"role": "system", "content": context_msg})
            
            # Make streaming API call
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                max_tokens=request.max_tokens or self.capabilities.max_tokens,
                temperature=request.temperature,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.get("content"):
                    yield chunk.choices[0].delta.content
                    
        except openai.error.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}", self.provider)
        except Exception as e:
            raise LLMError(f"OpenAI streaming failed: {str(e)}", self.provider)
    
    def _calculate_confidence(self, response: Any, request: LLMRequest) -> float:
        """Calculate confidence score based on response"""
        base_confidence = 0.8
        
        # Adjust based on finish reason
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "stop":
            confidence_adjustment = 0.0
        elif finish_reason == "length":
            confidence_adjustment = -0.1
        else:
            confidence_adjustment = -0.2
        
        # Adjust based on task complexity
        complexity_adjustment = {
            TaskComplexity.SIMPLE: 0.1,
            TaskComplexity.MEDIUM: 0.0,
            TaskComplexity.COMPLEX: -0.1,
            TaskComplexity.ENTERPRISE: -0.2
        }.get(request.complexity, 0.0)
        
        return max(0.1, min(1.0, base_confidence + confidence_adjustment + complexity_adjustment))
