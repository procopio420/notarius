import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from jinja2 import Environment, Template, TemplateError
from markdown2 import markdown
from weasyprint import HTML, CSS

from apps.auditoria.models import AuditLog
from .models import Template
from apps.documentos.models import Minuta
from .services.renderer import TemplateRenderer


class TemplateService:
    """Service for managing document templates and variable substitution."""

    def __init__(self):
        self.jinja_env = Environment(
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.renderer = TemplateRenderer()

    def render_template(self, template_id: str, variaveis: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template with provided variables.
        
        Args:
            template_id: UUID of the template
            variaveis: Dictionary of variables to substitute
            
        Returns:
            Rendered markdown content
            
        Raises:
            Template.DoesNotExist: If template not found
            TemplateError: If template rendering fails
            jsonschema.ValidationError: If variables don't match schema
        """
        template = Template.objects.get(id=template_id)
        
        # Validate variables against schema
        self.validate_variables(template_id, variaveis)
        
        # Use renderer for PII redaction and state-specific clauses
        uf = variaveis.get('uf') or variaveis.get('UF')
        rendered_content = self.renderer.render(
            template_content=template.corpo_template,
            normalized_data=variaveis,
            uf=uf
        )
        
        return rendered_content

    def validate_variables(self, template_id: str, variaveis: Dict[str, Any]) -> None:
        """
        Validate variables against template schema.
        
        Args:
            template_id: UUID of the template
            variaveis: Dictionary of variables to validate
            
        Raises:
            Template.DoesNotExist: If template not found
            jsonschema.ValidationError: If validation fails
        """
        template = Template.objects.get(id=template_id)
        schema = template.schema
        
        if not schema:
            return  # No schema defined, skip validation
            
        try:
            jsonschema.validate(variaveis, schema)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Variable validation failed: {e.message}")

    def list_required_variables(self, template_id: str) -> List[str]:
        """
        Extract required variables from template schema.
        
        Args:
            template_id: UUID of the template
            
        Returns:
            List of required variable names
        """
        template = Template.objects.get(id=template_id)
        schema = template.schema
        
        if not schema or "properties" not in schema:
            return []
            
        required = schema.get("required", [])
        return required

    def create_minuta_from_template(
        self, 
        template_id: str, 
        processo_id: str, 
        variaveis: Dict[str, Any],
        created_by
    ) -> Minuta:
        """
        Create a new minuta from a template with variable substitution.
        
        Args:
            template_id: UUID of the template
            processo_id: UUID of the processo
            variaveis: Variables for template rendering
            created_by: User creating the minuta
            
        Returns:
            Created Minuta instance
        """
        template = Template.objects.get(id=template_id)
        
        # Render template content
        rendered_content = self.render_template(template_id, variaveis)
        
        # Get next version number for this processo
        last_minuta = Minuta.objects.filter(
            processo_id=processo_id
        ).order_by('-versao').first()
        
        next_version = (last_minuta.versao + 1) if last_minuta else 1
        
        # Create minuta
        minuta = Minuta.objects.create(
            tenant=template.tenant,
            processo_id=processo_id,
            versao=next_version,
            gerada_por="usuario",
            corpo_md=rendered_content,
            variaveis_json=variaveis,
            created_by=created_by,
        )
        
        # Create audit log entry
        AuditLog.objects.create(
            tenant=minuta.tenant,
            actor=created_by,
            resource_type="minuta",
            resource_id=minuta.id,
            action="create",
            diff_json={
                "template_id": str(template_id),
                "template_nome": template.name,
                "versao": next_version,
                "variaveis_count": len(variaveis),
            },
            extra={
                "processo_id": str(processo_id),
                "template_document_type": template.document_type,
                "variaveis": variaveis,
            }
        )
        
        return minuta
