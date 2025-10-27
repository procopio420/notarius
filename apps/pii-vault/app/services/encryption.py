"""
PII encryption service with KMS support.
"""

import os
import hashlib
import base64
import logging
from typing import Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class EncryptionService:
    """Handles PII encryption and decryption with KMS support."""
    
    def __init__(self):
        self.kms_provider = os.getenv("KMS_PROVIDER", "local")
        self.kms_key_id = os.getenv("KMS_KEY_ID", "dev-key")
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption keys."""
        if self.kms_provider == "local":
            # For local development, use a deterministic key
            self._local_key = self._derive_key_from_id(self.kms_key_id)
            logger.info("Encryption initialized with local KMS")
        elif self.kms_provider == "aws":
            # AWS KMS integration would go here
            logger.info("Encryption initialized with AWS KMS")
        elif self.kms_provider == "gcp":
            # GCP KMS integration would go here
            logger.info("Encryption initialized with GCP KMS")
        else:
            raise ValueError(f"Unsupported KMS provider: {self.kms_provider}")
    
    def _derive_key_from_id(self, key_id: str) -> bytes:
        """Derive encryption key from key ID."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'notarius-pii-vault-salt',  # In production, use proper salt management
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(key_id.encode()))
    
    def encrypt(self, plaintext: str) -> Tuple[str, str]:
        """
        Encrypt PII value.
        
        Returns:
            Tuple of (encrypted_value, encryption_key_id)
        """
        if self.kms_provider == "local":
            fernet = Fernet(self._local_key)
            encrypted = fernet.encrypt(plaintext.encode())
            return base64.b64encode(encrypted).decode(), self.kms_key_id
        else:
            # KMS encryption would go here
            raise NotImplementedError(f"KMS provider {self.kms_provider} not yet implemented")
    
    def decrypt(self, encrypted_value: str, encryption_key_id: str) -> str:
        """
        Decrypt PII value.
        
        Args:
            encrypted_value: Base64-encoded encrypted value
            encryption_key_id: KMS key ID used for encryption
            
        Returns:
            Decrypted plaintext value
        """
        if self.kms_provider == "local":
            # Verify key ID matches
            if encryption_key_id != self.kms_key_id:
                logger.warning(f"Key ID mismatch: {encryption_key_id} != {self.kms_key_id}")
                # In production, this should fetch the correct key
            
            fernet = Fernet(self._local_key)
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        else:
            # KMS decryption would go here
            raise NotImplementedError(f"KMS provider {self.kms_provider} not yet implemented")
    
    def hash_value(self, value: str) -> str:
        """
        Create deterministic hash of PII value for lookups.
        
        Args:
            value: PII value to hash
            
        Returns:
            SHA-256 hash of the value
        """
        return hashlib.sha256(value.encode()).hexdigest()
    
    def rotate_key(self, old_key_id: str, new_key_id: str):
        """
        Rotate encryption keys.
        This would decrypt with old key and re-encrypt with new key.
        """
        raise NotImplementedError("Key rotation not yet implemented")

