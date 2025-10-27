"""
Document indexing service with BM25 and vector search.
"""

import logging
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ..models.lexnode import LegalDocument
from .embeddings import generate_embedding

logger = logging.getLogger(__name__)


class IndexerService:
    """Indexes legal documents for hybrid search."""
    
    async def index_document(
        self,
        db: AsyncSession,
        document: Dict
    ) -> str:
        """
        Index a single document.
        
        Args:
            db: Database session
            document: Normalized document to index
            
        Returns:
            Document ID
        """
        logger.info(f"Indexing document: {document.get('id')}")
        
        # Generate embedding for semantic search
        content_for_embedding = self._prepare_content_for_embedding(document)
        embedding = await generate_embedding(content_for_embedding)
        
        # Create or update legal document record
        doc_id = document.get("id") or str(uuid.uuid4())
        
        # Check if document exists
        query = select(LegalDocument).where(LegalDocument.id == doc_id)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.title = document.get("title")
            existing.content = document.get("content")
            existing.summary = document.get("summary")
            existing.embedding = embedding
            existing.metadata_json = document.get("metadata", {})
            logger.info(f"Updated existing document: {doc_id}")
        else:
            # Create new
            legal_doc = LegalDocument(
                id=doc_id,
                title=document.get("title"),
                content=document.get("content"),
                summary=document.get("summary"),
                embedding=embedding,
                source=document.get("source"),
                url=document.get("url"),
                document_type=document.get("type"),
                jurisdiction=document.get("jurisdiction", "RJ"),
                metadata_json=document.get("metadata", {}),
            )
            db.add(legal_doc)
            logger.info(f"Created new document: {doc_id}")
        
        await db.commit()
        
        return doc_id
    
    async def index_batch(
        self,
        db: AsyncSession,
        documents: List[Dict]
    ) -> List[str]:
        """
        Index multiple documents.
        
        Args:
            db: Database session
            documents: List of normalized documents
            
        Returns:
            List of document IDs
        """
        logger.info(f"Batch indexing {len(documents)} documents")
        
        doc_ids = []
        
        for document in documents:
            try:
                doc_id = await self.index_document(db, document)
                doc_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Failed to index document {document.get('id')}: {e}")
                # Continue with next document
        
        logger.info(f"Successfully indexed {len(doc_ids)}/{len(documents)} documents")
        
        return doc_ids
    
    def _prepare_content_for_embedding(self, document: Dict) -> str:
        """
        Prepare document content for embedding.
        Combines title, summary, and key content.
        """
        parts = []
        
        if document.get("title"):
            parts.append(document["title"])
        
        if document.get("summary"):
            parts.append(document["summary"])
        
        # Add first 500 chars of content
        if document.get("content"):
            parts.append(document["content"][:500])
        
        return " ".join(parts)
    
    async def delete_document(
        self,
        db: AsyncSession,
        document_id: str
    ) -> bool:
        """
        Delete document from index.
        
        Args:
            db: Database session
            document_id: Document ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        query = select(LegalDocument).where(LegalDocument.id == document_id)
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if document:
            await db.delete(document)
            await db.commit()
            logger.info(f"Deleted document: {document_id}")
            return True
        
        return False

