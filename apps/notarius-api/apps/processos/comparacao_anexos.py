"""Read-only comparison of literal, explicitly labelled attachment evidence."""
from collections import defaultdict

from django.db.models import F

from .comparacao_fontes import normalizar_campo
from .conferencia import assinatura, normalizar
from .ficha_estruturada_schema import schema_atual
from .models import PaginaAnexoAtendimento
from .organizacao_anexos import destinos, permite
from .propostas_dados import _rotulos, canais_pagina, ler_rotulos

MAX_EVIDENCIAS = 200
MAX_TRECHO = 2000
FINALIDADES_EXCLUIDAS = ['referencia_redacao', 'nao_utilizar']
PAGAMENTO = {
    'condicoes': 'Confira as condições combinadas para o pagamento.',
    'situacao_pagamento': 'Confira se o pagamento está previsto, foi declarado realizado ou tem comprovante apresentado.',
    'quitacao': 'Há uma declaração expressa de quitação? Confira o trecho com a escrevente.',
}


def _destino(file, numero, targets, objects):
    if not file.organizacao_atual_id:
        return None
    org = file.organizacao_atual
    owners = {link['objeto_id'] for link in org.vinculos if not link['paginas'] or numero in link['paginas']}
    if not owners or None in owners:
        return None
    compatible = [(obj, target) for target in targets for obj in objects[target['tipo']]
                  if destinos(obj) == owners and permite(file, obj, numero)]
    return compatible[0] if len(compatible) == 1 else None


def _valores_e_arquivos(sources):
    values = {assinatura(source['normalizado']) for source in sources}
    files = {source['anexo_id'] for source in sources}
    currencies = {source['normalizado']['moeda_explicita'] for source in sources
                  if isinstance(source['normalizado'], dict)}
    return values, files, currencies


def _estado(group):
    sources = group['fontes']
    reliable = [source for source in sources if not source['problemas']]
    values, files, currencies = _valores_e_arquivos(reliable)
    if len(values) > 1 and len(files) > 1 and len(currencies) <= 1:
        if group['objeto_id']:
            return 'divergencia', 'Qual valor deve ser registrado para este campo? Confira os trechos antes de decidir.'
        if group['tipo_registro'] == 'negociacao':
            return 'possivel_divergencia', 'Estes trechos tratam da mesma negociação? Confira o contexto e os valores.'
    if len(reliable) < len(sources) and (group['objeto_id'] or group['tipo_registro'] == 'negociacao'):
        readable = [source for source in sources if source['problemas'] in ([], ['leitura_incerta'])]
        read_values, read_files, read_currencies = _valores_e_arquivos(readable)
        if len(read_values) > 1 and len(read_files) > 1 and len(read_currencies) <= 1:
            return 'possivel_divergencia', 'A leitura sugere valores diferentes. Confira os originais e se os trechos se referem ao mesmo registro.'
    if len(reliable) < len(sources) or (len(values) > 1 and group['objeto_id']):
        return 'conferir_leitura', 'Confira no original os trechos ou valores que precisam de revisão.'
    if not group['objeto_id']:
        return 'conferir_vinculo', 'A qual registro cada trecho se refere? Confira a página e indique o destinatário.'
    if len(files) > 1:
        return 'coincidencia', 'Os valores comparáveis coincidem. Confira o campo antes de confirmar na ficha.'
    return 'sugestao', 'Confira o valor e a fonte antes de registrar na ficha.'


def comparar_anexos(atendimento):
    labels = _rotulos(atendimento)
    schema = schema_atual(atendimento)
    fields = {(kind, field['chave']): field for kind, entries in schema.items() for field in entries}
    objects = defaultdict(list)
    inactive = set()
    seen = set()
    for oid, value in atendimento.revisoes.filter(chave='estado_registro', objeto__isnull=False).order_by(
            'objeto_id', '-versao').values_list('objeto_id', 'valor'):
        if oid not in seen and value == 'inativo':
            inactive.add(oid)
        seen.add(oid)
    for obj in atendimento.objetos_ficha.exclude(tipo='legado'):
        if obj.id not in inactive:
            objects[obj.tipo].append(obj)

    pages = PaginaAnexoAtendimento.objects.filter(
        anexo__atendimento=atendimento, tenant_id=atendimento.tenant_id,
        leitura_versao=F('anexo__leitura_versao'),
    ).exclude(anexo__organizacao_atual__finalidade__in=FINALIDADES_EXCLUIDAS).select_related(
        'anexo__organizacao_atual',
    ).defer('anexo__conteudo').order_by('anexo__created_at', 'anexo_id', 'numero')
    groups = {}
    count = 0
    limited = False
    for page in pages.iterator(chunk_size=16):
        file = page.anexo
        channels = list(canais_pagina(page))
        uncertain = page.situacao != 'extraido' or bool(page.limites_leitura) or len(channels) > 1
        for channel, text in channels:
            for number, line, found in ler_rotulos(text, labels):
                if not found:
                    continue
                if len(line) > MAX_TRECHO or count >= MAX_EVIDENCIAS:
                    limited = True
                    if count >= MAX_EVIDENCIAS:
                        break
                    continue
                label, value, targets = found
                bound = _destino(file, page.numero, targets, objects)
                target = bound[1] if bound else targets[0] if len(targets) == 1 else None
                oid = str(bound[0].id) if bound else None
                kind = target['tipo'] if target else None
                key = target['chave'] if target else None
                group_key = (oid, kind, key or normalizar(label))
                group = groups.setdefault(group_key, {
                    'id': assinatura(group_key), 'objeto_id': oid, 'tipo_registro': kind,
                    'campo': key, 'rotulo': target['rotulo'] if target else label, 'fontes': [],
                })
                normalized = normalizar_campo(kind, key, value, fields.get((kind, key), {}).get('opcoes'))
                problems = list(normalized['problemas'])
                if uncertain:
                    problems.append('leitura_incerta')
                group['fontes'].append({
                    'anexo_id': str(file.id), 'arquivo': file.nome, 'pagina_id': str(page.id),
                    'pagina': page.numero, 'leitura_versao': page.leitura_versao, 'canal': channel,
                    'linha': number, 'trecho': line, 'valor_original': value,
                    'normalizado': normalized['valor'], 'problemas': problems,
                })
                count += 1
            if limited and count >= MAX_EVIDENCIAS:
                break
        if limited and count >= MAX_EVIDENCIAS:
            break

    for group in groups.values():
        group['estado'], group['pergunta'] = _estado(group)
        if group['campo'] in PAGAMENTO:
            group['pergunta'] += ' ' + PAGAMENTO[group['campo']]
        for source in group['fontes']:
            del source['normalizado']
    priority = ['divergencia', 'possivel_divergencia', 'conferir_leitura', 'conferir_vinculo', 'sugestao', 'coincidencia']
    return {'grupos': sorted(groups.values(), key=lambda group: (priority.index(group['estado']), group['rotulo'])),
            'limitado': limited, 'total_sugestoes': count}
