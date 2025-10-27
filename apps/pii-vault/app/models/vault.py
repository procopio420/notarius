"""
PII Vault database models.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PIIRecord(Base):
    """Encrypted PII record storage."""
    
    __tablename__ = "pii_records"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    pii_type = Column(String(50), nullable=False)  # cpf, cnpj, nome, etc.
    encrypted_value = Column(Text, nullable=False)
    encryption_key_id = Column(String(255), nullable=False)
    hash_value = Column(String(64), nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)
    accessed_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Audit
    metadata_json = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)


class PIIToken(Base):
    """PII token mapping."""
    
    __tablename__ = "pii_tokens"
    
    id = Column(String(36), primary_key=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    pii_record_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    pii_type = Column(String(50), nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
