"""
TRELLIS (Targeted Refinement of Emergent LLM Intelligence through Structured Segmentation) service.

Inspired by Oleve's approach to making AI predictable while keeping the magic.
"""

import re
from typing import List, Optional, Dict, Any
from uuid import uuid4

from packages.core.models import Intent, PIIEntity, TRELLISCluster
from packages.core.enums import ActType, Jurisdiction, PIIEntityType
from packages.pii.extractors import MultiLayerPIIExtractor
from packages.observability import get_logger

logger = get_logger(__name__)


class TRELLISIntentParser:
    """
    Targeted Refinement of Emergent LLM Intelligence through Structured Segmentation.
    
    Inspired by Oleve's approach to making AI predictable while keeping the magic.
    """
    
    def __init__(self):
        self.pii_extractor = MultiLayerPIIExtractor()
        self.clusters = self._initialize_clusters()
        self.deterministic_parsers = self._initialize_deterministic_parsers()
        self.llm_parser = None  # Will be injected
    
    def _initialize_clusters(self) -> Dict[str, TRELLISCluster]:
        """Initialize TRELLIS clusters for common intent patterns."""
        return {
            "procuracao_venda_imovel": TRELLISCluster(
                id="procuracao_venda_imovel",
                name="Procuração para Venda de Imóvel",
                description="Standard power of attorney for real estate sales",
                pattern=r".*(?:fazer|gerar|criar).*procura[çc][ãa]o.*(?:vender|venda).*im[óo]vel.*",
                confidence_threshold=0.9,
                sample_count=0,
                error_rate=0.0,
                is_active=True,
            ),
            "procuracao_geral": TRELLISCluster(
                id="procuracao_geral",
                name="Procuração Geral",
                description="General power of attorney",
                pattern=r".*(?:fazer|gerar|criar).*procura[çc][ãa]o.*geral.*",
                confidence_threshold=0.9,
                sample_count=0,
                error_rate=0.0,
                is_active=True,
            ),
            "escritura_compra_venda": TRELLISCluster(
                id="escritura_compra_venda",
                name="Escritura de Compra e Venda",
                description="Real estate purchase and sale deed",
                pattern=r".*(?:fazer|gerar|criar).*escritura.*(?:compra|venda).*",
                confidence_threshold=0.9,
                sample_count=0,
                error_rate=0.0,
                is_active=True,
            ),
        }
    
    def _initialize_deterministic_parsers(self) -> Dict[str, callable]:
        """Initialize deterministic parsers for high-confidence clusters."""
        return {
            "procuracao_venda_imovel": self._parse_procuracao_venda_imovel,
            "procuracao_geral": self._parse_procuracao_geral,
            "escritura_compra_venda": self._parse_escritura_compra_venda,
        }
    
    async def parse_intent(self, command: str) -> Intent:
        """
        Parse intent using TRELLIS framework.
        
        Args:
            command: Natural language command
            
        Returns:
            Parsed intent with PII entities
        """
        # 1. Check if command matches known cluster
        cluster = await self._classify_cluster(command)
        
        if cluster and cluster.confidence > 0.9:
            # Use deterministic parser for known pattern (fast, reliable)
            logger.info(f"Using deterministic parser for cluster: {cluster.id}")
            return await self.deterministic_parsers[cluster.id](command)
        
        # 2. Fall back to LLM for edge cases (flexible, magical)
        logger.info("Using LLM parser for edge case")
        intent = await self._llm_parse_intent(command)
        
        # 3. Log for future clustering
        await self._log_intent_for_clustering(command, intent, cluster)
        
        return intent
    
    async def _classify_cluster(self, command: str) -> Optional[TRELLISCluster]:
        """Classify command into a TRELLIS cluster."""
        command_lower = command.lower()
        
        for cluster in self.clusters.values():
            if not cluster.is_active:
                continue
            
            if re.search(cluster.pattern, command_lower, re.IGNORECASE):
                # Calculate confidence based on pattern match
                confidence = self._calculate_cluster_confidence(command, cluster)
                
                if confidence >= cluster.confidence_threshold:
                    return TRELLISCluster(
                        **cluster.dict(),
                        confidence=confidence
                    )
        
        return None
    
    def _calculate_cluster_confidence(self, command: str, cluster: TRELLISCluster) -> float:
        """Calculate confidence score for cluster classification."""
        # Simple confidence calculation based on pattern match
        # In production, this would use more sophisticated NLP
        
        command_lower = command.lower()
        pattern = cluster.pattern
        
        # Count keyword matches
        keywords = self._extract_keywords(pattern)
        matches = sum(1 for keyword in keywords if keyword in command_lower)
        
        # Calculate confidence based on match ratio
        confidence = matches / len(keywords) if keywords else 0.0
        
        # Boost confidence for exact pattern match
        if re.search(pattern, command_lower, re.IGNORECASE):
            confidence = min(1.0, confidence + 0.3)
        
        return confidence
    
    def _extract_keywords(self, pattern: str) -> List[str]:
        """Extract keywords from regex pattern."""
        # Simple keyword extraction
        # Remove regex syntax and extract meaningful words
        keywords = []
        
        # Remove regex syntax
        clean_pattern = re.sub(r'[.*+?^${}()|[\]\\]', ' ', pattern)
        clean_pattern = re.sub(r'\s+', ' ', clean_pattern)
        
        # Extract words
        words = clean_pattern.split()
        for word in words:
            if len(word) > 3:  # Only meaningful words
                keywords.append(word.lower())
        
        return keywords
    
    async def _parse_procuracao_venda_imovel(self, command: str) -> Intent:
        """Deterministic parser for real estate power of attorney."""
        # Extract PII entities
        pii_entities = await self.pii_extractor.extract(command)
        
        # Parse parties
        parties = []
        for i, entity in enumerate(pii_entities):
            if entity.type == PIIEntityType.NAME:
                parties.append({
                    "role": "outorgante" if i == 0 else "outorgado",
                    "pii_extracted": [entity.value]
                })
        
        # Extract jurisdiction (default to RJ)
        jurisdiction = self._extract_jurisdiction(command)
        
        return Intent(
            act_type=ActType.PROCURACAO,
            parties=parties,
            powers=["vender_imoveis"],
            jurisdiction=jurisdiction,
            confidence=0.95,
            intent_cluster="procuracao_venda_imovel",
            variables={"property_type": "imovel"},
            pii_entities=pii_entities,
            original_command=command,
        )
    
    async def _parse_procuracao_geral(self, command: str) -> Intent:
        """Deterministic parser for general power of attorney."""
        # Extract PII entities
        pii_entities = await self.pii_extractor.extract(command)
        
        # Parse parties
        parties = []
        for i, entity in enumerate(pii_entities):
            if entity.type == PIIEntityType.NAME:
                parties.append({
                    "role": "outorgante" if i == 0 else "outorgado",
                    "pii_extracted": [entity.value]
                })
        
        # Extract jurisdiction
        jurisdiction = self._extract_jurisdiction(command)
        
        return Intent(
            act_type=ActType.PROCURACAO,
            parties=parties,
            powers=["representacao_geral"],
            jurisdiction=jurisdiction,
            confidence=0.95,
            intent_cluster="procuracao_geral",
            variables={},
            pii_entities=pii_entities,
            original_command=command,
        )
    
    async def _parse_escritura_compra_venda(self, command: str) -> Intent:
        """Deterministic parser for real estate deed."""
        # Extract PII entities
        pii_entities = await self.pii_extractor.extract(command)
        
        # Parse parties
        parties = []
        for i, entity in enumerate(pii_entities):
            if entity.type == PIIEntityType.NAME:
                parties.append({
                    "role": "comprador" if i == 0 else "vendedor",
                    "pii_extracted": [entity.value]
                })
        
        # Extract jurisdiction
        jurisdiction = self._extract_jurisdiction(command)
        
        return Intent(
            act_type=ActType.ESCRITURA,
            parties=parties,
            powers=[],
            jurisdiction=jurisdiction,
            confidence=0.95,
            intent_cluster="escritura_compra_venda",
            variables={"transaction_type": "compra_venda"},
            pii_entities=pii_entities,
            original_command=command,
        )
    
    async def _llm_parse_intent(self, command: str, context: Optional[Dict] = None) -> Intent:
        """Fallback LLM parser using centralized LLM service."""
        import time
        from .llm import get_llm_service
        from ..prompts.intent_parsing import INTENT_PARSING_SYSTEM_PROMPT, INTENT_PARSING_USER_PROMPT
        from packages.core.models import LLMRequest
        
        llm_service = get_llm_service()
        
        # Render prompt with context
        user_prompt = INTENT_PARSING_USER_PROMPT.render(
            command=command,
            context=context
        )
        
        # Create LLM request
        llm_request = LLMRequest(
            messages=[
                {"role": "system", "content": INTENT_PARSING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Low temperature for structured output
            max_tokens=1000,
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        # Call LLM
        start_time = time.time()
        llm_response = await llm_service.call(llm_request)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Parse JSON response
        import json
        parsed = json.loads(llm_response.content)
        
        # Extract PII entities
        pii_entities = await self.pii_extractor.extract(command)
        
        # Build Intent object
        return Intent(
            act_type=ActType(parsed["act_type"]),
            parties=parsed["parties"],
            powers=parsed["powers"],
            jurisdiction=Jurisdiction(parsed["jurisdiction"]),
            confidence=parsed["confidence"],
            intent_cluster=None,  # LLM fallback, no cluster match
            variables=parsed.get("variables", {}),
            pii_entities=pii_entities,
            original_command=command,
            metadata={
                "llm_tokens": llm_response.usage.total_tokens,
                "llm_cost_usd": llm_response.cost_usd,
                "processing_time_ms": processing_time_ms
            }
        )
    
    def _extract_jurisdiction(self, command: str) -> Jurisdiction:
        """Extract jurisdiction from command."""
        command_lower = command.lower()
        
        if "sp" in command_lower or "são paulo" in command_lower:
            return Jurisdiction.SP
        elif "rj" in command_lower or "rio de janeiro" in command_lower:
            return Jurisdiction.RJ
        elif "mg" in command_lower or "minas gerais" in command_lower:
            return Jurisdiction.MG
        else:
            return Jurisdiction.RJ  # Default to RJ
    
    async def _log_intent_for_clustering(self, command: str, intent: Intent, cluster: Optional[TRELLISCluster]):
        """Log intent for future clustering analysis."""
        # This would log the intent for analysis and potential cluster creation
        logger.info(
            "Intent logged for clustering",
            command=command,
            act_type=intent.act_type.value,
            cluster_id=cluster.id if cluster else None,
            confidence=intent.confidence,
        )


class TRELLISService:
    """Main TRELLIS service for Intent Engine."""
    
    def __init__(self):
        self.parser = TRELLISIntentParser()
        self.analytics_service = None
    
    async def init(self):
        """Initialize analytics service."""
        from .trellis_analytics import TRELLISAnalyticsService
        self.analytics_service = TRELLISAnalyticsService()
        await self.analytics_service.init()
    
    async def parse_intent(self, command: str, user_id: str = "anonymous", session_id: str = "default") -> Intent:
        """Parse intent using TRELLIS framework with logging."""
        import time
        start_time = time.time()
        success = True
        error_type = None
        error_message = None
        intent = None
        cluster = None
        
        try:
            # 1. Check if command matches known cluster
            cluster = await self.parser._classify_cluster(command)
            
            if cluster and cluster.confidence > 0.9:
                # Use deterministic parser
                logger.info(f"Using deterministic parser for cluster: {cluster.id}")
                intent = await self.parser.deterministic_parsers[cluster.id](command)
            else:
                # Fall back to LLM
                logger.info("Using LLM parser for edge case")
                intent = await self.parser._llm_parse_intent(command)
            
        except Exception as e:
            success = False
            error_type = type(e).__name__
            error_message = str(e)
            raise
        finally:
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log interaction asynchronously (don't block on failure)
            if self.analytics_service:
                try:
                    await self.analytics_service.log_interaction(
                        user_id=user_id,
                        session_id=session_id,
                        original_command=command,
                        intent=intent if success else None,
                        cluster=cluster,
                        processing_time_ms=processing_time_ms,
                        success=success,
                        error_type=error_type,
                        error_message=error_message
                    )
                except Exception as log_error:
                    logger.warning("Failed to log interaction", error=str(log_error))
        
        return intent
    
    async def add_cluster(self, cluster: TRELLISCluster):
        """Add a new TRELLIS cluster."""
        self.parser.clusters[cluster.id] = cluster
        logger.info(f"Added new TRELLIS cluster: {cluster.id}")
    
    async def update_cluster(self, cluster_id: str, updates: Dict[str, Any]):
        """Update an existing TRELLIS cluster."""
        if cluster_id in self.parser.clusters:
            cluster = self.parser.clusters[cluster_id]
            for key, value in updates.items():
                setattr(cluster, key, value)
            logger.info(f"Updated TRELLIS cluster: {cluster_id}")
    
    async def get_clusters(self) -> List[TRELLISCluster]:
        """Get all TRELLIS clusters."""
        return list(self.parser.clusters.values())


# Global TRELLIS service instance
trellis_service: Optional[TRELLISService] = None


async def init_trellis():
    """Initialize TRELLIS service."""
    global trellis_service
    trellis_service = TRELLISService()
    await trellis_service.init()
    logger.info("TRELLIS service initialized")


def get_trellis_service() -> TRELLISService:
    """Get the global TRELLIS service instance."""
    if trellis_service is None:
        raise RuntimeError("TRELLIS service not initialized. Call init_trellis() first.")
    return trellis_service
