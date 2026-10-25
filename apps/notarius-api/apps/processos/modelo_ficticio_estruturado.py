"""Fictional executable fixture, not professional wording or legal requirements."""
MODELO_FICTICIO_ETAPA7 = {
 'corpo': '''MODELO FICTÍCIO DE TESTE — SEM VALIDADE PROFISSIONAL
Não homologado pela escrevente. Apenas demonstra campos e decisões explícitas.
PARTICIPANTES FICTÍCIOS
{% repetir pessoas vendedor,comprador %}Nome informado: {{item.nome}}
{% fim %}
{% se vendedor_papel {"campo":"papel_vendedor.tipo_papel","permitidos":["vendedor"],"incluir":["vendedor"]} %}Papel confirmado no teste: {{papel_vendedor.tipo_papel}} · {{vendedor.nome}}
{% fim %}
{% se comprador_papel {"campo":"papel_comprador.tipo_papel","permitidos":["comprador"],"incluir":["comprador"]} %}Papel confirmado no teste: {{papel_comprador.tipo_papel}} · {{comprador.nome}}
{% fim %}
Imóvel fictício: {{bem.descricao}}
Preço informado: {{negocio.preco}}
Situação informada: {{negocio.situacao_pagamento}}
{% se previsao {"campo":"negocio.situacao_pagamento","permitidos":["previsto"],"incluir":["previsto"]} %}BLOCO FICTÍCIO CONDICIONAL: condições informadas para revisão: {{negocio.condicoes}}
{% fim %}
FIM DA DEMONSTRAÇÃO. Não contém cláusulas profissionais de escritura.''',
 'representacao': '', 'observacoes': '',
 'registros_minuta': [
  {'chave':'vendedor','rotulo':'Pessoa indicada como vendedora no teste','tipo':'pessoa','vinculos':{}},
  {'chave':'comprador','rotulo':'Pessoa indicada como compradora no teste','tipo':'pessoa','vinculos':{}},
  {'chave':'papel_vendedor','rotulo':'Papel vendedor do teste','tipo':'papel','vinculos':{'pessoa_a':'vendedor'}},
  {'chave':'papel_comprador','rotulo':'Papel comprador do teste','tipo':'papel','vinculos':{'pessoa_a':'comprador'}},
  {'chave':'bem','rotulo':'Imóvel do teste','tipo':'imovel','vinculos':{}},
  {'chave':'negocio','rotulo':'Negociação do teste','tipo':'negociacao','vinculos':{'imovel':'bem'}}],
 'campos_qualificacao': [], 'campos_obrigatorios_ficha': [], 'dependencias_campos_ficha': []
}
