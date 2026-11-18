"""Parameterized structure of the supplied reference; never case evidence."""

from .modelo_escritura_fiel import CAMPO, CORPO, PAGINAS, chave_campo

TITULO_REFERENCIA = 'ESCRITURA DE COMPRA E VENDA QUE FAZEM ENTRE SI, NA FORMA ABAIXO:'

BASE_REFERENCIA_ANTERIOR = {
    'corpo': '''ESCRITURA DE COMPRA E VENDA

{{abertura}}

PARTE VENDEDORA
{{vendedores}}

REPRESENTAÇÃO
{{representacao}}

PARTE COMPRADORA
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

BASE_REFERENCIA_V3 = {
    'corpo': '{{cabecalho_serventia}}\n\n{{identificacao_ato}}\n\n' + TITULO_REFERENCIA + '\n\n' + ' '.join((
        'SAIBAM quantos esta pública escritura virem que, {{abertura}} partes entre si, justas e contratadas a saber:',
        'de um lado como Outorgantes Vendedores, doravante designados simplesmente OUTORGANTES: {{vendedores}}{{representacao}},',
        'e, de outro lado, como Outorgada Compradora, doravante denominada simplesmente OUTORGADA: {{compradores}}',
        '{{reconhecimento_partes}} E então, pelos contratantes, falando cada um por sua vez, uniforme e sucessivamente, foi dito o seguinte:',
        '1 - DO IMÓVEL E SUA TITULAÇÃO - 1.1. – {{titularidade}} {{imovel}} 1.2. – {{aquisicao}} 1.3. - {{onus}}',
        '2. - Assim, formalizando os entendimentos que mantiveram, os Outorgantes achando-se contratados com a outorgada,',
        'por esta escritura e na melhor forma de direito, para lhes venderem, como de fato vendido tem, o imóvel acima descrito,',
        'pelo preço certo e ajustado de {{preco}}, {{pagamento}} 2.1. - Assim, {{quitacao}} {{transmissao}}',
        '3. - {{declaracoes_vendedores}} 4. – {{declaracoes_compradores}} 5. – {{doi}}',
        '6. – O IMPOSTO DE TRANSMISSÃO INTER VIVOS, {{tributo}} 7. – {{certidoes}} {{consultas}}',
        '8. – Declaram as partes, {{declaracoes_partes}}',
        '9. – Requerem, desde já, as partes, {{requerimentos}}',
        '10. – Por fim, requerem as partes {{exigencias_registrais}} {{emolumentos}}',
        'ASSIM, justos e contratados, {{encerramento}} OUTORGANTES: {{assinaturas_vendedores}} OUTORGADA: {{assinaturas_compradores}}',
    )),
    'representacao': '',
    'observacoes': 'OBSERVAÇÕES CONFIRMADAS\n{{observacoes}}',
}

BASE_REFERENCIA = {'corpo': CORPO, 'representacao': '', 'observacoes': ''}
BASE_REFERENCIA_V4 = {**BASE_REFERENCIA, 'corpo': CORPO.replace('}}, em Notas do', '}} em Notas do', 1)}

REFERENCIA = {
    'nome': 'Modelo de escritura de compra e venda',
    'versao': 'referencia-imagens-v5',
    'aprovado': False,
    'aviso': 'Redação da escritura enviada, na ordem das quatro páginas. Os marcadores indicam dados do caso e trechos que exigem conferência.',
    'fontes': [
        {'arquivo': 'codex-clipboard-85004e7f-f269-4e5c-8ccc-3f77cc3fe8e9.png',
         'pagina': 1, 'leitura': 'visual_manual_referencia_v1', 'trecho': 'ESCRITURA DE COMPRA E VENDA',
         'blocos': ['cabecalho_serventia', 'identificacao_ato', 'abertura', 'vendedores', 'representacao', 'compradores']},
        {'arquivo': 'codex-clipboard-89e5fc7d-1c30-4f24-a7ad-44e2cdd21bd1.png',
         'pagina': 2, 'leitura': 'visual_manual_referencia_v1', 'trecho': '1 - DO IMÓVEL E SUA TITULAÇÃO',
         'blocos': ['reconhecimento_partes', 'imovel', 'titularidade', 'aquisicao', 'onus', 'preco', 'pagamento', 'quitacao',
                    'transmissao', 'declaracoes_vendedores', 'declaracoes_compradores', 'doi']},
        {'arquivo': 'codex-clipboard-5bcfa055-d389-40ef-80ba-7f55169e9a38.png',
         'pagina': 3, 'leitura': 'visual_manual_referencia_v1', 'trecho': 'TRANSMISSÃO INTER VIVOS',
         'blocos': ['tributo', 'certidoes', 'consultas', 'declaracoes_partes', 'requerimentos', 'exigencias_registrais', 'emolumentos']},
        {'arquivo': 'codex-clipboard-3144618b-e4ba-4b22-935f-0b31c4d3be36.png',
         'pagina': 4, 'leitura': 'visual_manual_referencia_v1', 'trecho': 'ASSIM, justos e contratados',
         'blocos': ['emolumentos', 'encerramento', 'assinaturas_vendedores', 'assinaturas_compradores']},
    ],
}

for fonte in REFERENCIA['fontes']:
    fonte['blocos'] = list(dict.fromkeys(chave_campo(rotulo) for rotulo in CAMPO.findall(PAGINAS[fonte['pagina'] - 1])))
