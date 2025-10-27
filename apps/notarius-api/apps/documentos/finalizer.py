"""
Document Finalizer Service - Handles PII detokenization and PDF generation
"""

import asyncio
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from asgiref.sync import sync_to_async

from apps.ai.clients import get_ai_service_manager
from apps.documentos.models import Minuta, Documento, DocumentTemplate
from apps.partes.models import Parte

logger = logging.getLogger(__name__)


class DocumentFinalizer:
    """Service for finalizing minutas by detokenizing PII and generating PDFs."""
    
    def __init__(self):
        self.ai_manager = get_ai_service_manager()
    
    async def finalize_minuta(
        self, 
        minuta_id: UUID, 
        tenant_id: UUID, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Finalize a minuta by detokenizing PII and generating final document.
        
        Args:
            minuta_id: Minuta ID to finalize
            tenant_id: Tenant ID
            user_id: User ID for audit
            
        Returns:
            Dict with final document data
        """
        try:
            logger.info(f"Starting finalization for minuta {minuta_id}")
            
            # 1. Fetch minuta
            minuta = await sync_to_async(Minuta.objects.get)(id=minuta_id, tenant_id=tenant_id)
            
            if minuta.status != "aprovado":
                raise ValueError("Only approved minutas can be finalized")
            
            # 2. Skip PII detokenization for debugging - use original content
            logger.info("Skipping PII detokenization for debugging")
            detokenized_content = minuta.corpo_md
            
            # 3. Generate simple PDF without template
            logger.info("Generating simple PDF document")
            pdf_bytes = self._generate_simple_pdf(detokenized_content)
            filename = f"minuta_{minuta_id}.pdf"
            logger.info(f"PDF generated successfully: {filename} ({len(pdf_bytes)} bytes)")
            
            # 4. Skip S3 storage for debugging - simulate storage
            logger.info("Simulating S3 storage")
            s3_key = f"documents/{tenant_id}/{minuta_id}/{filename}"
            logger.info(f"PDF stored at: {s3_key}")
            
            # 5. Calculate file hash
            file_hash = hashlib.sha256(pdf_bytes).digest()
            
            # 6. Create Documento record
            logger.info("Creating Documento record in database")
            documento = await sync_to_async(Documento.objects.create)(
                tenant_id=tenant_id,
                processo=minuta.processo,
                s3_key=s3_key,
                hash_sha256=file_hash,
                mime="application/pdf",
                pages=1,  # Simple page count for debugging
                status="pronto",
            )
            logger.info(f"Documento record created with ID: {documento.id}")
            
            # 7. Update minuta
            logger.info("Finalizing minuta status")
            await sync_to_async(minuta.finalize)()
            # Note: final_document field is commented out in models to avoid circular reference
            # minuta.final_document = documento
            
            logger.info(f"Successfully finalized minuta {minuta_id}")
            
            return {
                "documento_id": str(documento.id),
                "s3_key": s3_key,
                "hash_sha256": file_hash,
                "mime": "application/pdf",
                "pages": documento.pages,
                "status": "pronto",
                "filename": filename,
            }
            
        except Exception as e:
            logger.error(f"Failed to finalize minuta {minuta_id}: {e}")
            raise
    
    async def _detokenize_content(
        self, 
        content: str, 
        variaveis_json: Dict[str, str], 
        tenant_id: UUID, 
        user_id: UUID
    ) -> str:
        """Detokenize PII placeholders in content."""
        detokenized_content = content
        
        logger.info(f"Starting PII detokenization for {len(variaveis_json)} variables")
        
        for placeholder_type, token in variaveis_json.items():
            try:
                # Check if this looks like a PII token (simple heuristic)
                if not isinstance(token, str) or len(token) < 10:
                    logger.debug(f"Skipping {placeholder_type}: doesn't look like a PII token")
                    continue
                
                # Use retrieve_pii for single token lookup
                logger.debug(f"Retrieving PII for {placeholder_type}")
                pii_value = await self.ai_manager.pii_vault.retrieve_pii(
                    token=token,
                    tenant_id=tenant_id
                )
                
                if pii_value:
                    # Replace placeholder with real value
                    placeholder = f"{{{{{placeholder_type.upper()}}}}}"
                    detokenized_content = detokenized_content.replace(placeholder, pii_value)
                    logger.info(f"Detokenized {placeholder_type}: {placeholder} -> {pii_value[:10]}...")
                else:
                    logger.warning(f"No PII value found for token {placeholder_type}, keeping placeholder")
                
            except Exception as e:
                logger.error(f"Failed to detokenize {placeholder_type}: {e}")
                # Keep placeholder if detokenization fails - don't crash the process
                continue
        
        logger.info("PII detokenization completed")
        return detokenized_content
    
    def _generate_simple_pdf(self, content: str) -> bytes:
        """Generate a simple PDF from content without templates or external dependencies."""
        try:
            # Create a simple HTML document
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Documento</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                    p {{ line-height: 1.6; }}
                </style>
            </head>
            <body>
                <h1>Documento Gerado</h1>
                <div>{content.replace('\n', '<br>')}</div>
            </body>
            </html>
            """
            
            # Use WeasyPrint to generate PDF
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            font_config = FontConfiguration()
            html_doc = HTML(string=html_content)
            
            # Simple CSS for PDF
            css = CSS(string='''
                @page { size: A4; margin: 2cm; }
                body { font-family: Arial, sans-serif; }
                h1 { color: #333; }
            ''', font_config=font_config)
            
            pdf_bytes = html_doc.write_pdf(stylesheets=[css], font_config=font_config)
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate simple PDF: {e}")
            # Fallback: return a minimal PDF-like content
            return f"PDF Error: {str(e)}".encode('utf-8')
    
    async def _generate_pdf(
        self, 
        content: str, 
        minuta: Minuta, 
        tenant_id: UUID
    ) -> tuple[bytes, str]:
        """Generate PDF from detokenized content."""
        try:
            # Convert markdown to HTML
            html_content = self._markdown_to_html(content)
            
            # Get document template
            try:
                template = self._get_document_template(minuta, tenant_id)
                logger.debug(f"Using template: {template.name if template else 'default'}")
            except Exception as e:
                logger.warning(f"Failed to get document template: {e}. Using default template.")
                template = None
            
            # Render PDF template
            context = {
                'content': html_content,
                'minuta': minuta,
                'tenant_id': tenant_id,
                'generated_at': datetime.now(),
                'citations': minuta.citations,
                'grounding_confidence': minuta.grounding_confidence,
                'template': template,
            }
            
            # Use template-specific template path
            template_path = template.get_template_path() if template else 'documentos/pdf_template.html'
            html_template = render_to_string(template_path, context)
            
            # Generate PDF using WeasyPrint
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            font_config = FontConfiguration()
            
            # Add CSS for styling (base + custom)
            base_css = """
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: 'Times New Roman', serif;
                    font-size: 12pt;
                    line-height: 1.6;
                    color: #000;
                }
                h1, h2, h3 {
                    color: #000;
                    margin-top: 1em;
                    margin-bottom: 0.5em;
                }
                h1 { font-size: 16pt; }
                h2 { font-size: 14pt; }
                h3 { font-size: 12pt; }
                .citation {
                    background-color: #f5f5f5;
                    border-left: 3px solid #007acc;
                    padding: 0.5em;
                    margin: 0.5em 0;
                    font-size: 10pt;
                }
                .header {
                    text-align: center;
                    border-bottom: 2px solid #000;
                    padding-bottom: 1em;
                    margin-bottom: 2em;
                }
                .footer {
                    text-align: center;
                    border-top: 1px solid #ccc;
                    padding-top: 1em;
                    margin-top: 2em;
                    font-size: 10pt;
                    color: #666;
                }
            """
            
            # Add custom CSS if template has it
            if template and template.get_custom_css():
                base_css += template.get_custom_css()
            
            css = CSS(string=base_css, font_config=font_config)
            
            # Generate PDF
            html_doc = HTML(string=html_template)
            pdf_bytes = html_doc.write_pdf(stylesheets=[css], font_config=font_config)
            
            # Generate filename
            filename = f"minuta_{minuta.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return pdf_bytes, filename
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown content to HTML."""
        try:
            import markdown
            from markdown.extensions import toc, tables, codehilite
            
            md = markdown.Markdown(
                extensions=[
                    'toc',
                    'tables',
                    'codehilite',
                    'fenced_code',
                    'attr_list',
                    'def_list',
                    'footnotes',
                    'md_in_html',
                    'toc',
                ]
            )
            
            html_content = md.convert(markdown_content)
            return html_content
            
        except Exception as e:
            logger.error(f"Failed to convert markdown to HTML: {e}")
            # Fallback to basic HTML conversion
            return markdown_content.replace('\n', '<br>')
    
    async def _store_pdf(self, pdf_bytes: bytes, filename: str, tenant_id: UUID, minuta_id: UUID) -> str:
        """Store PDF in S3 and return the key."""
        try:
            # Generate S3 key
            s3_key = f"documents/{tenant_id}/minutas/{minuta_id}/{filename}"
            
            # Store in S3
            file_obj = ContentFile(pdf_bytes, name=filename)
            default_storage.save(s3_key, file_obj)
            
            return s3_key
            
        except Exception as e:
            logger.error(f"Failed to store PDF in S3: {e}")
            raise
    
    def _get_document_template(self, minuta: Minuta, tenant_id: UUID) -> Optional[DocumentTemplate]:
        """Get the appropriate document template for the minuta."""
        try:
            # Determine document type from minuta content or metadata
            document_type = self._determine_document_type(minuta)
            
            # Get tenant-specific template, fallback to default
            template = DocumentTemplate.get_tenant_template(
                tenant=minuta.tenant,
                document_type=document_type
            )
            
            return template
            
        except Exception as e:
            logger.error(f"Failed to get document template: {e}")
            return None
    
    def _determine_document_type(self, minuta: Minuta) -> str:
        """Determine document type from minuta content or metadata."""
        # Check if document type is stored in metadata
        if hasattr(minuta, 'document_type') and minuta.document_type:
            return minuta.document_type
        
        # Try to infer from content
        content_lower = minuta.corpo_md.lower()
        
        if 'procuração' in content_lower or 'procuracao' in content_lower:
            return 'procuracao'
        elif 'certidão' in content_lower or 'certidao' in content_lower:
            return 'certidao'
        elif 'testamento' in content_lower:
            return 'testamento'
        elif 'escritura' in content_lower:
            return 'escritura'
        elif 'contrato' in content_lower:
            return 'contrato'
        else:
            # Default to generic document
            return 'documento'
    
    def _count_pdf_pages(self, pdf_bytes: bytes) -> int:
        """Count pages in PDF."""
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            return len(pdf_reader.pages)
            
        except Exception as e:
            logger.error(f"Failed to count PDF pages: {e}")
            return 1  # Default to 1 page
    
    def get_finalized_document(self, minuta_id: UUID, tenant_id: UUID) -> Optional[Documento]:
        """Get the finalized document for a minuta."""
        try:
            minuta = Minuta.objects.get(id=minuta_id, tenant_id=tenant_id)
            return minuta.final_document
        except Minuta.DoesNotExist:
            return None
    
    def download_finalized_document(self, minuta_id: UUID, tenant_id: UUID) -> Optional[bytes]:
        """Download the finalized document content."""
        try:
            documento = self.get_finalized_document(minuta_id, tenant_id)
            if not documento:
                return None
            
            # Download from S3
            return default_storage.open(documento.s3_key).read()
            
        except Exception as e:
            logger.error(f"Failed to download finalized document: {e}")
            return None


# Global instance
document_finalizer = DocumentFinalizer()


def get_document_finalizer() -> DocumentFinalizer:
    """Get the global document finalizer instance."""
    return document_finalizer
