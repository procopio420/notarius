"""
Template matching service for LexNode RAG.
Provides semantic search for legal document templates by type and jurisdiction.
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import LegalTemplate
from .embeddings import generate_embedding

logger = logging.getLogger(__name__)


class TemplateMatchingService:
    """Service for finding legal document templates by type and jurisdiction."""
    
    def __init__(self):
        self.embedding_model = "text-embedding-ada-002"
    
    async def find_template_by_type_and_jurisdiction(
        self,
        db: AsyncSession,
        document_type: str,
        jurisdiction: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find templates by document type and jurisdiction using hybrid search.
        
        Args:
            db: Database session
            document_type: Type of document (e.g., "procuracao_venda_imovel")
            jurisdiction: Legal jurisdiction (e.g., "SP", "RJ")
            limit: Maximum number of results
            
        Returns:
            List of template dictionaries with relevance scores
        """
        try:
            # First, try exact matches
            exact_query = select(LegalTemplate).where(
                and_(
                    LegalTemplate.document_type == document_type,
                    LegalTemplate.jurisdiction == jurisdiction,
                    LegalTemplate.is_active == True
                )
            ).order_by(LegalTemplate.relevance_score.desc()).limit(limit)
            
            exact_results = await db.execute(exact_query)
            exact_templates = exact_results.scalars().all()
            
            if exact_templates:
                return [self._template_to_dict(t) for t in exact_templates]
            
            # If no exact matches, try semantic search
            return await self._semantic_template_search(
                db, document_type, jurisdiction, limit
            )
            
        except Exception as e:
            logger.error(f"Template search failed: {e}", exc_info=True)
            return []
    
    async def _semantic_template_search(
        self,
        db: AsyncSession,
        document_type: str,
        jurisdiction: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Perform semantic search for templates."""
        try:
            # Create search query
            search_query = f"{document_type} {jurisdiction} template modelo"
            
            # Get embedding for search query
            query_embedding = await generate_embedding(search_query)
            
            # Search for similar templates using vector similarity
            # Note: This assumes we have a vector similarity function in the database
            # For now, we'll do a text-based search as fallback
            similar_query = select(LegalTemplate).where(
                and_(
                    or_(
                        LegalTemplate.document_type.ilike(f"%{document_type}%"),
                        LegalTemplate.template_content.ilike(f"%{document_type}%")
                    ),
                    LegalTemplate.jurisdiction == jurisdiction,
                    LegalTemplate.is_active == True
                )
            ).order_by(LegalTemplate.relevance_score.desc()).limit(limit)
            
            results = await db.execute(similar_query)
            templates = results.scalars().all()
            
            return [self._template_to_dict(t) for t in templates]
            
        except Exception as e:
            logger.error(f"Semantic template search failed: {e}", exc_info=True)
            return []
    
    def _template_to_dict(self, template: LegalTemplate) -> Dict[str, Any]:
        """Convert LegalTemplate model to dictionary."""
        return {
            "id": str(template.id),
            "document_type": template.document_type,
            "jurisdiction": template.jurisdiction,
            "template_content": template.template_content,
            "schema": template.schema,
            "metadata": template.metadata_json,
            "source_url": template.source_url,
            "relevance_score": template.relevance_score,
            "created_at": template.created_at.isoformat() if template.created_at else None,
        }
    
    async def index_template(
        self,
        db: AsyncSession,
        document_type: str,
        jurisdiction: str,
        template_content: str,
        schema: Dict[str, Any],
        metadata: Dict[str, Any],
        source_url: str,
        relevance_score: float = 0.8
    ) -> LegalTemplate:
        """Index a new template in the database."""
        try:
            # Get embedding for the template content
            template_embedding = await generate_embedding(template_content)
            
            # Create new template
            template = LegalTemplate(
                document_type=document_type,
                jurisdiction=jurisdiction,
                template_content=template_content,
                schema=schema,
                metadata_json=metadata,
                source_url=source_url,
                relevance_score=relevance_score,
                embedding=template_embedding,
                is_active=True
            )
            
            db.add(template)
            await db.commit()
            await db.refresh(template)
            
            logger.info(f"Indexed template: {document_type} for {jurisdiction}")
            return template
            
        except Exception as e:
            logger.error(f"Template indexing failed: {e}", exc_info=True)
            await db.rollback()
            raise


# Global service instance
template_matcher = TemplateMatchingService()
