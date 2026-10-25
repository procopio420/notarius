"""Conservative comparison by explicit record ID; no identity matching or provider."""
import re
import unicodedata
from decimal import Decimal
from .conferencia import sem_dado, assinatura
from .ficha_estruturada_schema import schema_atual, verificar_cpf
from .dependencias_ficha import fonte_atual
from .organizacao_anexos import permite

VERSAO = 'comparacao_conservadora_v1'
LABELS = {'ausente': 'Dado ausente no registro', 'formato_invalido': 'Formato ou dígitos inconsistentes',
          'leitura_incerta': 'Leitura incerta ou substituída', 'vinculo_incerto': 'Vínculo incerto ou desatualizado',
          'divergencia': 'Valores divergentes'}


def normalizar_campo(tipo, chave, texto, opcoes=None):
    """Return a comparison representation, never a replacement for the saved value."""
    if sem_dado(texto):
        return {'valor': None, 'apresentacao': 'Sem dado registrado', 'problemas': ['ausente']}
    text = unicodedata.normalize('NFC', texto)
    value = ' '.join(text.split()).casefold()
    problems = []
    if any(ord(c) < 32 and c not in '\n\r\t' for c in texto):
        problems.append('formato_invalido')
    if chave == 'cpf':
        cpf = texto.strip()
        validation = verificar_cpf(cpf)
        if not validation['formato_consistente'] or not validation['digitos_consistentes']:
            problems.append('formato_invalido')
        value = re.sub(r'[.\-]', '', cpf) if validation['formato_consistente'] else None
    elif tipo == 'negociacao' and chave == 'preco':
        match = re.fullmatch(r'\s*(R\$\s*)?((?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?)\s*', texto)
        if not match:
            problems.append('formato_invalido'); value = None
        else:
            amount = match[2]
            # Unmarked 1.234 may mean a different convention: do not guess.
            if '.' in amount and ',' not in amount and not match[1]:
                problems.append('formato_invalido'); value = None
            else:
                value = {'numero': format(Decimal(amount.replace('.', '').replace(',', '.')), '.2f'),
                         'moeda_explicita': 'BRL' if match[1] else None}
    elif chave in ['documento_numero', 'matricula']:
        # Keep punctuation and leading zeros: no universal RG/registry grammar.
        if not any(c.isalnum() for c in text) or len(text) > 200:
            problems.append('formato_invalido')
    if opcoes and value not in [' '.join(unicodedata.normalize('NFC', option).split()).casefold() for option in opcoes]:
        problems.append('formato_invalido')
    presentation = (f"{value['numero']} · {value['moeda_explicita'] or 'moeda não informada neste valor'}"
                    if isinstance(value, dict) else str(value) if value is not None else 'Não comparável')
    return {'valor': value, 'apresentacao': presentation, 'problemas': sorted(set(problems))}


def comparar(atendimento):
    from .ficha_estruturada import origem
    from .propostas_dados import fonte_atual as proposta_atual
    objects = {str(o.id): o for o in atendimento.objetos_ficha.exclude(tipo='legado')}
    schema = schema_atual(atendimento)
    fields = {(t, f['chave']): f for t, fs in schema.items() for f in fs}
    revisions = list(atendimento.revisoes.filter(objeto__isnull=False).select_related(
        'mensagem', 'autor', 'organizacao_origem', 'pagina_origem__anexo__organizacao_atual',
        'revisao_origem__pagina_origem__anexo__organizacao_atual', 'revisao_origem__mensagem'))
    latest = {}
    for r in revisions:
        latest.setdefault((str(r.objeto_id), r.chave), r)
    inactive = {oid for (oid, key), r in latest.items() if key == 'estado_registro' and r.valor == 'inativo' and r.situacao == 'confirmado' and fonte_atual(r)}
    groups, unlinked, linked = {}, [], []

    def origem_visivel(r):
        result = origem(r)
        if result.get('tipo') == 'legado':
            return {**result['origem_anterior'], 'origem_legada': result,
                    'trecho_da_derivacao': result['trecho'], 'organizacao_versao': result.get('organizacao_versao', 0)}
        return result

    def group(oid, key):
        obj = objects[oid]
        return groups.setdefault((oid, key), {'chave': f'comparacao:{oid}:{key}', 'objeto_id': oid,
            'tipo_registro': obj.tipo, 'campo': key, 'rotulo': fields.get((obj.tipo, key), {}).get('rotulo', key),
            'versao_normalizacao': VERSAO, 'evidencias': []})

    def evidence(oid, key, eid, value, raw, source, kind, status, extra=None):
        obj = objects[oid]
        normalized = normalizar_campo(obj.tipo, key, value, fields.get((obj.tipo, key), {}).get('opcoes'))
        return {'id': eid, 'objeto_id': oid, 'campo': key, 'tipo_fonte': kind,
                'valor_original': raw, 'valor_considerado': value, 'normalizacao': normalized,
                'fonte': source, 'situacao': status, 'problemas': normalized['problemas'][:], **(extra or {})}

    for (oid, key), r in latest.items():
        if oid not in objects or oid in inactive or key == 'estado_registro':
            continue
        source = r.revisao_origem if r.revisao_origem_id else r
        p = source.pagina_origem
        flags = []
        if not fonte_atual(r) or r.situacao == 'ilegivel' or p and (p.situacao == 'revisao' or p.limites_leitura):
            flags.append('leitura_incerta')
        if r.situacao == 'ausente':
            flags.append('ausente')
        if r.situacao == 'divergente':
            flags.append('divergencia')
        if p and not fonte_atual(r):
            flags.append('vinculo_incerto')
        e = evidence(oid, key, f'ficha:{r.id}', r.valor, r.valor_original, origem_visivel(r), 'ficha', r.situacao,
                     {'revisao_id': str(r.id), 'versao': r.versao, 'fonte_atual': fonte_atual(r)})
        e['problemas'] = sorted(set(e['problemas'] + flags))
        e['comparavel'] = not e['problemas']
        group(oid, key)['evidencias'].append(e)

    # Keep separate documentary/conversation evidence from the revision that
    # explicitly associated it. Historical manual edits remain in sheet history.
    seen = set()
    for r in revisions:
        oid, key = str(r.objeto_id), r.chave
        if oid not in objects or oid in inactive or key == 'estado_registro':
            continue
        src = r.revisao_origem if r.revisao_origem_id else r
        if not src.pagina_origem_id and not (src.mensagem_id and not src.mensagem.pergunta):
            continue
        identity = (oid, key, str(src.pagina_origem_id or src.mensagem_id), src.canal_origem, r.trecho_origem, r.valor_original)
        if identity in seen:
            continue
        seen.add(identity)
        original = r.valor_original
        e = evidence(oid, key, f'fonte-revisao:{r.id}', original, original, origem_visivel(r),
            'documento' if src.pagina_origem_id else 'mensagem', 'fonte_associada_pela_escrevente',
            {'revisao_id': str(r.id), 'fonte_atual': fonte_atual(r)})
        if not fonte_atual(r):
            e['problemas'] += ['leitura_incerta', 'vinculo_incerto']
        elif src.pagina_origem_id and (src.pagina_origem.situacao == 'revisao' or src.pagina_origem.limites_leitura):
            e['problemas'].append('leitura_incerta')
        e['comparavel'] = not e['problemas']
        group(oid, key)['evidencias'].append(e)

    for p in atendimento.propostas_dados.select_related('pagina__anexo__organizacao_atual', 'mensagem').prefetch_related('decisoes__revisao', 'decisoes__organizacao_origem'):
        decisions = list(p.decisoes.all()); decision = decisions[0] if decisions else None
        if decision and decision.acao == 'rejeitada':
            continue
        source = ({'tipo': 'documento', 'anexo_id': str(p.pagina.anexo_id), 'arquivo': p.pagina.anexo.nome,
                   'pagina_id': str(p.pagina_id), 'pagina': p.pagina.numero, 'leitura_versao': p.pagina.leitura_versao,
                   'organizacao_versao': p.pagina.anexo.organizacao_atual.versao if p.pagina.anexo.organizacao_atual_id else 0}
                  if p.pagina_id else {'tipo': 'mensagem', 'mensagem_id': str(p.mensagem_id)})
        source.update(trecho=p.trecho, canal=p.canal, linha=p.linha)
        oid = str(decision.objeto_id) if decision and decision.objeto_id else None
        key = decision.campo or (decision.revisao.chave if decision.revisao_id else '') if decision else ''
        version = decision.versao if decision else 0
        if not oid or not key or oid not in objects:
            unlinked.append({'id': str(p.id), 'rotulo': p.rotulo, 'valor_original': p.valor_original,
                'fonte': source, 'destinos': p.destinos, 'versao_decisao': version,
                'fonte_atual': proposta_atual(p), 'problemas': ['vinculo_incerto']})
            continue
        if oid in inactive:
            continue
        linked.append({'id': str(p.id), 'rotulo': p.rotulo, 'valor_original': p.valor_original, 'fonte': source,
            'destinos': p.destinos, 'versao_decisao': version, 'fonte_atual': proposta_atual(p),
            'objeto_id': oid, 'campo': key})
        valid = proposta_atual(p)
        if p.pagina_id:
            org_id = decision.organizacao_origem_id or (decision.revisao.organizacao_origem_id if decision.revisao_id else None)
            valid = valid and org_id == p.pagina.anexo.organizacao_atual_id and permite(p.pagina.anexo, objects[oid], p.pagina.numero)
        frozen_source = dict(source)
        if p.pagina_id:
            snapshot = decision.organizacao_origem or (decision.revisao.organizacao_origem if decision.revisao_id else None)
            frozen_source.update(organizacao_atual_versao=source['organizacao_versao'], organizacao_versao=snapshot.versao if snapshot else 0)
        e = evidence(oid, key, f'proposta:{p.id}', p.valor_original, p.valor_original, frozen_source, source['tipo'], 'proposta_associada',
                     {'proposta_id': str(p.id), 'decisao_id': str(decision.id), 'versao_decisao': version, 'fonte_atual': bool(valid),
                      'associacao_autor_id': str(decision.autor_id), 'associacao_motivo': decision.justificativa})
        if not valid:
            e['problemas'] += ['vinculo_incerto', 'leitura_incerta']
        elif p.pagina_id and (p.pagina.situacao == 'revisao' or p.pagina.limites_leitura):
            e['problemas'].append('leitura_incerta')
        e['comparavel'] = not e['problemas']
        group(oid, key)['evidencias'].append(e)

    model = atendimento.modelos_minuta.first()
    required_specific = set()
    if model and model.registros_minuta:
        from .blocos_minuta import referencias
        binding = atendimento.vinculacoes_minuta.first()
        if binding and binding.modelo_id == model.id:
            for alias, key in referencias(model):
                if binding.registros.get(alias):
                    required_specific.add((binding.registros[alias], key))
    for rule in model.campos_obrigatorios_ficha if model else []:
        for oid, obj in objects.items():
            if oid not in inactive and obj.tipo == rule['tipo']:
                group(oid, rule['chave'])
    stored = set(atendimento.pendencias_ficha.filter(tipo='comparacao_fontes').values_list('chave', flat=True))
    for g in groups.values():
        g['evidencias'].sort(key=lambda e: e['id'])
        problems = {p for e in g['evidencias'] for p in e['problemas']}
        if not g['evidencias'] or (g['objeto_id'], g['campo']) not in latest:
            problems.add('ausente')
        values = {assinatura(e['normalizacao']['valor']) for e in g['evidencias'] if e['comparavel']}
        if len(values) > 1:
            problems.add('divergencia')
        g['problemas'] = sorted(problems)
        current = latest.get((g['objeto_id'], g['campo']))
        g['revisao_atual'] = {'id': str(current.id), 'situacao': current.situacao, 'versao': current.versao} if current else None
        g['exigido_modelo'] = (g['objeto_id'], g['campo']) in required_specific or any(
            rule['tipo'] == g['tipo_registro'] and rule['chave'] == g['campo'] for rule in (model.campos_obrigatorios_ficha if model else []))
        only_optional_absence = not g['exigido_modelo'] and problems == {'ausente'} and all('ausente' in e['problemas'] for e in g['evidencias'])
        g['conferencia_necessaria'] = bool((problems and not only_optional_absence) or g['chave'] in stored)
        g['normalizacao_aviso'] = 'Representação técnica apenas para comparar, sem substituir o original ou provar identidade. Acentos, zeros e negações são preservados.'
    return {'grupos': sorted(groups.values(), key=lambda g: g['chave']), 'sem_vinculo': unlinked, 'vinculadas': linked,
            'rotulos_problemas': LABELS, 'versao_normalizacao': VERSAO,
            'aviso': 'Sem associação por nome, sem preferência de IA. Dados com leitura/vínculo/formato incertos não são comparados como fatos divergentes.'}
