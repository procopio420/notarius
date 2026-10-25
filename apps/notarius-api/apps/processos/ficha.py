"""Initial working fields, not a legal completeness checklist."""
import re

CAMPOS = {
    'vendedores': ('Vendedores', True),
    'compradores': ('Compradores', True),
    'imovel': ('Imóvel', True),
    'preco': ('Preço', True),
    'pagamento': ('Forma de pagamento', True),
    'representacao': ('Representação por procuração', False),
    'observacoes': ('Observações', False),
}

CAMPOS_INICIAIS = tuple(CAMPOS)
CAMPOS.update({
    'abertura': ('Abertura do ato: data, local e serventia', False),
    'titularidade': ('Titularidade e descrição do imóvel', False),
    'aquisicao': ('Título de aquisição do imóvel', False),
    'onus': ('Ônus e disponibilidade do imóvel', False),
    'quitacao': ('Declaração específica sobre quitação', False),
    'transmissao': ('Transmissão e condições da venda', False),
    'declaracoes_vendedores': ('Declarações dos vendedores', False),
    'declaracoes_compradores': ('Declarações dos compradores ou representante', False),
    'doi': ('Declaração de Operações Imobiliárias', False),
    'tributo': ('Tributo de transmissão', False),
    'certidoes': ('Certidões e documentos apresentados', False),
    'consultas': ('Consultas: referências e resultados', False),
    'declaracoes_partes': ('Declarações específicas das partes', False),
    'requerimentos': ('Requerimentos ao registro', False),
    'encerramento': ('Encerramento e exigências do ato', False),
    'emolumentos': ('Emolumentos e despesas do ato', False),
})

TOKEN = re.compile(r'\{\{\s*([a-z_]+)\s*\}\}')

def campos_exigidos(atendimento):
    """Template variables are workflow requirements, never legal requirements."""
    required = {key for key, (_, mandatory) in CAMPOS.items() if mandatory}
    model = atendimento.modelos_minuta.first()
    if model:
        required.update(TOKEN.findall(model.corpo))
        for block in ['representacao', 'observacoes']:
            current = atendimento.revisoes.filter(objeto__isnull=True, chave=block).first()
            if current and current.valor.strip() and current.situacao == 'confirmado':
                required.update(TOKEN.findall(getattr(model, block)))
    return required & CAMPOS.keys()

def campos_ativos(atendimento):
    required = campos_exigidos(atendimento)
    active = set(CAMPOS_INICIAIS) | required
    active.update(atendimento.revisoes.filter(objeto__isnull=True).values_list('chave', flat=True))
    return {key: (label, key in required)
            for key, (label, _) in CAMPOS.items() if key in active}

PERGUNTAS = {
    'representacao': 'Quem representa quem neste atendimento, por qual instrumento? Identifique pessoa, papel e fonte separadamente. Se não houver representação, informe isso expressamente; não presumo sua existência pelo modelo.',
    'quitacao': 'Existe declaração de quitação para este atendimento? Informe o texto e sua fonte, ou registre expressamente que não há essa declaração. Condição de pagamento não comprova pagamento realizado.',
    'tributo': 'Qual é a informação de tributo confirmada para este atendimento e sua fonte? Diferencie valor previsto, guia apresentada e recolhimento efetivamente informado; não presumo recolhimento pelo modelo.',
    'certidoes': 'Quais documentos foram efetivamente apresentados? Identifique cada documento, a pessoa ou imóvel a que pertence, referência, data e fonte. A relação do exemplo não confirma documentos deste caso.',
    'consultas': 'Quais consultas foram efetivamente realizadas e quais são suas fontes e resultados? Separe cada consulta e seu objeto. Se não foram realizadas, registre essa situação explicitamente; não copio o resultado do exemplo.',
    'declaracoes_vendedores': 'Quais declarações dos vendedores foram efetivamente informadas neste atendimento? Identifique quem declarou e a fonte. Não atribuo aos vendedores as declarações do exemplo.',
    'declaracoes_compradores': 'Quais declarações dos compradores ou de seu representante foram efetivamente informadas? Identifique autor, papel e fonte sem confundir representado e representante.',
    'declaracoes_partes': 'Quais declarações específicas cada participante efetivamente prestou? Identifique pessoa e fonte; não presumo respostas sobre exposição política ou beneficiário final.',
    'encerramento': 'Qual texto de encerramento é aplicável ao estágio atual do ato? Registre somente os procedimentos efetivamente confirmados, com fonte. Preparação de minuta não comprova leitura ou assinatura.',
}

SITUACOES = ['ausente', 'informado', 'confirmado', 'divergente', 'ilegivel']
