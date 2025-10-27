"""
Hybrid retrieval service combining BM25 and vector search.
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
import numpy as np

from ..models.lexnode import LegalDocument
from .embeddings import generate_embedding, cosine_similarity

logger = logging.getLogger(__name__)


class RetrievalService:
    """Hybrid retrieval with BM25 and semantic search."""
    
    def __init__(self):
        self.bm25_weight = 0.4
        self.semantic_weight = 0.6
    
    async def retrieve(
        self,
        db: AsyncSession,
        query: str,
        jurisdiction: str = "RJ",
        document_types: Optional[List[str]] = None,
        limit: int = 10,
        min_score: float = 0.3,
    ) -> List[Dict]:
        """
        Hybrid retrieval combining keyword and semantic search.
        
        Args:
            db: Database session
            query: Search query
            jurisdiction: Legal jurisdiction
            document_types: Filter by document types
            limit: Maximum results to return
            min_score: Minimum relevance score
            
        Returns:
            Ranked list of relevant documents
        """
        logger.info(f"Retrieving documents for query: {query[:100]}")
        
        # Get BM25 results (keyword search)
        bm25_results = await self._bm25_search(
            db, query, jurisdiction, document_types, limit * 2
        )
        
        # Get semantic results (vector search)
        semantic_results = await self._semantic_search(
            db, query, jurisdiction, document_types, limit * 2
        )
        
        # Merge and re-rank
        merged_results = self._merge_and_rerank(
            bm25_results,
            semantic_results,
            limit,
            min_score
        )
        
        # Package with citations
        packaged_results = self._package_citations(merged_results)
        
        logger.info(f"Retrieved {len(packaged_results)} documents")
        
        return packaged_results
    
    async def _bm25_search(
        self,
        db: AsyncSession,
        query: str,
        jurisdiction: str,
        document_types: Optional[List[str]],
        limit: int
    ) -> List[Dict]:
        """
        BM25 keyword search.
        """
        # Build query
        stmt = select(LegalDocument).where(
            LegalDocument.jurisdiction == jurisdiction
        )
        
        if document_types:
            stmt = stmt.where(LegalDocument.document_type.in_(document_types))
        
        # Simple keyword matching (full-text search would be better)
        query_terms = query.lower().split()
        
        # Filter by keyword presence
        conditions = []
        for term in query_terms:
            conditions.append(LegalDocument.content.ilike(f"%{term}%"))
        
        if conditions:
            stmt = stmt.where(or_(*conditions))
        
        stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # Calculate BM25 scores (simplified)
        scored_docs = []
        for doc in documents:
            score = self._calculate_bm25_score(query_terms, doc.content)
            scored_docs.append({
                "document": doc,
                "bm25_score": score,
                "semantic_score": 0.0,  # Will be filled later
            })
        
        # Sort by BM25 score
        scored_docs.sort(key=lambda x: x["bm25_score"], reverse=True)
        
        return scored_docs
    
    async def _semantic_search(
        self,
        db: AsyncSession,
        query: str,
        jurisdiction: str,
        document_types: Optional[List[str]],
        limit: int
    ) -> List[Dict]:
        """
        Semantic vector search.
        """
        # Generate query embedding
        query_embedding = await generate_embedding(query)
        
        # Get all documents (in production, use pgvector for efficient search)
        stmt = select(LegalDocument).where(
            LegalDocument.jurisdiction == jurisdiction
        )
        
        if document_types:
            stmt = stmt.where(LegalDocument.document_type.in_(document_types))
        
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # Calculate cosine similarity
        scored_docs = []
        for doc in documents:
            if doc.embedding is not None and len(doc.embedding) > 0:
                try:
                    # Convert to list if it's not already
                    doc_embedding = list(doc.embedding) if not isinstance(doc.embedding, list) else doc.embedding
                    similarity = cosine_similarity(query_embedding, doc_embedding)
                    scored_docs.append({
                        "document": doc,
                        "bm25_score": 0.0,  # Will be filled later
                        "semantic_score": similarity,
                    })
                except Exception as e:
                    logger.warning(f"Failed to calculate similarity for doc {doc.id}: {e}")
        
        # Sort by semantic score
        scored_docs.sort(key=lambda x: x["semantic_score"], reverse=True)
        
        return scored_docs[:limit]
    
    def _calculate_bm25_score(self, query_terms: List[str], content: str) -> float:
        """
        Calculate simplified BM25 score.
        (Simplified version - production would use proper BM25)
        """
        content_lower = content.lower()
        
        # Count term frequencies
        score = 0.0
        for term in query_terms:
            tf = content_lower.count(term)
            if tf > 0:
                # Simplified BM25: log(1 + tf)
                score += np.log(1 + tf)
        
        # Normalize by query length
        if query_terms:
            score /= len(query_terms)
        
        return score
    
    def _merge_and_rerank(
        self,
        bm25_results: List[Dict],
        semantic_results: List[Dict],
        limit: int,
        min_score: float
    ) -> List[Dict]:
        """
        Merge BM25 and semantic results with hybrid scoring.
        """
        # Create dict of document ID to scores
        doc_scores = {}
        
        # Add BM25 scores
        for result in bm25_results:
            doc_id = result["document"].id
            doc_scores[doc_id] = {
                "document": result["document"],
                "bm25_score": result["bm25_score"],
                "semantic_score": 0.0
            }
        
        # Add/update with semantic scores
        for result in semantic_results:
            doc_id = result["document"].id
            if doc_id in doc_scores:
                doc_scores[doc_id]["semantic_score"] = result["semantic_score"]
            else:
                doc_scores[doc_id] = {
                    "document": result["document"],
                    "bm25_score": 0.0,
                    "semantic_score": result["semantic_score"]
                }
        
        # Calculate hybrid scores
        scored_docs = []
        for doc_id, scores in doc_scores.items():
            hybrid_score = (
                self.bm25_weight * scores["bm25_score"] +
                self.semantic_weight * scores["semantic_score"]
            )
            
            if hybrid_score >= min_score:
                scored_docs.append({
                    "document": scores["document"],
                    "bm25_score": scores["bm25_score"],
                    "semantic_score": scores["semantic_score"],
                    "hybrid_score": hybrid_score,
                })
        
        # Sort by hybrid score
        scored_docs.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return scored_docs[:limit]
    
    def _package_citations(self, scored_docs: List[Dict]) -> List[Dict]:
        """
        Package results as legal citations.
        """
        citations = []
        
        for result in scored_docs:
            doc = result["document"]
            
            citation = {
                "id": doc.id,
                "source": doc.title,
                "relevance": float(result["hybrid_score"]),
                "excerpt": doc.summary or doc.content[:300],
                "url": doc.url,
                "type": doc.document_type,
                "jurisdiction": doc.jurisdiction,
                "metadata": doc.metadata_json or {},
                "scores": {
                    "bm25": float(result["bm25_score"]),
                    "semantic": float(result["semantic_score"]),
                    "hybrid": float(result["hybrid_score"]),
                }
            }
            
            citations.append(citation)
        
        return citations

