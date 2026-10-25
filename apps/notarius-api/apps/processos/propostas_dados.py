"""Persisted local label proposals and human decisions. No semantic inference."""
import re
from django.db import transaction, OperationalError, connection
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import (PropostaDadoAtendimento, DecisaoPropostaAtendimento, EventoFichaAtendimento,
                     Atendimento, RevisaoDadoAtendimento)
from .conferencia import normalizar, assinatura
from .ficha_estruturada_schema import schema_atual
from .ficha_estruturada import FichaAlterada, reservar_atendimento


class PedidoSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    operacao = serializers.ChoiceField(choices=['extrair', 'rejeitar', 'associar'])
    objeto_id = serializers.UUIDField(required=False)
    campo = serializers.CharField(max_length=40, required=False)
    organizacao_versao = serializers.IntegerField(min_value=0, required=False)
    conferir_associacao = serializers.BooleanField(default=False)
    anexo_id = serializers.UUIDField(required=False)
    mensagem_id = serializers.UUIDField(required=False)
    leitura_versao = serializers.IntegerField(min_value=1, required=False)
    proposta_id = serializers.UUIDField(required=False)
    versao_esperada = serializers.IntegerField(min_value=0, required=False)
    justificativa = serializers.CharField(max_length=2000, required=False)


def fonte_atual(proposta):
    if not proposta.pagina_id:
        from .conversa_orientada import mensagem_atual
        return mensagem_atual(proposta.mensagem)
    org = proposta.pagina.anexo.organizacao_atual
    if proposta.analise_documental_id and (not org or org.versao != proposta.evidencia_estruturada.get('fonte', {}).get('organizacao_versao')):
        return False
    return proposta.pagina.leitura_versao == proposta.pagina.anexo.leitura_versao and (not org or org.finalidade not in ['referencia_redacao', 'nao_utilizar'])


def serializar(proposta):
    decisions = list(proposta.decisoes.all())
    last = decisions[0] if decisions else None
    current_source = fonte_atual(proposta)
    state = last.acao if last else 'pendente'
    if not current_source and state != 'rejeitada':
        state = 'reaberta' if last else 'leitura_substituida' if proposta.pagina_id else 'mensagem_corrigida'
    if last and last.revisao_id and current_source:
        current = proposta.atendimento.revisoes.filter(objeto_id=last.objeto_id, chave=last.revisao.chave).first()
        if current and current.id != last.revisao_id:
            state = 'substituida'
        else:
            from .organizacao_anexos import fonte_valida
            if not fonte_valida(last.revisao):
                state = 'reaberta'
    if proposta.pagina_id and proposta.pagina.anexo.organizacao_atual_id:
        purpose = proposta.pagina.anexo.organizacao_atual.finalidade
        if purpose in ['referencia_redacao', 'nao_utilizar']:
            state = purpose
    if proposta.pagina_id:
        page = proposta.pagina
        origin = {'tipo': 'documento', 'pagina_id': str(page.id), 'anexo_id': str(page.anexo_id),
                  'arquivo': page.anexo.nome, 'pagina': page.numero, 'leitura_versao': page.leitura_versao,
                  'leitura_situacao': page.situacao, 'leitura_aviso': page.aviso}
    else:
        origin = {'tipo': 'mensagem', 'mensagem_id': str(proposta.mensagem_id), 'pagina': None, 'leitura_versao': None}
    return {'id': str(proposta.id), 'rotulo': proposta.rotulo, 'valor_original': proposta.valor_original,
            'analise_documental_id': str(proposta.analise_documental_id) if proposta.analise_documental_id else None,
            'evidencia_estruturada': proposta.evidencia_estruturada,
            'trecho': proposta.trecho, 'destinos': proposta.destinos, 'origem': {**origin, 'canal': proposta.canal, 'linha': proposta.linha, 'metodo': proposta.metodo},
            'situacao': state, 'fonte_atual': current_source, 'versao_decisao': last.versao if last else 0,
            'confirmado': state == 'aceita',
            'decisoes': [{'id': str(d.id), 'versao': d.versao, 'acao': d.acao, 'objeto_id': str(d.objeto_id) if d.objeto_id else None,
                          'revisao_id': str(d.revisao_id) if d.revisao_id else None, 'autor_id': str(d.autor_id),
                          'campo': d.campo or (d.revisao.chave if d.revisao_id else ''),
                          'autor_nome': d.autor.get_full_name() or d.autor.username, 'data': d.created_at.isoformat(),
                          'justificativa': d.justificativa} for d in decisions]}


def consultar_propostas(atendimento):
    rows = atendimento.propostas_dados.select_related('pagina__anexo', 'mensagem', 'atendimento').prefetch_related('decisoes__autor', 'decisoes__revisao')
    return [serializar(p) for p in rows]


def _rotulos(atendimento):
    result = {}
    for tipo, fields in schema_atual(atendimento).items():
        for field in fields:
            if field['chave'] == 'estado_registro':
                continue
            for label in [field['chave'].replace('_', ' '), field['rotulo']]:
                target = {'tipo': tipo, 'chave': field['chave'], 'rotulo': field['rotulo']}
                values = result.setdefault(normalizar(label), [])
                if target not in values:
                    values.append(target)
    aliases = {'rg': ('pessoa', 'documento_numero'), 'documento de identificacao': ('pessoa', 'documento_numero'),
               'forma de pagamento': ('negociacao', 'condicoes'), 'condicoes de pagamento': ('negociacao', 'condicoes'),
               'situacao do pagamento': ('negociacao', 'situacao_pagamento'), 'preco de venda': ('negociacao', 'preco')}
    for label, (tipo, key) in aliases.items():
        field = next(f for f in schema_atual(atendimento)[tipo] if f['chave'] == key)
        result[label] = [{'tipo': tipo, 'chave': key, 'rotulo': field['rotulo']}]
    return result


def _extrair(atendimento, user, data):
    if bool(data.get('anexo_id')) == bool(data.get('mensagem_id')):
        raise ValidationError('Escolha um arquivo ou uma mensagem deste atendimento.')
    labels = _rotulos(atendimento)
    sources = []
    read_issues = []
    if data.get('anexo_id'):
        file = get_object_or_404(atendimento.anexos, id=data['anexo_id'], tenant_id=atendimento.tenant_id)
        if file.organizacao_atual_id and file.organizacao_atual.finalidade in ['referencia_redacao', 'nao_utilizar']:
            raise ValidationError('Documento de referência de redação ou desconsiderado não fornece propostas de dados do caso.')
        if data.get('leitura_versao') != file.leitura_versao:
            raise FichaAlterada()
        if file.situacao == 'revisao':
            read_issues.append(file.aviso or 'Arquivo com leitura pendente de revisão manual.')
        for page in file.paginas.filter(leitura_versao=file.leitura_versao):
            sources.append((page, None, 'ocr' if page.metodo == 'ocr_local' else 'texto', page.texto))
            if page.texto_ocr and page.texto_ocr != page.texto:
                sources.append((page, None, 'ocr', page.texto_ocr))
    else:
        msg = get_object_or_404(atendimento.mensagens, id=data['mensagem_id'], tenant_id=atendimento.tenant_id)
        from .conversa_orientada import mensagem_atual
        if not mensagem_atual(msg):
            raise FichaAlterada('Esta mensagem foi corrigida. Confira a última resposta; as propostas anteriores permanecem no histórico.')
        sources.append((None, msg, 'texto', msg.texto))
    ids, unmatched = [], 0
    for page, msg, channel, text in sources:
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            match = re.fullmatch(r'\s*([^:\n]{2,100}):([^\n]+)', line)
            targets = labels.get(normalizar(match[1])) if match else None
            if not targets or not match[2].strip():
                unmatched += 1
                continue
            if len(line) > 10000 or len(ids) >= 200:
                raise ValidationError('Limite de propostas locais atingido. Divida o arquivo ou confira os trechos manualmente; esta solicitação não foi salva.')
            digest = assinatura(['rotulos_locais_v1', str(page.id) if page else str(msg.id), channel, number, line])
            proposal, _ = PropostaDadoAtendimento.objects.get_or_create(atendimento=atendimento, origem_hash=digest,
                defaults={'tenant': atendimento.tenant, 'pagina': page, 'mensagem': msg, 'autor': user, 'canal': channel,
                          'linha': number, 'rotulo': match[1].strip(), 'valor_original': match[2], 'trecho': line, 'destinos': targets})
            ids.append(str(proposal.id))
    return {'propostas_ids': ids, 'linhas_nao_interpretadas': unmatched, 'problemas_leitura': read_issues, 'modo': 'simulacao_local',
            'aviso': 'Leitura local por rótulos, sem IA real. Trecho literal não garante interpretação correta. Nenhum registro, pessoa, papel ou pagamento foi confirmado. Confira também os trechos não interpretados.'}


def registrar(atendimento, user, payload):
    serializer = PedidoSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        with transaction.atomic():
            reservar_atendimento(atendimento)
            previous = atendimento.eventos_ficha.filter(client_id=data['client_id']).first()
            digest = assinatura(data)
            if previous:
                if previous.autor_id != user.id or previous.requisicao_hash != digest:
                    raise ValidationError('Identificador de operação já utilizado com outro conteúdo ou autora.')
                return previous.resultado, False
            if data['operacao'] == 'extrair':
                result = _extrair(atendimento, user, data)
            else:
                if not data.get('proposta_id') or 'versao_esperada' not in data or not data.get('justificativa'):
                    raise ValidationError('Informe proposta, versão e motivo da rejeição.')
                proposal = get_object_or_404(atendimento.propostas_dados, id=data['proposta_id'], tenant_id=atendimento.tenant_id)
                last = proposal.decisoes.first()
                if data['versao_esperada'] != (last.versao if last else 0):
                    raise FichaAlterada()
                if last and last.revisao_id:
                    current = RevisaoDadoAtendimento.objects.filter(objeto_id=last.objeto_id, chave=last.revisao.chave).first()
                    if current and current.id == last.revisao_id:
                        raise ValidationError('A proposta ainda sustenta o dado atual. Revise esse dado na ficha antes de rejeitar sua fonte.')
                obj, org = None, None
                if data['operacao'] == 'associar':
                    if not data['conferir_associacao'] or not fonte_atual(proposal):
                        raise ValidationError('Confira explicitamente a associação e a versão atual da fonte.')
                    obj = get_object_or_404(atendimento.objetos_ficha.exclude(tipo='legado'), id=data.get('objeto_id'), tenant_id=atendimento.tenant_id)
                    state = obj.revisoes.filter(chave='estado_registro').first()
                    if state and state.valor == 'inativo':
                        raise ValidationError('Registro desativado ou em desativação. Revise o registro antes de associar a fonte.')
                    if not any(d['tipo'] == obj.tipo and d['chave'] == data.get('campo') for d in proposal.destinos):
                        raise ValidationError('Escolha o registro e campo compatíveis com a proposta.')
                    if proposal.pagina_id:
                        from .organizacao_anexos import validar_fonte
                        page = proposal.pagina
                        org = validar_fonte(page.anexo, obj, page.numero, data.get('organizacao_versao'), True)
                decision = DecisaoPropostaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, proposta=proposal,
                    acao='associada' if obj else 'rejeitada', objeto=obj, campo=data.get('campo', '') if obj else '', organizacao_origem=org,
                    autor=user, justificativa=data['justificativa'], versao=(last.versao if last else 0)+1)
                result = {'proposta_id': str(proposal.id), 'decisao_id': str(decision.id)}
            EventoFichaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, autor=user,
                client_id=data['client_id'], requisicao_hash=digest, resultado=result)
            Atendimento.objects.filter(id=atendimento.id).update(updated_at=timezone.now())
            from .pendencias_ficha import sincronizar
            sincronizar(atendimento, user, data.get('justificativa') or 'Propostas locais atualizadas.')
            return result, True
    except OperationalError as error:
        if connection.vendor == 'sqlite' and 'locked' in str(error).lower():
            raise FichaAlterada() from None
        raise


def vincular_proposta(atendimento, user, obj, item, revision=None, reason=''):
    if not item.get('proposta_id'):
        return
    proposal = get_object_or_404(atendimento.propostas_dados.select_related('pagina__anexo'),
                                 id=item['proposta_id'], tenant_id=atendimento.tenant_id)
    last = proposal.decisoes.first()
    if item.get('versao_proposta') != (last.versao if last else 0) or not fonte_atual(proposal):
        raise FichaAlterada()
    if not item['conferir_associacao']:
        raise ValidationError('Confira explicitamente a associação da proposta à pessoa, papel ou imóvel escolhido.')
    if not any(d['tipo'] == obj.tipo and d['chave'] == item['chave'] for d in proposal.destinos):
        raise ValidationError('O rótulo da proposta não corresponde a esse tipo de registro/campo. Revise o contexto manualmente sem reutilizar uma associação incorreta.')
    if item.get('valor_original') != proposal.valor_original or item.get('trecho_origem') != proposal.trecho:
        raise ValidationError('Preserve o valor original e o trecho literal da proposta. Correções pertencem ao valor revisado.')
    if proposal.pagina_id:
        valid = item['origem'] == 'documento' and item.get('pagina_id') == proposal.pagina_id and item['canal_origem'] == proposal.canal
    else:
        valid = item['origem'] == 'mensagem' and item.get('mensagem_id') == proposal.mensagem_id
    if not valid:
        raise ValidationError('A proposta deve continuar vinculada à sua fonte original.')
    if last and last.objeto_id and last.objeto_id != obj.id and last.acao != 'rejeitada':
        raise ValidationError('A proposta já foi associada a outro registro. Revise a associação anterior antes de reutilizar a fonte.')
    if last and last.acao == 'associada' and last.campo and last.campo != item['chave']:
        raise ValidationError('O campo diverge da associação explícita. Corrija a associação antes de utilizar a proposta.')
    if revision:
        DecisaoPropostaAtendimento.objects.create(atendimento=atendimento, tenant=atendimento.tenant, proposta=proposal, objeto=obj,
            revisao=revision, acao='aceita' if item['situacao'] == 'confirmado' else 'associada', autor=user,
            justificativa=reason, versao=(last.versao if last else 0)+1)
