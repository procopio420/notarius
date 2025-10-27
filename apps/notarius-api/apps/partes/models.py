import hashlib
from django.db import models
from django.contrib.auth.models import User

from apps.base.models import BaseTenantModel


class Parte(BaseTenantModel):
    """
    Refactored Parte model using PII Vault tokens instead of raw sensitive data.
    All PII is stored as tokens in the PII Vault service.
    """
    
    TIPO = (
        ("pf", "Pessoa Física"),
        ("pj", "Pessoa Jurídica"),
    )
    
    # Non-sensitive fields
    tipo = models.CharField(max_length=2, choices=TIPO, null=True, blank=True)
    tipo_pessoa = models.CharField(max_length=2, choices=TIPO, help_text="pf or pj", null=True, blank=True)
    
    # PII stored as tokens (no raw sensitive data)
    nome_token = models.CharField(max_length=255, help_text="PII Vault token for name", null=True, blank=True)
    nome_hash = models.BinaryField(db_index=True, help_text="SHA256 hash for deduplication", null=True, blank=True)
    
    # Optional PII tokens
    cpf_token = models.CharField(max_length=255, null=True, blank=True, help_text="PII Vault token for CPF")
    cpf_hash = models.BinaryField(null=True, blank=True, db_index=True, help_text="SHA256 hash for CPF")
    
    cnpj_token = models.CharField(max_length=255, null=True, blank=True, help_text="PII Vault token for CNPJ")
    cnpj_hash = models.BinaryField(null=True, blank=True, db_index=True, help_text="SHA256 hash for CNPJ")
    
    endereco_token = models.CharField(max_length=255, null=True, blank=True, help_text="PII Vault token for address")
    telefone_token = models.CharField(max_length=255, null=True, blank=True, help_text="PII Vault token for phone")
    email_token = models.CharField(max_length=255, null=True, blank=True, help_text="PII Vault token for email")
    
    # Non-sensitive metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Non-sensitive data only")
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_partes', null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='updated_partes', null=True, blank=True)

    class Meta:
        db_table = "partes"
        indexes = [
            models.Index(fields=["tenant", "nome_hash"], name="ix_parte_tenant_nome_hash"),
            models.Index(fields=["tenant", "cpf_hash"], name="ix_parte_tenant_cpf_hash"),
            models.Index(fields=["tenant", "cnpj_hash"], name="ix_parte_tenant_cnpj_hash"),
            models.Index(fields=["tenant", "tipo_pessoa"], name="ix_parte_tenant_tipo"),
        ]

    def __str__(self):
        return f"Parte {self.id} ({self.tipo_pessoa})"
    
    def get_display_name(self):
        """Get display name for UI (shows token, not actual name)."""
        return f"[{self.nome_token[:8]}...]"
    
    @classmethod
    def create_from_pii_tokens(cls, tenant, tipo_pessoa, pii_tokens, created_by, **kwargs):
        """
        Create a new Parte from PII tokens.
        
        Args:
            tenant: Tenant instance
            tipo_pessoa: "pf" or "pj"
            pii_tokens: Dict with token data from PII Vault
            created_by: User instance
            **kwargs: Additional fields
        """
        # Generate hashes for deduplication
        nome_hash = hashlib.sha256(pii_tokens.get('nome', '').encode()).digest()
        cpf_hash = hashlib.sha256(pii_tokens.get('cpf', '').encode()).digest() if pii_tokens.get('cpf') else None
        cnpj_hash = hashlib.sha256(pii_tokens.get('cnpj', '').encode()).digest() if pii_tokens.get('cnpj') else None
        
        return cls.objects.create(
            tenant=tenant,
            tipo=tipo_pessoa,
            tipo_pessoa=tipo_pessoa,
            nome_token=pii_tokens.get('nome_token'),
            nome_hash=nome_hash,
            cpf_token=pii_tokens.get('cpf_token'),
            cpf_hash=cpf_hash,
            cnpj_token=pii_tokens.get('cnpj_token'),
            cnpj_hash=cnpj_hash,
            endereco_token=pii_tokens.get('endereco_token'),
            telefone_token=pii_tokens.get('telefone_token'),
            email_token=pii_tokens.get('email_token'),
            created_by=created_by,
            **kwargs
        )
