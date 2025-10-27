"""
Document rewrite service for Intent Engine.
Provides AI-powered document content rewriting and improvement.
"""

import logging
import re
import time
import os
from typing import Dict, Any, Optional

from packages.core.service_base import BaseService, ServiceManager, register_service
from .llm import get_llm_service

logger = logging.getLogger(__name__)


class DocumentRewriteService(BaseService):
    """Service for rewriting and improving document content using AI."""
    
    def __init__(self, dependencies: Optional[Dict[str, Any]] = None):
        super().__init__(dependencies)
        # LLM service will be initialized when needed
    
    async def rewrite_content(
        self,
        content: str,
        improvement_prompt: str,
        document_type: str,
        preserve_variables: bool = True,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rewrite document content using AI based on improvement prompt.
        
        Args:
            content: Original document content
            improvement_prompt: User's improvement request
            document_type: Type of document (e.g., 'procuracao', 'escritura')
            preserve_variables: Whether to preserve {{VARIABLE}} placeholders
            tenant_id: Tenant ID for tracking
            user_id: User ID for tracking
            
        Returns:
            Dict with rewritten content, confidence, and metadata
        """
        try:
            # Extract variables if we need to preserve them
            variables = {}
            if preserve_variables:
                variables = self._extract_variables(content)
                logger.info(f"Extracted {len(variables)} variables to preserve")
            
            # Create the prompt
            prompt = self._build_rewrite_prompt(
                content, improvement_prompt, document_type, variables
            )
            
            # Use LLM service with routing and cost management
            start_time = time.time()
            llm_service = get_llm_service()
            
            messages = [
                {"role": "system", "content": "You are a legal document expert specializing in Brazilian notarial documents."},
                {"role": "user", "content": prompt}
            ]
            
            rewritten_content = await llm_service.chat_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=3000
            )
            
            duration = time.time() - start_time
            
            # Restore variables if needed
            if preserve_variables and variables:
                rewritten_content = self._restore_variables(rewritten_content, variables)
                logger.info("Restored variables in rewritten content")
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence_from_content(rewritten_content, improvement_prompt)
            
            return {
                "rewritten_content": rewritten_content,
                "confidence": confidence,
                "tokens_used": len(rewritten_content.split()),  # Approximate token count
                "model_used": "gpt-4o-mini",
                "provider": "openai",
                "variables_preserved": len(variables) if variables else 0,
                "improvement_applied": improvement_prompt,
                "original_length": len(content),
                "rewritten_length": len(rewritten_content),
            }
            
        except Exception as e:
            logger.error(f"Failed to rewrite content: {e}", exc_info=True)
            raise
    
    def _extract_variables(self, content: str) -> Dict[str, str]:
        """Extract {{VARIABLE}} placeholders from content."""
        variables = {}
        pattern = r'\{\{([^}]+)\}\}'
        
        for match in re.finditer(pattern, content):
            var_name = match.group(1)
            var_placeholder = match.group(0)
            variables[var_name] = var_placeholder
        
        return variables
    
    def _restore_variables(self, content: str, variables: Dict[str, str]) -> str:
        """Restore {{VARIABLE}} placeholders in content."""
        # This is a simple implementation - in practice, you might want
        # more sophisticated variable restoration logic
        for var_name, placeholder in variables.items():
            # Look for the variable name without braces and replace with placeholder
            pattern = rf'\b{re.escape(var_name)}\b'
            content = re.sub(pattern, placeholder, content)
        
        return content
    
    def _build_rewrite_prompt(
        self,
        content: str,
        improvement_prompt: str,
        document_type: str,
        variables: Dict[str, str]
    ) -> str:
        """Build the LLM prompt for document rewriting."""
        
        variables_info = ""
        if variables:
            variables_info = f"""
IMPORTANT: The document contains the following variables that MUST be preserved exactly as they are:
{', '.join([f"{{{{{name}}}}}" for name in variables.keys()])}

Do not modify these variable placeholders in any way.
"""
        
        return f"""You are a legal document expert specializing in Brazilian notarial documents. 
Rewrite the following {document_type} document according to the user's improvement request.

{variables_info}

ORIGINAL DOCUMENT:
{content}

USER'S IMPROVEMENT REQUEST:
{improvement_prompt}

INSTRUCTIONS:
1. Improve the document according to the user's request
2. Maintain the legal structure and formal language
3. Preserve all variable placeholders exactly as they are: {{VARIABLE_NAME}}
4. Ensure the document remains legally sound and professional
5. If the request is unclear, make reasonable improvements to enhance clarity and professionalism
6. Return only the rewritten document content, no explanations

REWRITTEN DOCUMENT:"""
    
    def _calculate_confidence_from_content(self, content: str, improvement_prompt: str) -> float:
        """Calculate confidence score for the rewrite based on content quality."""
        # Base confidence on response quality indicators
        base_confidence = 0.8
        
        # Adjust based on content length (too short might indicate issues)
        content_length = len(content)
        if content_length < 100:
            base_confidence -= 0.2
        elif content_length > 5000:
            base_confidence -= 0.1
        
        # Adjust based on content quality indicators
        if "{{" in content and "}}" in content:
            base_confidence += 0.1  # Bonus for preserving variables
        
        # Check for common issues that reduce confidence
        if content.lower().strip() == "i cannot" or "i can't" in content.lower():
            base_confidence -= 0.3
        
        if len(content.split()) < 20:  # Very short response
            base_confidence -= 0.2
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, base_confidence))
    
    async def initialize(self) -> None:
        """Initialize the rewrite service."""
        # Rewrite service doesn't require async initialization
        self._mark_initialized()
        self._mark_healthy()
        logger.info("Document rewrite service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup rewrite service resources."""
        # No resources to cleanup since we use the shared LLM service
        logger.info("Document rewrite service cleaned up")


# Service manager for rewrite service
_service_manager = register_service(DocumentRewriteService)


async def init_rewrite_service():
    """Initialize rewrite service."""
    await _service_manager.initialize()
    logger.info("Document rewrite service initialized")


def get_rewrite_service() -> DocumentRewriteService:
    """Get the global rewrite service instance."""
    return _service_manager.get_instance()
