"""
Retrieval endpoints for LexNode RAG service.
"""

import logging
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.database import get_db
from ..services.retrieval import RetrievalService
from ..services.template_matcher import template_matcher

router = APIRouter()
logger = logging.getLogger(__name__)


class RetrieveRequest(BaseModel):
    """Request model for document retrieval."""
    query: str = Field(..., description="Search query")
    constraints: Optional[dict] = Field(None, description="Search constraints")
    top_k: int = Field(10, description="Number of results to return")


class RetrieveResponse(BaseModel):
    """Response model for document retrieval."""
    hits: List[dict] = Field(..., description="Search results")
    trace: dict = Field(..., description="Search trace information")


class GroundedDraftRequest(BaseModel):
    """Request model for grounded draft generation."""
    act_type: str = Field(..., description="Type of legal act")
    variables: dict = Field(..., description="Template variables")
    constraints: Optional[dict] = Field(None, description="Search constraints")


class GroundedDraftResponse(BaseModel):
    """Response model for grounded draft generation."""
    sections: List[dict] = Field(..., description="Draft sections")
    confidence: float = Field(..., description="Overall confidence score")
    trace: dict = Field(..., description="Generation trace information")


# Initialize retrieval service
retrieval_service = RetrievalService()


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(
    request: RetrieveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve legal documents using hybrid search."""
    start_time = time.time()
    
    try:
        # Extract constraints
        jurisdiction = request.constraints.get("jurisdiction", "RJ") if request.constraints else "RJ"
        document_types = request.constraints.get("document_types") if request.constraints else None
        
        # Perform hybrid retrieval
        results = await retrieval_service.retrieve(
            db=db,
            query=request.query,
            jurisdiction=jurisdiction,
            document_types=document_types,
            limit=request.top_k
        )
        
        # Record metrics
        duration = time.time() - start_time
        
        logger.info(
            f"Document retrieval completed: {len(results)} results in {duration:.2f}s"
        )
        
        return RetrieveResponse(
            hits=results,
            trace={
                "query": request.query,
                "search_time_ms": int(duration * 1000),
                "jurisdiction": jurisdiction,
                "results_count": len(results),
            }
        )
        
    except Exception as e:
        logger.error(f"Document retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Retrieval failed")


@router.post("/grounded-draft", response_model=GroundedDraftResponse)
async def generate_grounded_draft(
    request: GroundedDraftRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a grounded legal draft with citations."""
    start_time = time.time()
    metrics = get_metrics_collector()
    correlation_id = get_correlation_id()
    
    try:
        # Extract constraints
        jurisdiction = request.constraints.get("jurisdiction", "RJ") if request.constraints else "RJ"
        act_type = request.act_type
        
        # Generate draft sections with citations
        sections = await _generate_draft_sections(
            db=db,
            act_type=act_type,
            variables=request.variables,
            jurisdiction=jurisdiction
        )
        
        # Calculate overall confidence
        confidence = sum(section.get("confidence", 0) for section in sections) / len(sections) if sections else 0
        
        # Record metrics
        duration = time.time() - start_time
        metrics.record_lexnode_retrieve(jurisdiction, act_type, duration, confidence)
        
        logger.info(
            "Grounded draft generation completed",
            act_type=act_type,
            jurisdiction=jurisdiction,
            sections_count=len(sections),
            confidence=confidence,
            duration=duration,
            correlation_id=correlation_id,
        )
        
        return GroundedDraftResponse(
            sections=sections,
            confidence=confidence,
            trace={
                "retrieval_time_ms": int(duration * 1000),
                "generation_time_ms": int(duration * 1000),
                "jurisdiction": jurisdiction,
                "act_type": act_type,
            }
        )
        
    except Exception as e:
        # Record error metrics
        metrics.record_error("grounded_draft_error")
        
        logger.error(
            "Grounded draft generation failed",
            error=str(e),
            act_type=request.act_type,
            correlation_id=correlation_id,
        )
        
        raise HTTPException(status_code=500, detail="Grounded draft generation failed")


async def _hybrid_search(
    db: AsyncSession,
    query: str,
    query_embedding: List[float],
    jurisdiction: str,
    act_type: str,
    top_k: int
) -> List[dict]:
    """Perform hybrid search using vector similarity + BM25."""
    # This is a simplified implementation
    # In production, this would use pgvector for similarity search and PostgreSQL full-text search for BM25
    
    # Mock results for now
    results = [
        {
            "doc_id": "doc_1",
            "section_id": "art_678_p3",
            "snippet": "O procurador tem poderes para representar o outorgante em atos de venda de imóveis...",
            "citation": {
                "uri": "https://www.tjrj.jus.br/resolucao-678",
                "anchor": "Art. 678, §3º",
                "title": "Código de Normas CGJ-RJ",
                "effective_date": "2023-03-15",
                "status": "active"
            },
            "score": 0.92
        },
        {
            "doc_id": "doc_2", 
            "section_id": "art_123_p1",
            "snippet": "A procuração deve conter a qualificação completa das partes...",
            "citation": {
                "uri": "https://www.tjrj.jus.br/resolucao-123",
                "anchor": "Art. 123, §1º",
                "title": "Código de Normas CGJ-RJ",
                "effective_date": "2023-01-10",
                "status": "active"
            },
            "score": 0.88
        }
    ]
    
    return results[:top_k]


async def _generate_draft_sections(
    db: AsyncSession,
    act_type: str,
    variables: dict,
    jurisdiction: str
) -> List[dict]:
    """Generate draft sections with citations."""
    # This is a simplified implementation
    # In production, this would use templates and real legal content
    
    if act_type == "procuracao":
        sections = [
            {
                "title": "Qualificação",
                "content_md": "**OUTORGANTE:** {{PARTY_1_NAME}}, {{PARTY_1_CPF}}, residente e domiciliado em {{PARTY_1_ADDRESS}}.\n\n**OUTORGADO:** {{PARTY_2_NAME}}, {{PARTY_2_CPF}}, residente e domiciliado em {{PARTY_2_ADDRESS}}.",
                "citations": [
                    {
                        "uri": "https://www.tjrj.jus.br/resolucao-123",
                        "anchor": "Art. 123, §1º",
                        "title": "Código de Normas CGJ-RJ",
                        "effective_date": "2023-01-10",
                        "status": "active"
                    }
                ],
                "confidence": 0.95
            },
            {
                "title": "Poderes Outorgados",
                "content_md": "O OUTORGANTE outorga ao OUTORGADO poderes para:\n\n1. Representar o outorgante em atos de venda de imóveis;\n2. Assinar contratos de compra e venda;\n3. Receber valores decorrentes das transações.",
                "citations": [
                    {
                        "uri": "https://www.tjrj.jus.br/resolucao-678",
                        "anchor": "Art. 678, §3º",
                        "title": "Código de Normas CGJ-RJ",
                        "effective_date": "2023-03-15",
                        "status": "active"
                    }
                ],
                "confidence": 0.88
            }
        ]
    else:
        sections = [
            {
                "title": "Conteúdo",
                "content_md": "Conteúdo do documento {{act_type}} conforme legislação aplicável.",
                "citations": [],
                "confidence": 0.7
            }
        ]
    
    return sections


class RetrieveTemplateRequest(BaseModel):
    """Request model for template retrieval."""
    document_type: str = Field(..., description="Type of document (e.g., 'procuracao_venda_imovel')")
    jurisdiction: str = Field(..., description="Legal jurisdiction (e.g., 'SP', 'RJ')")
    constraints: Optional[dict] = Field(None, description="Additional constraints")
    limit: int = Field(5, description="Maximum number of templates to return")


class RetrieveTemplateResponse(BaseModel):
    """Response model for template retrieval."""
    templates: List[dict] = Field(..., description="Found templates")
    trace: dict = Field(..., description="Search trace information")


@router.post("/retrieve-template", response_model=RetrieveTemplateResponse)
async def retrieve_template(
    request: RetrieveTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve legal document templates by type and jurisdiction."""
    start_time = time.time()
    
    try:
        # Find templates using template matcher
        templates = await template_matcher.find_template_by_type_and_jurisdiction(
            db=db,
            document_type=request.document_type,
            jurisdiction=request.jurisdiction,
            limit=request.limit
        )
        
        # Record metrics
        duration = time.time() - start_time
        
        logger.info(
            f"Template retrieval completed: {len(templates)} templates found in {duration:.2f}s"
        )
        
        return RetrieveTemplateResponse(
            templates=templates,
            trace={
                "document_type": request.document_type,
                "jurisdiction": request.jurisdiction,
                "search_time_ms": int(duration * 1000),
                "templates_found": len(templates),
            }
        )
        
    except Exception as e:
        logger.error(f"Template retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Template retrieval failed")
