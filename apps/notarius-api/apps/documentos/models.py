from django.db import models
from django.conf import settings

from apps.base.models import BaseTenantModel


class Minuta(BaseTenantModel):
    """
    Minuta model for AI-generated document drafts with PII tokenization.
    """
    processo = models.ForeignKey('processos.Processo', on_delete=models.CASCADE, related_name='minutas')
    corpo_md = models.TextField(help_text='Markdown content of the minuta')
    variaveis_json = models.JSONField(default=dict, help_text='PII variables as tokens')
    status = models.CharField(
        max_length=20,
        choices=[
            ('rascunho', 'Rascunho'),
            ('aprovado', 'Aprovado'),
            ('rejeitado', 'Rejeitado'),
            ('finalizado', 'Finalizado')
        ],
        default='rascunho'
    )
    versao = models.PositiveIntegerField(default=1)
    gerada_por = models.CharField(
        max_length=20,
        choices=[
            ('usuario', 'Usuário'),
            ('ai', 'IA')
        ],
        default='usuario'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='approved_minutas'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    # final_document will be added later to avoid circular reference
    # final_document = models.ForeignKey(
    #     'Documento',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='source_minuta'
    # )
    citations = models.JSONField(default=list, help_text='Legal citations used in generation')
    grounding_confidence = models.FloatField(null=True, help_text='Confidence score for legal grounding')
    skeleton_cache_key = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text='Cache key for document skeleton'
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        db_table = 'minutas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Minuta {self.id} - {self.get_status_display()}"
    
    def can_be_approved(self) -> bool:
        """Check if minuta can be approved."""
        return self.status in ['rascunho', 'pronto']
    
    def approve(self, user):
        """Approve the minuta."""
        if not self.can_be_approved():
            raise ValueError("Minuta cannot be approved in current state")
        
        from django.utils import timezone
        
        self.status = 'aprovado'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def finalize(self):
        """Mark minuta as finalized."""
        if self.status != 'aprovado':
            raise ValueError("Only approved minutas can be finalized")
        
        from django.utils import timezone
        
        self.status = 'finalizado'
        self.finalized_at = timezone.now()
        self.save()


class Documento(BaseTenantModel):
    """
    Final document model for storing completed documents.
    """
    processo = models.ForeignKey('processos.Processo', on_delete=models.CASCADE, related_name='documentos')
    s3_key = models.CharField(max_length=500)
    hash_sha256 = models.BinaryField()
    mime = models.CharField(max_length=100)
    pages = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=[
            ('novo', 'Novo'),
            ('processando', 'Processando'),
            ('pronto', 'Pronto'),
            ('erro', 'Erro')
        ],
        default='novo'
    )
    
    class Meta:
        db_table = 'documentos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Documento {self.id} - {self.get_status_display()}"

