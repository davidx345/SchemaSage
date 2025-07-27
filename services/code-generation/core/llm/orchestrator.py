"""
Multi-LLM Orchestration Service
Orchestrates multiple LLM providers with intelligent routing and fallback
"""
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
import logging
from datetime import datetime

from .base import (
    LLMProvider, LLMRequest, LLMResponse, TaskType, TaskComplexity,
    LLMError, RateLimitError, ModelUnavailableError
)
from .router import LLMRouter, RoutingDecision
from .openai_provider import OpenAIProvider
from .claude_provider import ClaudeProvider
from .llama_provider import LlamaProvider
from .gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    """Orchestrates multiple LLM providers with intelligent routing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.router = LLMRouter(config.get("routing", {}))
        self.retry_attempts = config.get("retry_attempts", 3)
        self.fallback_enabled = config.get("fallback_enabled", True)
        
        # Initialize providers based on config
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured LLM providers"""
        
        provider_configs = self.config.get("providers", {})
        
        # Initialize OpenAI if configured
        if "openai" in provider_configs:
            try:
                openai_provider = OpenAIProvider(provider_configs["openai"])
                self.router.register_provider(openai_provider)
                logger.info("Initialized OpenAI provider")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        # Initialize Claude if configured
        if "anthropic" in provider_configs:
            try:
                claude_provider = ClaudeProvider(provider_configs["anthropic"])
                self.router.register_provider(claude_provider)
                logger.info("Initialized Claude provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Claude provider: {e}")
        
        # Initialize Llama if configured
        if "llama" in provider_configs:
            try:
                llama_provider = LlamaProvider(provider_configs["llama"])
                self.router.register_provider(llama_provider)
                logger.info("Initialized Llama provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Llama provider: {e}")
        
        # Initialize Gemini if configured
        if "gemini" in provider_configs:
            try:
                gemini_provider = GeminiProvider(provider_configs["gemini"])
                self.router.register_provider(gemini_provider)
                logger.info("Initialized Gemini provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using optimal provider with fallback"""
        
        # Route the request
        try:
            routing_decision = await self.router.route_request(request)
        except ModelUnavailableError as e:
            raise LLMError(f"No available providers for request: {e}")
        
        # Try primary provider
        primary_provider = self.router.providers[routing_decision.provider]
        
        for attempt in range(self.retry_attempts):
            try:
                response = await primary_provider.generate(request)
                
                # Update metrics
                self.router.update_metrics(
                    routing_decision.provider, request, response, None
                )
                
                logger.info(
                    f"Generated response using {routing_decision.provider.value} "
                    f"(attempt {attempt + 1})"
                )
                
                return response
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit for {routing_decision.provider.value}: {e}")
                
                # Try fallback if enabled and available
                if self.fallback_enabled and routing_decision.fallback_providers:
                    return await self._try_fallback_providers(
                        request, routing_decision.fallback_providers
                    )
                
                # Update metrics and re-raise
                self.router.update_metrics(
                    routing_decision.provider, request, None, e
                )
                raise
                
            except Exception as e:
                logger.error(
                    f"Error with {routing_decision.provider.value} "
                    f"(attempt {attempt + 1}): {e}"
                )
                
                # Update metrics
                self.router.update_metrics(
                    routing_decision.provider, request, None, e
                )
                
                # If this is the last attempt, try fallback
                if attempt == self.retry_attempts - 1:
                    if self.fallback_enabled and routing_decision.fallback_providers:
                        return await self._try_fallback_providers(
                            request, routing_decision.fallback_providers
                        )
                    else:
                        raise LLMError(f"All attempts failed: {e}")
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
        
        raise LLMError("Maximum retry attempts exceeded")
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate response using optimal provider"""
        
        # Route the request
        try:
            routing_decision = await self.router.route_request(request)
        except ModelUnavailableError as e:
            raise LLMError(f"No available providers for request: {e}")
        
        # Get the provider
        provider = self.router.providers[routing_decision.provider]
        
        try:
            async for chunk in provider.stream_generate(request):
                yield chunk
            
            # Update metrics (successful streaming)
            self.router.update_metrics(
                routing_decision.provider, request, 
                LLMResponse(
                    content="[streamed]",
                    provider=routing_decision.provider,
                    model=provider.model if hasattr(provider, 'model') else "unknown",
                    tokens_used=0,
                    cost=0.0,
                    latency_ms=0.0,
                    confidence=0.8
                ), 
                None
            )
            
        except Exception as e:
            # Update metrics (failed streaming)
            self.router.update_metrics(
                routing_decision.provider, request, None, e
            )
            raise LLMError(f"Streaming failed: {e}")
    
    async def _try_fallback_providers(
        self, 
        request: LLMRequest, 
        fallback_providers: List[LLMProvider]
    ) -> LLMResponse:
        """Try fallback providers in order"""
        
        for provider_type in fallback_providers:
            provider = self.router.providers.get(provider_type)
            if not provider or not provider.is_available:
                continue
            
            try:
                logger.info(f"Trying fallback provider: {provider_type.value}")
                response = await provider.generate(request)
                
                # Update metrics
                self.router.update_metrics(provider_type, request, response, None)
                
                logger.info(f"Fallback successful with {provider_type.value}")
                return response
                
            except Exception as e:
                logger.warning(f"Fallback provider {provider_type.value} failed: {e}")
                self.router.update_metrics(provider_type, request, None, e)
                continue
        
        raise LLMError("All fallback providers failed")
    
    async def batch_generate(
        self, 
        requests: List[LLMRequest]
    ) -> List[LLMResponse]:
        """Generate responses for multiple requests concurrently"""
        
        # Create tasks for concurrent execution
        tasks = [self.generate(request) for request in requests]
        
        # Execute with timeout
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to error responses
            results = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    error_response = LLMResponse(
                        content=f"Error: {str(response)}",
                        provider=LLMProvider.LOCAL_MODEL,  # Default for errors
                        model="error",
                        tokens_used=0,
                        cost=0.0,
                        latency_ms=0.0,
                        confidence=0.0,
                        metadata={"error": str(response)}
                    )
                    results.append(error_response)
                else:
                    results.append(response)
            
            return results
            
        except Exception as e:
            raise LLMError(f"Batch generation failed: {e}")
    
    async def get_optimal_provider(
        self, 
        task_type: TaskType, 
        complexity: TaskComplexity
    ) -> RoutingDecision:
        """Get the optimal provider for a task without executing"""
        
        request = LLMRequest(
            prompt="",  # Empty prompt for routing decision only
            task_type=task_type,
            complexity=complexity
        )
        
        return await self.router.route_request(request)
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        
        status = {}
        for provider_type, provider in self.router.providers.items():
            status[provider_type.value] = {
                "available": provider.is_available,
                "capabilities": {
                    "max_tokens": provider.capabilities.max_tokens,
                    "context_window": provider.capabilities.context_window,
                    "supports_streaming": provider.capabilities.supports_streaming,
                    "cost_per_1k_tokens": provider.capabilities.cost_per_1k_tokens,
                    "task_strengths": [t.value for t in provider.capabilities.task_strengths]
                }
            }
        
        return status
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing and performance statistics"""
        
        return {
            "provider_statistics": self.router.get_provider_statistics(),
            "total_requests": sum(
                metrics.total_requests 
                for metrics in self.router.metrics.values()
            ),
            "routing_strategy": self.router.routing_strategy,
            "fallback_enabled": self.fallback_enabled
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        
        health_status = {}
        
        for provider_type, provider in self.router.providers.items():
            try:
                is_healthy = await provider.health_check()
                health_status[provider_type.value] = {
                    "healthy": is_healthy,
                    "available": provider.is_available,
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health_status[provider_type.value] = {
                    "healthy": False,
                    "available": False,
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        
        return health_status

# Global orchestrator instance (will be initialized with config)
_orchestrator: Optional[LLMOrchestrator] = None

def get_orchestrator() -> LLMOrchestrator:
    """Get the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        raise RuntimeError("LLM orchestrator not initialized")
    return _orchestrator

def initialize_orchestrator(config: Dict[str, Any]):
    """Initialize the global orchestrator"""
    global _orchestrator
    _orchestrator = LLMOrchestrator(config)
    logger.info("LLM orchestrator initialized")

# Convenience functions
async def generate_with_llm(
    prompt: str,
    task_type: TaskType,
    complexity: TaskComplexity = TaskComplexity.MEDIUM,
    **kwargs
) -> LLMResponse:
    """Convenience function for generating with LLM"""
    
    request = LLMRequest(
        prompt=prompt,
        task_type=task_type,
        complexity=complexity,
        **kwargs
    )
    
    orchestrator = get_orchestrator()
    return await orchestrator.generate(request)
