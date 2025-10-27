"""
Core domain models as Pydantic schemas.

These models are shared between Django (converted to ORM) and FastAPI services.
They ensure type safety and consistency across all services in the monorepo.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

from .enums import (
    ActType,
    AuditAction,
    DocumentStatus,
    Jurisdiction,
    PartyRole,
    PIIEntityType,
)


class BaseModelWithTimestamps(BaseModel):
    """Base model with created_at and updated_at timestamps."""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PIIEntity(BaseModel):
    """Represents a PII entity extracted from text."""
    
    type: PIIEntityType
    value: str
    start: int
    end: int
    confidence: float = Field(ge=0.0, le=1.0)
    context: Optional[str] = None
    
    @validator('value')
    def validate_value(cls, v, values):
        """Validate PII value based on type."""
        if 'type' not in values:
            return v
            
        pii_type = values['type']
        
        if pii_type == PIIEntityType.CPF:
            # Basic CPF format validation
            import re
            if not re.match(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', v):
                raise ValueError('Invalid CPF format')
        elif pii_type == PIIEntityType.CNPJ:
            # Basic CNPJ format validation
            import re
            if not re.match(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', v):
                raise ValueError('Invalid CNPJ format')
        elif pii_type == PIIEntityType.EMAIL:
            # Basic email validation
            import re
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
                raise ValueError('Invalid email format')
                
        return v


class TokenResult(BaseModel):
    """Result of PII tokenization."""
    
    token: str = Field(..., description="Token handle like 'token://party_1_cpf/<uuid>'")
    hash: str = Field(..., description="SHA256 hash for cache keys")
    scope: str = Field(..., description="PII scope like 'cpf', 'name'")
    ttl_days: Optional[int] = Field(None, description="Time to live in days")


class Party(BaseModel):
    """Represents a party in a notarial act."""
    
    id: UUID
    role: PartyRole
    # PII stored as tokens (no raw sensitive data)
    nome_token: str
    cpf_token: Optional[str] = None
    cnpj_token: Optional[str] = None
    endereco_token: Optional[str] = None
    telefone_token: Optional[str] = None
    email_token: Optional[str] = None
    # Non-sensitive metadata
    tipo_pessoa: str = Field(..., description="pf or pj")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Clause(BaseModel):
    """Represents a legal clause with grounding."""
    
    id: UUID
    title: str
    content: str
    citations: List['Citation']
    confidence: float = Field(ge=0.0, le=1.0)
    act_type: ActType
    jurisdiction: Jurisdiction
    is_required: bool = False
    conditions: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Represents a legal citation with provenance."""
    
    uri: str = Field(..., description="Source URL")
    anchor: str = Field(..., description="Article/section reference")
    title: str = Field(..., description="Document title")
    effective_date: datetime
    status: str = Field(..., description="active, revoked, superseded")
    jurisdiction: Jurisdiction
    doc_type: str = Field(..., description="resolution, norm, manual")
    snippet: str = Field(..., description="Relevant text snippet")
    score: float = Field(ge=0.0, le=1.0, description="Relevance score")


class Intent(BaseModel):
    """Represents a parsed user intent."""
    
    act_type: ActType
    parties: List[Party]
    powers: List[str] = Field(default_factory=list)
    jurisdiction: Jurisdiction
    confidence: float = Field(ge=0.0, le=1.0)
    intent_cluster: Optional[str] = Field(None, description="TRELLIS cluster ID")
    variables: Dict[str, Any] = Field(default_factory=dict)
    pii_entities: List[PIIEntity] = Field(default_factory=list)
    original_command: str


class Draft(BaseModel):
    """Represents a generated legal draft."""
    
    id: UUID
    act_type: ActType
    jurisdiction: Jurisdiction
    content_md: str = Field(..., description="Markdown content with placeholders")
    variables_json: Dict[str, str] = Field(..., description="PII tokens mapping")
    citations: List[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    skeleton_cache_key: str = Field(..., description="Cache key for legal skeleton")
    generated_by: str = Field(..., description="ai or humano")
    template_version: str
    lexnode_trace: Dict[str, Any] = Field(default_factory=dict)


class Act(BaseModel):
    """Represents a notarial act."""
    
    id: UUID
    act_type: ActType
    jurisdiction: Jurisdiction
    status: DocumentStatus
    parties: List[Party]
    draft: Optional[Draft] = None
    final_document_id: Optional[UUID] = None
    created_by: UUID
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CacheKey(BaseModel):
    """Represents a cache key for different strategies."""
    
    strategy: str = Field(..., description="skeleton, embedding, template, citation")
    key: str = Field(..., description="HMAC hash of relevant parameters")
    ttl_seconds: int = Field(..., description="Time to live in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TRELLISCluster(BaseModel):
    """Represents a TRELLIS intent cluster."""
    
    id: str
    name: str
    description: str
    pattern: str = Field(..., description="Regex or pattern for matching")
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.9)
    sample_count: int = Field(ge=0, description="Number of samples in cluster")
    error_rate: float = Field(ge=0.0, le=1.0, description="Current error rate")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class AuditEvent(BaseModel):
    """Represents an audit event."""
    
    id: UUID
    tenant_id: UUID
    actor_id: Optional[UUID] = None
    resource_type: str
    resource_id: UUID
    action: AuditAction
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    diff_json: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
    pii_touched: bool = Field(False, description="Whether PII was accessed")


class LLMRequest(BaseModel):
    """Represents an LLM request for routing and monitoring."""
    
    provider: str
    model: str
    prompt: str
    max_tokens: int
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    tenant_id: UUID
    estimated_cost: Optional[float] = None
    request_id: UUID = Field(default_factory=UUID)


class LLMResponse(BaseModel):
    """Represents an LLM response."""
    
    content: str
    usage: Dict[str, int] = Field(..., description="Token usage stats")
    model: str
    provider: str
    latency_ms: int
    cost: Optional[float] = None
    request_id: UUID


class FeedbackLog(BaseModel):
    """Represents user feedback for continuous learning."""
    
    id: UUID
    tenant_id: UUID
    minuta_id: UUID
    original_text: str
    edited_text: str
    edit_type: str = Field(..., description="grammar, legal, factual, style")
    section: str = Field(..., description="Which section was edited")
    confidence_before: float = Field(ge=0.0, le=1.0)
    confidence_after: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: UUID


# Update forward references
Clause.model_rebuild()
Draft.model_rebuild()
Act.model_rebuild()
