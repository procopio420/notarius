# Etapa 2 — versão parcial do padrão para revisão

25/10/2026 · `piloto-imagens-v0` · **Rascunho parcial, não aprovado.**

## Material recebido e preservação

Cinco imagens fornecidas pelo usuário, examinadas visualmente. Para este relatório, I1 a I5 correspondem à ordem dos anexos: abertura/qualificação; imóvel e negócio; tributo e certidões; encerramento e despesas; manifesto de assinaturas. Esta ordem é uma hipótese de sequência visual, não comprovação de integralidade. Há tarjas em trechos relevantes e dados de um caso anterior ainda visíveis. Nada sob as tarjas foi reconstruído.

Os cinco originais foram copiados para uma pasta privada fora do repositório: `Documents/Notarius-Privado/piloto-profissional-etapa2-20261025`, no perfil local do usuário. Não se copiou nenhum original, dado pessoal, identificador de validação, valor, data do negócio, dado bancário ou assinatura para os arquivos versionados. Não houve consulta aos links de validação, envio externo, importação em atendimento ou alteração do banco. A cópia local preserva o material, mas não representa validação das permissões de acesso ou do backup.

O fornecimento permite preparar esta adaptação para revisão; autorização da escrevente para adotar o padrão e aprovação da redação ainda precisam ser registradas por ela. O manifesto não comprova, nesta análise, autenticidade ou validade de assinaturas.

## Entrega e limite

`modelo-v0.txt` contém títulos visíveis e marcadores já reconhecidos pelo mecanismo existente (`ficha.py` / `modelo_referencia.py`). É uma peça de revisão textual, sem carregamento automático na biblioteca ou em atendimento. Não configura posições, regras de obrigatoriedade, vínculos, dependências ou cenários: isso pertence à etapa 3, após decisão profissional.

Não se apresenta o rascunho como transcrição literal integral. O título foi simplificado, as qualificações foram agrupadas e a representação foi separada para revisão. A alternativa singular/plural do título dos compradores é uma anotação editorial a resolver, não uma seleção automática. As fórmulas profissionais foram mantidas como blocos variáveis quando contêm declaração, consequência ou situação que precisa de confirmação. Isso evita embutir no texto fixo fatos do exemplo. Ainda faltam texto-base integral legível, decisões de aplicação e aprovação para concluir a etapa 2.

## Separação do padrão, dados e confirmações

| Origem | Parte / marcador do rascunho | Tratamento proposto para revisão |
|---|---|---|
| I1 | Título e títulos de partes | Texto fixo candidato; confirmar título, singular/plural e posição de representante. Cabeçalho e contatos da serventia do exemplo não foram transferidos. |
| I1 | `abertura` | Data, local, serventia, autoridade e comparecimento variáveis. Comparecimento, capacidade e identificação dependem de confirmação específica; não são texto factual automático. |
| I1–I2 | `vendedores`, `compradores` | Qualificações variáveis: pessoa, identificação, nacionalidade, profissão, estado civil, endereço e demais elementos efetivamente requeridos pelo padrão aprovado. Não usar nomes/dados do exemplo. Pessoas e papéis serão vinculados explicitamente na etapa 3. |
| I1 | `representacao` | Separar representado, representante, instrumento, órgão, livro/folha, data e poderes/limites. Presença de representação neste exemplo não a torna obrigatória em outro caso. |
| I2 | `titularidade`, `imovel`, `aquisicao` | Descrição literal, matrícula/registro, localização, fração, acessórios e título aquisitivo são variáveis. Fração, garagem e financiamento aparecem no exemplo; não viram características padrão de todos os imóveis. |
| I2 | `onus` | A afirmação de inexistência de ônus/impedimentos é declaração a conferir, nunca valor inicial. Distinguir documento apresentado e conclusão profissional. |
| I2 | `preco`, `pagamento` | Separar preço, moeda, parcelas, meios, vencimentos e comprovantes. Contas, bancos e pagamento descritos no exemplo foram retirados. Cronograma não prova execução. |
| I2 | `quitacao`, `transmissao` | Redação integral pendente de revisão. Declaração de quitação, transferência e efeitos da venda não devem ser incluídos por mera existência de preço ou parcela. |
| I2 | `declaracoes_vendedores` | Declarações sobre ações/impedimentos e responsabilidade são específicas de quem declara e do caso. Não herdar declaração negativa. |
| I2 | `declaracoes_compradores` | Ciência/aceitação e declarações do representante dependem da pessoa que as presta, poderes e confirmação. Não atribuir automaticamente ao comprador declaração de procurador. |
| I2 | `doi` | A indicação de apresentação futura não comprova apresentação realizada. Confirmar redação e quem responde por essa providência. |
| I2–I3 | `tributo` | Guia, base, avaliação, valor, data e recolhimento variáveis. Documento/guia apresentada não é confirmação automática de pagamento. Não converter valores do exemplo em fórmula tributária. |
| I3 | `certidoes` | Lista variável por pessoa/imóvel, emissor, referência, data e resultado. A lista visível é inventário do exemplo, não exigência jurídica universal. Confirmar quais documentos e trechos compõem o padrão aplicável. |
| I3 | `consultas` | Consultas de indisponibilidade, óbito e demais consultas visíveis precisam de sujeito, fonte, data, código e resultado do novo caso. Nunca iniciar com resultado negativo ou reutilizar código. |
| I3 | `declaracoes_partes` | Declarações sobre enquadramento e situações específicas dependem de decisão e confirmação individual. Não presumir negativas a partir da cláusula do exemplo. |
| I3 | `requerimentos` | Definir atos solicitados, destinatário, fundamento e aplicabilidade. Referências normativas do documento não foram validadas como vigentes nem adotadas como regras do sistema. |
| I3–I4 | `encerramento` | Redação de leitura, aceitação, lavratura, subscrição, assinaturas e eventual dispensa de testemunhas depende de confirmação e orientação profissional. Não declarar ato concluído em minuta. |
| I3–I4 | `emolumentos` | Rubricas, valores e referências variáveis; não copiar tabela, percentuais ou totais do exemplo. Confirmar também a quebra entre páginas, pois a seção atravessa as imagens. |
| I5 | Sem bloco factual importado | Manifesto pertence à execução/assinatura do documento anterior. Não reutilizar logotipos, selo, assinaturas, horários, matrícula profissional ou links/códigos como parte do novo ato. |

## Condições propostas para decisão, ainda não implementadas

| Bloco | Condição a aprovar pela escrevente | Se faltar decisão/evidência |
|---|---|---|
| Representação | Quando houver representação expressamente identificada, instrumento e poderes revisados; definir redação para ausência de representação. | Não inferir pelo nome, estado civil ou pelo modelo. |
| Qualificação conjugal e participantes múltiplos | Definir papéis, relações e quantidade/ordem dos participantes para o cenário escolhido. | Não presumir que cônjuge seja vendedor, anuente ou representante. |
| Fração, garagem e aquisição financiada | Incluir somente características/título do imóvel efetivamente confirmados e cobertos pelo padrão escolhido. | Não carregar o histórico do exemplo. |
| Quitação | Declaração específica confirmada e redação aprovada, com distinção entre pagamento previsto e realizado. | Não incluir fórmula de quitação como consequência de preencher preço. |
| Tributo, certidões e consultas | Evidência individual atual, destinatário correto e confirmação do estado/resultado; regra profissional de aplicação aprovada. | Preservar pendência; não declarar recolhido, apresentado ou negativo. |
| Declarações e requerimentos | Aprovação da redação e confirmação por quem declara, com aplicabilidade no caso. | Não incluir/omitir automaticamente uma declaração desconhecida. |
| Encerramento, testemunhas e assinaturas | Definir o que pode constar da minuta e o que somente se afirma após a prática do ato. | Não reproduzir assinaturas, selos ou afirmação de conclusão. |

Esta tabela descreve decisões necessárias, não orientação jurídica ou um conjunto de condições já homologado. Nenhuma cláusula condicional foi ativada no software nesta rodada.

## Perguntas para a escrevente concluir a revisão

1. As cinco imagens cobrem o padrão completo e na ordem correta? Fornecer texto editável ou cópia legível dos trechos fixos cobertos; dados pessoais podem continuar ocultos. Onde a tarja cobre só dado variável, confirmar o nome/função do campo, sem necessidade de expor seu valor.
2. Autoriza este padrão como base do piloto? Qual versão deve prevalecer? Indicar trechos que são fixos e os que só pertencem ao exemplo.
3. Revisar especialmente representação, ônus, quitação, transmissão, declarações negativas, tributo/consultas, encerramento e dispensa de testemunhas. Fornecer a redação autorizada e a condição de aplicação de cada bloco.
4. Escolher o primeiro cenário e confirmar participantes, relações, imóvel e pagamento cobertos. Essas decisões serão usadas somente quando a etapa 3 for solicitada.
5. Aprovar ou corrigir o rascunho textual antes de carregá-lo como modelo. Conferência de Word/PDF e apresentação final continua para a etapa 5.

## Verificações

Revisão visual dos cinco anexos; 23 marcadores conferidos contra os campos existentes, delimitadores íntegros; rascunho sem CPF, e-mail, links, valores ou datas do exemplo. Revisão manual da entrega versionada para evitar transferência de dados pessoais. **6 testes de `tests.test_modelo_referencia` passaram em 9,422 segundos**, em banco isolado; verificação de sistema e `git diff --check` sem problemas. Essa regressão verifica o mecanismo existente com dados fictícios, não a correção profissional deste rascunho. Sem novos testes de interface ou exportação, pois não houve alteração de código ou configuração nem geração de minuta.

**Estado:** preparação parcial entregue para revisão; etapa 2 permanece pendente de material legível e decisões da escrevente. Etapas 3 a 6 não executadas. IA externa permanece bloqueada.
