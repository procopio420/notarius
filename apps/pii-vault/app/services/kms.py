"""
KMS (Key Management Service) integration for PII encryption.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional

import boto3
from cryptography.fernet import Fernet
from google.cloud import kms

from packages.core.exceptions import VaultException


class KMSProvider(ABC):
    """Abstract base class for KMS providers."""
    
    @abstractmethod
    async def encrypt(self, plaintext: bytes, key_id: str) -> bytes:
        """Encrypt plaintext using the specified key."""
        pass
    
    @abstractmethod
    async def decrypt(self, ciphertext: bytes, key_id: str) -> bytes:
        """Decrypt ciphertext using the specified key."""
        pass
    
    @abstractmethod
    async def generate_data_key(self, key_id: str) -> tuple[bytes, bytes]:
        """Generate a data encryption key."""
        pass


class LocalKMSProvider(KMSProvider):
    """Local KMS provider using Fernet for development."""
    
    def __init__(self, key_id: str = "dev-key"):
        self.key_id = key_id
        # Generate or load key from environment
        key = os.getenv("FERNET_KEY")
        if not key:
            key = Fernet.generate_key()
            print(f"Generated Fernet key: {key.decode()}")
            print("Set FERNET_KEY environment variable for production")
        
        self.fernet = Fernet(key)
    
    async def encrypt(self, plaintext: bytes, key_id: str) -> bytes:
        """Encrypt using Fernet."""
        if key_id != self.key_id:
            raise VaultException(f"Unknown key ID: {key_id}")
        
        return self.fernet.encrypt(plaintext)
    
    async def decrypt(self, ciphertext: bytes, key_id: str) -> bytes:
        """Decrypt using Fernet."""
        if key_id != self.key_id:
            raise VaultException(f"Unknown key ID: {key_id}")
        
        return self.fernet.decrypt(ciphertext)
    
    async def generate_data_key(self, key_id: str) -> tuple[bytes, bytes]:
        """Generate a data encryption key."""
        if key_id != self.key_id:
            raise VaultException(f"Unknown key ID: {key_id}")
        
        # For local development, just return the same key
        key = Fernet.generate_key()
        return key, key


class AWSKMSProvider(KMSProvider):
    """AWS KMS provider."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.client = boto3.client('kms', region_name=region)
    
    async def encrypt(self, plaintext: bytes, key_id: str) -> bytes:
        """Encrypt using AWS KMS."""
        try:
            response = self.client.encrypt(
                KeyId=key_id,
                Plaintext=plaintext
            )
            return response['CiphertextBlob']
        except Exception as e:
            raise VaultException(f"AWS KMS encryption failed: {e}")
    
    async def decrypt(self, ciphertext: bytes, key_id: str) -> bytes:
        """Decrypt using AWS KMS."""
        try:
            response = self.client.decrypt(
                CiphertextBlob=ciphertext,
                KeyId=key_id
            )
            return response['Plaintext']
        except Exception as e:
            raise VaultException(f"AWS KMS decryption failed: {e}")
    
    async def generate_data_key(self, key_id: str) -> tuple[bytes, bytes]:
        """Generate a data encryption key using AWS KMS."""
        try:
            response = self.client.generate_data_key(
                KeyId=key_id,
                KeySpec='AES_256'
            )
            return response['Plaintext'], response['CiphertextBlob']
        except Exception as e:
            raise VaultException(f"AWS KMS data key generation failed: {e}")


class GCPKMSProvider(KMSProvider):
    """Google Cloud KMS provider."""
    
    def __init__(self, project_id: str, location: str = "global"):
        self.project_id = project_id
        self.location = location
        self.client = kms.KeyManagementServiceClient()
    
    async def encrypt(self, plaintext: bytes, key_id: str) -> bytes:
        """Encrypt using Google Cloud KMS."""
        try:
            key_name = self.client.crypto_key_path(
                self.project_id, self.location, "notarius", key_id
            )
            
            response = self.client.encrypt(
                request={
                    "name": key_name,
                    "plaintext": plaintext
                }
            )
            return response.ciphertext
        except Exception as e:
            raise VaultException(f"GCP KMS encryption failed: {e}")
    
    async def decrypt(self, ciphertext: bytes, key_id: str) -> bytes:
        """Decrypt using Google Cloud KMS."""
        try:
            key_name = self.client.crypto_key_path(
                self.project_id, self.location, "notarius", key_id
            )
            
            response = self.client.decrypt(
                request={
                    "name": key_name,
                    "ciphertext": ciphertext
                }
            )
            return response.plaintext
        except Exception as e:
            raise VaultException(f"GCP KMS decryption failed: {e}")
    
    async def generate_data_key(self, key_id: str) -> tuple[bytes, bytes]:
        """Generate a data encryption key using Google Cloud KMS."""
        try:
            key_name = self.client.crypto_key_path(
                self.project_id, self.location, "notarius", key_id
            )
            
            response = self.client.generate_random_bytes(
                request={
                    "name": key_name,
                    "length_bytes": 32
                }
            )
            return response.data, response.data
        except Exception as e:
            raise VaultException(f"GCP KMS data key generation failed: {e}")


class KMSManager:
    """KMS manager for handling multiple providers."""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = None
    
    def add_provider(self, name: str, provider: KMSProvider, is_default: bool = False):
        """Add a KMS provider."""
        self.providers[name] = provider
        if is_default:
            self.default_provider = provider
    
    def get_provider(self, name: Optional[str] = None) -> KMSProvider:
        """Get a KMS provider by name or default."""
        if name:
            if name not in self.providers:
                raise VaultException(f"Unknown KMS provider: {name}")
            return self.providers[name]
        
        if not self.default_provider:
            raise VaultException("No default KMS provider configured")
        
        return self.default_provider


# Global KMS manager instance
kms_manager = KMSManager()


async def init_kms():
    """Initialize KMS providers based on configuration."""
    provider_type = os.getenv("KMS_PROVIDER", "local")
    key_id = os.getenv("KMS_KEY_ID", "dev-key")
    
    if provider_type == "local":
        provider = LocalKMSProvider(key_id)
        kms_manager.add_provider("local", provider, is_default=True)
    
    elif provider_type == "aws":
        region = os.getenv("AWS_REGION", "us-east-1")
        provider = AWSKMSProvider(region)
        kms_manager.add_provider("aws", provider, is_default=True)
    
    elif provider_type == "gcp":
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise VaultException("GCP_PROJECT_ID environment variable required")
        
        location = os.getenv("GCP_LOCATION", "global")
        provider = GCPKMSProvider(project_id, location)
        kms_manager.add_provider("gcp", provider, is_default=True)
    
    else:
        raise VaultException(f"Unknown KMS provider: {provider_type}")


def get_kms_provider(name: Optional[str] = None) -> KMSProvider:
    """Get a KMS provider instance."""
    return kms_manager.get_provider(name)
