"""
Intelligent LLM Router and Orchestrator
Routes requests to optimal LLM based on task requirements and model capabilities
"""
import asyncio
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque

from .base import (
    LLMProvider, LLMRequest, LLMResponse, TaskType, TaskComplexity,
    BaseLLMProvider, LLMError, ModelUnavailableError, RateLimitError
)

logger = logging.getLogger(__name__)

@dataclass
class RoutingDecision:
    """Decision made by the router"""
    provider: LLMProvider
    confidence: float
    reasoning: str
    fallback_providers: List[LLMProvider]
    estimated_cost: float
    estimated_latency: float

@dataclass
class ProviderMetrics:
    """Metrics for a provider"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0
    total_latency: float = 0.0
    average_confidence: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    error_rate: float = 0.0
    availability_score: float = 1.0

class LLMRouter:
    """Intelligent router for LLM requests"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.metrics: Dict[LLMProvider, ProviderMetrics] = defaultdict(ProviderMetrics)
        self.request_history: deque = deque(maxlen=1000)
        self.routing_strategy = config.get("routing_strategy", "intelligent")
        self.cost_optimization = config.get("cost_optimization", True)
        self.max_retries = config.get("max_retries", 3)
        
        # Task-specific provider preferences
        self.task_preferences = {
            TaskType.SCHEMA_GENERATION: [
                LLMProvider.OPENAI_GPT4,
                LLMProvider.GOOGLE_GEMINI,
                LLMProvider.META_LLAMA
            ],
            TaskType.CODE_REVIEW: [
                LLMProvider.ANTHROPIC_CLAUDE,
                LLMProvider.OPENAI_GPT4,
                LLMProvider.GOOGLE_GEMINI
            ],
            TaskType.CODE_GENERATION: [
                LLMProvider.META_LLAMA,
                LLMProvider.OPENAI_GPT4,
                LLMProvider.GOOGLE_GEMINI
            ],
            TaskType.DATA_ANALYSIS: [
                LLMProvider.GOOGLE_GEMINI,
                LLMProvider.OPENAI_GPT4,
                LLMProvider.ANTHROPIC_CLAUDE
            ],
            TaskType.CRITIQUE: [
                LLMProvider.ANTHROPIC_CLAUDE,
                LLMProvider.OPENAI_GPT4
            ],
            TaskType.OPTIMIZATION: [
                LLMProvider.ANTHROPIC_CLAUDE,
                LLMProvider.GOOGLE_GEMINI,
                LLMProvider.OPENAI_GPT4
            ]
        }
    
    def register_provider(self, provider: BaseLLMProvider):
        """Register a new LLM provider"""
        self.providers[provider.provider] = provider
        logger.info(f"Registered LLM provider: {provider.provider.value}")
    
    async def route_request(self, request: LLMRequest) -> RoutingDecision:
        """Route a request to the optimal provider"""
        
        if self.routing_strategy == "round_robin":
            return self._route_round_robin(request)
        elif self.routing_strategy == "cost_optimized":
            return self._route_cost_optimized(request)
        elif self.routing_strategy == "performance_optimized":
            return self._route_performance_optimized(request)
        else:
            return await self._route_intelligent(request)
    
    async def _route_intelligent(self, request: LLMRequest) -> RoutingDecision:
        """Intelligent routing based on multiple factors"""
        
        # Get candidate providers
        candidates = self._get_candidate_providers(request)
        
        if not candidates:
            raise ModelUnavailableError("No available providers for request")
        
        # Score each candidate
        scored_candidates = []
        for provider_type in candidates:
            provider = self.providers.get(provider_type)
            if not provider or not provider.is_available:
                continue
            
            score = await self._calculate_provider_score(provider, request)
            scored_candidates.append((provider_type, provider, score))
        
        if not scored_candidates:
            raise ModelUnavailableError("No available providers for request")
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[2], reverse=True)
        
        # Select best provider
        best_provider_type, best_provider, best_score = scored_candidates[0]
        
        # Prepare fallback list
        fallback_providers = [p[0] for p in scored_candidates[1:3]]
        
        # Estimate cost and latency
        estimated_cost = best_provider.estimate_cost(
            request.max_tokens or best_provider.capabilities.max_tokens
        )
        estimated_latency = self._estimate_latency(best_provider, request)
        
        return RoutingDecision(
            provider=best_provider_type,
            confidence=best_score,
            reasoning=f"Selected {best_provider_type.value} based on task type, performance, and availability",
            fallback_providers=fallback_providers,
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency
        )
    
    def _get_candidate_providers(self, request: LLMRequest) -> List[LLMProvider]:
        """Get candidate providers for a request"""
        
        # Start with task-specific preferences
        candidates = self.task_preferences.get(request.task_type, [])
        
        # Add all available providers if no specific preferences
        if not candidates:
            candidates = list(self.providers.keys())
        
        # Filter by availability and capabilities
        filtered_candidates = []
        for provider_type in candidates:
            provider = self.providers.get(provider_type)
            if (provider and provider.is_available and 
                self._meets_requirements(provider, request)):
                filtered_candidates.append(provider_type)
        
        return filtered_candidates
    
    def _meets_requirements(self, provider: BaseLLMProvider, request: LLMRequest) -> bool:
        """Check if provider meets request requirements"""
        
        # Check token limits
        max_tokens = request.max_tokens or provider.capabilities.max_tokens
        if max_tokens > provider.capabilities.max_tokens:
            return False
        
        # Check streaming support if required
        if request.stream and not provider.capabilities.supports_streaming:
            return False
        
        return True
    
    async def _calculate_provider_score(
        self, 
        provider: BaseLLMProvider, 
        request: LLMRequest
    ) -> float:
        """Calculate a score for a provider for a specific request"""
        
        # Base score from task suitability
        task_score = provider.get_task_score(request.task_type, request.complexity)
        
        # Performance metrics
        metrics = self.metrics[provider.provider]
        
        # Availability score
        availability_score = metrics.availability_score
        
        # Error rate penalty
        error_penalty = metrics.error_rate * 0.5
        
        # Cost optimization (if enabled)
        cost_score = 1.0
        if self.cost_optimization:
            # Prefer cheaper providers for simple tasks
            if request.complexity in [TaskComplexity.SIMPLE, TaskComplexity.MEDIUM]:
                cost_score = 1.0 - (provider.capabilities.cost_per_1k_tokens / 0.1)
                cost_score = max(0.1, cost_score)
        
        # Latency score
        latency_score = provider.capabilities.latency_score
        
        # Recent performance
        recent_performance = self._get_recent_performance_score(provider.provider)
        
        # Combine scores with weights
        final_score = (
            task_score * 0.3 +
            availability_score * 0.2 +
            (1.0 - error_penalty) * 0.15 +
            cost_score * 0.15 +
            latency_score * 0.1 +
            recent_performance * 0.1
        )
        
        return max(0.0, min(1.0, final_score))
    
    def _get_recent_performance_score(self, provider: LLMProvider) -> float:
        """Get recent performance score for a provider"""
        
        # Look at last 10 requests for this provider
        recent_requests = [
            req for req in list(self.request_history)[-50:]
            if req.get("provider") == provider
        ]
        
        if not recent_requests:
            return 0.5  # Neutral score
        
        # Calculate success rate and average confidence
        successes = sum(1 for req in recent_requests if req.get("success", False))
        success_rate = successes / len(recent_requests)
        
        avg_confidence = sum(
            req.get("confidence", 0.5) for req in recent_requests
        ) / len(recent_requests)
        
        return (success_rate + avg_confidence) / 2
    
    def _route_round_robin(self, request: LLMRequest) -> RoutingDecision:
        """Simple round-robin routing"""
        available_providers = [
            p for p, provider in self.providers.items()
            if provider.is_available and self._meets_requirements(provider, request)
        ]
        
        if not available_providers:
            raise ModelUnavailableError("No available providers")
        
        # Simple round-robin selection
        selected = available_providers[len(self.request_history) % len(available_providers)]
        
        return RoutingDecision(
            provider=selected,
            confidence=0.5,
            reasoning="Round-robin selection",
            fallback_providers=available_providers[1:],
            estimated_cost=self.providers[selected].estimate_cost(
                request.max_tokens or 1000
            ),
            estimated_latency=100.0
        )
    
    def _route_cost_optimized(self, request: LLMRequest) -> RoutingDecision:
        """Cost-optimized routing"""
        candidates = self._get_candidate_providers(request)
        
        if not candidates:
            raise ModelUnavailableError("No available providers")
        
        # Sort by cost (lowest first)
        sorted_by_cost = sorted(
            candidates,
            key=lambda p: self.providers[p].capabilities.cost_per_1k_tokens
        )
        
        selected = sorted_by_cost[0]
        
        return RoutingDecision(
            provider=selected,
            confidence=0.7,
            reasoning="Cost-optimized selection",
            fallback_providers=sorted_by_cost[1:],
            estimated_cost=self.providers[selected].estimate_cost(
                request.max_tokens or 1000
            ),
            estimated_latency=150.0
        )
    
    def _route_performance_optimized(self, request: LLMRequest) -> RoutingDecision:
        """Performance-optimized routing"""
        candidates = self._get_candidate_providers(request)
        
        if not candidates:
            raise ModelUnavailableError("No available providers")
        
        # Sort by latency score (highest first)
        sorted_by_performance = sorted(
            candidates,
            key=lambda p: self.providers[p].capabilities.latency_score,
            reverse=True
        )
        
        selected = sorted_by_performance[0]
        
        return RoutingDecision(
            provider=selected,
            confidence=0.8,
            reasoning="Performance-optimized selection",
            fallback_providers=sorted_by_performance[1:],
            estimated_cost=self.providers[selected].estimate_cost(
                request.max_tokens or 1000
            ),
            estimated_latency=50.0
        )
    
    def _estimate_latency(self, provider: BaseLLMProvider, request: LLMRequest) -> float:
        """Estimate response latency for a request"""
        
        base_latency = 100.0 / provider.capabilities.latency_score
        
        # Adjust for token count
        token_count = request.max_tokens or 1000
        token_adjustment = token_count / 1000 * 50
        
        # Adjust for complexity
        complexity_adjustment = {
            TaskComplexity.SIMPLE: 0,
            TaskComplexity.MEDIUM: 25,
            TaskComplexity.COMPLEX: 50,
            TaskComplexity.ENTERPRISE: 100
        }.get(request.complexity, 25)
        
        return base_latency + token_adjustment + complexity_adjustment
    
    def update_metrics(
        self, 
        provider: LLMProvider, 
        request: LLMRequest, 
        response: Optional[LLMResponse], 
        error: Optional[Exception]
    ):
        """Update provider metrics after a request"""
        
        metrics = self.metrics[provider]
        metrics.total_requests += 1
        
        # Record request in history
        request_record = {
            "provider": provider,
            "task_type": request.task_type,
            "complexity": request.complexity,
            "timestamp": datetime.now(),
            "success": response is not None,
            "error": str(error) if error else None
        }
        
        if response:
            metrics.successful_requests += 1
            metrics.total_cost += response.cost
            metrics.total_latency += response.latency_ms
            metrics.last_success = datetime.now()
            request_record.update({
                "confidence": response.confidence,
                "cost": response.cost,
                "latency": response.latency_ms
            })
            
            # Update average confidence
            if metrics.successful_requests > 0:
                metrics.average_confidence = (
                    (metrics.average_confidence * (metrics.successful_requests - 1) + 
                     response.confidence) / metrics.successful_requests
                )
        else:
            metrics.failed_requests += 1
            metrics.last_failure = datetime.now()
        
        # Update error rate
        metrics.error_rate = metrics.failed_requests / metrics.total_requests
        
        # Update availability score based on recent performance
        recent_failures = sum(
            1 for req in list(self.request_history)[-20:]
            if req.get("provider") == provider and not req.get("success", True)
        )
        metrics.availability_score = max(0.1, 1.0 - (recent_failures / 20))
        
        self.request_history.append(request_record)
    
    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        
        stats = {}
        for provider_type, metrics in self.metrics.items():
            if metrics.total_requests > 0:
                stats[provider_type.value] = {
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.successful_requests / metrics.total_requests,
                    "error_rate": metrics.error_rate,
                    "average_cost": metrics.total_cost / max(1, metrics.successful_requests),
                    "average_latency": metrics.total_latency / max(1, metrics.successful_requests),
                    "average_confidence": metrics.average_confidence,
                    "availability_score": metrics.availability_score,
                    "last_success": metrics.last_success.isoformat() if metrics.last_success else None,
                    "last_failure": metrics.last_failure.isoformat() if metrics.last_failure else None
                }
        
        return stats
