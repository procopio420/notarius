# Compra e venda — mapa do primeiro caso

Versão 0.1 — 24/10/2026 — **aguardando revisão da escrevente**

Atualização de escopo em 24/10/2026: o usuário escolheu preparar participação direta e procuração para comparação. Os dois materiais estão em `homologacao-compra-venda/COMPARACAO_PARA_ESCREVENTE.md`; execução e verificações na seção 13 de `EXECUCAO_FLUXO_PRINCIPAL.md`. Essa escolha não homologa este mapa nem resolve as decisões profissionais abaixo.

Referência recebida posteriormente: cinco imagens de escritura e manifesto, com dados do exemplo rasurados e uma possível duplicata. A imagem complementar enviada em seguida supriu a continuação do item 6 até o fragmento final. A leitura visual, fontes e pendências estão em `COMPRA_VENDA_REFERENCIA_IMAGENS.md`. O recebimento não foi tratado como aprovação do modelo nem como confirmação dos fatos para outro atendimento.

Este mapa define o que o software deve perguntar, extrair, comparar e encaminhar à revisão humana. Não é uma lista de exigências legais. Os documentos necessários, as regras profissionais e o texto do ato serão definidos pela escrevente para o cenário escolhido. Nenhuma aprovação foi presumida.

## 1. Resultado que queremos obter

A escrevente abre um atendimento, anexa os documentos, complementa informações pela conversa e recebe perguntas curtas sobre o que faltar. O sistema apresenta evidências e divergências, registra suas decisões e preenche um modelo aprovado. A escrevente revisa, edita e exporta a minuta.

O sistema não declara por conta própria que houve pagamento, consulta, assinatura, manifestação de vontade ou qualquer outro acontecimento. Não resolve dúvidas jurídicas nem comprova autenticidade apenas comparando arquivos.

## 2. Cenário inicial proposto

Para reduzir a primeira entrega a algo testável, propomos um imóvel e participantes pessoas físicas, com um único modelo profissional definido pela escrevente. Quantidade de participantes, situação conjugal, representação e condições do negócio ainda precisam ser delimitadas por ela.

O exemplo enviado tem representação por procuração. Isso é uma variante a mapear, não uma condição obrigatória de toda compra e venda.

**Decisão pendente:** começar com participantes assinando diretamente ou incluir representação já no primeiro cenário? Quando aparecer algo fora do cenário aprovado, o sistema deve interromper a tarefa e encaminhar à escrevente, sem adaptar cláusulas automaticamente.

## 3. Documentos e outras fontes

Esta é uma organização preliminar das fontes observadas no exemplo. A escrevente deve informar o nome exato, quando cada documento se aplica e o que precisa conferir nele. Não estão definidos prazos de validade, obrigatoriedade ou critérios jurídicos.

| Grupo de informação | Fontes a confirmar com a escrevente | O que precisamos decidir |
|---|---|---|
| Identificação dos participantes | Documentos de identificação apresentados no atendimento | Quais arquivos aceita e quais campos compara |
| Situação conjugal e participação de cônjuge | Documentos e declarações usados por ela para essa finalidade | Campos, datas e situações que precisam de decisão profissional |
| Identificação e histórico do imóvel | Matrícula e demais documentos que ela utiliza | Identificadores, descrição e trechos que devem ser preservados literalmente |
| Representação | Instrumento de procuração, quando aplicável | Quais dados extrair e quais verificações ficam obrigatoriamente com a escrevente |
| Preço e condições | Informação expressa das partes/escrevente e documentos apresentados | Como registrar negociação, parcelas, datas e alterações |
| Pagamento declarado ou comprovado | Declaração ou comprovante identificado pela escrevente | Distinguir condição combinada, pagamento declarado e comprovante recebido |
| Tributos, certidões e consultas | Documentos e resultados efetivamente utilizados no caso | Lista aplicável, responsável pela obtenção e resultado a registrar |
| Redação | Modelo fornecido e aprovado pela escrevente | Versão, trechos fixos e condições de inclusão de cláusulas |

Uma escritura anterior serve como referência de redação. Não é fonte dos nomes, valores, certidões ou acontecimentos de um atendimento novo.

## 4. Campos da ficha futura

Hoje o protótipo tem sete campos amplos. A proposta abaixo os desdobra; **esses campos detalhados ainda não foram implementados nem aprovados**. A escrevente pode remover, acrescentar ou alterar cada item.

| Bloco | Dados propostos | Origem e conferência esperadas |
|---|---|---|
| Pessoas e papéis | Nome, identificadores apresentados, papel no ato, demais dados de qualificação definidos no modelo | Vincular cada dado à pessoa certa e comparar suas ocorrências nas fontes |
| Situação conjugal | Situação informada, cônjuge e informações documentais utilizadas | Mostrar fontes e diferenças; não decidir participação ou regime aplicável |
| Imóvel | Identificadores, localização, descrição e informações utilizadas sobre titularidade | Guardar transcrição e página; não resumir a descrição silenciosamente |
| Representação | Representante, representado, instrumento e trechos pertinentes | Extrair evidências; adequação dos poderes e efeitos exige decisão profissional |
| Negócio | Preço, condições, parcelas e datas expressamente informadas | Comparar fontes; calcular soma de parcelas por código, se o cenário aprovado usar parcelas |
| Pagamento | Situação declarada, evidência recebida e informação confirmada | Não converter “pagamento previsto” em “pagamento realizado” |
| Documentação complementar | Tipo, referência, data, resultado e origem das consultas/documentos | Não preencher resultado ou declarar consulta realizada com base no modelo |
| Redação e revisão | Modelo e versão, decisões, correções e texto preparado | Preservar autoria, origem dos dados e versões |

Se um campo admitir várias pessoas, bens ou parcelas, será uma coleção de registros, não um texto único em que a IA misture os elementos.

## 5. O que cada informação deve guardar

- Valor exatamente extraído, separado de eventual valor normalizado para comparação.
- Pessoa, imóvel ou parcela a que pertence, quando identificado com segurança.
- Arquivo e página, trecho literal e localização visual quando disponível; ou mensagem de origem.
- Situação: proposta extraída, informada pela escrevente, confirmada pela escrevente, ausente, divergente ou leitura incerta.
- Quem confirmou ou corrigiu, quando e por qual motivo.
- Versões anteriores e decisão sobre eventual divergência.

“Extraído” não significa “correto”, “confirmado” não significa “autenticidade comprovada” e “não encontrado” não significa que o fato não existe. Informação normalizada nunca deve substituir a transcrição original sem rastreabilidade.

## 6. Conversa e perguntas

A tela principal continua sendo a conversa. O sistema deve perguntar sobre um assunto de cada vez e reunir campos relacionados em um pop-up curto quando isso facilitar a resposta. Não mostrar um formulário extenso como ponto de partida.

| Situação | Exemplo de pergunta ou aviso |
|---|---|
| Arquivo sem leitura suficiente | “Não consegui ler este trecho da página 2. Pode enviar outra cópia ou conferir o original?” |
| Pessoa não identificada com segurança | “Não consegui associar este documento ao participante. A quem ele pertence?” |
| Duas grafias de um nome | “Estes arquivos apresentam nomes diferentes. Confira os trechos e informe como devemos registrar.” |
| Preço ausente | “Qual é o preço informado para este negócio? De onde veio essa informação?” |
| Condições incompletas | “Você informou parcelas, mas faltam os valores ou as datas. Pode complementar?” |
| Pagamento ambíguo | “Isso descreve uma condição combinada ou um pagamento já informado como realizado?” |
| Modelo inadequado | “O modelo não cobre esta situação. Preciso da revisão da escrevente antes de redigir.” |
| Falha técnica | “Não consegui concluir esta tarefa. A etapa continua pendente; não substituí o resultado por uma suposição.” |

Esses exemplos são propostas de interação, não perguntas jurídicas definitivas. A escrevente deve ajustar sua linguagem e os campos relacionados.

## 7. Situações que interrompem o avanço

1. Falta um documento ou dado classificado como necessário para o cenário aprovado.
2. Leitura incerta, página ausente ou arquivo que o sistema não consegue processar.
3. Valores, identificadores ou outras informações divergentes entre fontes.
4. Dúvida sobre qual pessoa, imóvel ou parcela corresponde a um trecho.
5. Situação fora do cenário coberto pelo modelo ou dúvida de interpretação.
6. Falha de serviço ou de validação.
7. Modelo não aprovado ou informação obrigatória ainda não confirmada.
8. Dados ou documentos alterados depois da confirmação ou da preparação da minuta.

Parar significa suspender a tarefa afetada e a preparação enquanto houver bloqueios relevantes, informar a causa e permitir que a escrevente resolva a pendência. A conversa e a consulta ao histórico continuam disponíveis.

Uma revisão manual não deve apagar o aviso de que a leitura automática falhou. Deve registrar a decisão humana separadamente. Uma nova evidência exige nova conferência; a decisão anterior não aprova automaticamente o material novo.

## 8. Separação do modelo

| Categoria | Tratamento proposto |
|---|---|
| Texto fixo profissional | Fornecido e aprovado pela escrevente; não completado livremente pela IA |
| Dados variáveis | Preenchidos com informações confirmadas e rastreáveis |
| Cláusulas condicionais | Usadas somente sob condições explicitamente definidas e aprovadas para o cenário |
| Afirmações sobre fatos e procedimentos | Exigem evidência ou confirmação específica; não entram por estarem em uma escritura anterior |
| Campo não resolvido | Mantém pendência e impede apresentar a minuta como pronta |

Ainda precisamos marcar no modelo profissional quais trechos pertencem a cada categoria. O mapa não autoriza reutilizar cláusulas legais ou valores de exemplos antigos sem revisão.

## 9. Caso fictício de referência

Os arquivos `docs/teste-escrevente/01-dados-ficticios.txt` e `02-preco-divergente.txt` servem para testar a infraestrutura já existente. Eles não representam um conjunto documental completo de uma compra e venda.

Para validar a interpretação por IA, a escrevente deverá revisar um conjunto fictício representativo do cenário escolhido. Antes de executar a IA, registraremos o resultado esperado: pessoas e papéis, campos e fontes, informações ausentes, divergências, perguntas necessárias, cláusulas autorizadas e texto final esperado.

Não criaremos identificadores pessoais, matrícula ou comprovantes que possam ser confundidos com documentos reais. Não é necessário enviar dados de clientes para aprovar este mapa.

## 10. Critérios para aprovar o primeiro cenário

- Cada informação proposta pode ser conferida na fonte ou está identificada como fornecida pela escrevente.
- O sistema não inventa fatos para completar campos ou cláusulas.
- Divergências e problemas de leitura preparados para o teste são apresentados e bloqueiam o avanço.
- A pergunta sem resposta ou sem confirmação não desaparece.
- Correções e decisões ficam no histórico; dados novos reabrem a conferência.
- A minuta usa o modelo aprovado e não contém afirmações não confirmadas.
- Word/PDF preservam o conteúdo da versão salva e têm aparência revisada pela escrevente.

O teste de um cenário não comprova cobertura de outros tipos de imóvel, participantes ou condições. A ampliação será feita explicitamente, caso a caso.

## 11. Respostas que precisamos da escrevente

Pode responder nesta conversa, sem editar este arquivo e sem informar dados pessoais:

1. **Primeiro cenário:** qual tipo de compra e venda simples quer usar como referência? Incluir procuração agora ou depois?
2. **Documentos:** quais arquivos normalmente recebe nesse cenário e quais só se aplicam em situações específicas?
3. **Informações externas aos anexos:** o que costuma perguntar diretamente às partes ou receber por mensagem?
4. **Conferências prioritárias:** quais erros ou divergências encontra com mais frequência e quais impedem continuar?
5. **Modelo:** qual versão sem dados reais devemos usar, e quais trechos variam conforme o caso?
6. **Ponto final do trabalho:** qual conteúdo e formatação a minuta precisa ter para ser útil antes da revisão final dela?

**Estado atual:** proposta preparada, aguardando essas respostas. Depois incorporaremos as decisões, registraremos a versão aprovada e só então trataremos o mapa como especificação do primeiro cenário.
