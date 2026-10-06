import uuid
from django.db import models
from apps.base.models import TimeStampedModel


class Tenant(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    uf = models.CharField(max_length=2)
    municipio = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.CharField(max_length=64, null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "tenants"
        constraints = [
            models.UniqueConstraint(fields=["nome", "uf"], name="uq_tenant_nome_uf"),
        ]
        indexes = [
            models.Index(fields=["nome", "uf"], name="ix_tenant_nome_uf"),
            models.Index(fields=["municipio"], name="ix_tenant_municipio"),
            models.Index(fields=["uf"], name="ix_tenant_uf"),
        ]

    def __str__(self):
        return f"{self.nome}-{self.uf}"


class RegistryRequest(TimeStampedModel):
    """Model for storing tenant (cartório) registration requests"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    uf = models.CharField(max_length=2)
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "registry_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nome} - {self.municipio}/{self.uf}"
