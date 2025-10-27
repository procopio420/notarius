from django.conf import settings
from django.db import models

from apps.base.models import BaseTenantModel


# Create your models here.
class Processo(BaseTenantModel):
    STATUS = (
        ("rascunho", "Rascunho"),
        ("analise", "Em Análise"),
        ("assinatura", "Assinatura"),
        ("selagem", "Selagem"),
        ("arquivado", "Arquivado"),
        ("cancelado", "Cancelado"),
    )
    tipo_ato = models.CharField(max_length=64, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS, default="rascunho", db_index=True)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="processos_responsaveis",
    )
    sla_at = models.DateTimeField(null=True, blank=True)
    metadados = models.JSONField(default=dict, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "processos"
        indexes = [
            models.Index(fields=["tenant", "status"], name="ix_proc_tenant_status"),
            models.Index(
                fields=["tenant", "tipo_ato", "status"], name="ix_proc_tenant_tipo_status"
            ),
        ]

    def __str__(self):
        return f"{self.tipo_ato} ({self.status})"


class ProcessoParte(BaseTenantModel):
    PAPEL = (
        ("outorgante", "Outorgante"),
        ("outorgado", "Outorgado"),
        ("testemunha", "Testemunha"),
        ("interveniente", "Interveniente"),
        ("outro", "Outro"),
    )
    processo = models.ForeignKey(Processo, on_delete=models.PROTECT, related_name="partes")
    parte = models.ForeignKey(
        "partes.Parte", on_delete=models.PROTECT, related_name="participacoes"
    )
    papel = models.CharField(max_length=32, choices=PAPEL)

    class Meta:
        db_table = "processo_partes"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "processo", "parte", "papel"], name="uq_processo_parte_papel"
            ),
        ]

    def __str__(self):
        return f"{self.processo_id} - {self.parte_id} ({self.papel})"


class Protocolo(BaseTenantModel):
    TIPO = (
        ("entrada", "Entrada"),
        ("saida", "Saída"),
        ("interno", "Interno"),
    )
    
    numero = models.PositiveIntegerField(db_index=True)
    ano = models.PositiveIntegerField(db_index=True)
    processo = models.ForeignKey(
        Processo, on_delete=models.PROTECT, related_name="protocolos"
    )
    tipo = models.CharField(max_length=16, choices=TIPO, default="entrada")
    observacoes = models.TextField(blank=True)

    class Meta:
        db_table = "protocolos"
        indexes = [
            models.Index(fields=["tenant", "ano", "numero"], name="ix_protocolo_tenant_ano_numero"),
            models.Index(fields=["tenant", "processo"], name="ix_protocolo_tenant_processo"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "numero", "ano"], name="uq_protocolo_tenant_numero_ano"
            ),
        ]

    def __str__(self):
        return f"PROT-{self.ano}-{self.numero:06d}"

    @property
    def numero_formatado(self):
        return f"PROT-{self.ano}-{self.numero:06d}"
