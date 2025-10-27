"""
PII Vault storage service.
Orchestrates encryption, tokenization, and storage.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.vault import PIIRecord, PIIToken
from .encryption import EncryptionService
from .tokenizer import TokenizerService

logger = logging.getLogger(__name__)


class VaultService:
    """Main PII Vault service orchestrating all operations."""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.tokenizer_service = TokenizerService()
    
    async def store_pii(
        self,
        db: AsyncSession,
        pii_value: str,
        pii_type: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """
        Store PII value and return token.
        
        Args:
            db: Database session
            pii_value: The PII value to store
            pii_type: Type of PII
            tenant_id: Tenant ID
            user_id: User who stored it (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            Dict with record_id, token, and hash
        """
        # Generate hash for deduplication
        hash_value = self.encryption_service.hash_value(pii_value)
        
        # Check if this PII already exists for this tenant
        query = select(PIIRecord).where(
            and_(
                PIIRecord.tenant_id == tenant_id,
                PIIRecord.hash_value == hash_value,
                PIIRecord.pii_type == pii_type,
                PIIRecord.is_deleted == False
            )
        )
        result = await db.execute(query)
        existing_record = result.scalar_one_or_none()
        
        if existing_record:
            # Update access tracking
            existing_record.accessed_count += 1
            existing_record.last_accessed_at = datetime.utcnow()
            await db.commit()
            
            # Get existing token
            token_query = select(PIIToken).where(
                PIIToken.pii_record_id == existing_record.id
            )
            token_result = await db.execute(token_query)
            existing_token = token_result.scalar_one()
            
            logger.info(f"Reusing existing PII record: {existing_record.id}")
            
            return {
                "record_id": existing_record.id,
                "token": existing_token.token,
                "hash": hash_value,
                "reused": True
            }
        
        # Encrypt the PII value
        encrypted_value, encryption_key_id = self.encryption_service.encrypt(pii_value)
        
        # Create PII record
        record_id = str(uuid.uuid4())
        pii_record = PIIRecord(
            id=record_id,
            tenant_id=tenant_id,
            pii_type=pii_type,
            encrypted_value=encrypted_value,
            encryption_key_id=encryption_key_id,
            hash_value=hash_value,
            created_by=user_id,
            metadata_json=metadata or {},
            accessed_count=0,
        )
        
        db.add(pii_record)
        
        # Generate token
        token = self.tokenizer_service.generate_token(pii_value, pii_type, tenant_id)
        
        # Create token record
        token_record = PIIToken(
            id=str(uuid.uuid4()),
            token=token,
            pii_record_id=record_id,
            tenant_id=tenant_id,
            pii_type=pii_type,
            usage_count=0,
        )
        
        db.add(token_record)
        await db.commit()
        
        logger.info(f"Stored new PII record: {record_id}")
        
        return {
            "record_id": record_id,
            "token": token,
            "hash": hash_value,
            "reused": False
        }
    
    async def retrieve_pii(
        self,
        db: AsyncSession,
        token: str,
        tenant_id: str,
    ) -> Optional[str]:
        """
        Retrieve PII value by token.
        
        Args:
            db: Database session
            token: PII token
            tenant_id: Tenant ID for authorization
            
        Returns:
            Decrypted PII value or None if not found
        """
        # Validate token format
        if not self.tokenizer_service.validate_token_format(token):
            logger.warning(f"Invalid token format: {token}")
            return None
        
        # Get token record
        query = select(PIIToken).where(
            and_(
                PIIToken.token == token,
                PIIToken.tenant_id == tenant_id,
                PIIToken.is_active == True
            )
        )
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            logger.warning(f"Token not found or inactive: {token}")
            return None
        
        # Get PII record
        record_query = select(PIIRecord).where(
            and_(
                PIIRecord.id == token_record.pii_record_id,
                PIIRecord.is_deleted == False
            )
        )
        record_result = await db.execute(record_query)
        pii_record = record_result.scalar_one_or_none()
        
        if not pii_record:
            logger.warning(f"PII record not found: {token_record.pii_record_id}")
            return None
        
        # Update usage tracking
        token_record.usage_count += 1
        token_record.last_used_at = datetime.utcnow()
        pii_record.accessed_count += 1
        pii_record.last_accessed_at = datetime.utcnow()
        await db.commit()
        
        # Decrypt value
        decrypted_value = self.encryption_service.decrypt(
            pii_record.encrypted_value,
            pii_record.encryption_key_id
        )
        
        logger.info(f"Retrieved PII for token: {token}")
        
        return decrypted_value
    
    async def detokenize_batch(
        self,
        db: AsyncSession,
        tokens: List[str],
        tenant_id: str,
    ) -> Dict[str, Optional[str]]:
        """
        Detokenize multiple tokens at once.
        
        Args:
            db: Database session
            tokens: List of tokens to detokenize
            tenant_id: Tenant ID
            
        Returns:
            Dict mapping tokens to decrypted values
        """
        result = {}
        
        for token in tokens:
            value = await self.retrieve_pii(db, token, tenant_id)
            result[token] = value
        
        return result
    
    async def delete_pii(
        self,
        db: AsyncSession,
        token: str,
        tenant_id: str,
    ) -> bool:
        """
        Soft delete PII record.
        
        Args:
            db: Database session
            token: PII token
            tenant_id: Tenant ID
            
        Returns:
            True if deleted, False if not found
        """
        # Get token record
        query = select(PIIToken).where(
            and_(
                PIIToken.token == token,
                PIIToken.tenant_id == tenant_id
            )
        )
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            return False
        
        # Get PII record
        record_query = select(PIIRecord).where(
            PIIRecord.id == token_record.pii_record_id
        )
        record_result = await db.execute(record_query)
        pii_record = record_result.scalar_one_or_none()
        
        if pii_record:
            # Soft delete
            pii_record.is_deleted = True
            pii_record.deleted_at = datetime.utcnow()
        
        # Deactivate token
        token_record.is_active = False
        
        await db.commit()
        
        logger.info(f"Deleted PII for token: {token}")
        
        return True
    
    async def get_audit_log(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Get audit log for PII operations.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            limit: Number of records to return
            
        Returns:
            List of audit log entries
        """
        query = select(PIIRecord).where(
            PIIRecord.tenant_id == tenant_id
        ).order_by(PIIRecord.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        audit_log = []
        for record in records:
            audit_log.append({
                "record_id": record.id,
                "pii_type": record.pii_type,
                "created_at": record.created_at.isoformat(),
                "created_by": record.created_by,
                "accessed_count": record.accessed_count,
                "last_accessed_at": record.last_accessed_at.isoformat() if record.last_accessed_at else None,
                "is_deleted": record.is_deleted,
            })
        
        return audit_log

