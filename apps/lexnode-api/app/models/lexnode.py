"""
LexNode database models using SQLAlchemy with pgvector support.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import pgvector extension
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class LegalDocument(Base):
    """Model for legal documents."""
    
    __tablename__ = "legal_documents"
    
    id = Column(String(255), primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String(50), nullable=True, index=True)
    url = Column(Text, nullable=True)
    document_type = Column(String(50), nullable=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="RJ")
    embedding = Column(Vector(1536), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_jurisdiction_type', 'jurisdiction', 'document_type'),
        Index('idx_indexed_at', 'indexed_at'),
        Index('idx_metadata_gin', 'metadata_json', postgresql_using='gin'),
    )


class LegalChunk(Base):
    """Model for legal document chunks with embeddings."""
    
    __tablename__ = "legal_chunks"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    section_id = Column(String(50), nullable=True, index=True)  # "art_123_p2_item_a"
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-small dimension
    metadata_json = Column(JSONB, nullable=True)  # {act_type: "procuracao", jurisdiction: "SP"}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_document_section', 'document_id', 'section_id'),
        Index('idx_embedding_cosine', 'embedding', postgresql_using='ivfflat'),
        Index('idx_metadata_json_gin', 'metadata_json', postgresql_using='gin'),
    )


class CrawlJob(Base):
    """Model for crawl jobs."""
    
    __tablename__ = "crawl_jobs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name = Column(String(50), nullable=False, index=True)  # "cnj", "cgj_rj"
    base_url = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, index=True)  # "pending", "running", "completed", "failed"
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    documents_found = Column(Integer, default=0)
    documents_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_crawl_job_source_status', 'source_name', 'status'),
        Index('idx_crawl_job_created_at', 'created_at'),
    )


class CrawlLog(Base):
    """Model for crawl operation logs."""
    
    __tablename__ = "crawl_logs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    url = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    content_length = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_crawl_log_job_created', 'job_id', 'created_at'),
        Index('idx_crawl_log_status_code', 'status_code'),
    )


class RetrievalLog(Base):
    """Model for retrieval operation logs."""
    
    __tablename__ = "retrieval_logs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    query = Column(Text, nullable=False)
    jurisdiction = Column(String(10), nullable=True, index=True)
    act_type = Column(String(50), nullable=True, index=True)
    results_count = Column(Integer, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    confidence_score = Column(Integer, nullable=True)  # Average confidence * 100
    user_feedback = Column(String(20), nullable=True)  # "positive", "negative", "neutral"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_retrieval_log_jurisdiction_act', 'jurisdiction', 'act_type'),
        Index('idx_retrieval_log_created_at', 'created_at'),
        Index('idx_retrieval_log_user_feedback', 'user_feedback'),
    )


class LegalTemplate(Base):
    """Model for legal document templates."""
    
    __tablename__ = "legal_templates"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_type = Column(String(100), nullable=False, index=True)  # "procuracao_venda_imovel"
    jurisdiction = Column(String(10), nullable=False, index=True)  # "SP", "RJ"
    template_content = Column(Text, nullable=False)  # The actual template text
    schema = Column(JSONB, nullable=True)  # Variable schema definition
    metadata_json = Column(JSONB, nullable=True)  # Additional metadata
    source_url = Column(Text, nullable=True)  # URL where template was found
    relevance_score = Column(Float, nullable=False, default=0.8)  # 0.0 to 1.0
    embedding = Column(Vector(1536), nullable=True)  # For semantic search
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_template_type_jurisdiction', 'document_type', 'jurisdiction'),
        Index('idx_template_active', 'is_active'),
        Index('idx_template_relevance', 'relevance_score'),
        Index('idx_template_embedding', 'embedding', postgresql_using='ivfflat'),
    )


class LegalRule(Base):
    """Model for legal rules with citations and checklist items."""
    
    __tablename__ = "legal_rules"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    fonte = Column(String(100), nullable=False, index=True)  # "Lei 6.015/73", "CNJ Provimento X", "CGJ/SP"
    artigo = Column(String(50), nullable=True, index=True)  # "Art. 123", "Art. 123, §2º"
    provimento = Column(String(100), nullable=True)  # "Provimento CNJ 123/2024"
    data = Column(DateTime, nullable=True, index=True)  # Effective date
    uf = Column(String(2), nullable=True, index=True)  # State jurisdiction (SP, RJ, etc.)
    document_types = Column(JSONB, nullable=True)  # ["escritura_compra_venda", "registro_compra_venda_ri"]
    checklist_items = Column(JSONB, nullable=True)  # ["Certidão de matrícula (<=30 dias)", "ITBI quitado"]
    citation = Column(Text, nullable=False)  # "Lei 6.015/73, Art. 123"
    precedence = Column(String(20), nullable=False, index=True, default="federal")  # "federal", "state", "internal"
    content = Column(Text, nullable=False)  # Full rule text
    embedding = Column(Vector(1536), nullable=True)  # For semantic search
    metadata_json = Column(JSONB, nullable=True)  # Additional metadata
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_rule_fonte_artigo', 'fonte', 'artigo'),
        Index('idx_rule_doctype', 'document_types', postgresql_using='gin'),  # GIN for JSONB queries
        Index('idx_rule_uf', 'uf'),  # B-tree for VARCHAR equality queries
        Index('idx_rule_precedence', 'precedence'),
        Index('idx_rule_active', 'is_active'),
        Index('idx_rule_embedding', 'embedding', postgresql_using='ivfflat'),
    )
