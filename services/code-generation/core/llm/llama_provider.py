"""
Meta Llama Provider Implementation (Local/Offline)
"""
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, AsyncGenerator
import logging
from datetime import datetime

from .base import (
    BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse, 
    ModelCapabilities, TaskType, TaskComplexity,
    LLMError, ModelUnavailableError
)

logger = logging.getLogger(__name__)

class LlamaProvider(BaseLLMProvider):
    """Meta Llama provider for local/offline generation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.model_path = config.get("model_path")
        self.executable_path = config.get("executable_path", "llama-cpp-python")
        self.max_context = config.get("max_context", 4096)
        super().__init__(config)
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.META_LLAMA
    
    def _get_capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            max_tokens=2048,
            context_window=self.max_context,
            supports_streaming=True,
            supports_functions=False,
            cost_per_1k_tokens=0.0,  # Local model, no cost
            task_strengths=[
                TaskType.CODE_GENERATION,
                TaskType.SCHEMA_GENERATION,
                TaskType.DOCUMENTATION
            ],
            availability_score=0.99,  # Always available if installed
            latency_score=0.6  # Slower than cloud models
        )
    
    def _initialize(self):
        """Initialize local Llama model"""
        if not self.model_path or not os.path.exists(self.model_path):
            raise ValueError(f"Llama model path not found: {self.model_path}")
        
        # Test if executable is available
        try:
            subprocess.run([self.executable_path, "--version"], 
                         capture_output=True, check=True)
            self.is_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Llama executable not found, provider unavailable")
            self.is_available = False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using local Llama model"""
        start_time = datetime.now()
        
        try:
            # Prepare prompt with context
            full_prompt = request.prompt
            if request.context:
                full_prompt = f"Context: {request.context}\n\n{request.prompt}"
            
            # Prepare command arguments
            cmd_args = [
                self.executable_path,
                "--model", self.model_path,
                "--prompt", full_prompt,
                "--max-tokens", str(request.max_tokens or self.capabilities.max_tokens),
                "--temperature", str(request.temperature),
                "--ctx-size", str(self.max_context)
            ]
            
            # Run model
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise ModelUnavailableError(f"Llama execution failed: {result.stderr}")
            
            # Parse output
            content = result.stdout.strip()
            
            # Estimate tokens (rough approximation)
            tokens_used = len(content.split()) + len(full_prompt.split())
            
            # Calculate metrics
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            cost = 0.0  # Local model, no cost
            confidence = self._calculate_confidence(content, request)
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model="llama-local",
                tokens_used=tokens_used,
                cost=cost,
                latency_ms=latency_ms,
                confidence=confidence,
                metadata={
                    "model_path": self.model_path,
                    "execution_time": latency_ms
                }
            )
            
        except subprocess.TimeoutExpired:
            raise LLMError("Llama generation timed out", self.provider)
        except Exception as e:
            raise LLMError(f"Llama generation failed: {str(e)}", self.provider)
    
    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream generate response using local Llama model"""
        # For simplicity, we'll simulate streaming by yielding chunks
        response = await self.generate(request)
        
        # Split response into chunks and yield
        words = response.content.split()
        chunk_size = 5
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            if i + chunk_size < len(words):
                chunk += " "
            yield chunk
    
    def _calculate_confidence(self, content: str, request: LLMRequest) -> float:
        """Calculate confidence score based on content quality"""
        base_confidence = 0.7
        
        # Simple heuristics for confidence
        if len(content) < 10:
            confidence_adjustment = -0.3
        elif len(content) > 1000:
            confidence_adjustment = 0.1
        else:
            confidence_adjustment = 0.0
        
        # Adjust based on task complexity
        complexity_adjustment = {
            TaskComplexity.SIMPLE: 0.2,
            TaskComplexity.MEDIUM: 0.0,
            TaskComplexity.COMPLEX: -0.2,
            TaskComplexity.ENTERPRISE: -0.3
        }.get(request.complexity, 0.0)
        
        return max(0.1, min(1.0, base_confidence + confidence_adjustment + complexity_adjustment))
