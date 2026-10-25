"""Parameterized structure of the supplied reference; never case evidence."""

BASE_REFERENCIA = {
    'corpo': '''ESCRITURA DE COMPRA E VENDA

{{abertura}}

OUTORGANTES VENDEDORES
{{vendedores}}

REPRESENTAÇÃO
{{representacao}}

OUTORGADOS COMPRADORES
{{compradores}}

1.- DO IMÓVEL E SUA TITULAÇÃO
1.1.- {{titularidade}}
{{imovel}}
1.2.- {{aquisicao}}
1.3.- {{onus}}

2.- DA COMPRA E VENDA
PREÇO: {{preco}}
{{pagamento}}
2.1.- {{quitacao}}
{{transmissao}}

3.- {{declaracoes_vendedores}}

4.- {{declaracoes_compradores}}

5.- {{doi}}

6.- IMPOSTO DE TRANSMISSÃO INTER VIVOS
{{tributo}}

7.- CERTIDÕES E DOCUMENTOS
{{certidoes}}
CONSULTAS
{{consultas}}

8.- {{declaracoes_partes}}

9.- {{requerimentos}}

10.- {{encerramento}}
{{emolumentos}}''',
    'representacao': '',
    'observacoes': 'OBSERVAÇÕES CONFIRMADAS\n{{observacoes}}',
}

REFERENCIA = {
    'nome': 'Estrutura da escritura enviada — para revisão',
    'versao': 'referencia-imagens-v1',
    'aprovado': False,
    'aviso': 'Adaptação da estrutura visível, não transcrição integral homologada. Cada bloco variável exige texto e fonte do atendimento, conferidos pela escrevente. Para este roteiro, representação exige resposta explícita, inclusive quando não se aplica. O modelo não comprova acontecimentos nem define exigências legais.',
    'fontes': [
        {'arquivo': 'codex-clipboard-85004e7f-f269-4e5c-8ccc-3f77cc3fe8e9.png',
         'pagina': None, 'leitura': 'visual_manual_referencia_v1', 'trecho': 'ESCRITURA DE COMPRA E VENDA',
         'blocos': ['abertura', 'vendedores', 'representacao', 'compradores']},
        {'arquivo': 'codex-clipboard-89e5fc7d-1c30-4f24-a7ad-44e2cdd21bd1.png',
         'pagina': None, 'leitura': 'visual_manual_referencia_v1', 'trecho': '1.- DO IMÓVEL E SUA TITULAÇÃO',
         'blocos': ['imovel', 'titularidade', 'aquisicao', 'onus', 'preco', 'pagamento', 'quitacao',
                    'transmissao', 'declaracoes_vendedores', 'declaracoes_compradores', 'doi']},
        {'arquivo': 'codex-clipboard-5bcfa055-d389-40ef-80ba-7f55169e9a38.png',
         'pagina': None, 'leitura': 'visual_manual_referencia_v1', 'trecho': 'TRANSMISSÃO INTER VIVOS',
         'blocos': ['tributo', 'certidoes', 'consultas', 'declaracoes_partes', 'requerimentos', 'encerramento']},
        {'arquivo': 'codex-clipboard-3144618b-e4ba-4b22-935f-0b31c4d3be36.png',
         'pagina': None, 'leitura': 'visual_manual_referencia_v1', 'trecho': 'OUTORGANTES',
         'blocos': ['emolumentos', 'encerramento']},
    ],
}
