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
from .template_service import TemplateService


class PDFService:
    """Service for generating PDF documents from templates."""

    def __init__(self):
        self.temp_dir = Path(settings.PDF_TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_pdf_from_template(
        self, 
        template_id: str, 
        variaveis: Dict[str, Any]
    ) -> tuple[bytes, str]:
        """
        Generate PDF directly from template with variables.
        
        Args:
            template_id: UUID of the template
            variaveis: Variables for template rendering
            
        Returns:
            Tuple of (pdf_bytes, filename)
        """
        template = Template.objects.get(id=template_id)
        
        # Render template
        template_service = TemplateService()
        rendered_content = template_service.render_template(template_id, variaveis)
        
        # Convert markdown to HTML
        html_content = markdown(
            rendered_content,
            extras=['fenced-code-blocks', 'tables', 'header-ids']
        )
        
        # Apply CSS styling
        styled_html = self._apply_css_styling(html_content, template)
        
        # Generate PDF
        pdf_bytes = self._html_to_pdf(styled_html)
        
        # Generate filename
        filename = f"template_{template.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return pdf_bytes, filename

    def _apply_css_styling(self, html_content: str, template) -> str:
        """Apply CSS styling to HTML content."""
        # Basic CSS for document formatting
        css_styles = """
        <style>
            body {
                font-family: 'Times New Roman', serif;
                line-height: 1.6;
                margin: 2cm;
                color: #333;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #2c3e50;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }
            h1 { font-size: 24px; }
            h2 { font-size: 20px; }
            h3 { font-size: 18px; }
            p { margin-bottom: 1em; }
            .document-header {
                text-align: center;
                margin-bottom: 2em;
                border-bottom: 2px solid #2c3e50;
                padding-bottom: 1em;
            }
            .document-footer {
                margin-top: 2em;
                text-align: center;
                font-size: 12px;
                color: #666;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 1em 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
        </style>
        """
        
        # Add template-specific CSS if available
        if hasattr(template, 'custom_css') and template.custom_css:
            css_styles += f"<style>{template.custom_css}</style>"
        
        # Wrap content with styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {css_styles}
        </head>
        <body>
            <div class="document-header">
                <h1>{template.name}</h1>
                <p>Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            <div class="document-content">
                {html_content}
            </div>
            <div class="document-footer">
                <p>Página 1 de 1</p>
            </div>
        </body>
        </html>
        """
        
        return styled_html

    def _html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML content to PDF bytes."""
        try:
            # Create HTML object
            html_obj = HTML(string=html_content)
            
            # Generate PDF
            pdf_bytes = html_obj.write_pdf()
            
            return pdf_bytes
            
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
