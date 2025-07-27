"""
Google Gemini Provider Implementation
"""
import google.generativeai as genai
from typing import Dict, Any, AsyncGenerator
import logging
from datetime import datetime

from .base import (
    BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse, 
    ModelCapabilities, TaskType, TaskComplexity,
    LLMError, RateLimitError, QuotaExceededError, ModelUnavailableError
)

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.model_name = config.get("model", "gemini-pro")
        super().__init__(config)
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.GOOGLE_GEMINI
    
    def _get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            max_tokens=8192,
            context_window=32768,
            supports_streaming=True,
            supports_functions=True,
            cost_per_1k_tokens=0.0005,
            task_strengths=[
                TaskType.DATA_ANALYSIS,
                TaskType.SCHEMA_GENERATION,
                TaskType.CODE_GENERATION,
                TaskType.OPTIMIZATION
            ],
            availability_score=0.90,
            latency_score=0.85
        )
    
    def _initialize(self):
        """Initialize Gemini client"""
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.is_available = True
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini API"""
        start_time = datetime.now()
        
        try:
            # Prepare prompt with context
            full_prompt = request.prompt
            if request.context:
                full_prompt = f"Context: {request.context}\n\n{request.prompt}"
            
            # Configure generation
            generation_config = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens or self.capabilities.max_tokens,
            }
            
            # Make API call
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            
            # Extract response data
            content = response.text
            
            # Estimate tokens (Gemini doesn't provide exact count)
            tokens_used = len(content.split()) + len(full_prompt.split())
            
            # Calculate metrics
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            cost = self.estimate_cost(tokens_used)
            confidence = self._calculate_confidence(response, request)
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=self.model_name,
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                confidence=confidence,
                metadata={
                    "finish_reason": getattr(response, 'finish_reason', 'stop'),
                    "model_version": self.model_name
                }
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                raise RateLimitError(f"Gemini rate limit exceeded: {str(e)}", self.provider)
            elif "not found" in error_msg or "unavailable" in error_msg:
                raise ModelUnavailableError(f"Gemini model unavailable: {str(e)}", self.provider)
            else:
                raise LLMError(f"Gemini generation failed: {str(e)}", self.provider)
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate response using Gemini API"""
        try:
            # Prepare prompt with context
            full_prompt = request.prompt
            if request.context:
                full_prompt = f"Context: {request.context}\n\n{request.prompt}"
            
            # Configure generation
            generation_config = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens or self.capabilities.max_tokens,
            }
            
            # Make streaming API call
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                raise RateLimitError(f"Gemini rate limit exceeded: {str(e)}", self.provider)
            else:
                raise LLMError(f"Gemini streaming failed: {str(e)}", self.provider)
    
    def _calculate_confidence(self, response: Any, request: LLMRequest) -> float:
        """Calculate confidence score based on response"""
        base_confidence = 0.82
        
        # Adjust based on response characteristics
        content_length = len(response.text) if hasattr(response, 'text') else 0
        if content_length < 10:
            confidence_adjustment = -0.3
        elif content_length > 1000:
            confidence_adjustment = 0.1
        else:
            confidence_adjustment = 0.0
        
        # Adjust based on task complexity
        complexity_adjustment = {
            TaskComplexity.SIMPLE: 0.15,
            TaskComplexity.MEDIUM: 0.05,
            TaskComplexity.COMPLEX: -0.05,
            TaskComplexity.ENTERPRISE: -0.15
        }.get(request.complexity, 0.0)
        
        return max(0.1, min(1.0, base_confidence + confidence_adjustment + complexity_adjustment))
