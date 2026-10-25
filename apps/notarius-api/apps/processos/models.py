from django.conf import settings
from django.db import models

from apps.base.models import BaseTenantModel


class Atendimento(BaseTenantModel):
    titulo = models.CharField(max_length=160)
    tipo_ato = models.CharField(max_length=64, default='compra_venda', editable=False)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    situacao = models.CharField(max_length=20, default='em_andamento', choices=[('em_andamento', 'Em andamento'), ('aguardando', 'Aguardando informação'), ('pausado', 'Pausado')])
    versao_cadastro = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-updated_at', '-id']


class HistoricoOrganizacaoAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='historico_organizacao')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    titulo_anterior = models.CharField(max_length=160)
    titulo_novo = models.CharField(max_length=160)
    situacao_anterior = models.CharField(max_length=20)
    situacao_nova = models.CharField(max_length=20)
    motivo = models.TextField(max_length=2000)
    versao = models.PositiveIntegerField()

    class Meta:
        ordering = ['-versao']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'versao'], name='uq_organizacao_atendimento_versao')]


class RevisaoDadoAtendimento(BaseTenantModel):
    organizacao_origem = models.ForeignKey('OrganizacaoAnexoAtendimento', on_delete=models.PROTECT, null=True, blank=True, related_name='revisoes_fontes')
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='revisoes')
    chave = models.CharField(max_length=40)
    valor = models.TextField(blank=True, max_length=10000)
    situacao = models.CharField(max_length=20)
    mensagem = models.ForeignKey('MensagemAtendimento', on_delete=models.PROTECT, null=True, blank=True)
    pagina_origem = models.ForeignKey('PaginaAnexoAtendimento', on_delete=models.PROTECT, null=True, blank=True)
    trecho_origem = models.TextField(blank=True, max_length=10000)
    canal_origem = models.CharField(max_length=10, default='texto')
    justificativa = models.TextField(max_length=2000)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    versao = models.PositiveIntegerField()
    objeto = models.ForeignKey('ObjetoFichaAtendimento', on_delete=models.PROTECT, null=True, blank=True, related_name='revisoes')
    revisao_origem = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='derivacoes')
    rotulo_original = models.CharField(max_length=120, blank=True)
    valor_original = models.TextField(blank=True, max_length=10000)
    dependencias_ficha = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['chave', '-versao']
        constraints = [
            models.UniqueConstraint(fields=['atendimento', 'chave', 'versao'], condition=models.Q(objeto__isnull=True), name='uq_dado_atendimento_versao'),
            models.UniqueConstraint(fields=['objeto', 'chave', 'versao'], name='uq_objeto_campo_versao'),
        ]


class ObjetoFichaAtendimento(BaseTenantModel):
    TIPOS = [(k, k) for k in ['pessoa', 'papel', 'relacao', 'imovel', 'negociacao', 'ato', 'complemento', 'legado']]
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='objetos_ficha')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    pessoa_a = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    pessoa_b = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    imovel = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    motivo_criacao = models.TextField(max_length=2000, blank=True)

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [models.UniqueConstraint(fields=['atendimento'], condition=models.Q(tipo='legado'), name='uq_ficha_legado_atendimento')]


class EventoFichaAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='eventos_ficha')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    client_id = models.UUIDField()
    requisicao_hash = models.CharField(max_length=64)
    resultado = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['atendimento', 'client_id'], name='uq_ficha_evento_client_id')]


class PropostaDadoAtendimento(BaseTenantModel):
    analise_documental = models.ForeignKey('AnaliseDocumentalAtendimento', on_delete=models.PROTECT, null=True, blank=True, related_name='propostas')
    evidencia_estruturada = models.JSONField(default=dict, blank=True)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='propostas_dados')
    pagina = models.ForeignKey('PaginaAnexoAtendimento', on_delete=models.PROTECT, null=True, blank=True)
    mensagem = models.ForeignKey('MensagemAtendimento', on_delete=models.PROTECT, null=True, blank=True)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    metodo = models.CharField(max_length=40, default='rotulos_locais_v1')
    canal = models.CharField(max_length=10, default='texto')
    linha = models.PositiveIntegerField()
    rotulo = models.CharField(max_length=120)
    valor_original = models.TextField(max_length=10000)
    trecho = models.TextField(max_length=10000)
    destinos = models.JSONField(default=list)
    origem_hash = models.CharField(max_length=64)

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [
            models.UniqueConstraint(fields=['atendimento', 'origem_hash'], name='uq_proposta_origem'),
            models.CheckConstraint(condition=(models.Q(pagina__isnull=False, mensagem__isnull=True) | models.Q(pagina__isnull=True, mensagem__isnull=False)), name='ck_proposta_fonte_unica'),
        ]


class DecisaoPropostaAtendimento(BaseTenantModel):
    campo = models.CharField(max_length=40, blank=True)
    organizacao_origem = models.ForeignKey('OrganizacaoAnexoAtendimento', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='decisoes_propostas')
    proposta = models.ForeignKey(PropostaDadoAtendimento, on_delete=models.PROTECT, related_name='decisoes')
    objeto = models.ForeignKey(ObjetoFichaAtendimento, on_delete=models.PROTECT, null=True, blank=True)
    revisao = models.ForeignKey(RevisaoDadoAtendimento, on_delete=models.PROTECT, null=True, blank=True, related_name='decisoes_proposta')
    acao = models.CharField(max_length=20, choices=[('associada', 'associada'), ('aceita', 'aceita'), ('rejeitada', 'rejeitada')])
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    justificativa = models.TextField(max_length=2000)
    versao = models.PositiveIntegerField()

    class Meta:
        ordering = ['-versao']
        constraints = [models.UniqueConstraint(fields=['proposta', 'versao'], name='uq_decisao_proposta_versao')]


class AnaliseDocumentalAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='analises_documentais')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    client_id = models.UUIDField()
    requisicao_hash = models.CharField(max_length=64)
    contexto_assinatura = models.CharField(max_length=64)
    provedor = models.CharField(max_length=40)
    entrada = models.JSONField()
    saida = models.JSONField()

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'client_id'], name='uq_analise_documental_client')]


class PendenciaFichaAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='pendencias_ficha')
    chave = models.CharField(max_length=180)
    tipo = models.CharField(max_length=40)
    objeto = models.ForeignKey(ObjetoFichaAtendimento, on_delete=models.PROTECT, null=True, blank=True)
    campo = models.CharField(max_length=40, blank=True)
    situacao = models.CharField(max_length=20, default='aberta')
    versao = models.PositiveIntegerField(default=0)
    assinatura = models.CharField(max_length=64)
    contexto = models.JSONField(default=dict)
    resolucao = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'chave'], name='uq_pendencia_ficha_chave')]


class HistoricoPendenciaFicha(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='historico_pendencias_ficha')
    pendencia = models.ForeignKey(PendenciaFichaAtendimento, on_delete=models.PROTECT, related_name='historico')
    versao = models.PositiveIntegerField()
    situacao = models.CharField(max_length=20)
    assinatura = models.CharField(max_length=64)
    contexto = models.JSONField(default=dict)
    resolucao = models.JSONField(default=dict)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    motivo = models.TextField(max_length=2000)

    class Meta:
        ordering = ['-versao']
        constraints = [models.UniqueConstraint(fields=['pendencia', 'versao'], name='uq_hist_pendencia_versao')]


class AnexoAtendimento(BaseTenantModel):
    organizacao_atual = models.ForeignKey('OrganizacaoAnexoAtendimento', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    metadados_leitura = models.JSONField(default=dict, blank=True)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='anexos')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    nome = models.CharField(max_length=200)
    mime = models.CharField(max_length=80)
    tamanho = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    conteudo = models.BinaryField(editable=False)
    situacao = models.CharField(max_length=30)
    aviso = models.TextField(blank=True)
    leitura_versao = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'sha256'], name='uq_atendimento_anexo_hash')]


class PaginaAnexoAtendimento(BaseTenantModel):
    limites_leitura = models.JSONField(default=list, blank=True)
    anexo = models.ForeignKey(AnexoAtendimento, on_delete=models.CASCADE, related_name='paginas')
    numero = models.PositiveIntegerField()
    leitura_versao = models.PositiveIntegerField(default=1)
    texto = models.TextField(blank=True)
    situacao = models.CharField(max_length=30)
    aviso = models.TextField(blank=True)
    metodo = models.CharField(max_length=30, default='texto')
    texto_ocr = models.TextField(blank=True)
    regioes_ocr = models.JSONField(default=list, blank=True)
    largura_imagem = models.PositiveIntegerField(default=0)
    altura_imagem = models.PositiveIntegerField(default=0)
    ocr_idioma = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['numero']
        constraints = [models.UniqueConstraint(fields=['anexo', 'numero', 'leitura_versao'], name='uq_anexo_pagina_leitura')]


class OrganizacaoAnexoAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='organizacoes_anexos')
    anexo = models.ForeignKey(AnexoAtendimento, on_delete=models.PROTECT, related_name='organizacoes')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    versao = models.PositiveIntegerField()
    client_id = models.UUIDField()
    requisicao_hash = models.CharField(max_length=64)
    finalidade = models.CharField(max_length=30)
    tipo_documento = models.CharField(max_length=120, blank=True)
    vinculos = models.JSONField(default=list)
    leitura_versao = models.PositiveIntegerField()
    motivo = models.TextField(max_length=2000)

    class Meta:
        ordering = ['-versao']
        constraints = [models.UniqueConstraint(fields=['anexo', 'versao'], name='uq_anexo_organizacao_versao'),
                       models.UniqueConstraint(fields=['atendimento', 'client_id'], name='uq_anexo_organizacao_client')]


class MensagemAtendimento(BaseTenantModel):
    correcao_de = models.OneToOneField('self', on_delete=models.PROTECT, null=True, blank=True, related_name='correcao_seguinte')
    motivo_correcao = models.TextField(max_length=2000, blank=True)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='mensagens')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    texto = models.TextField(max_length=10000)
    client_id = models.UUIDField()
    campo = models.CharField(max_length=40, blank=True)
    pergunta = models.TextField(blank=True)
    requisicao_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'client_id'], name='uq_atendimento_client_message')]


class DecisaoConferencia(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='decisoes')
    chave = models.CharField(max_length=80)
    assinatura = models.CharField(max_length=64)
    justificativa = models.TextField(max_length=2000)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revisao = models.ForeignKey(RevisaoDadoAtendimento, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']


class ModeloReutilizavel(BaseTenantModel):
    registros_minuta = models.JSONField(default=list, blank=True)
    nome = models.CharField(max_length=120)
    corpo = models.TextField(max_length=60000)
    representacao = models.TextField(blank=True, max_length=10000)
    observacoes = models.TextField(blank=True, max_length=10000)
    campos_qualificacao = models.JSONField(default=list, blank=True)
    campos_obrigatorios_ficha = models.JSONField(default=list, blank=True)
    dependencias_campos_ficha = models.JSONField(default=list, blank=True)
    origem = models.ForeignKey('ModeloAtendimento', on_delete=models.PROTECT, related_name='publicacoes')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.UniqueConstraint(fields=['tenant', 'origem', 'nome'], name='uq_modelo_reuso_origem_nome')]


class ModeloAtendimento(BaseTenantModel):
    registros_minuta = models.JSONField(default=list, blank=True)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='modelos_minuta')
    versao = models.PositiveIntegerField()
    corpo = models.TextField(max_length=60000)
    representacao = models.TextField(blank=True, max_length=10000)
    observacoes = models.TextField(blank=True, max_length=10000)
    campos_qualificacao = models.JSONField(default=list, blank=True)
    campos_obrigatorios_ficha = models.JSONField(default=list, blank=True)
    dependencias_campos_ficha = models.JSONField(default=list, blank=True)
    aprovado = models.BooleanField(default=False)
    justificativa = models.TextField(max_length=2000)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    referencia = models.ForeignKey(ModeloReutilizavel, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ['-versao']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'versao'], name='uq_modelo_atendimento_versao')]


class MinutaAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='minutas_preparadas')
    modelo = models.ForeignKey(ModeloAtendimento, on_delete=models.PROTECT)
    versao = models.PositiveIntegerField()
    corpo = models.TextField()
    dados = models.JSONField()
    assinatura = models.CharField(max_length=64)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    base = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    tipo = models.CharField(max_length=12, default='preparada')
    motivo = models.TextField(blank=True, max_length=2000)
    client_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ['-versao']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'versao'], name='uq_minuta_atendimento_versao'),
                       models.UniqueConstraint(fields=['atendimento', 'client_id'], name='uq_minuta_edicao_client_id')]


class VinculacaoMinutaAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='vinculacoes_minuta')
    modelo = models.ForeignKey(ModeloAtendimento, on_delete=models.PROTECT)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    versao = models.PositiveIntegerField()
    client_id = models.UUIDField()
    requisicao_hash = models.CharField(max_length=64)
    registros = models.JSONField()
    exclusoes = models.JSONField(default=list)
    motivo = models.TextField(max_length=2000)

    class Meta:
        ordering = ['-versao']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'versao'], name='uq_vinculacao_minuta_versao'),
                       models.UniqueConstraint(fields=['atendimento', 'client_id'], name='uq_vinculacao_minuta_client')]


class FeedbackTesteAtendimento(BaseTenantModel):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='feedbacks_teste')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    client_id = models.UUIDField()
    requisicao_hash = models.CharField(max_length=64)
    etapa = models.CharField(max_length=20)
    tipo = models.CharField(max_length=20)
    descricao = models.TextField(max_length=4000)
    esperado = models.TextField(blank=True, max_length=2000)
    contexto = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.UniqueConstraint(fields=['atendimento', 'client_id'], name='uq_feedback_teste_client_id')]


class RevisaoFinalMinuta(BaseTenantModel):
    minuta = models.OneToOneField(MinutaAtendimento, on_delete=models.PROTECT, related_name='revisao_final')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    motivo = models.TextField(max_length=2000)
    texto_sha256 = models.CharField(max_length=64)


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
