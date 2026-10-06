"""
RTD/RCPJ central integration stub.
"""

import uuid
from typing import Dict, Any, Optional


class RTDPJCentralClient:
    """Client for RTD/RCPJ central (stub)."""
    
    def register(self, doc_pdf: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Register document.
        
        Args:
            doc_pdf: PDF bytes of the document
            metadata: Optional metadata
            
        Returns:
            Registration ID (GUID)
        """
        return str(uuid.uuid4())
    
    def status(self, registration_id: str) -> Dict[str, Any]:
        """
        Get registration status.
        
        Args:
            registration_id: Registration GUID
            
        Returns:
            Status dictionary
        """
        return {
            "registration_id": registration_id,
            "status": "registered",
            "protocol_number": None,
            "created_at": "2024-01-01T00:00:00Z",
        }

