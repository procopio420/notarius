"""Transcrição parametrizada das quatro páginas da escritura de referência."""

import re
import unicodedata
from hashlib import sha256


def chave_campo(rotulo):
    ascii_text = unicodedata.normalize('NFKD', rotulo).encode('ascii', 'ignore').decode()
    key = 'fiel_' + re.sub(r'[^a-z]+', '_', ascii_text.lower()).strip('_')
    if len(key) <= 40:
        return key
    suffix = sha256(key.encode()).hexdigest()[:10].translate(str.maketrans('0123456789', 'ghijklmnop'))
    return key[:29] + '_' + suffix


PAGINAS = (
    (
        '⟦Identificação e contato da serventia⟧\n'
        '\n'
        'ATO: ⟦Número do ato⟧\n'
        'LIVRO: ⟦Número do livro⟧\n'
        'FOLHAS: ⟦Folhas do ato⟧\n'
        '⟦Identificação do traslado quando expedido⟧\n'
        '\n'
        'ESCRITURA DE COMPRA E VENDA QUE FAZEM ENTRE SI, NA FORMA ABAIXO:\n'
        '\n'
        'S A I B A M quantos esta pública escritura virem que, aos ⟦Dia da lavratura por extenso e em algarismos⟧ dias do'
        ' mês de ⟦Mês da lavratura⟧ do ano de ⟦Ano da lavratura por extenso e em algarismos⟧ nesta Serventia do '
        '⟦Ofício de Justiça⟧, perante mim ⟦Nome da autoridade lavrante⟧ ⟦Cargo da autoridade lavrante⟧, '
        '⟦Conferência do comparecimento⟧compareceram partes entre si, justas e contratadas a saber: de um lado como '
        'Outorgantes Vendedores, doravante designado simplesmente OUTORGANTES: ⟦Nome do vendedor⟧, '
        '⟦Nacionalidade do vendedor⟧, casado, ⟦Profissão do vendedor⟧, nascido na cidade de ⟦Naturalidade do vendedor⟧, '
        'em ⟦Nascimento do vendedor⟧ filho de ⟦Filiação do vendedor⟧ portador da CNH nº ⟦CNH do vendedor⟧ expedida pelo '
        '⟦Emissor da CNH do vendedor⟧ em ⟦Emissão da CNH do vendedor⟧, onde consta o documento de identidade nº '
        '⟦Identidade do vendedor⟧ e CPF nº ⟦CPF do vendedor⟧ e sua esposa ⟦Nome da vendedora⟧, '
        '⟦Nacionalidade da vendedora⟧, casada, ⟦Profissão da vendedora⟧, nascida na cidade de ⟦Naturalidade da vendedora⟧'
        ', em ⟦Nascimento da vendedora⟧, filha de ⟦Filiação da vendedora⟧ portadora da carteira de identidade nº '
        '⟦Identidade da vendedora⟧ expedida pelo ⟦Emissor da identidade da vendedora⟧ em '
        '⟦Emissão da identidade da vendedora⟧ inscrita no CPF sob o nº ⟦CPF da vendedora⟧ casados pelo regime da '
        '⟦Regime de bens dos vendedores⟧, ⟦Vigência legal do regime dos vendedores⟧ cujo matrimônio foi realizado em '
        '⟦Data do casamento dos vendedores⟧ conforme Certidão de Casamento nº ⟦Certidão de casamento dos vendedores⟧, '
        'lavrada pelo cartório do ⟦Cartório do casamento dos vendedores⟧, no Livro ⟦Livro do casamento dos vendedores⟧ às'
        ' fls. ⟦Folhas do casamento dos vendedores⟧ Matrícula ⟦Matrícula do casamento dos vendedores⟧, '
        '⟦Situação do endereço eletrônico dos vendedores⟧, residentes e domiciliados na rua ⟦Endereço dos vendedores⟧, '
        'neste ato representados por seu bastante procurador ⟦Nome do procurador⟧, ⟦Nacionalidade do procurador⟧, '
        '⟦Estado civil do procurador⟧, ⟦Profissão do procurador⟧, nascido na cidade de ⟦Naturalidade do procurador⟧, em '
        '⟦Nascimento do procurador⟧, filho de ⟦Filiação do procurador⟧ portador da CNH nº ⟦CNH do procurador⟧ expedida '
        'pela ⟦Emissor da CNH do procurador⟧ em ⟦Emissão da CNH do procurador⟧ onde consta o documento de identidade '
        'profissional nº ⟦Identidade profissional e conselho do procurador⟧ e CPF nº ⟦CPF do procurador⟧, residente e '
        'domiciliado na rua ⟦Endereço do procurador⟧, conforme procuração lavrada em ⟦Data da procuração⟧, em Notas do '
        'Cartório do ⟦Cartório da procuração⟧, no livro ⟦Livro da procuração⟧, às folhas ⟦Folhas da procuração⟧ ato nº '
        '⟦Número do ato da procuração⟧ ⟦Conferência da procuração e do arquivamento⟧confirmada com a serventia e pelo '
        'link do selo, devidamente arquivadas, e, de outro lado, como Outorgada Compradora, doravante denominada '
        'simplesmente OUTORGADA: ⟦Nome da compradora⟧, ⟦Nacionalidade da compradora⟧, casada, ⟦Profissão da compradora⟧, '
        'nascida na cidade do ⟦Naturalidade da compradora⟧, em ⟦Nascimento da compradora⟧ filha de '
        '⟦Filiação da compradora⟧ portadora da carteira de identidade nº ⟦Identidade da compradora⟧ expedida pelo '
        '⟦Emissor da identidade da compradora⟧ em ⟦Emissão da identidade da compradora⟧ inscrita no CPF sob o nº '
        '⟦CPF da compradora⟧, assistida por seu marido ⟦Nome do marido da compradora⟧, '
        '⟦Nacionalidade do marido da compradora⟧, casado, ⟦Profissão do marido da compradora⟧, nascido na cidade de '
        '⟦Naturalidade do marido da compradora⟧, em ⟦Nascimento do marido da compradora⟧, filho de '
        '⟦Filiação do marido da compradora⟧, portador da carteira de identidade nº ⟦Identidade do marido da compradora⟧ '
        'expedida pelo ⟦Emissor da identidade do marido da compradora⟧ em ⟦Emissão da identidade do marido da compradora⟧'
        ', onde consta o CPF nº ⟦CPF do marido da compradora⟧,'
    ),
    (
        'casados pelo regime da ⟦Regime de bens da compradora⟧, ⟦Vigência legal do regime da compradora⟧, ambos com o '
        'endereço eletrônico ⟦Endereço eletrônico da compradora e do marido⟧, residentes e domiciliados na rua '
        '⟦Endereço da compradora e do marido⟧. ⟦Conferência de identidade e capacidade⟧Os presentes reconhecidos como os '
        'próprios, capazes, e identificados face a documentação ora exibida, do que dou fé. E então, pelos contratantes, '
        'falando cada um por sua vez, uniforme e sucessivamente, foi dito o seguinte: 1 - DO IMÓVEL E SUA TITULAÇÃO - '
        '1.1. – Que os Outorgantes são senhores e legítimos proprietários a justo título e absolutamente livre e '
        'desembaraçado de qualquer ônus judicial, extrajudicial, hipoteca legal, foro e pensão do '
        '⟦Tipo e identificação do imóvel⟧ situado na rua ⟦Endereço do imóvel⟧, ⟦Vaga e localização registral do imóvel⟧, '
        'e a respectiva fração ideal de ⟦Fração ideal⟧ do terreno, inscrito na Prefeitura local sob o nº '
        '⟦Inscrição municipal do imóvel⟧ tudo devidamente descrito e caracterizado na matrícula ⟦Matrícula do imóvel⟧ do '
        'Registro de Imóveis da ⟦Circunscrição do imóvel⟧. 1.2. – O imóvel foi adquirido pelos outorgantes por '
        '⟦Denominação do título aquisitivo⟧, datados no ⟦Local do título aquisitivo⟧ em ⟦Data do título aquisitivo⟧ e em '
        '⟦Local do instrumento complementar⟧ em ⟦Data do instrumento complementar⟧, respectivamente Contrato '
        '⟦Contrato do título aquisitivo⟧ da ⟦Instituição do contrato do título aquisitivo⟧, registrada no '
        '⟦Registro do título aquisitivo⟧ e Cancelamento de Alienação no ⟦Averbação de cancelamento de alienação⟧ na '
        'matrícula do Registro de Imóveis antes mencionado. 1.3. - ⟦Conferência dos ônus e da disponibilidade⟧O imóvel '
        'acima descrito está completamente livre e desembaraçado de todo e qualquer ônus, judicial ou extrajudicial, '
        'hipoteca legal ou convencional, arresto, sequestro, não é foreiro, sobre ele não pesando, nem sobre os '
        'Outorgantes, qualquer ação ou execução que impeça a sua livre disponibilidade. 2. - Assim, formalizando os '
        'entendimentos que mantiveram, os Outorgantes achando-se contratados com a outorgada, por esta escritura e na '
        'melhor forma de direito, para lhes venderem, como de fato vendido tem, o imóvel acima descrito, pelo preço certo'
        ' e ajustado de ⟦Preço da venda⟧ (⟦Preço da venda por extenso⟧), sendo pagos da seguinte forma: '
        '⟦Conferência do pagamento⟧⟦Sinal da venda⟧ (⟦Sinal da venda por extenso⟧) através do cheque nº '
        '⟦Número do cheque do sinal⟧, ⟦Banco do cheque do sinal⟧, conta corrente nº ⟦Conta corrente do cheque⟧ agência '
        '⟦Agência do cheque⟧, de titularidade da outorgada ⟦Nome da compradora⟧, em favor do procurador dos outorgantes '
        '⟦Nome do procurador⟧, em ⟦Data do sinal⟧ a título de sinal e princípio de pagamento e ⟦Saldo da venda⟧ ('
        '⟦Saldo da venda por extenso⟧) pagos neste ato por meio de transferência bancária entre contas, débito da conta '
        'poupança nº ⟦Conta poupança debitada⟧ agência ⟦Agência da conta debitada⟧ ⟦Banco da conta debitada⟧, de '
        'titularidade da outorgada ⟦Nome da compradora⟧ em favor do procurador dos outorgantes ⟦Nome do procurador⟧, '
        'crédito da conta corrente nº ⟦Conta corrente creditada⟧ agência ⟦Agência da conta creditada⟧ '
        '⟦Banco da conta creditada⟧. 2.1. - Assim, ⟦Conferência da quitação e da transmissão⟧pagos e plenamente '
        'satisfeitos, os Outorgantes dão a Outorgada, plena, rasa, geral e irrevogável quitação, para nada mais reclamar,'
        ' em tempo algum e sob qualquer pretexto, transmitindo a posse, direito e ação que sobre o referido imóvel '
        'exercia, para que a outorgada dele possam usar, gozar e dispor, obrigando-se os Outorgantes por si, herdeiros e '
        'sucessores, a fazer a presente venda sempre boa, firme e valiosa e a responder pela evicção. 3. - '
        '⟦Conferência da declaração dos outorgantes⟧Os outorgantes através de seu procurador declaram sob '
        'responsabilidade civil e criminal, que não existem quaisquer ações reais ou pessoais reipersecutórias, que '
        'possam impedir a conclusão do presente negócio. 4. – ⟦Conferência da aceitação pelas partes⟧Pelo procurador dos '
        'outorgantes e pela outorgada me foi dito, que aceitam a presente escritura, tal como se acha redigida. 5. – A '
        'Declaração de Operações Imobiliárias (DOI) será apresentada nos termos da legislação em vigor. 6. – O IMPOSTO DE'
    ),
    (
        'TRANSMISSÃO INTER VIVOS, ⟦Conferência do recolhimento do ITBI⟧foi recolhido em ⟦Data de recolhimento do ITBI⟧, '
        'no valor de ⟦Valor do ITBI⟧ (⟦Valor do ITBI por extenso⟧), conforme guia nº ⟦Número da guia do ITBI⟧, tendo sido'
        ' atribuído pela Prefeitura Municipal de ⟦Município do ITBI⟧, o valor de avaliação de '
        '⟦Valor de avaliação do imóvel⟧ (⟦Valor de avaliação por extenso⟧), cujos documentos ficam arquivados nestas '
        'Notas. 7. – ⟦Conferência das certidões e do condomínio⟧As certidões exigidas pelo Decreto Federal nº 93240, '
        'referente a Lei 7433/85, em nome dos outorgantes e do imóvel se encontram arquivadas nestas notas e são as '
        'seguintes: Certidão de Ações e Execuções, Feitos Cíveis, Executivos Fiscais, expedidas pelo Distribuidor de '
        '⟦Município do distribuidor⟧; Certidão de Interdições, Tutelas, Curatelas e Demais Atos, expedidas pelo '
        '⟦Emissor da certidão de interdições⟧, Executivos Fiscais do imóvel; Certidões Negativas da Justiça Federal; '
        'Certidão de Ônus Reais emitida pelo Registro de Imóveis competente; Certidão Negativa de IPTU, emitida pela '
        'Secretaria Municipal de Fazenda e Certidão Negativa FUNESBOM, apresentado o último comprovante de pagamento do '
        'condomínio com vencimento em ⟦Vencimento do condomínio⟧, pago em ⟦Data de pagamento do condomínio⟧, assumindo os'
        ' vendedores a responsabilidade pelo pagamento de eventuais débitos, isentando essa Serventia de Notas e Registro'
        ' de Imóveis de quaisquer responsabilidades; Certidão Negativa de Débitos Trabalhistas, emitida pela Justiça do '
        'Trabalho, ⟦Base normativa da certidão trabalhista⟧. Consultas ao BIB feita em ⟦Data das consultas ao BIB⟧, sob '
        'os nºs ⟦Códigos das consultas ao BIB⟧, referentes a lavratura de escrituras na forma da '
        '⟦Base normativa das consultas ao BIB⟧ e indisponibilidade de bens, tendo como resultado, '
        '⟦Resultado das consultas ao BIB⟧. Consultas feitas em ⟦Data das consultas à CNIB⟧ junto à CNIB, Código HASH: '
        '⟦Códigos das consultas à CNIB⟧ resultado: ⟦Resultado das consultas à CNIB⟧. Consultas '
        '⟦Resultado das consultas de óbito⟧ feitas em ⟦Data das consultas de óbito⟧ de Óbito em nome de '
        '⟦Pessoas consultadas para óbito⟧, Códigos dos números de consultas: ⟦Códigos das consultas de óbito⟧. 8. – '
        '⟦Conferência das declarações específicas das partes⟧Declaram as partes, sob pena de responsabilidade civil e '
        'criminal, para efeitos do ⟦Base normativa das declarações das partes⟧, que: a) não se enquadram, ou possuem '
        'familiar ou estreito colaborador que se enquadre, na definição de pessoa politicamente exposta, nos termos da '
        '⟦Base normativa de pessoa politicamente exposta⟧; b) não se enquadram, ou possuem familiar ou estreito '
        'colaborador que se enquadre, na definição de beneficiário final de pessoa jurídica, nos termos do '
        '⟦Base normativa do beneficiário final⟧; c) não se enquadram, ou mantêm relação profissional ou pessoal com quem '
        'se enquadre, como pessoa investigada ou acusada de terrorismo e/ou sancionada pelo Conselho de Segurança da '
        'Organização das Nações Unidas. 9. – Requerem, desde já, as partes, sejam praticados todos os atos necessários ao'
        ' registro da presente escritura pública junto ao Serviço de Registro de Imóvel competente. 10. – Por fim, '
        'requerem as partes sejam as eventuais exigências do Serviço Registral formuladas de forma clara e fundamentada, '
        'nos termos do ⟦Código de Normas aplicável às exigências registrais⟧, indicando ainda os dispositivos legais em '
        'que se escoram, em respeito à vinculação da atividade administrativa registral ao princípio da legalidade '
        'estrita. ⟦Conferência dos emolumentos e acréscimos⟧CERTIFICO que pelo presente ato são devidos os emolumentos e '
        'demais acréscimos legais, como se segue: ⟦Tabela e item dos emolumentos⟧'
    ),
    (
        '⟦Valor dos emolumentos⟧; PMVCMV-⟦Base e valor do PMVCMV⟧; FETJ-⟦Base e valor do FETJ⟧; FUNDPERJ-'
        '⟦Base e valor do FUNDPERJ⟧; FUNPERJ-⟦Base e valor do FUNPERJ⟧; FUNARPEN-⟦Base e valor do FUNARPEN⟧; '
        'Distribuição-⟦Base e valor da distribuição⟧; Consultas sobre Indisponibilidade de bens e lavratura de '
        'escrituras-⟦Base e valor das consultas e lavratura⟧; Selo de Fiscalização ⟦Valor do selo de fiscalização⟧; ISS '
        '⟦Valor do ISS⟧; que serão recolhidos na forma legal. ⟦Conferência da lavratura e das assinaturas⟧ASSIM, justos e'
        ' contratados, me pediram lhes lavrasse a presente escritura, o que lhes fiz, li em voz alta e bem clara perante '
        'todos que aceitam, outorgam e assinam, dispensando a presença de testemunhas nos termos do '
        '⟦Base normativa da dispensa de testemunhas⟧. Eu, ⟦Nome da autoridade lavrante⟧, ⟦Cargo da autoridade lavrante⟧, '
        'cadastro ⟦Cadastro da autoridade lavrante⟧, lavrei, li, conferi e encerro o presente ato, colhendo as '
        'assinaturas das partes, subscrevo e assino. OUTORGANTES: ⟦Identificação dos signatários outorgantes⟧. OUTORGADA:'
        ' ⟦Identificação dos signatários da outorgada⟧.'
    ),
)

CAMPO = re.compile(r'⟦([^⟧]+)⟧')
ROTULOS = {chave_campo(rotulo): rotulo for pagina in PAGINAS for rotulo in CAMPO.findall(pagina)}
CONFERENCIAS = frozenset(chave for chave in ROTULOS if chave.startswith('fiel_conferencia_'))
CORPO = ' '.join(CAMPO.sub(lambda match: '{{' + chave_campo(match[1]) + '}}', pagina) for pagina in PAGINAS)
CONFERENCIA_CENARIO = chave_campo('Conferência do cenário da escritura')
ROTULOS[CONFERENCIA_CENARIO] = 'Conferência do cenário da escritura'
CONFERENCIAS |= {CONFERENCIA_CENARIO}
CORPO = '{{' + CONFERENCIA_CENARIO + '}}' + CORPO
