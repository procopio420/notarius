import uuid
from django.db import models
from apps.base.models import TimeStampedModel


class Tenant(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    uf = models.CharField(max_length=2)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "tenants"
        constraints = [
            models.UniqueConstraint(fields=["nome", "uf"], name="uq_tenant_nome_uf"),
        ]

    def __str__(self):
        return f"{self.nome}-{self.uf}"
