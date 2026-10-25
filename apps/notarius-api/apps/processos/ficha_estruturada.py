"""Typed local sheet using the existing immutable field-revision history."""
import uuid
from django.db import transaction, connection, OperationalError
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from .models import (Atendimento, ObjetoFichaAtendimento, EventoFichaAtendimento,
                     RevisaoDadoAtendimento, MensagemAtendimento, PaginaAnexoAtendimento)
from .serializers import RevisaoDadoSerializer
from .conferencia import assinatura, sem_dado
from .ficha_estruturada_schema import schema_atual, verificar_cpf


class FichaAlterada(APIException):
    status_code = 409
    default_detail = 'A ficha ou a leitura mudou. Atualize e confira antes de salvar.'


class DadoSerializer(serializers.Serializer):
    organizacao_versao = serializers.IntegerField(min_value=0, required=False)
    contexto_assinatura = serializers.CharField(max_length=64, required=False)
    proposta_id = serializers.UUIDField(required=False, allow_null=True)
    versao_proposta = serializers.IntegerField(min_value=0, required=False)
    conferir_associacao = serializers.BooleanField(default=False)
    chave = serializers.RegexField(r'^[a-z][a-z0-9_]{0,39}$')
    valor = serializers.CharField(max_length=10000, allow_blank=True, trim_whitespace=False)
    valor_original = serializers.CharField(max_length=10000, allow_blank=True, trim_whitespace=False, required=False)
    situacao = serializers.ChoiceField(choices=['ausente', 'extraido', 'informado', 'confirmado', 'divergente', 'ilegivel'])
    versao_esperada = serializers.IntegerField(min_value=0)
    confirmar = serializers.BooleanField(default=False)
    conferir_fonte = serializers.BooleanField(default=False)
    origem = serializers.ChoiceField(choices=['manual', 'mensagem', 'documento', 'legado'])
    mensagem_id = serializers.UUIDField(required=False, allow_null=True)
    pagina_id = serializers.UUIDField(required=False, allow_null=True)
    revisao_origem_id = serializers.UUIDField(required=False, allow_null=True)
    leitura_versao = serializers.IntegerField(min_value=1, required=False)
    trecho_origem = serializers.CharField(max_length=10000, allow_blank=True, required=False, trim_whitespace=False)
    canal_origem = serializers.ChoiceField(choices=['texto', 'ocr'], default='texto')


class AlteracaoSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    operacao = serializers.ChoiceField(choices=['criar', 'salvar'])
    justificativa = serializers.CharField(max_length=2000)
    modelo_id = serializers.UUIDField(allow_null=True)
    tipo = serializers.ChoiceField(choices=['pessoa', 'papel', 'relacao', 'imovel', 'negociacao', 'ato', 'complemento'], required=False)
    escopo = serializers.ChoiceField(choices=['atendimento', 'pessoa', 'imovel', 'pessoa_imovel'], required=False)
    pessoa_a_id = serializers.UUIDField(required=False, allow_null=True)
    pessoa_b_id = serializers.UUIDField(required=False, allow_null=True)
    imovel_id = serializers.UUIDField(required=False, allow_null=True)
    objeto_id = serializers.UUIDField(required=False)
    campos = DadoSerializer(many=True, required=False, max_length=30)

    def validate(self, data):
        if data['operacao'] == 'criar' and ('campos' in data or 'objeto_id' in data):
            raise ValidationError('Crie o registro primeiro e informe seus campos na alteração seguinte.')
        if data['operacao'] == 'salvar' and any(k in data for k in ['tipo', 'escopo', 'pessoa_a_id', 'pessoa_b_id', 'imovel_id']):
            raise ValidationError('Os vínculos de um registro são preservados. Para corrigir uma associação, registre a desativação e crie o vínculo correto.')
        return data


def origem(revision):
    if revision.revisao_origem_id:
        return {'tipo': 'legado', 'revisao_id': str(revision.revisao_origem_id),
                'organizacao_versao': revision.organizacao_origem.versao if revision.organizacao_origem_id else 0,
                'trecho': revision.trecho_origem, 'campo': revision.revisao_origem.chave,
                'versao': revision.revisao_origem.versao,
                'origem_anterior': RevisaoDadoSerializer(revision.revisao_origem).data['origem']}
    result = RevisaoDadoSerializer(revision).data['origem']
    if revision.mensagem_id and revision.trecho_origem:
        result['trecho'] = revision.trecho_origem
    return result


def serializar_revisao(revision, atendimento=None, dependencias=None):
    data = dict(RevisaoDadoSerializer(revision).data)
    data.update(valor_original=revision.valor_original if revision.objeto_id else revision.valor,
                rotulo_original=revision.rotulo_original, origem=origem(revision),
                natureza_origem='extraida' if revision.pagina_origem_id else 'legada' if revision.revisao_origem_id else 'informada',
                confirmacao={'autor_id': str(revision.autor_id), 'autor_nome': data['autor_nome'],
                             'data': revision.created_at.isoformat()} if revision.situacao == 'confirmado' else None)
    source_revision = revision.revisao_origem if revision.revisao_origem_id else revision
    from .dependencias_ficha import fonte_atual
    data['fonte_atual'] = fonte_atual(revision)
    from .dependencias_ficha import capturar
    if revision.objeto_id and dependencias is None:
        dependencias = capturar(atendimento or revision.atendimento, revision.objeto, revision.chave)
    data['dependencias_atuais'] = not revision.objeto_id or revision.dependencias_ficha == dependencias
    data['confirmacao_atual'] = bool(data['confirmacao'] and data['fonte_atual'] and data['dependencias_atuais'])
    data['situacao_efetiva'] = revision.situacao if data['fonte_atual'] and data['dependencias_atuais'] else 'reaberta'
    if revision.chave == 'cpf':
        data['validacao_formato'] = verificar_cpf(revision.valor)
    data['propostas_ids'] = [str(d.proposta_id) for d in revision.decisoes_proposta.all()]
    return data


def consultar(atendimento):
    from .propostas_dados import consultar_propostas
    from .dependencias_ficha import capturar
    schema = schema_atual(atendimento)
    revisions = list(atendimento.revisoes.select_related('autor', 'mensagem', 'pagina_origem__anexo', 'revisao_origem__pagina_origem__anexo').prefetch_related('decisoes_proposta').all())
    from .rotulos_ficha import rotulos
    labels = rotulos(atendimento, revisions)
    objects = []
    for obj in atendimento.objetos_ficha.exclude(tipo='legado').select_related('autor'):
        history = [r for r in revisions if r.objeto_id == obj.id]
        fields = {f['chave']: f for f in schema[obj.tipo]}
        # Model reconfiguration never hides historical qualification attributes.
        for r in history:
            fields.setdefault(r.chave, {'chave': r.chave, 'rotulo': r.rotulo_original or r.chave, 'grupo': 'Histórico do modelo'})
        # Reuse only within this read. Every later query/mutation re-evaluates
        # dependencies; no state survives between requests or write phases.
        contexts = {key: capturar(atendimento, obj, key) for key in fields}
        serialized = {r.id: serializar_revisao(r, atendimento, contexts[r.chave]) for r in history}
        objects.append({'id': str(obj.id), 'rotulo': labels[str(obj.id)], 'tipo': obj.tipo, 'pessoa_a_id': str(obj.pessoa_a_id) if obj.pessoa_a_id else None,
                        'criacao': {'autor_id': str(obj.autor_id), 'autor_nome': obj.autor.get_full_name() or obj.autor.username,
                                    'data': obj.created_at.isoformat(), 'motivo': obj.motivo_criacao},
                        'pessoa_b_id': str(obj.pessoa_b_id) if obj.pessoa_b_id else None,
                        'imovel_id': str(obj.imovel_id) if obj.imovel_id else None,
                        'campos': [{**f, 'contexto_assinatura': assinatura(contexts[key]),
                                    'historico': [serialized[r.id] for r in history if r.chave == key],
                                    'atual': next((serialized[r.id] for r in history if r.chave == key), None)} for key, f in fields.items()]})
    legacy = [serializar_revisao(r) for r in revisions if r.objeto_id is None]
    model = atendimento.modelos_minuta.first()
    return {'objetos': objects, 'legado': legacy, 'schema': schema, 'modelo_id': str(model.id) if model else None,
            'propostas': consultar_propostas(atendimento),
            'aviso': 'Dados separados por registro. Nenhuma pessoa, papel ou relação foi deduzida. O conteúdo antigo permanece inteiro para revisão; a minuta por blocos não é atualizada automaticamente.'}


def _related(atendimento, object_id, expected_type):
    return get_object_or_404(atendimento.objetos_ficha, id=object_id, tenant_id=atendimento.tenant_id, tipo=expected_type)


def _source(atendimento, data, objeto=None):
    selected = [bool(data.get(k)) for k in ['mensagem_id', 'pagina_id', 'revisao_origem_id']]
    kind = data['origem']
    if sum(selected) != (0 if kind == 'manual' else 1):
        raise ValidationError('Escolha uma única fonte para cada dado.')
    fields = {'mensagem': None, 'pagina_origem': None, 'revisao_origem': None, 'organizacao_origem': None}
    text = ''
    if kind == 'documento' and data.get('pagina_id'):
        page = get_object_or_404(PaginaAnexoAtendimento.objects.select_related('anexo'), id=data['pagina_id'],
                                anexo__atendimento=atendimento, tenant_id=atendimento.tenant_id)
        if data.get('leitura_versao') != page.leitura_versao or page.leitura_versao != page.anexo.leitura_versao:
            raise FichaAlterada()
        text = page.texto_ocr if data['canal_origem'] == 'ocr' else page.texto
        fields['pagina_origem'] = page
        from .organizacao_anexos import validar_fonte
        fields['organizacao_origem'] = validar_fonte(page.anexo, objeto, page.numero,
            data.get('organizacao_versao'), data['situacao'] == 'confirmado')
    elif kind == 'mensagem' and data.get('mensagem_id'):
        fields['mensagem'] = get_object_or_404(atendimento.mensagens, id=data['mensagem_id'], tenant_id=atendimento.tenant_id)
        from .conversa_orientada import mensagem_atual
        if not mensagem_atual(fields['mensagem']):
            raise FichaAlterada('Esta mensagem foi corrigida. Confira a mensagem atual antes de utilizar seus dados.')
        text = fields['mensagem'].texto
    elif kind == 'legado' and data.get('revisao_origem_id'):
        fields['revisao_origem'] = get_object_or_404(atendimento.revisoes, id=data['revisao_origem_id'],
                                                   objeto__isnull=True, tenant_id=atendimento.tenant_id)
        text = fields['revisao_origem'].valor
        old = fields['revisao_origem']
        if old.mensagem_id:
            from .conversa_orientada import mensagem_atual
            if not mensagem_atual(old.mensagem):
                raise FichaAlterada('A mensagem do conteúdo antigo foi corrigida. Confira a fonte atual.')
        if old.pagina_origem_id and old.pagina_origem.leitura_versao != old.pagina_origem.anexo.leitura_versao:
            raise FichaAlterada('O conteúdo antigo referencia uma leitura substituída. Confira a fonte atual.')
        if old.pagina_origem_id:
            from .organizacao_anexos import validar_fonte
            fields['organizacao_origem'] = validar_fonte(old.pagina_origem.anexo, objeto, old.pagina_origem.numero,
                data.get('organizacao_versao'), data['situacao'] == 'confirmado')
    elif kind != 'manual':
        raise ValidationError('A fonte informada não corresponde ao tipo selecionado.')
    excerpt = data.get('trecho_origem', '')
    if kind != 'manual' and (not excerpt.strip() or excerpt not in text):
        raise ValidationError('O trecho deve existir literalmente na fonte selecionada.')
    if data['situacao'] == 'extraido' and (kind != 'documento' or data['valor'] not in excerpt):
        raise ValidationError('Dado extraído precisa manter valor literal dentro do trecho documental.')
    original = data.get('valor_original', data['valor'])
    if kind != 'manual' and original and original not in excerpt:
        raise ValidationError('O valor original deve existir no trecho. Registre correções no valor revisado, preservando o original.')
    return fields, original, excerpt


def alterar(atendimento, user, payload):
    try:
        return _alterar(atendimento, user, payload)
    except OperationalError as error:
        if connection.vendor == 'sqlite' and 'locked' in str(error).lower():
            raise FichaAlterada('Outra alteração está em andamento. Atualize e tente novamente; nada desta requisição foi salvo.') from None
        raise


def reservar_atendimento(atendimento):
    if connection.vendor == 'sqlite':
        Atendimento.objects.filter(pk=atendimento.pk, tenant_id=atendimento.tenant_id).update(updated_at=F('updated_at'))
    else:
        Atendimento.objects.select_for_update().get(pk=atendimento.pk, tenant_id=atendimento.tenant_id)


def _alterar(atendimento, user, payload):
    serializer = AlteracaoSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    digest = assinatura(data)
    with transaction.atomic():
        # First query inside this transaction is a write on SQLite: reserve the
        # writer before reading versions, so competing writers recheck fresh state.
        reservar_atendimento(atendimento)
        previous = atendimento.eventos_ficha.filter(client_id=data['client_id']).first()
        if previous:
            if previous.autor_id != user.id or previous.requisicao_hash != digest:
                raise ValidationError('Identificador de alteração já utilizado com outro conteúdo ou autora.')
            return previous.resultado, False
        model = atendimento.modelos_minuta.first()
        if data['modelo_id'] != (model.id if model else None):
            raise FichaAlterada('O modelo e seus campos mudaram. Atualize a ficha.')
        if data['operacao'] == 'criar':
            tipo = data.get('tipo')
            if not tipo:
                raise ValidationError('Escolha o tipo de registro.')
            if tipo == 'complemento' and not data.get('escopo'):
                raise ValidationError('Escolha explicitamente a quem este complemento se refere.')
            if tipo != 'complemento' and data.get('escopo'):
                raise ValidationError('Escopo específico é usado somente em complementos.')
            obj_fields = {}
            for link in ['pessoa_a_id', 'pessoa_b_id', 'imovel_id']:
                target = data.get(link)
                needed = link == 'pessoa_a_id' and tipo in ['papel', 'relacao'] or link == 'pessoa_b_id' and tipo == 'relacao' or link == 'imovel_id' and tipo == 'negociacao'
                if tipo == 'complemento':
                    needed = (link == 'pessoa_a_id' and data['escopo'] in ['pessoa', 'pessoa_imovel'] or
                              link == 'imovel_id' and data['escopo'] in ['imovel', 'pessoa_imovel'])
                if needed and not target:
                    raise ValidationError('Selecione explicitamente as pessoas ou imóvel deste registro.')
                if target and not needed:
                    raise ValidationError('Vínculo incompatível com o tipo de registro.')
                if target:
                    _related(atendimento, target, 'imovel' if link == 'imovel_id' else 'pessoa')
                    obj_fields[link] = target
            if tipo == 'relacao' and data['pessoa_a_id'] == data['pessoa_b_id']:
                raise ValidationError('Uma relação deve apontar duas pessoas distintas.')
            obj = ObjetoFichaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, autor=user,
                                                        tipo=tipo, motivo_criacao=data['justificativa'], **obj_fields)
            result = {'objeto_id': str(obj.id), 'revisoes': []}
        else:
            if not data.get('objeto_id') or not data.get('campos'):
                raise ValidationError('Selecione o registro e pelo menos um campo.')
            obj = get_object_or_404(atendimento.objetos_ficha.exclude(tipo='legado'), id=data['objeto_id'], tenant_id=atendimento.tenant_id)
            definitions = {f['chave']: f for f in schema_atual(atendimento)[obj.tipo]}
            revisions = []
            keys = [item['chave'] for item in data['campos']]
            if len(keys) != len(set(keys)):
                raise ValidationError('Não repita um campo na mesma alteração.')
            # Check the opened context before any write in the batch. A changed
            # person/classification must never be silently accepted by capturing
            # the newer dependency state after a stale human confirmation.
            from .dependencias_ficha import capturar
            for item in data['campos']:
                dependencies = capturar(atendimento, obj, item['chave'])
                if (dependencies or obj.tipo == 'complemento') and item.get('contexto_assinatura') != assinatura(dependencies):
                    raise FichaAlterada('O registro vinculado, a classificação ou a situação mudou. Reabra o campo e confira seu contexto antes de salvar.')
            for item in data['campos']:
                key = item['chave']
                definition = definitions.get(key)
                current = obj.revisoes.filter(chave=key).first()
                if not definition:
                    if not current:
                        raise ValidationError('Campo não configurado para este registro.')
                    definition = {'rotulo': current.rotulo_original or key}
                if item['versao_esperada'] != (current.versao if current else 0):
                    raise FichaAlterada()
                status, value = item['situacao'], item['valor']
                if status == 'confirmado' and (not item['confirmar'] or not item['conferir_fonte'] or sem_dado(value)):
                    raise ValidationError('Confirme explicitamente o dado e a conferência de sua fonte; informação desconhecida continua pendente.')
                if status == 'ausente' and value.strip() or status in ['informado', 'extraido', 'divergente'] and not value.strip():
                    raise ValidationError('Situação e valor incompatíveis.')
                if definition.get('opcoes') and value and value not in definition['opcoes']:
                    raise ValidationError('Use uma das opções do campo, sem alterar seu significado.')
                from .propostas_dados import vincular_proposta
                vincular_proposta(atendimento, user, obj, item)
                source, original, excerpt = _source(atendimento, item, obj)
                if item['origem'] == 'manual':
                    original = value
                    message = MensagemAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, autor=user,
                        client_id=uuid.uuid4(), texto=value, pergunta=f"Ficha detalhada: {definition['rotulo']}")
                    source['mensagem'] = message
                    excerpt = value
                revision = RevisaoDadoAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, autor=user,
                    objeto=obj, chave=key, valor=value, valor_original=original, rotulo_original=definition['rotulo'], situacao=status,
                    versao=(current.versao if current else 0) + 1, justificativa=data['justificativa'],
                    trecho_origem=excerpt, canal_origem=item['canal_origem'], **source)
                vincular_proposta(atendimento, user, obj, item, revision, data['justificativa'])
                revisions.append(str(revision.id))
            from .dependencias_ficha import capturar
            for revision in atendimento.revisoes.filter(id__in=revisions):
                revision.dependencias_ficha = capturar(atendimento, obj, revision.chave)
                revision.save(update_fields=['dependencias_ficha'])
            result = {'objeto_id': str(obj.id), 'revisoes': revisions}
        EventoFichaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, autor=user,
            client_id=data['client_id'], requisicao_hash=digest, resultado=result)
        Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
        from .pendencias_ficha import sincronizar
        sincronizar(atendimento, user, data['justificativa'])
        return result, True
