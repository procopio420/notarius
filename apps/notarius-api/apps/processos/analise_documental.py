"""Atomic proposal-only pipeline. Provider output has no write authority over the sheet."""
import json
import re
from copy import deepcopy
from django.conf import settings
from django.db import connection, transaction, OperationalError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from pydantic import ValidationError as ContratoInvalido
from .contratos_documentais import PedidoAnalise, EntradaDocumental, SaidaDocumental
from .provedor_documental import ProvedorIndisponivel, RespostaInvalida, ProvedorReal, provedor_do_ambiente
from .conferencia import assinatura, normalizar
from .politica_documental import LIMITES, codigo_falha
from .ficha_estruturada import FichaAlterada, reservar_atendimento
from .ficha_estruturada_schema import schema_atual
from .models import AnaliseDocumentalAtendimento, PropostaDadoAtendimento, Atendimento


def ambiente_de_teste():
    name = str(connection.settings_dict['NAME'])
    return bool(getattr(settings, 'NOTARIUS_TESTE_ANALISE_DOCUMENTAL', False)
                and (name.startswith('file:memorydb_') or name == ':memory:' or name.rsplit('/', 1)[-1].startswith('test_')))


def suspeita(text):
    return bool(re.search(r'(ignore|desconsidere).*(instruco|regras|sistema)|(^|\s)(system|assistant|developer)\s*:|confirme tudo|revele.*chave|execute.*comando', normalizar(text)))


def montar_entrada(atendimento, pedido):
    ids = [d.documento_id for d in pedido.documentos]
    if len(set(ids)) != len(ids):
        raise ValidationError('Documento repetido na mesma análise.')
    unidades, documentos = [], []
    for selected in pedido.documentos:
        file = get_object_or_404(atendimento.anexos.select_related('organizacao_atual'), id=selected.documento_id, tenant_id=atendimento.tenant_id)
        org = file.organizacao_atual
        if file.leitura_versao != selected.leitura_versao or not org or org.versao != selected.organizacao_versao:
            raise FichaAlterada('A leitura ou classificação mudou. Reabra os documentos antes da análise.')
        if org.finalidade != 'caso' or not org.tipo_documento or not org.vinculos or org.leitura_versao != file.leitura_versao:
            raise ValidationError('Somente documentos do caso com classificação e vínculos atuais podem ser analisados. Referências de redação são excluídas.')
        pages = list(file.paginas.filter(leitura_versao=file.leitura_versao).order_by('numero'))
        if not pages:
            raise ValidationError('Arquivo sem páginas disponíveis para análise. Confira a falha de leitura no original.')
        documentos.append([str(file.id), file.sha256, file.leitura_versao, str(org.id), file.metadados_leitura, file.situacao, file.aviso])
        for page in pages:
            channels = [('ocr' if page.metodo == 'ocr_local' else 'texto', page.texto)]
            if page.texto_ocr and page.texto_ocr != page.texto:
                channels.append(('ocr', page.texto_ocr))
            for channel, text in channels:
                lines = [(n, line) for n, line in enumerate(text.splitlines(), 1) if line.strip()] or [(1, '')]
                for n, line in lines:
                    unidades.append({'unidade_id': f'{page.id}:{channel}:{n}',
                        'fonte': {'documento_id': str(file.id), 'pagina_id': str(page.id), 'pagina': page.numero,
                                  'leitura_versao': page.leitura_versao, 'organizacao_versao': org.versao, 'canal': channel},
                        'linha': n, 'texto': line, 'leitura_incerta': page.situacao == 'revisao' or not text.strip(),
                        'limites': sorted(set(page.limites_leitura + file.metadados_leitura.get('limites', []))),
                        'instrucao_suspeita': suspeita(line),
                        'destinatarios': sorted({v['objeto_id'] for v in org.vinculos if not v['paginas'] or page.numero in v['paginas']}, key=str)})
                    if len(unidades) > LIMITES.unidades or len(line) > LIMITES.caracteres_unidade:
                        raise ValidationError('Limite de 200 unidades ou 4.000 caracteres por linha atingido. Nenhum trecho foi truncado; selecione um conjunto menor.')
    if sum(len(u['texto']) for u in unidades) > LIMITES.caracteres_texto:
        raise ValidationError('Limite de 100.000 caracteres atingido; nenhuma análise parcial foi aplicada.')
    registros = [{'id': str(o.id), 'tipo': o.tipo,
                  **{k: str(getattr(o, k)) if getattr(o, k) else None for k in ['pessoa_a_id', 'pessoa_b_id', 'imovel_id']}}
                 for o in atendimento.objetos_ficha.exclude(tipo='legado')]
    campos = [{'tipo': tipo, 'chave': f['chave'], 'rotulo': f['rotulo'], 'opcoes': f.get('opcoes')}
              for tipo, fields in schema_atual(atendimento).items() for f in fields if f['chave'] != 'estado_registro']
    material = {'contrato': 'documental_v1', 'atendimento_id': str(atendimento.id), 'unidades': unidades, 'registros': registros, 'campos': campos}
    if len(json.dumps(material, ensure_ascii=False).encode('utf-8')) > LIMITES.bytes_requisicao:
        raise ValidationError('Entrada completa excede o limite de bytes, incluindo metadados. Nenhum dado truncado ou enviado.')
    model = atendimento.modelos_minuta.first()
    context = assinatura([material, documentos, str(model.id) if model else None,
                          list(atendimento.mensagens.order_by('id').values_list('id', 'correcao_de_id')),
                          list(atendimento.revisoes.order_by('id').values_list('id', flat=True))])
    if len(json.dumps({**material,'contexto_assinatura':context},ensure_ascii=False).encode('utf-8'))>LIMITES.bytes_requisicao:
        raise ValidationError('Entrada documental com contexto excede o limite de bytes. Nenhum dado truncado ou enviado.')
    try:
        return EntradaDocumental.model_validate({**material, 'contexto_assinatura': context})
    except ContratoInvalido:
        raise ValidationError('Entrada fora dos limites do contrato documental. Nenhum conteúdo foi truncado ou enviado.') from None


def validar_saida(entrada, raw):
    try:
        if isinstance(raw, SaidaDocumental):
            raw = raw.model_dump()
        if len(json.dumps(raw, ensure_ascii=False).encode('utf-8')) > LIMITES.bytes_resposta:
            raise RespostaInvalida('Resposta acima do limite de 500.000 bytes.')
        saida = SaidaDocumental.model_validate(raw).model_dump()
    except (ContratoInvalido, ValueError, TypeError, RecursionError):
        raise RespostaInvalida('Contrato de saída inválido. Nenhuma proposta foi aplicada.') from None
    if saida['contexto_assinatura'] != entrada.contexto_assinatura:
        raise RespostaInvalida('Resposta pertence a outro contexto.')
    expected = {u.unidade_id: u for u in entrada.unidades}
    actual = [u['unidade_id'] for u in saida['unidades']]
    if len(set(actual)) != len(actual) or set(actual) != set(expected):
        raise RespostaInvalida('Há unidade omitida, duplicada ou inexistente; operação inteira interrompida.')
    fields = {(f.tipo, f.chave): f for f in entrada.campos}
    objects = {r.id: r for r in entrada.registros}
    original = deepcopy(saida)
    count = 0
    for row in saida['unidades']:
        unit = expected[row['unidade_id']]
        if any(not d.strip() for d in row['duvidas']):
            raise RespostaInvalida('Dúvida vazia não resolve unidade sem interpretação.')
        if not row['propostas'] and not row['duvidas'] or row['situacao'] == 'revisao_manual' and not row['duvidas'] or row['situacao'] == 'propostas' and not row['propostas']:
            raise RespostaInvalida('Unidade sem proposta ou dúvida explícita; ausência de informação não é inexistência do fato.')
        if (unit.instrucao_suspeita or not unit.texto.strip()) and (row['propostas'] or not row['duvidas']):
            raise RespostaInvalida('Instrução suspeita ou página sem texto exige dúvida, não propostas.')
        seen = set()
        for p in row['propostas']:
            count += 1
            digest = assinatura(p)
            if digest in seen or count > 200:
                raise RespostaInvalida('Propostas duplicadas ou limite de 200 propostas atingido.')
            seen.add(digest)
            if p['fonte'] != unit.fonte.model_dump() or p['fim'] <= p['inicio'] or p['fim'] > len(unit.texto) or unit.texto[p['inicio']:p['fim']] != p['trecho']:
                raise RespostaInvalida('Documento, página, leitura, canal, versão ou trecho não corresponde à fonte enviada.')
            if not p['valor'].strip() or p['valor'] not in p['trecho'] or (p['tipo_registro'], p['campo']) not in fields:
                raise RespostaInvalida('Valor inventado ou campo fora do modelo configurado. Nenhuma proposta aplicada.')
            field = fields[p['tipo_registro'], p['campo']]
            if field.opcoes is not None and p['valor'] not in field.opcoes:
                raise RespostaInvalida('Valor incompatível com as opções do campo. Não normalize ou suponha: encaminhe para dúvida.')
            oid, related = p['registro_sugerido_id'], p['relacionado_id']
            if p['associacao'] == 'incerta' and (oid or related) or p['associacao'] == 'sugerida' and (not oid or not related):
                raise RespostaInvalida('Associação incerta deve manter os identificadores nulos.')
            if oid:
                obj = objects.get(oid)
                if not obj or obj.tipo != p['tipo_registro'] or obj.tipo not in ['pessoa', 'imovel'] or related != oid:
                    raise RespostaInvalida('Registro incompatível ou associação automática de papel/relação/negócio. A escrevente deve escolher esses vínculos.')
                if related not in unit.destinatarios:
                    raise RespostaInvalida('Pessoa/imóvel não corresponde ao vínculo de página conferido pela escrevente.')
                if unit.destinatarios != [oid]:
                    p.update(registro_sugerido_id=None, relacionado_id=None, associacao='incerta')
                    row['duvidas'].append('Vários destinatários nesta página: sugestão de associação retirada; a escrevente deve identificar a quem pertence cada dado.')
            if p['associacao'] == 'incerta':
                row['duvidas'].append('Destino incerto para esta proposta: escolher pessoa, imóvel, papel ou relação explicitamente; nomes e trechos literais não resolvem o vínculo.')
        # Never treat a coverage declaration as a completeness guarantee.
        if unit.leitura_incerta or unit.limites:
            row['duvidas'].append('Leitura parcial, incerta ou limitada: conferir o original. Não inferir inexistência de fatos.')
        row['duvidas'] = list(dict.fromkeys(row['duvidas']))
    return {'resposta': original, 'validada': saida}


def verificar_provedor(provider):
    if type(provider) is ProvedorReal:
        raise ProvedorIndisponivel(codigo='ia_bloqueada')
    if not ambiente_de_teste() or getattr(provider, 'identificador', None) != 'simulado_documental_teste_v1':
        raise ProvedorIndisponivel(codigo='simulacao_fora_teste')


def executar(atendimento, user, payload, *, provedor=None):
    try:
        pedido = PedidoAnalise.model_validate(payload)
    except ContratoInvalido:
        raise ValidationError('Pedido documental inválido: informe identificador e até cinco documentos com leitura/classificação esperadas. Outros campos não são aceitos.') from None
    digest = assinatura(pedido.model_dump())
    previous = atendimento.analises_documentais.filter(client_id=pedido.client_id).first()
    if previous:
        if previous.autor_id != user.id or previous.requisicao_hash != digest:
            raise ValidationError('Identificador de análise já utilizado com outra autora ou conteúdo.')
        verificar_provedor(provedor if provedor is not None else provedor_do_ambiente())
        return resultado(previous), False
    entrada = montar_entrada(atendimento, pedido)
    provider = provedor if provedor is not None else provedor_do_ambiente()
    verificar_provedor(provider)
    try:
        raw = provider.analisar(entrada.model_copy(deep=True))
    except ProvedorIndisponivel as error:
        raise ProvedorIndisponivel(codigo=codigo_falha(error)) from None
    except RespostaInvalida:
        raise RespostaInvalida('Resposta recusada ou incompleta pelo provedor; nenhuma proposta aplicada.') from None
    except Exception as error:
        raise ProvedorIndisponivel(codigo=codigo_falha(error)) from None
    saida = validar_saida(entrada, raw)
    try:
        with transaction.atomic():
            reservar_atendimento(atendimento)
            previous = atendimento.analises_documentais.filter(client_id=pedido.client_id).first()
            if previous:
                if previous.autor_id != user.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador já utilizado com outro conteúdo/autora.')
                return resultado(previous), False
            if montar_entrada(atendimento, pedido).contexto_assinatura != entrada.contexto_assinatura:
                raise FichaAlterada('Fontes, ficha ou modelo mudaram durante a análise; nenhuma proposta foi aplicada.')
            # Compare only explicitly suggested identical records/fields. Never
            # group unassigned names or different people's values as one fact.
            groups = {}
            for row in saida['validada']['unidades']:
                for p in row['propostas']:
                    if p['registro_sugerido_id']:
                        key = (p['registro_sugerido_id'], p['campo'])
                        groups.setdefault(key, []).append((row, p['valor']))
            for (oid, key), group in groups.items():
                current = atendimento.revisoes.filter(objeto_id=oid, chave=key).first()
                values = {v for _, v in group} | ({current.valor} if current else set())
                if len(values) > 1:
                    for row, _ in group:
                        row['duvidas'] = list(dict.fromkeys(row['duvidas'] + ['Divergência para o mesmo registro/campo: a escrevente deve comparar as fontes e decidir; nenhum valor foi escolhido ou sobrescrito.']))
            try:
                SaidaDocumental.model_validate(saida['validada'])
            except ContratoInvalido:
                raise RespostaInvalida('Limites do resultado validado atingidos, inclusive dúvidas de revisão. Nenhuma proposta foi aplicada.') from None
            record = AnaliseDocumentalAtendimento.objects.create(atendimento=atendimento, tenant_id=atendimento.tenant_id,
                autor=user, client_id=pedido.client_id, requisicao_hash=digest, contexto_assinatura=entrada.contexto_assinatura,
                provedor=provider.identificador, entrada=entrada.model_dump(), saida=saida)
            units = {u.unidade_id: u for u in entrada.unidades}
            fields = {(f.tipo, f.chave): f for f in entrada.campos}
            for row in saida['validada']['unidades']:
                unit = units[row['unidade_id']]
                for p in row['propostas']:
                    field = fields[p['tipo_registro'], p['campo']]
                    PropostaDadoAtendimento.objects.create(atendimento=atendimento, tenant_id=atendimento.tenant_id, autor=user,
                        pagina_id=unit.fonte.pagina_id, metodo='documental_simulado_teste_v1' if type(provider) is not ProvedorReal else 'documental_ia_v1',
                        analise_documental=record, evidencia_estruturada={**p, 'unidade_id': unit.unidade_id, 'contexto': unit.texto},
                        canal=unit.fonte.canal, linha=unit.linha, rotulo=field.rotulo, valor_original=p['valor'], trecho=p['trecho'],
                        destinos=[{'tipo': field.tipo, 'chave': field.chave, 'rotulo': field.rotulo}],
                        origem_hash=assinatura([str(record.id), unit.unidade_id, p]))
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, user, 'Análise documental estruturada: somente propostas e dúvidas, sem confirmação.')
            Atendimento.objects.filter(pk=atendimento.pk).update(updated_at=timezone.now())
            return resultado(record), True
    except OperationalError as error:
        if connection.vendor == 'sqlite' and 'locked' in str(error).lower():
            raise FichaAlterada() from None
        raise


def resultado(record):
    return {'analise_id': str(record.id), 'provedor': record.provedor,
            'simulado': record.provedor != ProvedorReal.identificador,
            'propostas_ids': [str(i) for i in record.propostas.values_list('id', flat=True)],
            'unidades': record.saida['validada']['unidades'], 'confirmado': False,
            'aviso': 'Somente propostas para revisão humana. Trecho literal não garante interpretação correta. Nenhum campo confirmado foi alterado.'}


def duvidas_atuais(atendimento):
    """Persistent questions derived from immutable analysis, using current source state."""
    result = []
    latest = {}
    for r in atendimento.revisoes.filter(objeto__isnull=False):
        latest.setdefault((r.objeto_id, r.chave), r)
    for record in atendimento.analises_documentais.all():
        for row in record.saida['validada']['unidades']:
            if not row['duvidas']:
                continue
            unit = next(u for u in record.entrada['unidades'] if u['unidade_id'] == row['unidade_id'])
            source = unit['fonte']
            page = atendimento.anexos.filter(id=source['documento_id']).select_related('organizacao_atual').first()
            org = page.organizacao_atual if page else None
            current = bool(page and page.leitura_versao == source['leitura_versao'] and org and org.versao == source['organizacao_versao'] and org.finalidade == 'caso')
            result.append({'chave': f'analise:{record.id}:{unit["unidade_id"]}',
                'titulo': 'Dúvida da análise documental (simulada em teste)' if record.provedor != ProvedorReal.identificador else 'Dúvida da análise documental',
                'pergunta': ('Fonte da análise substituída ou reclassificada. A dúvida continua pendente até decisão explícita da escrevente. ' if not current else '') + ' '.join(row['duvidas']), 'ativa': True,
                'contexto': {'analise_id': str(record.id), 'unidade_id': unit['unidade_id'], 'fonte': source,
                            'trecho': unit['texto'], 'duvidas': row['duvidas'], 'fonte_atual': current,
                            'usos_atuais': [str(r.id) for r in latest.values() if current and str(r.pagina_origem_id) == source['pagina_id']
                                           and r.trecho_origem and (unit['texto'] in r.trecho_origem or r.trecho_origem in unit['texto'])]}})
    return result
