"""
Template renderer service with PII redaction and state-specific clauses.
"""

import logging
from typing import Dict, Optional
from jinja2 import Environment, Template

try:
    from packages.pii.redaction import LogSanitizer
    PII_REDACTION_AVAILABLE = True
except ImportError:
    PII_REDACTION_AVAILABLE = False
    LogSanitizer = None

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Renders templates with normalized data, PII redaction, and state-specific clauses."""
    
    def __init__(self):
        self.jinja_env = Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.sanitizer = LogSanitizer() if PII_REDACTION_AVAILABLE else None
    
    def render(
        self,
        template_content: str,
        normalized_data: Dict,
        uf: Optional[str] = None
    ) -> str:
        """
        Render template with normalized data.
        
        Args:
            template_content: Jinja2 template content
            normalized_data: Normalized form data
            uf: State jurisdiction for state-specific clauses
            
        Returns:
            Rendered content with PII redacted in logs
        """
        # Add state-specific data if UF provided
        context = self._prepare_context(normalized_data, uf)
        
        # Render template
        template = self.jinja_env.from_string(template_content)
        rendered = template.render(**context)
        
        # Log with PII redaction
        if self.sanitizer:
            log_content = self.sanitizer.sanitize(rendered)
            logger.info(f"Rendered template for UF={uf}, content length={len(rendered)}")
        else:
            logger.info(f"Rendered template for UF={uf}, content length={len(rendered)}")
        
        return rendered
    
    def _prepare_context(self, normalized_data: Dict, uf: Optional[str]) -> Dict:
        """Prepare template context with state-specific clauses."""
        context = normalized_data.copy()
        
        # Add state-specific clauses based on UF
        if uf:
            context['uf'] = uf
            context['state_clauses'] = self._get_state_clauses(uf)
        
        return context
    
    def _get_state_clauses(self, uf: str) -> Dict:
        """Get state-specific clauses for template."""
        # State-specific clause mappings
        clauses = {
            'SP': {
                'itbi_text': 'ITBI conforme legislação municipal',
                'registro_text': 'Registro conforme normas CGJ/SP'
            },
            'RJ': {
                'itbi_text': 'ITBI conforme legislação municipal',
                'registro_text': 'Registro conforme normas CGJ/RJ'
            },
            'PR': {
                'itbi_text': 'ITBI conforme legislação municipal',
                'registro_text': 'Registro conforme normas CGJ/PR'
            },
        }
        
        return clauses.get(uf, {
            'itbi_text': 'ITBI conforme legislação aplicável',
            'registro_text': 'Registro conforme normas aplicáveis'
        })

