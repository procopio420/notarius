"""
LLM service for Intent Engine using OpenAI with routing and cost management.
"""

import os
import time
from typing import List, Optional, Dict, Any
from uuid import UUID

import openai
from openai import AsyncOpenAI

from packages.core.models import LLMRequest, LLMResponse
from packages.core.enums import LLMProvider
from packages.observability import get_logger, get_metrics_collector
from packages.core.service_base import BaseService, ServiceManager, register_service

logger = get_logger(__name__)


class LLMRouter:
    """Route LLM requests based on cost, latency, and availability."""
    
    def __init__(self):
        self.providers = {
            LLMProvider.OPENAI: {
                "priority": 1,
                "max_cost_per_day": float(os.getenv("LLM_MAX_COST_PER_DAY", "100.0")),
                "max_tokens_per_request": int(os.getenv("LLM_MAX_TOKENS_PER_REQUEST", "4000")),
            },
            LLMProvider.AZURE_OPENAI: {
                "priority": 2,
                "max_cost_per_day": float(os.getenv("LLM_MAX_COST_PER_DAY", "100.0")),
                "max_tokens_per_request": int(os.getenv("LLM_MAX_TOKENS_PER_REQUEST", "4000")),
            },
            LLMProvider.LOCAL_LLAMA: {
                "priority": 3,
                "max_cost_per_day": 0.0,  # Free
                "max_tokens_per_request": 4000,
            }
        }
        
        self.daily_costs = {provider: 0.0 for provider in self.providers}
        self.metrics = get_metrics_collector("intent-engine")
    
    async def route_request(self, request: LLMRequest) -> LLMResponse:
        """Route request to appropriate LLM provider."""
        # Select provider based on priority and constraints
        provider = self._select_provider(request)
        
        # Route to selected provider
        if provider == LLMProvider.OPENAI:
            return await self._route_to_openai(request)
        elif provider == LLMProvider.AZURE_OPENAI:
            return await self._route_to_azure_openai(request)
        elif provider == LLMProvider.LOCAL_LLAMA:
            return await self._route_to_local_llama(request)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _select_provider(self, request: LLMRequest) -> LLMProvider:
        """Select the best provider for the request."""
        # Check daily cost limits
        for provider, config in self.providers.items():
            if self.daily_costs[provider] < config["max_cost_per_day"]:
                return provider
        
        # If all providers are over cost limit, use the one with lowest cost
        return min(self.providers.keys(), key=lambda p: self.daily_costs[p])
    
    async def _route_to_openai(self, request: LLMRequest) -> LLMResponse:
        """Route request to OpenAI."""
        start_time = time.time()
        
        try:
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = await client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": "You are a legal document parser. Extract structured data from natural language commands."},
                    {"role": "user", "content": request.prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            
            duration = time.time() - start_time
            
            # Calculate cost (simplified)
            cost = self._calculate_cost(request.model, response.usage.total_tokens)
            self.daily_costs[LLMProvider.OPENAI] += cost
            
            # Record metrics
            self.metrics.record_llm_request(
                provider="openai",
                model=request.model,
                duration=duration,
                tokens={
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                },
                cost=cost,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                model=request.model,
                provider="openai",
                latency_ms=int(duration * 1000),
                cost=cost,
                request_id=request.request_id,
            )
            
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            raise
    
    async def _route_to_azure_openai(self, request: LLMRequest) -> LLMResponse:
        """Route request to Azure OpenAI."""
        # Similar implementation to OpenAI but with Azure-specific configuration
        # For now, fallback to OpenAI
        return await self._route_to_openai(request)
    
    async def _route_to_local_llama(self, request: LLMRequest) -> LLMResponse:
        """Route request to local Llama model."""
        # This would integrate with a local Llama model
        # For now, return a mock response
        return LLMResponse(
            content="Mock response from local Llama model",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            model="llama-3.1-8b",
            provider="local_llama",
            latency_ms=1000,
            cost=0.0,
            request_id=request.request_id,
        )
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for OpenAI model usage."""
        # Simplified cost calculation
        # In production, this would use actual OpenAI pricing
        if "gpt-4" in model:
            return tokens * 0.00003  # $0.03 per 1K tokens
        elif "gpt-3.5" in model:
            return tokens * 0.000002  # $0.002 per 1K tokens
        else:
            return tokens * 0.00001  # Default rate


class LLMService(BaseService):
    """Main LLM service for Intent Engine."""
    
    def __init__(self, dependencies: Optional[Dict[str, Any]] = None):
        super().__init__(dependencies)
        self.router = LLMRouter()
        self.metrics = get_metrics_collector("intent-engine")
    
    async def parse_intent(self, command: str, tenant_id: str) -> Dict[str, Any]:
        """Parse natural language command into structured intent."""
        request = LLMRequest(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            prompt=f"""
Parse the following Brazilian notarial command into structured JSON:

Command: "{command}"

Return JSON with:
- act_type: "procuracao", "escritura", "autenticacao", etc.
- parties: [{{"role": "outorgante", "pii_extracted": ["name", "cpf"]}}]
- powers: ["vender_imoveis", "representacao_judicial", etc.]
- jurisdiction: "SP", "RJ", "MG", etc.
- confidence: 0.0-1.0

Use placeholders like {{PARTY_1_NAME}} for PII.
""",
            max_tokens=1000,
            temperature=0.1,
            tenant_id=tenant_id,
        )
        
        response = await self.router.route_request(request)
        
        # Parse JSON response
        import json
        try:
            intent_data = json.loads(response.content)
            return intent_data
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "act_type": "procuracao",
                "parties": [],
                "powers": [],
                "jurisdiction": "RJ",
                "confidence": 0.7,
            }
    
    async def generate_draft(self, intent: Dict[str, Any], template: str) -> str:
        """Generate legal draft from intent and template."""
        request = LLMRequest(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            prompt=f"""
Generate a legal document draft based on the intent and template:

Intent: {intent}
Template: {template}

Return the draft in Markdown format with placeholders for PII.
""",
            max_tokens=2000,
            temperature=0.3,
            tenant_id=intent.get("tenant_id", "default"),
        )
        
        response = await self.router.route_request(request)
        return response.content
    
    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini", 
                            temperature: float = 0.7, max_tokens: int = 2000, tenant_id: Optional[UUID] = None) -> str:
        """Simple chat completion interface for backward compatibility."""
        # Convert messages to a single prompt
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        # Use a default tenant_id if not provided (for backward compatibility)
        if tenant_id is None:
            import uuid
            tenant_id = uuid.UUID('00000000-0000-0000-0000-000000000000')  # Default UUID
        
        request = LLMRequest(
            provider=LLMProvider.OPENAI,
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            tenant_id=tenant_id,
        )
        
        response = await self.router.route_request(request)
        return response.content
    
    async def initialize(self) -> None:
        """Initialize the LLM service."""
        # LLM service doesn't require async initialization
        self._mark_initialized()
        self._mark_healthy()
        logger.info("LLM service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup LLM service resources."""
        # LLM service doesn't require cleanup
        logger.info("LLM service cleaned up")


# Service manager for LLM service
_service_manager = register_service(LLMService)


async def init_llm():
    """Initialize LLM service."""
    await _service_manager.initialize()
    logger.info("LLM service initialized")


def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    return _service_manager.get_instance()
