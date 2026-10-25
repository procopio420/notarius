from rest_framework import serializers

from .models import Processo, ProcessoParte, Protocolo, Atendimento, MensagemAtendimento
from .models import RevisaoDadoAtendimento
from .ficha import CAMPOS, SITUACOES
from .models import AnexoAtendimento, PaginaAnexoAtendimento
from .models import ModeloAtendimento
from .models import FeedbackTesteAtendimento


class ModeloMinutaSerializer(serializers.ModelSerializer):
    referencia_id = serializers.UUIDField(read_only=True, allow_null=True)
    class Meta:
        model = ModeloAtendimento
        fields = ['id', 'versao', 'corpo', 'representacao', 'observacoes', 'registros_minuta', 'campos_qualificacao', 'campos_obrigatorios_ficha', 'dependencias_campos_ficha', 'aprovado', 'justificativa', 'created_at', 'referencia_id']
        read_only_fields = ['id', 'versao', 'created_at']


class SalvarModeloSerializer(serializers.Serializer):
    registros_minuta = serializers.ListField(child=serializers.DictField(), default=list, max_length=60)
    campos_obrigatorios_ficha = serializers.ListField(child=serializers.DictField(), default=list, max_length=100)
    dependencias_campos_ficha = serializers.ListField(child=serializers.DictField(), default=list, max_length=100)
    campos_qualificacao = serializers.ListField(child=serializers.DictField(), required=False, default=list, max_length=25)

    def validate_campos_qualificacao(self, value):
        from .ficha_estruturada_schema import validar_qualificacao
        return validar_qualificacao(value)

    referencia_id = serializers.UUIDField(required=False, allow_null=True)
    corpo = serializers.CharField(max_length=60000)
    representacao = serializers.CharField(max_length=10000, allow_blank=True)
    observacoes = serializers.CharField(max_length=10000, allow_blank=True)
    aprovado = serializers.BooleanField()
    justificativa = serializers.CharField(max_length=2000)
    versao_esperada = serializers.IntegerField(min_value=0)

    def validate(self, data):
        from .ficha_estruturada_schema import validar_regras
        validar_regras(data['campos_obrigatorios_ficha'], data['dependencias_campos_ficha'], data['campos_qualificacao'])
        from .redacao_estruturada import validar_configuracao
        validar_configuracao(data['registros_minuta'], data['campos_qualificacao'])
        return data


class EditarMinutaSerializer(serializers.Serializer):
    minuta_id = serializers.UUIDField()
    versao_esperada = serializers.IntegerField(min_value=1)
    client_id = serializers.UUIDField()
    corpo = serializers.CharField(max_length=150000, trim_whitespace=False)
    motivo = serializers.CharField(max_length=2000)

    def validate_corpo(self, value):
        if not value.strip():
            raise serializers.ValidationError('A minuta não pode ficar vazia.')
        if '{{' in value or '}}' in value:
            raise serializers.ValidationError('Resolva os marcadores de preenchimento antes de salvar.')
        if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
            raise serializers.ValidationError('O texto contém caracteres de controle inválidos.')
        return value


class PaginaAnexoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaginaAnexoAtendimento
        fields = ['id', 'numero', 'texto', 'situacao', 'aviso', 'metodo', 'texto_ocr', 'regioes_ocr', 'largura_imagem', 'altura_imagem', 'ocr_idioma', 'leitura_versao', 'limites_leitura']


class AnexoAtendimentoSerializer(serializers.ModelSerializer):
    paginas = serializers.SerializerMethodField()
    organizacao = serializers.SerializerMethodField()
    cobertura = serializers.SerializerMethodField()

    def get_organizacao(self, obj):
        from .organizacao_anexos import resumo
        return resumo(obj)

    def get_cobertura(self, obj):
        pages = [p for p in obj.paginas.all() if p.leitura_versao == obj.leitura_versao]
        return {**obj.metadados_leitura, 'paginas_processadas': len(pages),
                'paginas_sem_texto': [p.numero for p in pages if not p.texto.strip() and not p.texto_ocr.strip()],
                'paginas_incertas': [p.numero for p in pages if p.situacao == 'revisao'],
                'aviso': 'Sem texto reconhecido não significa inexistência do fato. A extração não comprova leitura integral.'}

    def get_paginas(self, obj):
        return PaginaAnexoSerializer([p for p in obj.paginas.all() if p.leitura_versao == obj.leitura_versao], many=True).data

    class Meta:
        model = AnexoAtendimento
        fields = ['id', 'nome', 'mime', 'tamanho', 'sha256', 'situacao', 'aviso', 'created_at', 'paginas', 'leitura_versao', 'organizacao', 'cobertura']


class RevisaoDadoSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.get_full_name', read_only=True)
    origem = serializers.SerializerMethodField()

    def get_origem(self, obj):
        if obj.pagina_origem_id:
            return {'tipo': 'documento', 'mensagem_id': None, 'pagina_id': str(obj.pagina_origem_id),
                    'anexo_id': str(obj.pagina_origem.anexo_id), 'arquivo': obj.pagina_origem.anexo.nome,
                    'pagina': obj.pagina_origem.numero, 'trecho': obj.trecho_origem, 'canal': obj.canal_origem,
                    'leitura_versao': obj.pagina_origem.leitura_versao,
                    'organizacao_versao': obj.organizacao_origem.versao if obj.organizacao_origem_id else 0}
        return {'tipo': 'mensagem' if obj.mensagem_id else 'manual',
                'mensagem_id': str(obj.mensagem_id) if obj.mensagem_id else None,
                'trecho': obj.mensagem.texto if obj.mensagem_id else None}

    class Meta:
        model = RevisaoDadoAtendimento
        fields = ['id', 'chave', 'valor', 'situacao', 'origem', 'justificativa', 'autor_nome', 'versao', 'created_at']


class AtualizarDadoSerializer(serializers.Serializer):
    organizacao_versao = serializers.IntegerField(min_value=0, required=False)
    chave = serializers.ChoiceField(choices=list(CAMPOS))
    valor = serializers.CharField(max_length=10000, allow_blank=True)
    situacao = serializers.ChoiceField(choices=SITUACOES)
    mensagem_id = serializers.UUIDField(required=False, allow_null=True)
    pagina_id = serializers.UUIDField(required=False, allow_null=True)
    trecho_origem = serializers.CharField(max_length=10000, required=False, allow_blank=True)
    canal_origem = serializers.ChoiceField(choices=['texto', 'ocr'], default='texto')
    justificativa = serializers.CharField(max_length=2000)
    versao_esperada = serializers.IntegerField(min_value=0)

    def validate(self, data):
        if data.get('mensagem_id') and data.get('pagina_id'):
            raise serializers.ValidationError('Escolha uma única origem para a informação.')
        if data.get('pagina_id') and not data.get('trecho_origem', '').strip():
            raise serializers.ValidationError('Informe o trecho literal da página de origem.')
        if data.get('trecho_origem') and not data.get('pagina_id'):
            raise serializers.ValidationError('O trecho precisa de uma página de origem.')
        if data['situacao'] in ['informado', 'confirmado', 'divergente'] and not data['valor'].strip():
            raise serializers.ValidationError('Informe o conteúdo do campo.')
        if data['situacao'] == 'ausente' and data['valor'].strip():
            raise serializers.ValidationError('Um campo ausente deve ficar sem valor.')
        return data


class AtendimentoSerializer(serializers.ModelSerializer):
    titulo = serializers.CharField(max_length=160, trim_whitespace=True)

    class Meta:
        model = Atendimento
        fields = ['id', 'titulo', 'tipo_ato', 'created_at', 'updated_at', 'situacao', 'versao_cadastro']
        read_only_fields = ['id', 'tipo_ato', 'created_at', 'updated_at', 'situacao', 'versao_cadastro']


class MensagemAtendimentoSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.get_full_name', read_only=True)
    texto = serializers.CharField(max_length=10000, trim_whitespace=False)

    def validate_texto(self, value):
        if not value.strip():
            raise serializers.ValidationError('Informe uma mensagem com conteúdo.')
        return value

    class Meta:
        model = MensagemAtendimento
        fields = ['id', 'client_id', 'texto', 'autor_nome', 'created_at', 'campo', 'pergunta', 'correcao_de', 'motivo_correcao']
        read_only_fields = ['id', 'autor_nome', 'created_at', 'campo', 'pergunta', 'correcao_de', 'motivo_correcao']


class RespostaConferenciaSerializer(serializers.Serializer):
    chave = serializers.CharField(max_length=80)
    assinatura = serializers.RegexField(r'^[0-9a-f]{64}$')
    versao_esperada = serializers.IntegerField(min_value=0)
    client_id = serializers.UUIDField()
    valor = serializers.CharField(max_length=10000, allow_blank=True)
    confirmar = serializers.BooleanField()
    justificativa = serializers.CharField(max_length=2000)


class ProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Processo
        fields = [
            "id",
            "tenant",
            "tipo_ato",
            "status",
            "responsavel",
            "sla_at",
            "metadados",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tenant", "created_at", "updated_at"]


class ProcessoParteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessoParte
        fields = ["id", "tenant", "processo", "parte", "papel", "created_at", "updated_at"]
        read_only_fields = ["tenant", "created_at", "updated_at"]


class ProtocoloSerializer(serializers.ModelSerializer):
    numero_formatado = serializers.ReadOnlyField()
    
    class Meta:
        model = Protocolo
        fields = [
            "id",
            "tenant",
            "numero",
            "ano",
            "processo",
            "tipo",
            "observacoes",
            "numero_formatado",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tenant", "numero", "created_at", "updated_at"]

class CriarFeedbackTesteSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    etapa = serializers.ChoiceField(choices=['conversa','anexos','ficha','modelo','minuta','exportacao','outro'])
    tipo = serializers.ChoiceField(choices=['erro','duvida','sugestao'])
    descricao = serializers.CharField(max_length=4000)
    esperado = serializers.CharField(max_length=2000, allow_blank=True, default='')


class FeedbackTesteSerializer(serializers.ModelSerializer):
    autor_nome = serializers.SerializerMethodField()

    def get_autor_nome(self, obj):
        return obj.autor.get_full_name() or obj.autor.username

    class Meta:
        model = FeedbackTesteAtendimento
        fields = ['id','client_id','etapa','tipo','descricao','esperado','contexto','autor_nome','created_at']
        read_only_fields = fields
