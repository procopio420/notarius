"""Literal approved-template filling. Never generate clauses or infer missing facts."""
import re
from rest_framework.exceptions import ValidationError
from .conferencia import assinatura, conferir, sem_dado, normalizar
from .ficha import CAMPOS, TOKEN, campos_exigidos

BASE = {
    'corpo': 'MINUTA DE COMPRA E VENDA — PARA REVISÃO\n\nVENDEDORES\n{{vendedores}}\n\nCOMPRADORES\n{{compradores}}\n\nIMÓVEL\n{{imovel}}\n\nPREÇO INFORMADO\n{{preco}}\n\nFORMA DE PAGAMENTO INFORMADA\n{{pagamento}}',
    'representacao': 'REPRESENTAÇÃO\n{{representacao}}',
    'observacoes': 'OBSERVAÇÕES CONFIRMADAS\n{{observacoes}}',
}
REQUIRED = ['vendedores', 'compradores', 'imovel', 'preco', 'pagamento']

def validar_fatos_fixos(model):
    """Conservative lexical stop, not semantic or legal validation of prose."""
    patterns = [
        r'\b(?:quitacao|quitad[oa]s?|pag[oa]s?|pagou|pagaram|recebeu|receberam)\b',
        r'\b(?:assinad[oa]s?|assinaram|assinou|assinam|assina)\b',
        r'\b(?:consultad[oa]s?|consultei|consultou|consultaram)\b',
        r'\b(?:consult\w*|pagamento\w*)\b[^.!?\n]{0,100}\b(?:realizad\w*|efetuad\w*|concluid\w*)\b',
        r'\b(?:realizad\w*|efetuad\w*|concluid\w*)\b[^.!?\n]{0,100}\b(?:consult\w*|pagamento\w*)\b',
    ]
    for block in ['corpo', 'representacao', 'observacoes']:
        from .redacao_estruturada import TOKEN as STRUCTURED_TOKEN
        from .blocos_minuta import plano
        text = ''.join(node['texto'] for node in plano(model)[block]) if model.registros_minuta else getattr(model, block)
        fixed = normalizar(TOKEN.sub('', STRUCTURED_TOKEN.sub('', text)))
        if any(re.search(pattern, fixed) for pattern in patterns):
            raise ValidationError('O texto fixo do modelo contém possível declaração de pagamento, quitação, consulta ou assinatura. Não use o modelo como evidência do acontecimento. Revise esse trecho e registre fatos efetivamente confirmados nos campos, com sua fonte.')

def validar_modelo(data):
    if data.get('registros_minuta'):
        from .redacao_estruturada import validar_modelo as validar_estruturado
        return validar_estruturado(data)
    if any(t in data[b] for b in ['corpo', 'representacao', 'observacoes'] for t in ['{%', '%}']):
        raise ValidationError('Blocos explícitos exigem modelo com posições da ficha detalhada.')
    for block in ['corpo', 'representacao', 'observacoes']:
        text = data[block]
        tokens = TOKEN.findall(text)
        allowed = list(CAMPOS)
        if set(tokens) - set(allowed) or '{{' in TOKEN.sub('', text) or '}}' in TOKEN.sub('', text):
            raise ValidationError(f'Campos inválidos no bloco {block}. Use somente os marcadores oferecidos.')
        required = REQUIRED if block == 'corpo' else [block] if text.strip() else []
        if set(required) - set(tokens):
            raise ValidationError(f'O bloco {block} precisa manter os campos: {", ".join(required)}.')

def modelo_atual(atendimento):
    return atendimento.modelos_minuta.first()

def snapshot(atendimento):
    from .serializers import RevisaoDadoSerializer
    model = modelo_atual(atendimento)
    latest = {}
    for r in atendimento.revisoes.filter(objeto__isnull=True).select_related('mensagem', 'pagina_origem__anexo').order_by('chave', '-versao'):
        latest.setdefault(r.chave, r)
    values = {k: {'valor': r.valor, 'revisao_id': str(r.id), 'versao': r.versao, 'situacao': r.situacao,
                  'origem': RevisaoDadoSerializer(r).data['origem']}
              for k, r in latest.items() if k in CAMPOS}
    state = {'modelo': str(model.id) if model else None, 'dados': values,
        'anexos': list(atendimento.anexos.order_by('id').values_list('id', 'sha256', 'leitura_versao')),
        'mensagens': list(atendimento.mensagens.order_by('id').values_list('id', flat=True)),
        'decisoes': list(atendimento.decisoes.order_by('id').values_list('id', flat=True))}
    structured = list(atendimento.objetos_ficha.exclude(tipo='legado').order_by('id').values_list('id', 'tipo', 'pessoa_a_id', 'pessoa_b_id', 'imovel_id'))
    if structured:
        state.update(objetos_ficha=structured,
                     ficha_estruturada=list(atendimento.eventos_ficha.order_by('id').values_list('id', flat=True)),
                     revisoes_estruturadas=list(atendimento.revisoes.filter(objeto__isnull=False).order_by('id').values_list('id', flat=True)))
        state['vinculacoes_minuta'] = list(atendimento.vinculacoes_minuta.order_by('id').values_list('id', flat=True))
    proposals = list(atendimento.propostas_dados.order_by('id').values_list('id', flat=True))
    analyses = list(atendimento.analises_documentais.order_by('id').values_list('id', flat=True))
    if analyses:
        state['analises_documentais'] = analyses
    if proposals:
        state.update(propostas=proposals, decisoes_propostas=list(atendimento.decisoes_propostas.order_by('id').values_list('id', flat=True)))
    if atendimento.pendencias_ficha.exists():
        state['pendencias_ficha'] = list(atendimento.historico_pendencias_ficha.order_by('id').values_list('id', flat=True))
    if atendimento.organizacoes_anexos.exists():
        state['organizacoes_anexos'] = list(atendimento.organizacoes_anexos.order_by('id').values_list('id', flat=True))
    fingerprint = assinatura(state)
    if structured or model and model.registros_minuta:
        from .redacao_estruturada import preencher
        try:
            values, _ = preencher(atendimento)
        except ValidationError:
            values = {}
    return model, values, fingerprint

def preparar(atendimento):
    report = conferir(atendimento)
    if report['bloqueado']:
        raise ValidationError('Resolva as pendências de conferência antes de preparar a minuta.')
    model, values, fingerprint = snapshot(atendimento)
    if not model or not model.aprovado:
        raise ValidationError('Revise e aprove explicitamente a versão atual do modelo antes de preparar a minuta.')
    if model.registros_minuta:
        from .redacao_estruturada import preencher
        validar_modelo({'corpo': model.corpo, 'representacao': model.representacao, 'observacoes': model.observacoes,
                        'registros_minuta': model.registros_minuta, 'campos_qualificacao': model.campos_qualificacao})
        validar_fatos_fixos(model)
        values, text = preencher(atendimento)
        return model, values, fingerprint, text
    validar_modelo({'corpo': model.corpo, 'representacao': model.representacao, 'observacoes': model.observacoes})
    validar_fatos_fixos(model)
    for key in campos_exigidos(atendimento):
        if key not in values or values[key]['situacao'] != 'confirmado' or sem_dado(values[key]['valor']):
            raise ValidationError(f'O campo {key} precisa estar confirmado e preenchido.')
    def fill(text):
        def replace(match):
            value = values.get(match[1])
            if not value or value['situacao'] != 'confirmado' or sem_dado(value['valor']):
                raise ValidationError(f'Informação não confirmada: {match[1]}.')
            if '{{' in value['valor'] or '}}' in value['valor']:
                raise ValidationError(f'O campo {match[1]} ainda contém marcadores de preenchimento.')
            return value['valor']
        return TOKEN.sub(replace, text)
    blocks = [fill(model.corpo)]
    for key in ['representacao', 'observacoes']:
        if key in TOKEN.findall(model.corpo):
            continue
        value = values.get(key)
        if value and value['valor'].strip() and value['situacao'] == 'confirmado':
            if not getattr(model, key).strip():
                raise ValidationError(f'Existe informação confirmada de {key}, mas falta aprovar seu bloco no modelo.')
            blocks.append(fill(getattr(model, key)))
    return model, values, fingerprint, '\n\n'.join(blocks)
