"""Conservative checks over explicit evidence. No inferred facts or model confidence."""
import hashlib
import json
import re
import unicodedata
from decimal import Decimal
from .ficha import CAMPOS, campos_exigidos, PERGUNTAS

ALIASES = {'vendedores': 'vendedores', 'vendedor': 'vendedores', 'compradores': 'compradores',
           'comprador': 'compradores', 'imovel': 'imovel', 'preco': 'preco',
           'preco de venda': 'preco', 'forma de pagamento': 'pagamento', 'pagamento': 'pagamento',
           'representacao': 'representacao'}

def normalizar(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c)).split())

def comparar(key, value):
    if key == 'preco':
        money = re.fullmatch(r'(?:R\$\s*)?(\d[\d.,]*)(?:\s*reais)?', value.strip(), re.I)
        if money:
            number = money[1]
            if re.fullmatch(r'\d{1,3}(?:\.\d{3})+(?:,\d{2})?|\d+(?:,\d{2})?', number):
                return Decimal(number.replace('.', '').replace(',', '.'))
            if re.fullmatch(r'\d+\.\d{2}', number):
                return Decimal(number)
    return normalizar(value)

def assinatura(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, default=str).encode()).hexdigest()

def sem_dado(value):
    return not value.strip() or bool(re.fullmatch(r'x+|[.\-]+|nao (?:sei|informad[oa]|disponivel)|a confirmar|pendente|sem informacao', normalizar(value)))

def extrair_rotulos(text):
    aliases = {**{normalizar(label): key for key, (label, _) in CAMPOS.items()},
               **{normalizar(key.replace('_', ' ')): key for key in CAMPOS}, **ALIASES}
    for line in text.splitlines():
        match = re.fullmatch(r'\s*([^:\n]{2,45}):\s*(\S.{0,1999})\s*', line)
        if match and normalizar(match[1]) in aliases:
            yield aliases[normalizar(match[1])], match[2].strip(), line

def orientar_conversa(atendimento, questions):
    """A live, source-bound guide; never a generated assertion or a confirmation."""
    message = atendimento.mensagens.order_by('-created_at', '-id').first()
    identified = []
    unrecognized = []
    if message:
        if message.campo in CAMPOS:
            identified = [{'chave': message.campo, 'rotulo': CAMPOS[message.campo][0],
                           'valor': message.texto, 'trecho': message.texto}]
        elif not message.pergunta:
            handled = set()
            if atendimento.objetos_ficha.exclude(tipo='legado').exists():
                from .pendencias_ficha import consultar
                handled = {p['chave'] for p in consultar(atendimento) if p['situacao'] == 'resolvida' and (not p['contexto'].get('propostas') or p['contexto'].get('tratado'))}
                from .propostas_dados import consultar_propostas
                handled.update(f"trecho:{message.id}:{p['origem']['linha']}" for p in consultar_propostas(atendimento) if p['origem'].get('mensagem_id') == str(message.id) and p['situacao'] in ['aceita', 'rejeitada', 'substituida'])
            for number, line in enumerate(message.texto.splitlines(), 1):
                if f'trecho:{message.id}:{number}' in handled:
                    continue
                if not line.strip():
                    continue
                matches = list(extrair_rotulos(line))
                if matches:
                    key, value, excerpt = matches[0]
                    identified.append({'chave': key, 'rotulo': CAMPOS[key][0], 'valor': value, 'trecho': excerpt})
                else:
                    unrecognized.append(line)
    if not message:
        text = 'Vamos organizar a compra e venda. Envie os documentos ou escreva as informações que já possui.'
    elif unrecognized:
        text = 'Sua mensagem está salva. Não consegui associar todos os trechos aos campos com segurança. Revise os trechos abaixo; não completei nem confirmei os dados.'
    elif identified:
        text = 'Localizei informações com campos identificados na sua última mensagem. Elas são propostas para revisão; ainda precisam da conferência da escrevente.'
    else:
        text = 'Sua mensagem está salva. Confira as pendências antes de continuar.'
    return {'modo': 'orientacao_local', 'texto': text,
            'mensagem_id': str(message.id) if message else None,
            'identificados': identified, 'nao_interpretados': unrecognized,
            'proxima_chave': questions[0]['chave'] if questions else None,
            'limite': 'Esta orientação usa campos explícitos e regras locais. Não interpreta livremente textos nem verifica a veracidade dos fatos.'}

def conferir(atendimento):
    current_model = atendimento.modelos_minuta.first()
    if atendimento.objetos_ficha.exclude(tipo='legado').exists() or current_model and current_model.registros_minuta:
        from .pendencias_ficha import consultar
        issues = consultar(atendimento)
        questions = [{'chave': p['chave'], 'tipo': 'pendencia_ficha', 'rotulo': p['titulo'],
                      'assinatura': p['assinatura'], 'versao': p['versao'], 'pergunta': p['pergunta'],
                      'destino': {'pendencia_id': p['id'], 'subtipo': p['tipo'], 'objeto_id': p['objeto_id'], 'campo': p['campo'],
                                  'proposta_id': p['contexto'].get('proposta', {}).get('id'),
                                  'mensagem_id': p['contexto'].get('mensagem_id'), 'pagina_id': p['contexto'].get('pagina_id'),
                                  'anexo_id': p['contexto'].get('anexo_id'),
                                  'trecho': p['contexto'].get('trecho'), 'tarefa': p['pergunta']},
                      'candidatos': [], 'atual': None} for p in issues if p['situacao'] != 'resolvida']
        from .organizacao_anexos import pendencias as pendencias_documentos
        questions = pendencias_documentos(atendimento) + questions
        from .redacao_estruturada import vinculo_atual, preencher
        from rest_framework.exceptions import ValidationError
        try:
            vinculo_atual(atendimento)
        except ValidationError as e:
            questions.append({'chave': 'ficha_estruturada', 'tipo': 'vinculacao_minuta', 'rotulo': 'Vinculação ao modelo profissional',
                              'assinatura': assinatura(questions), 'versao': 0, 'candidatos': [], 'atual': None,
                              'pergunta': ' '.join(map(str, e.detail))})
        else:
            try:
                preencher(atendimento)
            except ValidationError as e:
                questions.append({'chave': 'campos_minuta', 'tipo': 'estrutura', 'rotulo': 'Dados usados no modelo',
                                  'assinatura': assinatura(questions), 'versao': 0, 'candidatos': [], 'atual': None,
                                  'pergunta': ' '.join(map(str, e.detail))})
        return {'pendencias': questions, 'bloqueado': bool(questions), 'pode_redigir': not questions,
                'orientacao': orientar_conversa(atendimento, questions),
                'mensagem': 'Resolva cada dúvida no registro correspondente.' if questions else 'Dados e vinculação disponíveis para preenchimento literal do modelo aprovado.',
                'limite': 'Conferência local, sem interpretação por IA e sem exigências jurídicas presumidas.'}
    required_fields = campos_exigidos(atendimento)
    candidates = {key: [] for key in CAMPOS}
    unmapped = set()
    for msg in atendimento.mensagens.order_by('created_at', 'id'):
        if msg.campo in CAMPOS:
            candidates[msg.campo].append({'valor': msg.texto, 'origem': 'mensagem', 'situacao': 'informado', 'id': str(msg.id), 'trecho': msg.texto})
        elif not msg.pergunta:
            for key, value, line in extrair_rotulos(msg.texto):
                candidates[key].append({'valor': value, 'origem': 'mensagem', 'situacao': 'informado', 'id': str(msg.id), 'trecho': line})
    attachments = list(atendimento.anexos.defer('conteudo').prefetch_related('paginas'))
    for attachment in attachments:
        if attachment.organizacao_atual_id and attachment.organizacao_atual.finalidade in ['referencia_redacao', 'nao_utilizar']:
            continue
        found = False
        for page in attachment.paginas.all():
            if page.leitura_versao != attachment.leitura_versao:
                continue
            channels = [('ocr' if page.metodo == 'ocr_local' else 'texto', page.texto)]
            if page.texto_ocr and page.texto_ocr != page.texto:
                channels.append(('ocr', page.texto_ocr))
            for channel, text in channels:
                for key, value, line in extrair_rotulos(text):
                    found = True
                    candidates[key].append({'valor': value, 'origem': 'documento', 'id': str(page.id),
                                            'anexo_id': str(attachment.id), 'leitura_versao': page.leitura_versao,
                                            'situacao': 'extraido', 'arquivo': attachment.nome, 'pagina': page.numero, 'trecho': line, 'canal': channel})
        if not found:
            unmapped.add(attachment.id)
    latest = {}
    for revision in atendimento.revisoes.filter(objeto__isnull=True).select_related('pagina_origem__anexo').order_by('chave', '-versao'):
        latest.setdefault(revision.chave, revision)
    decisions = list(atendimento.decisoes.all())
    questions = []
    from .organizacao_anexos import pendencias as pendencias_documentos
    questions.extend(pendencias_documentos(atendimento))
    if atendimento.analises_documentais.exists():
        from .pendencias_ficha import consultar
        questions.extend({'chave': p['chave'], 'tipo': 'pendencia_ficha', 'rotulo': p['titulo'],
            'assinatura': p['assinatura'], 'versao': p['versao'], 'pergunta': p['pergunta'],
            'candidatos': [], 'atual': None} for p in consultar(atendimento)
            if p['tipo'] == 'analise_documental' and p['situacao'] != 'resolvida')
    from .propostas_dados import consultar_propostas
    pending_proposals = [p for p in consultar_propostas(atendimento) if p['situacao'] in ['pendente', 'associada', 'reaberta']]
    if pending_proposals:
        questions.append({'chave': 'propostas_dados', 'tipo': 'estrutura', 'rotulo': 'Propostas com fonte aguardando decisão',
            'assinatura': assinatura([(p['id'], p['versao_decisao'], p['situacao']) for p in pending_proposals]),
            'pergunta': 'Confira as propostas e suas fontes na ficha detalhada. Escolha explicitamente o registro e o campo, confirme a associação ou rejeite a proposta com motivo. Trecho literal não garante interpretação correta.',
            'candidatos': [], 'atual': None, 'versao': 0})
    structured = list(atendimento.objetos_ficha.exclude(tipo='legado').values_list('id', flat=True))
    if structured:
        questions.append({'chave': 'ficha_estruturada', 'tipo': 'estrutura', 'rotulo': 'Ficha detalhada de compra e venda',
            'assinatura': assinatura([structured, list(atendimento.eventos_ficha.values_list('id', flat=True))]),
            'pergunta': 'Há registros separados por pessoa, relação, imóvel ou negociação. Revise-os na ficha detalhada. A redação por blocos antigos não pode ignorar esses registros; sua vinculação ao modelo será tratada na etapa de redação.',
            'candidatos': [], 'atual': None, 'versao': 0})
    for msg in atendimento.mensagens.order_by('created_at', 'id'):
        if msg.pergunta or msg.campo in CAMPOS:
            continue
        unknown = [line for line in msg.texto.splitlines() if line.strip() and not list(extrair_rotulos(line))]
        if not unknown:
            continue
        key = f'mensagem:{msg.id}'
        sign = assinatura([key, msg.texto])
        if any(d.chave == key and d.assinatura == sign for d in decisions):
            continue
        questions.append({'chave': key, 'tipo': 'mensagem', 'rotulo': 'Trecho da conversa sem interpretação',
            'assinatura': sign, 'pergunta': 'Não interpretei todos os trechos desta mensagem. Resolva as dúvidas e registre os dados relevantes nos campos antes de concluir a revisão.',
            'candidatos': [], 'atual': msg.texto, 'mensagem_id': str(msg.id), 'versao': 0})
    if not attachments:
        questions.append({'chave': 'anexos', 'tipo': 'anexar', 'rotulo': 'Documentos do atendimento',
            'assinatura': assinatura([]), 'pergunta': 'Anexe os documentos do atendimento para iniciar a conferência. Não vou presumir o conteúdo de documentos ausentes.',
            'candidatos': [], 'atual': None, 'versao': 0})
    for attachment in attachments:
        if attachment.organizacao_atual_id and attachment.organizacao_atual.finalidade in ['referencia_redacao', 'nao_utilizar']:
            continue
        key = f'anexo:{attachment.id}'
        sign = assinatura([key, attachment.sha256, attachment.leitura_versao])
        if not any(d.chave == key and d.assinatura == sign for d in decisions):
            explanation = ('Há problema de leitura; não vou presumir o conteúdo.' if attachment.situacao == 'revisao' else
                           'Não consegui associar os dados automaticamente aos campos do atendimento.' if attachment.id in unmapped else
                           'Extraí alguns campos, mas não interpretei integralmente o documento. Confira o original.')
            questions.append({'chave': key, 'tipo': 'documento', 'rotulo': attachment.nome, 'assinatura': sign,
                'pergunta': f'Preciso da sua conferência de “{attachment.nome}”. {explanation}',
                'candidatos': [], 'atual': None, 'versao': 0})
    for key, (label, required) in CAMPOS.items():
        required = key in required_fields
        current = latest.get(key)
        from .dependencias_ficha import fonte_atual
        old_source = bool(current and not fonte_atual(current))
        evidence = candidates[key]
        sign = assinatura(evidence)
        values = {comparar(key, c['valor']) for c in evidence}
        if current and current.valor:
            values.add(comparar(key, current.valor))
        conflict = len(values) > 1
        resolved = current and not sem_dado(current.valor) and current.situacao == 'confirmado' and any(d.chave == key and d.assinatura == sign and d.revisao_id == current.id for d in decisions)
        if not old_source and (resolved or (current and not sem_dado(current.valor) and current.situacao == 'confirmado' and not evidence and not conflict)):
            continue
        if not required and not evidence and (not current or current.situacao == 'ausente'):
            continue
        kind = 'divergencia' if conflict else 'leitura' if old_source or current and current.situacao in ['divergente', 'ilegivel'] else 'confirmacao'
        question = (f'Encontrei informações diferentes para {label.lower()}. Confira as origens e decida qual registrar.' if kind == 'divergencia' else
                    f'Preciso da sua revisão de {label.lower()}; não consigo continuar com essa pendência.' if kind == 'leitura' else
                    PERGUNTAS.get(key, f'Qual é a informação de {label.lower()}? Confira os dados antes de confirmar.'))
        questions.append({'chave': key, 'tipo': kind, 'rotulo': label, 'assinatura': sign,
                          'pergunta': question, 'candidatos': evidence, 'atual': current.valor if current else None,
                          'versao': current.versao if current else 0})
    questions.sort(key=lambda q: {'organizacao_documento': -2, 'pendencia_ficha': -1, 'estrutura': -1, 'anexar': 0, 'documento': 0, 'mensagem': 1, 'divergencia': 1, 'leitura': 2, 'confirmacao': 3}[q['tipo']])
    return {'pendencias': questions, 'bloqueado': bool(questions), 'pode_redigir': not questions,
            'orientacao': orientar_conversa(atendimento, questions),
            'mensagem': 'A redação está bloqueada até a revisão das pendências.' if questions else 'Verificações iniciais respondidas; isso não substitui a conferência jurídica e documental.',
            'limite': 'Comparação conservadora de campos explicitamente rotulados; documentos livres exigem conferência humana.'}

def exigir_pronto(atendimento):
    from rest_framework.exceptions import ValidationError
    report = conferir(atendimento)
    if report['bloqueado']:
        raise ValidationError('Redação bloqueada: resolva as pendências da conferência.')
    return report
