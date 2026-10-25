"""Reference sections as empty, source-bound positions. Never an approved deed."""
from .cenarios_homologacao import especificacao
from .modelo_referencia import REFERENCIA


def referencia_complementar(variante):
    model = especificacao(variante)['modelo']
    extras = [
        ('transmissao', 'Transmissão informada', {'imovel': 'bem'}),
        ('declaracao_vendedor', 'Declaração do vendedor', {'pessoa_a': 'vendedor'}),
        ('declaracao_comprador', 'Declaração do comprador', {'pessoa_a': 'comprador'}),
        ('doi', 'Informação de DOI', {'imovel': 'bem'}),
        ('tributo', 'Informação de tributo', {'imovel': 'bem'}),
        ('certidao_imovel', 'Documento do imóvel', {'imovel': 'bem'}),
        ('consulta_vendedor', 'Consulta relativa ao vendedor', {'pessoa_a': 'vendedor'}),
        ('consulta_comprador', 'Consulta relativa ao comprador', {'pessoa_a': 'comprador'}),
        ('declaracao_especifica_vendedor', 'Declaração específica do vendedor', {'pessoa_a': 'vendedor'}),
        ('declaracao_especifica_comprador', 'Declaração específica do comprador', {'pessoa_a': 'comprador'}),
        ('requerimento', 'Requerimento relativo ao imóvel', {'imovel': 'bem'}),
        ('despesas', 'Informação de despesas', {}),
    ]
    model['registros_minuta'] += [{'chave': 'ato', 'rotulo': 'Dados gerais do ato', 'tipo': 'ato', 'vinculos': {}}]
    model['registros_minuta'] += [{'chave': key, 'rotulo': label, 'tipo': 'complemento', 'vinculos': links,
        'categoria': 'declaracao' if key.startswith('declaracao') else 'certidao' if key.startswith('certidao') else 'consulta' if key.startswith('consulta') else key} for key, label, links in extras]
    # Keep qualification/representation and property data already reviewed as a
    # proposed structure. Replace no source value or approval in existing cases.
    body = model['corpo'].replace('RASCUNHO FICTÍCIO DE COMPRA E VENDA — PARA HOMOLOGAÇÃO', 'RASCUNHO DE ESTRUTURA COMPLEMENTAR — PARA HOMOLOGAÇÃO')
    body = body.replace('SEM VALIDADE PROFISSIONAL', 'NÃO HOMOLOGADO — NÃO É ATO CONCLUÍDO\n\n{{ato.abertura}}')
    body = body.replace('{{ato.abertura}}', '{{ato.abertura}}\nData informada: {{ato.data_informada}}\nLocal informado: {{ato.local}}\nServentia informada: {{ato.serventia}}')
    body += '''

2.1.- {{negocio.quitacao}}
{{transmissao.conteudo}}

3.- DECLARAÇÃO DO VENDEDOR
{{declaracao_vendedor.conteudo}}

4.- DECLARAÇÃO DO COMPRADOR
{{declaracao_comprador.conteudo}}

5.- INFORMAÇÃO DE DOI
{{doi.conteudo}}

6.- INFORMAÇÃO DE TRIBUTO
{{tributo.conteudo}}

7.- DOCUMENTO DO IMÓVEL
{{certidao_imovel.conteudo}}
CONSULTA RELATIVA AO VENDEDOR
{{consulta_vendedor.conteudo}}
CONSULTA RELATIVA AO COMPRADOR
{{consulta_comprador.conteudo}}

8.- DECLARAÇÕES ESPECÍFICAS
{{declaracao_especifica_vendedor.conteudo}}
{{declaracao_especifica_comprador.conteudo}}

9.- REQUERIMENTO
{{requerimento.conteudo}}

10.- ENCERRAMENTO INFORMADO
{{ato.encerramento}}
DESPESAS INFORMADAS
{{despesas.conteudo}}'''
    model.update(corpo=body, aprovado=False,
        justificativa='Estrutura de campos para revisão; não transcreve, aprova ou confirma fatos da escritura de referência.')
    return {'nome': 'Estrutura complementar — ' + ('participação direta' if variante == 'direta' else 'com procuração'),
            'versao': 'estrutura-complementar-v1', 'fontes_estrutura': REFERENCIA['fontes'],
            'variante': variante, 'aprovado': False, 'modelo': model,
            'aviso': 'Rascunho de organização, não modelo profissional homologado. Cada complemento é separado por assunto e destinatário. Não cria registros nem afirma pagamento, consulta, apresentação de documento ou assinatura. Remova ou adapte posições que não se apliquem somente após revisão da escrevente.'}
