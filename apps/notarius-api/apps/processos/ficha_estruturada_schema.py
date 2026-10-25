"""Optional working fields, not a list of legal documentary requirements."""
import re
from rest_framework import serializers


def campo(chave, rotulo, grupo, opcoes=None):
    return {'chave': chave, 'rotulo': rotulo, 'grupo': grupo, **({'opcoes': opcoes} if opcoes else {})}


SCHEMA = {
    'ato': [campo('abertura', 'Texto de abertura informado', 'Abertura'),
            campo('data_informada', 'Data informada para o ato', 'Abertura'),
            campo('local', 'Local informado para o ato', 'Abertura'),
            campo('serventia', 'Serventia informada', 'Abertura'),
            campo('referencia', 'Referência do ato', 'Abertura'),
            campo('encerramento', 'Texto de encerramento informado', 'Encerramento')],
    'complemento': [campo('categoria', 'Categoria do complemento', 'Classificação',
                         ['declaracao', 'transmissao', 'doi', 'tributo', 'certidao', 'consulta', 'requerimento', 'despesas', 'outro']),
                   campo('assunto', 'Assunto do complemento', 'Conteúdo'),
                   campo('conteudo', 'Conteúdo informado do complemento', 'Conteúdo'),
                   campo('referencia', 'Referência informada do complemento', 'Fonte'),
                   campo('situacao', 'Situação informada do complemento', 'Classificação',
                         ['a_esclarecer', 'previsto', 'informado', 'declarado_realizado', 'documento_apresentado', 'nao_realizado', 'nao_se_aplica'])],
    'pessoa': [
        campo('nome', 'Nome', 'Identificação'), campo('cpf', 'CPF', 'Identificação'),
        campo('documento_tipo', 'Tipo do documento de identificação', 'Identificação'),
        campo('documento_numero', 'RG / número do documento', 'Identificação'),
        campo('orgao_emissor', 'Órgão emissor', 'Identificação'),
        campo('nacionalidade', 'Nacionalidade', 'Qualificação'), campo('profissao', 'Profissão', 'Qualificação'),
        campo('estado_civil', 'Estado civil informado', 'Qualificação'),
        campo('data_nascimento', 'Data de nascimento', 'Qualificação'),
        campo('naturalidade', 'Naturalidade', 'Qualificação'), campo('filiacao', 'Filiação informada', 'Qualificação'),
        campo('regime_bens', 'Regime de bens informado', 'Qualificação'),
        campo('endereco', 'Endereço', 'Contato'), campo('email', 'E-mail', 'Contato'),
    ],
    'papel': [campo('tipo_papel', 'Papel no negócio', 'Papel', ['vendedor', 'comprador', 'interveniente', 'outro']),
              campo('descricao', 'Detalhes do papel', 'Papel')],
    'relacao': [campo('tipo_relacao', 'Relação da primeira pessoa com a segunda', 'Relação', ['conjuge_de', 'representante_de', 'outro']),
                campo('instrumento', 'Instrumento / fonte da representação', 'Relação'),
                campo('descricao', 'Detalhes e limites informados', 'Relação')],
    'imovel': [campo('descricao', 'Descrição literal do imóvel', 'Imóvel'), campo('matricula', 'Matrícula / referência', 'Imóvel'),
               campo('registro', 'Serventia de registro', 'Imóvel'), campo('endereco', 'Localização', 'Imóvel'),
               campo('titularidade', 'Titularidade informada', 'Histórico do imóvel'),
               campo('aquisicao', 'Título de aquisição', 'Histórico do imóvel'), campo('onus', 'Ônus informados', 'Histórico do imóvel')],
    'negociacao': [campo('preco', 'Preço informado (texto original)', 'Negociação'), campo('moeda', 'Moeda informada', 'Negociação'),
                   campo('condicoes', 'Condições de pagamento combinadas', 'Negociação'),
                   campo('situacao_pagamento', 'Situação do pagamento', 'Pagamento', ['a_esclarecer', 'previsto', 'nao_realizado', 'declarado_realizado', 'comprovante_apresentado']),
                   campo('declaracao_pagamento', 'Declaração sobre pagamento', 'Pagamento'),
                   campo('comprovante', 'Referência ao comprovante apresentado', 'Pagamento'),
                   campo('quitacao', 'Declaração específica de quitação', 'Pagamento')],
}
REGISTRO = campo('estado_registro', 'Manter ou desativar este registro', 'Registro', ['ativo', 'inativo'])


class CampoQualificacaoSerializer(serializers.Serializer):
    chave = serializers.RegexField(r'^[a-z][a-z0-9_]{0,39}$')
    rotulo = serializers.CharField(max_length=120)
    grupo = serializers.ChoiceField(choices=['Identificação', 'Qualificação', 'Contato'], default='Qualificação')


def validar_qualificacao(value):
    serializer = CampoQualificacaoSerializer(data=value, many=True)
    serializer.is_valid(raise_exception=True)
    fields = serializer.validated_data
    reserved = {f['chave'] for f in SCHEMA['pessoa']} | {'estado_registro'}
    keys = [f['chave'] for f in fields]
    if len(fields) > 25 or len(set(keys)) != len(keys) or set(keys) & reserved:
        raise serializers.ValidationError('Use até 25 campos adicionais com identificadores distintos dos campos básicos.')
    return [dict(f) for f in fields]


def schema_atual(atendimento):
    model = atendimento.modelos_minuta.first()
    result = {k: [dict(f) for f in fields] + [REGISTRO] for k, fields in SCHEMA.items()}
    if model:
        result['pessoa'] = result['pessoa'][:-1] + validar_qualificacao(model.campos_qualificacao) + [REGISTRO]
    return result


def verificar_cpf(value):
    # Mathematical/format advisory only; never changes a value or confirms a person.
    digits = re.sub(r'\D', '', value)
    formato = bool(re.fullmatch(r'\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2}', value))
    valid = formato and len(set(digits)) > 1
    if valid:
        for count in (9, 10):
            digit = (sum(int(digits[i]) * (count + 1 - i) for i in range(count)) * 10 % 11) % 10
            if digit != int(digits[count]):
                valid = False
    return {'formato_consistente': formato, 'digitos_consistentes': bool(valid), 'identidade_comprovada': False,
            'aviso': 'Validação de formato e dígitos apenas. Não comprova identidade, titularidade do CPF ou autenticidade do documento.'}


def validar_regras(required, dependencies, qualification):
    allowed = {tipo: {f['chave'] for f in fields} for tipo, fields in SCHEMA.items()}
    allowed['pessoa'].update(f['chave'] for f in qualification)
    seen, edges = set(), {}
    for field in allowed['complemento']:
        edges[('complemento', field)] = [('complemento', key) for key in dependencias_classificacao(field)]
    for rules, dependent in [(required, False), (dependencies, True)]:
        local = set()
        for rule in rules:
            if set(rule) != ({'tipo', 'chave', 'depende_de'} if dependent else {'tipo', 'chave'}):
                raise serializers.ValidationError('Regra de revisão inválida.')
            tipo, key = rule['tipo'], rule['chave']
            if not isinstance(tipo, str) or not isinstance(key, str) or tipo not in allowed or key not in allowed[tipo] or (tipo, key) in local:
                raise serializers.ValidationError('Use campos configurados e não repita regras.')
            local.add((tipo, key))
            if dependent:
                values = rule['depende_de']
                if not isinstance(values, list) or not values or len(values) > 20 or any(not isinstance(k, str) or k not in allowed[tipo] or k == key for k in values):
                    raise serializers.ValidationError('Dependência inválida ou referência ao próprio campo.')
                edges.setdefault((tipo, key), []).extend((tipo, k) for k in values)
    def visit(node, stack):
        if node in stack:
            raise serializers.ValidationError('As dependências não podem formar um ciclo.')
        if node in seen:
            return
        for child in edges.get(node, []):
            visit(child, stack | {node})
        seen.add(node)
    for node in edges:
        visit(node, set())


def dependencias_classificacao(chave):
    """Technical meaning/scope changes require review; no legal default rules."""
    return [] if chave == 'categoria' else ['categoria'] if chave == 'situacao' else ['categoria', 'situacao']
