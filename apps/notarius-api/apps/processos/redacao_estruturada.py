"""Explicit template positions and literal, traceable field insertion. No inference."""
import re
from django.db import transaction, OperationalError, connection
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .conferencia import assinatura, sem_dado
from .dependencias_ficha import confirmacao_atual
from .ficha_estruturada_schema import SCHEMA
from .models import VinculacaoMinutaAtendimento, Atendimento

TOKEN = re.compile(r'\{\{\s*([a-z][a-z0-9_]{0,39})\.([a-z][a-z0-9_]{0,39})\s*\}\}')


def validar_configuracao(registros, qualification):
    if not isinstance(registros, list) or len(registros) > 60:
        raise ValidationError('Configure até 60 posições explícitas no modelo.')
    aliases = {}
    for r in registros:
        base_keys = {'chave', 'rotulo', 'tipo', 'vinculos'}
        if not isinstance(r, dict) or set(r) != base_keys | ({'categoria'} if r.get('tipo') == 'complemento' else set()):
            raise ValidationError('Cada posição exige identificador, rótulo, tipo e vínculos explícitos.')
        key, tipo = r['chave'], r['tipo']
        if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,39}', key) or key in aliases:
            raise ValidationError('Use identificadores distintos para as posições do modelo.')
        if not isinstance(tipo, str) or tipo not in SCHEMA or not isinstance(r['rotulo'], str) or not r['rotulo'].strip() or len(r['rotulo']) > 120 or not isinstance(r['vinculos'], dict):
            raise ValidationError('Tipo, rótulo ou vínculos da posição inválidos.')
        if tipo == 'complemento' and r['categoria'] not in next(f['opcoes'] for f in SCHEMA['complemento'] if f['chave'] == 'categoria'):
            raise ValidationError('Escolha a categoria de complemento esperada nesta posição do modelo.')
        aliases[key] = r
    for r in registros:
        needed = {'pessoa_a': 'pessoa'} if r['tipo'] == 'papel' else {'pessoa_a': 'pessoa', 'pessoa_b': 'pessoa'} if r['tipo'] == 'relacao' else {'imovel': 'imovel'} if r['tipo'] == 'negociacao' else {}
        if r['tipo'] == 'complemento':
            if set(r['vinculos']) - {'pessoa_a', 'imovel'}:
                raise ValidationError('Um complemento pode referir-se à pessoa, imóvel ou ao atendimento, sem outro vínculo presumido.')
            needed = {key: 'pessoa' if key == 'pessoa_a' else 'imovel' for key in r['vinculos']}
        if set(r['vinculos']) != set(needed):
            raise ValidationError('Configure as pessoas do papel/relação e o imóvel da negociação, sem deduzi-los.')
        for link, target in r['vinculos'].items():
            if not isinstance(target, str) or target not in aliases or aliases[target]['tipo'] != needed[link]:
                raise ValidationError('O vínculo deve apontar para uma posição do tipo correspondente.')
    fields = {t: {f['chave'] for f in fs} - {'estado_registro'} for t, fs in SCHEMA.items()}
    fields['pessoa'].update(f['chave'] for f in qualification)
    return aliases, fields


def validar_modelo(data):
    from .blocos_minuta import plano, referencias, expansoes
    aliases, fields = validar_configuracao(data['registros_minuta'], data.get('campos_qualificacao', []))
    used = set()
    refs = referencias(data)
    for alias, field in refs:
        if alias not in aliases or field not in fields[aliases[alias]['tipo']]:
            raise ValidationError(f'Marcador ou condição não configurado: {alias}.{field}.')
        used.add(alias)
    for nodes in plano(data).values():
        for node in nodes:
            if node['tipo'] == 'repetir':
                if any(a not in aliases for a in node['posicoes']) or len({aliases[a]['tipo'] for a in node['posicoes']}) != 1:
                    raise ValidationError('Cada repetição deve reunir somente posições configuradas do mesmo tipo, sem misturar pessoas, papéis ou imóveis.')
            for text, _ in expansoes(node):
                remainder = TOKEN.sub('', text)
                if any(mark in remainder for mark in ['{{', '}}', '{%', '%}']):
                    raise ValidationError('Marcador ou diretiva incompleto; não há execução de expressões livres.')
    linked = {a for r in aliases.values() for a in r['vinculos'].values()}
    if not refs or set(aliases) - used - linked:
        raise ValidationError('Toda posição deve aparecer no texto, condição ou vínculo configurado.')


def objetos_ativos(atendimento):
    objects = list(atendimento.objetos_ficha.exclude(tipo='legado'))
    return [o for o in objects if not ((r := o.revisoes.filter(chave='estado_registro').first()) and r.valor == 'inativo' and confirmacao_atual(atendimento, r))]


def escopo(atendimento):
    model = atendimento.modelos_minuta.first()
    return assinatura([str(model.id) if model else None,
                      list(atendimento.objetos_ficha.exclude(tipo='legado').order_by('id').values_list('id', 'tipo', 'pessoa_a_id', 'pessoa_b_id', 'imovel_id')),
                      list(atendimento.revisoes.filter(objeto__isnull=False).order_by('id').values_list('id', flat=True))])


def conferir_vinculos(atendimento, model, registers, exclusions):
    active = {str(o.id): o for o in objetos_ativos(atendimento)}
    definitions = {r['chave']: r for r in model.registros_minuta}
    if set(registers) != set(definitions):
        raise ValidationError('Escolha um registro para cada posição do modelo atual.')
    for alias, oid in registers.items():
        if not isinstance(oid, str) or oid not in active or active[oid].tipo != definitions[alias]['tipo']:
            raise ValidationError('Registro ausente, desativado, de outro atendimento ou incompatível com a posição.')
        if active[oid].tipo == 'complemento':
            actual = {link for link in ['pessoa_a', 'imovel'] if getattr(active[oid], f'{link}_id')}
            if actual != set(definitions[alias]['vinculos']):
                raise ValidationError('O âmbito do complemento não corresponde ao modelo: atendimento, pessoa e imóvel não podem ser trocados implicitamente.')
            category = active[oid].revisoes.filter(chave='categoria').first()
            if not category or not confirmacao_atual(atendimento, category) or category.valor != definitions[alias]['categoria']:
                raise ValidationError('Confira a categoria e sua fonte: consulta, certidão, tributo e declaração não são intercambiáveis na mesma posição.')
        for link, target in definitions[alias]['vinculos'].items():
            if str(getattr(active[oid], f'{link}_id')) != registers[target]:
                raise ValidationError('Pessoas, papéis, relações ou imóveis não correspondem aos vínculos escolhidos no modelo.')
    excluded_ids = [e['objeto_id'] for e in exclusions]
    if len(set(excluded_ids)) != len(excluded_ids) or set(excluded_ids) & set(registers.values()) or set(excluded_ids) | set(registers.values()) != set(active):
        raise ValidationError('Cada registro ativo precisa estar vinculado ou explicitamente fora desta minuta, sem sobreposição.')
    for e in exclusions:
        if not e['motivo'].strip():
            raise ValidationError('Informe o motivo individual de cada registro fora da minuta.')
        current = sorted(str(i) for i in active[e['objeto_id']].revisoes.values_list('id', flat=True))
        if 'revisoes' in e and e['revisoes'] != current:
            raise ValidationError('Um registro fora da minuta mudou. Revise sua destinação explicitamente.')
    return active


def vinculo_atual(atendimento):
    model = atendimento.modelos_minuta.first()
    binding = atendimento.vinculacoes_minuta.first()
    if not model or not model.registros_minuta or not model.aprovado:
        raise ValidationError('Configure e aprove o modelo com posições e marcadores da ficha detalhada.')
    if not binding or binding.modelo_id != model.id:
        raise ValidationError('Revise a vinculação dos registros à versão atual do modelo.')
    conferir_vinculos(atendimento, model, binding.registros, binding.exclusoes)
    return model, binding


class ExclusaoSerializer(serializers.Serializer):
    objeto_id = serializers.UUIDField()
    motivo = serializers.CharField(max_length=2000)


class VincularSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    modelo_id = serializers.UUIDField()
    versao_esperada = serializers.IntegerField(min_value=0)
    escopo_assinatura = serializers.CharField(max_length=64)
    registros = serializers.DictField(child=serializers.UUIDField())
    exclusoes = ExclusaoSerializer(many=True, max_length=200, default=list)
    motivo = serializers.CharField(max_length=2000)
    conferir = serializers.BooleanField()


def consultar(atendimento):
    latest = atendimento.vinculacoes_minuta.first()
    model = atendimento.modelos_minuta.first()
    try:
        vinculo_atual(atendimento); error = ''
    except ValidationError as e:
        error = ' '.join(map(str, e.detail))
    return {'modelo_id': str(model.id) if model else None, 'modelo_aprovado': bool(model and model.aprovado), 'posicoes': model.registros_minuta if model else [],
            'versao': latest.versao if latest else 0, 'escopo_assinatura': escopo(atendimento),
            'registros': latest.registros if latest else {}, 'exclusoes': latest.exclusoes if latest else [],
            'atual': not error, 'motivo_bloqueio': error,
            'historico': [{'id': str(v.id), 'versao': v.versao, 'modelo_id': str(v.modelo_id), 'registros': v.registros,
                          'exclusoes': v.exclusoes, 'motivo': v.motivo, 'autor': v.autor.get_full_name() or v.autor.username,
                          'data': v.created_at.isoformat()} for v in atendimento.vinculacoes_minuta.select_related('autor')]}


def salvar(atendimento, user, payload):
    from .ficha_estruturada import reservar_atendimento, FichaAlterada
    serializer = VincularSerializer(data=payload); serializer.is_valid(raise_exception=True); data = serializer.validated_data
    digest = assinatura(data)
    try:
        with transaction.atomic():
            reservar_atendimento(atendimento)
            previous = atendimento.vinculacoes_minuta.filter(client_id=data['client_id']).first()
            if previous:
                if previous.autor_id != user.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador já utilizado com outra decisão ou autora.')
                return {'id': str(previous.id), 'versao': previous.versao}, False
            model = atendimento.modelos_minuta.first(); latest = atendimento.vinculacoes_minuta.first()
            if not model or model.id != data['modelo_id'] or data['versao_esperada'] != (latest.versao if latest else 0) or data['escopo_assinatura'] != escopo(atendimento):
                raise FichaAlterada('O modelo, os dados ou a vinculação mudaram. Reabra e confira antes de salvar.')
            if not model.aprovado or not model.registros_minuta or not data['conferir']:
                raise ValidationError('Confira explicitamente as posições, os vínculos e as exclusões do modelo aprovado.')
            registers = {k: str(v) for k, v in data['registros'].items()}
            exclusions = [{'objeto_id': str(e['objeto_id']), 'motivo': e['motivo']} for e in data['exclusoes']]
            active = conferir_vinculos(atendimento, model, registers, exclusions)
            for e in exclusions:
                e['revisoes'] = sorted(str(i) for i in active[e['objeto_id']].revisoes.values_list('id', flat=True))
            binding = VinculacaoMinutaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, modelo=model,
                autor=user, versao=(latest.versao if latest else 0) + 1, client_id=data['client_id'], requisicao_hash=digest,
                registros=registers, exclusoes=exclusions, motivo=data['motivo'])
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, user, data['motivo'])
            Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
            return {'id': str(binding.id), 'versao': binding.versao}, True
    except OperationalError as e:
        if connection.vendor == 'sqlite' and 'locked' in str(e).lower():
            raise FichaAlterada() from None
        raise


def preencher(atendimento):
    from .ficha_estruturada import serializar_revisao
    from .blocos_minuta import plano, referencias, expansoes
    model, binding = vinculo_atual(atendimento)
    nodes_by_block = plano(model)
    values = {}
    # All configured references are required, even in omitted blocks. This
    # conservative first grammar has no optional or inferred case participants.
    for alias, key in referencias(model):
        marker = f'{alias}.{key}'
        if marker in values:
            continue
        r = atendimento.revisoes.filter(objeto_id=binding.registros.get(alias), chave=key).select_related('autor', 'objeto', 'mensagem', 'pagina_origem__anexo', 'revisao_origem__pagina_origem__anexo').first()
        detail = serializar_revisao(r, atendimento) if r else None
        if not r or not detail['confirmacao_atual'] or sem_dado(r.valor) or any(t in r.valor for t in ['{{', '}}', '{%', '%}']):
            raise ValidationError(f'Confira e confirme o dado {marker} e sua fonte atual; não há preenchimento por suposição.')
        values[marker] = {'valor': r.valor, 'valor_original': r.valor_original, 'revisao_id': str(r.id),
            'versao': r.versao, 'situacao': r.situacao, 'objeto_id': str(r.objeto_id), 'tipo': r.objeto.tipo,
            'chave': key, 'origem': detail['origem'], 'confirmacao': detail['confirmacao'],
            'propostas_ids': detail['propostas_ids'], 'dependencias': r.dependencias_ficha,
            'vinculacao_id': str(binding.id), 'modelo_id': str(model.id), 'ocorrencias': []}
    blocks = []; offset = 0
    for block, nodes in nodes_by_block.items():
        if not getattr(model, block).strip():
            continue
        parts = []; length = 0
        for node in nodes:
            if node['tipo'] == 'se':
                rule = node['regra']; datum = values[rule['campo']]; actual = datum['valor']
                if actual not in rule['permitidos']:
                    raise ValidationError(f"Fora do cenário aprovado no bloco {node['chave']}: {rule['campo']}. A escrevente deve decidir e revisar o modelo; não foi preparada minuta parcial.")
                include = actual in rule['incluir']
                datum.setdefault('decisoes_blocos', []).append({'chave': node['chave'], 'bloco': block,
                    'configuracao': rule, 'incluido': include, 'valor_confirmado': actual,
                    'revisao_id': datum['revisao_id'], 'modelo_id': str(model.id), 'modelo_versao': model.versao})
                if not include:
                    continue
            if node['tipo'] == 'repetir':
                ids = [binding.registros[a] for a in node['posicoes']]
                if len(set(ids)) != len(ids):
                    raise ValidationError('A repetição aponta duas posições para o mesmo registro. Confira os participantes explicitamente.')
            for template, repetition in expansoes(node):
                cursor = 0
                for match in TOKEN.finditer(template):
                    literal = template[cursor:match.start()]; parts.append(literal); length += len(literal)
                    marker = f'{match[1]}.{match[2]}'; value = values[marker]['valor']
                    occurrence = {'bloco': block, 'inicio': offset + length, 'fim': offset + length + len(value)}
                    if repetition: occurrence['repeticao'] = repetition
                    if node['tipo'] == 'se': occurrence['condicional'] = node['chave']
                    values[marker]['ocorrencias'].append(occurrence)
                    parts.append(value); length += len(value); cursor = match.end()
                    if offset + length > 150000:
                        raise ValidationError('O preenchimento excede 150.000 caracteres. Nada será truncado.')
                literal = template[cursor:]; parts.append(literal); length += len(literal)
                if offset + length > 150000:
                    raise ValidationError('O preenchimento excede 150.000 caracteres. Nada será truncado.')
        rendered = ''.join(parts); blocks.append(rendered); offset += len(rendered) + 2
    used = {k: v for k, v in values.items() if v['ocorrencias'] or v.get('decisoes_blocos')}
    return used, '\n\n'.join(blocks)
