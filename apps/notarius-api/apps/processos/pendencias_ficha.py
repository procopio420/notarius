"""Versioned review issues derived from evidence and explicit human decisions."""
import json
import uuid
from django.db import transaction, OperationalError, connection
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import (PendenciaFichaAtendimento, HistoricoPendenciaFicha, EventoFichaAtendimento,
                     RevisaoDadoAtendimento)
from .conferencia import assinatura, sem_dado
from .dependencias_ficha import capturar, confirmacao_atual, fonte_atual, resumo_revisao


def _json(value):
    return json.loads(json.dumps(value, default=str, ensure_ascii=False))


def _refs(atendimento, ids):
    result = []
    for rid in ids:
        r = atendimento.revisoes.filter(id=rid, objeto__isnull=False).select_related('objeto', 'pagina_origem__anexo', 'revisao_origem__pagina_origem__anexo').first()
        current = r.objeto.revisoes.filter(chave=r.chave).first() if r else None
        dependencies = capturar(atendimento, r.objeto, r.chave) if r else None
        valid = bool(r and current and current.id == r.id and r.situacao == 'confirmado' and fonte_atual(r)
                     and r.dependencias_ficha == dependencies)
        result.append({'id': str(rid), 'atual': str(current.id) if current else None, 'valida': valid,
                       'dependencias': dependencies})
    return result


def calcular(atendimento):
    from .propostas_dados import consultar_propostas
    from .ficha_estruturada import serializar_revisao
    objects = list(atendimento.objetos_ficha.exclude(tipo='legado'))
    stored = {p.chave: p for p in atendimento.pendencias_ficha.all()}
    proposals = consultar_propostas(atendimento)
    if not objects and not proposals and not stored and not atendimento.analises_documentais.exists():
        return {}
    latest = {}
    for r in atendimento.revisoes.filter(objeto__isnull=False).select_related('objeto', 'autor', 'mensagem', 'pagina_origem__anexo', 'revisao_origem__pagina_origem__anexo'):
        latest.setdefault((r.objeto_id, r.chave), r)
    rows = {}
    inactive = {obj.id for obj in objects if (r := latest.get((obj.id, 'estado_registro'))) and r.valor == 'inativo' and confirmacao_atual(atendimento, r)}
    model = atendimento.modelos_minuta.first()
    required = model.campos_obrigatorios_ficha if model else []
    required_specific = {}
    if model and model.registros_minuta:
        from .blocos_minuta import referencias
        binding = atendimento.vinculacoes_minuta.first()
        if binding and binding.modelo_id == model.id:
            for alias, key in referencias(model):
                oid = binding.registros.get(alias)
                if oid:
                    required_specific.setdefault(oid, set()).add(key)

    def add(key, tipo, title, question, active=True, obj=None, field='', context=None, actions=None):
        old = stored.get(key)
        resolution = old.resolucao if old else {}
        context = _json(context or {})
        if actions:
            refs = _refs(atendimento, resolution.get('revisoes_ids', []))
            context['referencias_resolucao'] = refs
            resolved = (resolution.get('acao') in actions and resolution.get('alvo_hash') == assinatura(context)
                        and all(r['valida'] for r in refs))
            if resolution.get('acao') == 'nao_utilizar':
                resolved = resolved and not context.get('usos_atuais')
            active = not resolved
        rows[key] = {'chave': key, 'tipo': tipo, 'titulo': title, 'pergunta': question, 'ativa': bool(active),
                     'objeto_id': str(obj.id) if obj else None, 'campo': field, 'contexto': context,
                     'acoes': actions or [], 'resolucao': resolution}

    for obj in objects:
        if obj.id in inactive:
            continue
        fields = {key for oid, key in latest if oid == obj.id}
        if obj.tipo == 'complemento':
            fields |= {'categoria', 'situacao'}
        fields |= {r['chave'] for r in required if r['tipo'] == obj.tipo}
        fields |= required_specific.get(str(obj.id), set())
        values = [r for (oid, key), r in latest.items() if oid == obj.id and key != 'estado_registro' and r.valor.strip()]
        add(f'registro:{obj.id}', 'registro_vazio', f'Registro de {obj.tipo} sem dados',
            'Informe os dados que pertencem a este registro ou registre sua desativação na ficha. Não deduzo pessoa, papel ou imóvel.',
            not values, obj, context={'registros': [resumo_revisao(r) for r in values]})
        for key in sorted(fields):
            r = latest.get((obj.id, key))
            mandatory = any(d['tipo'] == obj.tipo and d['chave'] == key for d in required) or key in required_specific.get(str(obj.id), set())
            model_mandatory = mandatory
            mandatory = mandatory or obj.tipo == 'complemento' and key in ['categoria', 'situacao']
            dependencies = capturar(atendimento, obj, key)
            stale = bool(r and r.dependencias_ficha != dependencies)
            kind = ('ausencia' if not r or sem_dado(r.valor) else 'leitura' if not fonte_atual(r) or r.situacao == 'ilegivel'
                    else 'dependencia' if stale else 'divergencia' if r.situacao == 'divergente' else 'confirmacao')
            active = bool((mandatory and (not r or sem_dado(r.valor) or r.situacao == 'ausente')) or
                          r and (not fonte_atual(r) or stale or r.situacao in ['extraido', 'informado', 'divergente', 'ilegivel'] or r.situacao == 'confirmado' and sem_dado(r.valor)))
            if obj.tipo == 'complemento' and key == 'situacao' and r and r.valor == 'a_esclarecer':
                active = True
            label = r.rotulo_original if r and r.rotulo_original else key.replace('_', ' ')
            add(f'dado:{obj.id}:{key}', kind, f'{label} · {obj.tipo}',
                'Confira este dado, sua fonte e o registro correto na ficha detalhada. Uma confirmação de outro campo ou de arquivo inteiro não resolve esta pendência.',
                active, obj, key, {'revisao': serializar_revisao(r, atendimento, dependencies) if r else None, 'dependencias': dependencies,
                                  'exigido_modelo': model_mandatory, **({'classificacao_tecnica': key in ['categoria', 'situacao']} if obj.tipo == 'complemento' else {}),
                                  'modelo_regra': str(model.id) if model and model_mandatory else None})
        for parent_id in [obj.pessoa_a_id, obj.pessoa_b_id, obj.imovel_id]:
            if parent_id:
                add(f'vinculo:{obj.id}:{parent_id}', 'vinculo_inativo', 'Vínculo com registro desativado',
                    'Este papel, relação ou negócio aponta para um registro desativado. Confira a associação e corrija os registros explicitamente na ficha.',
                    parent_id in inactive, obj, context={'registro_vinculado': str(parent_id), 'inativo': parent_id in inactive})

    from .comparacao_fontes import comparar
    for comparison in comparar(atendimento)['grupos']:
        if comparison['conferencia_necessaria']:
            obj = next(o for o in objects if str(o.id) == comparison['objeto_id'])
            add(comparison['chave'], 'comparacao_fontes', f"Comparação de fontes · {comparison['rotulo']}",
                'Confira as fontes lado a lado, corrija o dado na ficha se necessário e registre a decisão humana com todas as evidências consideradas. Nenhuma fonte foi escolhida automaticamente.',
                obj=obj, field=comparison['campo'], context=comparison,
                actions=['vincular', 'nao_utilizar'] if not comparison['exigido_modelo'] and comparison['revisao_atual'] and comparison['revisao_atual']['situacao'] == 'ausente' else ['vincular'])

    for proposal in proposals:
        last = proposal['decisoes'][0] if proposal['decisoes'] else None
        obj = next((o for o in objects if last and str(o.id) == last['objeto_id']), None)
        add(f"proposta:{proposal['id']}", 'proposta', f"Proposta: {proposal['rotulo']}",
            'Abra a fonte e o contexto. Associe e confirme na ficha ou registre explicitamente que não usará a proposta.',
            proposal['situacao'] in ['pendente', 'associada', 'reaberta'], obj,
            context={'proposta': proposal})

    for message in atendimento.mensagens.filter(pergunta='', campo=''):
        for number, line in enumerate(message.texto.splitlines(), 1):
            if not line.strip():
                continue
            represented = [p for p in proposals if p['origem'].get('mensagem_id') == str(message.id) and p['origem']['linha'] == number and p['trecho'] == line]
            resolved = represented and all(p['situacao'] in ['aceita', 'rejeitada', 'substituida'] for p in represented)
            key = f'trecho:{message.id}:{number}'
            if represented:
                add(key, 'trecho', 'Trecho da conversa', 'A revisão deste trecho acompanha as propostas vinculadas à mesma linha.',
                    False, context={'mensagem_id': str(message.id), 'linha': number, 'trecho': line, 'propostas': [p['id'] for p in represented], 'tratado': bool(resolved)})
            else:
                add(key, 'trecho', 'Trecho da conversa ainda sem destino',
                    'Confira a linha inteira. Vincule-a a dados efetivamente revisados ou registre, com motivo, que não será utilizada. Uma mensagem mais recente não encerra esta dúvida.',
                    context={'mensagem_id': str(message.id), 'linha': number, 'trecho': line}, actions=['vincular', 'nao_utilizar'])

    for file in atendimento.anexos.defer('conteudo').prefetch_related('paginas'):
        if file.organizacao_atual_id and file.organizacao_atual.finalidade in ['referencia_redacao', 'nao_utilizar']:
            continue
        pages = [p for p in file.paginas.all() if p.leitura_versao == file.leitura_versao]
        if not pages:
            add(f'arquivo:{file.id}:{file.leitura_versao}', 'arquivo_sem_leitura', file.nome,
                'Não há leitura suficiente deste arquivo. Envie outra cópia ou registre explicitamente que não o utilizará; não presumo seu conteúdo.',
                context={'anexo_id': str(file.id), 'leitura_versao': file.leitura_versao, 'aviso': file.aviso}, actions=['nao_utilizar'])
        for page in pages:
            uses = [r for r in latest.values() if r.objeto_id not in inactive and (r.pagina_origem_id == page.id or r.revisao_origem_id and r.revisao_origem.pagina_origem_id == page.id)]
            page_proposals = [p for p in proposals if p['origem'].get('pagina_id') == str(page.id)]
            add(f'pagina:{page.id}', 'pagina', f'{file.nome} · página {page.numero}',
                'Confira esta página no original e o destino de seus dados. A revisão da página não confirma campos nem resolve propostas pendentes.',
                context={'pagina_id': str(page.id), 'anexo_id': str(file.id), 'arquivo': file.nome, 'numero': page.numero,
                         'leitura_versao': page.leitura_versao, 'situacao_leitura': page.situacao, 'aviso': page.aviso,
                         'texto': page.texto, 'texto_ocr': page.texto_ocr,
                         'usos_atuais': [str(r.id) for r in uses],
                         'propostas': [{'id': p['id'], 'situacao': p['situacao'], 'versao': p['versao_decisao']} for p in page_proposals]},
                actions=['vincular', 'nao_utilizar'])

    from .analise_documental import duvidas_atuais
    for issue in duvidas_atuais(atendimento):
        add(issue['chave'], 'analise_documental', issue['titulo'], issue['pergunta'],
            active=issue['ativa'], context=issue['contexto'],
            actions=['vincular', 'nao_utilizar'] if issue['contexto']['fonte_atual'] else ['nao_utilizar'])

    for old in stored.values():
        if old.tipo == 'manual' and old.objeto_id not in inactive:
            obj = next((o for o in objects if o.id == old.objeto_id), None)
            r = latest.get((old.objeto_id, old.campo))
            add(old.chave, 'manual', old.contexto.get('titulo', 'Dúvida registrada pela escrevente'),
                old.contexto.get('pergunta', 'Confira a dúvida registrada.'), obj=obj, field=old.campo,
                context={'titulo': old.contexto.get('titulo'), 'pergunta': old.contexto.get('pergunta'),
                         'revisao_atual': resumo_revisao(r), 'dependencias': capturar(atendimento, obj, old.campo) if obj else {}}, actions=['vincular'])
    return rows


def _estado(old, row):
    if not row or not row['ativa']:
        return 'resolvida'
    revision = row['contexto'].get('revisao') or {}
    return 'reaberta' if (old and old.situacao in ['resolvida', 'reaberta']) or (row['tipo'] in ['dependencia', 'leitura'] and revision.get('situacao') == 'confirmado') else 'aberta'


def sincronizar(atendimento, autor=None, motivo='Conferência atualizada a partir dos registros e decisões existentes.'):
    rows = calcular(atendimento)
    existing = {p.chave: p for p in atendimento.pendencias_ficha.all()}
    for key in set(rows) | set(existing):
        row, old = rows.get(key), existing.get(key)
        if not old and not row['ativa']:
            continue
        context = row['contexto'] if row else {'condicao_atual': 'Não se aplica ao estado atual dos registros; histórico preservado.'}
        state = _estado(old, row)
        digest = assinatura([context, state])
        if old and old.assinatura == digest:
            continue
        if not old:
            old = PendenciaFichaAtendimento(atendimento=atendimento, tenant=atendimento.tenant,
                id=uuid.uuid5(uuid.NAMESPACE_URL, f'notarius:{atendimento.id}:{key}'), chave=key,
                tipo=row['tipo'], objeto_id=row['objeto_id'], campo=row['campo'])
        old.situacao = state; old.assinatura = digest; old.contexto = context; old.versao += 1
        if row:
            old.tipo = row['tipo']
        old.save()
        HistoricoPendenciaFicha.objects.create(atendimento=atendimento, tenant=atendimento.tenant, pendencia=old,
            versao=old.versao, situacao=state, assinatura=digest, contexto=context, resolucao=old.resolucao,
            autor=autor, motivo=motivo)
    return rows


def consultar(atendimento):
    rows = calcular(atendimento)
    old = {p.chave: p for p in atendimento.pendencias_ficha.prefetch_related('historico__autor')}
    result = []
    for key in set(rows) | set(old):
        row, record = rows.get(key), old.get(key)
        if not record and not row['ativa']:
            continue
        state = _estado(record, row)
        context = row['contexto'] if row else {'condicao_atual': 'Não se aplica ao estado atual dos registros; histórico preservado.'}
        digest = assinatura([context, state])
        version = (record.versao if record else 0) + int(not record or record.assinatura != digest)
        result.append({**(row or {'chave': key, 'tipo': record.tipo, 'titulo': record.contexto.get('titulo', key),
                       'pergunta': 'Condição encerrada; consulte o histórico.', 'objeto_id': str(record.objeto_id) if record.objeto_id else None,
                       'campo': record.campo, 'acoes': [], 'ativa': False}),
                       'id': str(record.id if record else uuid.uuid5(uuid.NAMESPACE_URL, f'notarius:{atendimento.id}:{key}')),
                       'situacao': state, 'assinatura': digest, 'versao': version, 'contexto': context,
                       'historico': [{'versao': h.versao, 'situacao': h.situacao, 'autor': h.autor.get_full_name() or h.autor.username if h.autor else 'Atualização de estado',
                                     'data': h.created_at.isoformat(), 'motivo': h.motivo, 'contexto': h.contexto,
                                     'resolucao': h.resolucao} for h in record.historico.all()] if record else []})
    return sorted(result, key=lambda r: (r['situacao'] == 'resolvida', r['chave']))


class PedidoSerializer(serializers.Serializer):
    operacao = serializers.ChoiceField(choices=['atualizar', 'abrir', 'resolver'])
    client_id = serializers.UUIDField(required=False)
    objeto_id = serializers.UUIDField(required=False)
    campo = serializers.CharField(max_length=40, required=False)
    pergunta = serializers.CharField(max_length=2000, required=False)
    pendencia_id = serializers.UUIDField(required=False)
    assinatura = serializers.CharField(max_length=64, required=False)
    versao_esperada = serializers.IntegerField(min_value=1, required=False)
    justificativa = serializers.CharField(max_length=2000, required=False)
    acao = serializers.ChoiceField(choices=['vincular', 'nao_utilizar'], required=False)
    revisoes_ids = serializers.ListField(child=serializers.UUIDField(), max_length=100, default=list)
    evidencias_ids = serializers.ListField(child=serializers.CharField(max_length=180), max_length=500, default=list)
    confirmei_revisao = serializers.BooleanField(default=False)


def executar(atendimento, user, payload):
    from .ficha_estruturada import FichaAlterada, reservar_atendimento
    from .ficha_estruturada_schema import schema_atual
    s = PedidoSerializer(data=payload); s.is_valid(raise_exception=True); data = s.validated_data
    try:
        with transaction.atomic():
            reservar_atendimento(atendimento)
            if data['operacao'] == 'atualizar':
                sincronizar(atendimento)
                return {'pendencias': consultar(atendimento)}, False
            if not data.get('client_id') or not data.get('justificativa'):
                raise ValidationError('Informe motivo e identificador da decisão.')
            digest = assinatura(data)
            previous = atendimento.eventos_ficha.filter(client_id=data['client_id']).first()
            if previous:
                if previous.autor_id != user.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador já utilizado com outro conteúdo ou autora.')
                return previous.resultado, False
            sincronizar(atendimento)
            if data['operacao'] == 'abrir':
                obj = get_object_or_404(atendimento.objetos_ficha.exclude(tipo='legado'), id=data.get('objeto_id'), tenant_id=atendimento.tenant_id)
                if data.get('campo') not in {f['chave'] for f in schema_atual(atendimento)[obj.tipo]} or not data.get('pergunta'):
                    raise ValidationError('Escolha campo configurado e descreva a dúvida.')
                key = f'manual:{data["client_id"]}'
                record = PendenciaFichaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant,
                    chave=key, tipo='manual', objeto=obj, campo=data['campo'], assinatura='',
                    contexto={'titulo': 'Dúvida registrada pela escrevente', 'pergunta': data['pergunta']})
            else:
                record = get_object_or_404(atendimento.pendencias_ficha, id=data.get('pendencia_id'), tenant_id=atendimento.tenant_id)
                row = next((r for r in consultar(atendimento) if r['id'] == str(record.id)), None)
                if not row or row['situacao'] == 'resolvida' or data.get('assinatura') != row['assinatura'] or data.get('versao_esperada') != row['versao']:
                    raise FichaAlterada('A pendência ou suas fontes mudaram. Atualize antes de decidir.')
                if data.get('acao') not in row['acoes'] or not data['confirmei_revisao']:
                    raise ValidationError('Esta pendência exige revisão específica na ficha ou nas propostas; não pode ser encerrada genericamente.')
                ids = [str(i) for i in data['revisoes_ids']]
                if data['acao'] == 'vincular' and (not ids or not all(r['valida'] for r in _refs(atendimento, ids))):
                    raise ValidationError('Vincule revisões atuais, confirmadas e com fontes/dependências atuais.')
                context = row['contexto']
                revisions = list(atendimento.revisoes.filter(id__in=ids, objeto__isnull=False))
                if row['tipo'] == 'comparacao_fontes':
                    considered = data['evidencias_ids']
                    expected = [e['id'] for e in context['evidencias']]
                    if len(considered) != len(set(considered)) or set(considered) != set(expected):
                        raise ValidationError('Confira e identifique todas as evidências deste conjunto, inclusive as que não utilizará.')
                    if data['acao'] == 'vincular':
                        if len(revisions) != 1 or len(ids) != 1 or str(revisions[0].objeto_id) != row['objeto_id'] or revisions[0].chave != row['campo']:
                            raise ValidationError('Escolha somente a revisão confirmada atual deste registro e campo.')
                        from .comparacao_fontes import normalizar_campo
                        chosen = revisions[0]
                        configured = next((f for f in schema_atual(atendimento)[chosen.objeto.tipo] if f['chave'] == chosen.chave), {})
                        if normalizar_campo(chosen.objeto.tipo, chosen.chave, chosen.valor, configured.get('opcoes'))['problemas']:
                            raise ValidationError('Corrija o dado ausente ou de formato inconsistente antes de escolhê-lo para a minuta.')
                    elif context['exigido_modelo'] or not context['revisao_atual'] or context['revisao_atual']['situacao'] != 'ausente':
                        raise ValidationError('Somente campo opcional explicitamente marcado ausente pode ficar sem uso.')
                if row['tipo'] == 'manual' and any(str(r.objeto_id) != row['objeto_id'] or r.chave != row['campo'] for r in revisions):
                    raise ValidationError('A revisão deve corresponder exatamente ao registro e campo desta dúvida.')
                if row['tipo'] == 'trecho' and any(str(r.mensagem_id) != context['mensagem_id'] or context['trecho'] not in r.trecho_origem for r in revisions):
                    raise ValidationError('As revisões precisam manter esta mensagem e a linha inteira como fonte.')
                if row['tipo'] == 'analise_documental' and any(str(r.pagina_origem_id) != context['fonte']['pagina_id'] or not r.trecho_origem or r.trecho_origem not in context['trecho'] for r in revisions):
                    raise ValidationError('A resolução deve apontar para dados revisados desta unidade documental, sem misturar páginas ou participantes.')
                if row['tipo'] == 'pagina':
                    if any(p['situacao'] not in ['aceita', 'rejeitada', 'substituida'] for p in context['propostas']):
                        raise ValidationError('Resolva as propostas desta página individualmente antes da revisão da página.')
                    if data['acao'] == 'vincular' and (not set(context['usos_atuais']).issubset(ids) or any(str(r.pagina_origem_id) != context['pagina_id'] and not (r.revisao_origem_id and str(r.revisao_origem.pagina_origem_id) == context['pagina_id']) for r in revisions)):
                        raise ValidationError('Inclua todos os dados atuais que utilizam esta página, sem misturar outras fontes.')
                if data['acao'] == 'nao_utilizar' and (ids or context.get('usos_atuais')):
                    raise ValidationError('Revise os dados que ainda usam esta fonte antes de desconsiderá-la.')
                record.resolucao = {'acao': data['acao'], 'revisoes_ids': ids, 'autor_id': str(user.id), 'motivo': data['justificativa']}
                if row['tipo'] == 'comparacao_fontes':
                    record.resolucao.update(evidencias_ids=data['evidencias_ids'], evidencias_consideradas=context['evidencias'],
                        revisao_escolhida_id=ids[0] if ids else None, valor_escolhido=revisions[0].valor if revisions else None,
                        campo_opcional_sem_uso=data['acao'] == 'nao_utilizar', versao_normalizacao=context['versao_normalizacao'])
                record.save(update_fields=['resolucao'])
                new_context = calcular(atendimento)[record.chave]['contexto']
                record.resolucao['alvo_hash'] = assinatura(new_context)
                record.save(update_fields=['resolucao'])
            sincronizar(atendimento, user, data['justificativa'])
            result = {'pendencia_id': str(record.id)}
            EventoFichaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, autor=user,
                client_id=data['client_id'], requisicao_hash=digest, resultado=result)
            return result, True
    except OperationalError as error:
        if connection.vendor == 'sqlite' and 'locked' in str(error).lower():
            raise FichaAlterada() from None
        raise
