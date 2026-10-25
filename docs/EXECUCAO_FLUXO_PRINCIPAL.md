# Notarius — documento único de execução do fluxo principal

Versão 1.15 · 25/10/2026 · Diagnóstico original preservado nas seções 1–8; ficha na seção 9; propostas na seção 10; pendências na seção 11; preenchimento na seção 12; cenários na seção 13; ato e complementos na seção 14; homologação na seção 15; ensaio técnico integral na seção 16; documentos vinculados na seção 17; contrato de análise documental na seção 18; comparação entre fontes na seção 19; conversa orientada pelas pendências na seção 20; blocos explícitos da minuta na seção 21; teste integrado na seção 22; preparação offline para IA real na seção 23.

A numeração das solicitações do usuário prevalece sobre o roteiro proposto originalmente: a **Etapa 2 autorizada é a ficha estruturada**, não a homologação do cenário. Sua execução não marca decisões profissionais pendentes como aprovadas.

## 1. Objetivo, escopo e uso deste documento

A escrevente abre uma compra e venda, envia documentos, complementa informações pela conversa, resolve dúvidas e recebe uma minuta preenchida conforme modelo profissional aprovado, com revisão e exportação da versão correta.

Este documento é a referência de execução das próximas etapas. Consolida a situação encontrada no código local, as propostas de estrutura e os critérios de conclusão. Os documentos anteriores permanecem como histórico e fontes; não constituem planos paralelos. Atualizar este arquivo ao concluir cada etapa, registrando evidência, limitações e decisões profissionais, sem apagar o diagnóstico original. Planos aqui descritos não representam funcionalidades implementadas nem autorização para executar todas as etapas nesta rodada.

**Diagnóstico central:** existe um percurso técnico local de anexos até Word/PDF, com revisão humana e histórico. Entretanto, os dados são principalmente blocos textuais, a leitura assistida reconhece rótulos explícitos e a referência da escritura é uma estrutura parametrizada. Isso ainda não demonstra o objetivo completo de organizar documentos livres, distinguir participantes e produzir automaticamente uma minuta profissional fiel ao padrão homologado.

### 1.1 Limites obrigatórios

- Manter a interface em **Conversa, Documentos e Minuta** e reaproveitar os componentes e serviços existentes.
- Nenhum dado novo por suposição. Separar extração, informação da escrevente, confirmação, aplicabilidade e problemas de leitura/interpretação.
- Toda proposta deve ter fonte e trecho literal. A literalidade não garante interpretação correta, autenticidade ou verdade.
- Somente a escrevente resolve associações ambíguas, divergências, questões profissionais e confirma dados. Não transformar decisão genérica de revisar arquivo em confirmação de todos os seus dados.
- Impedir uso na minuta de dados afetados por pendência, leitura desatualizada, associação duvidosa ou interpretação não resolvida.
- Modelo e escritura anterior são fontes de redação, nunca prova de fatos do novo atendimento. Pagamento realizado, consulta efetuada, leitura do ato ou assinatura exigem informação e confirmação específicas do caso.
- Requisitos documentais, prazos, cláusulas, cenários e critérios jurídicos devem ser **configuração versionada a homologar pela escrevente**, sem exigências jurídicas criadas pelo software.
- Nesta fase: arquivos fictícios, simulação explicitamente identificada, sem envio a provedores externos. Não alterar cobrança nem consultar/exibir chaves.
- Preservar isolamento por cartório e atendimento, autoria, versões e proteção contra alterações concorrentes.

### 1.2 Base e alcance da análise

Inspeção estática do checkout local sobre o commit-base `228b932`, incluindo alterações locais já existentes; esse commit sozinho não representa o código analisado. Foram lidos modelos, serializers, endpoints de atendimento, leitura/OCR local, conferência, redação, exportação, telas e testes associados. As referências C01–C31 ao final apontam para arquivos e linhas verificados nesta leitura. Linhas podem mudar: conservar também o nome do símbolo citado.

Na Etapa 1 não foram alterados código, banco, configuração, servidores ou testes. Não houve envio externo, homologação jurídica, validação de documentos reais nem nova execução dos testes funcionais naquela etapa. Resultados de testes de rodadas anteriores são evidência histórica, discriminada na seção 7. A implementação posterior da Etapa 2 está registrada na seção 9.

## 2. Fluxo completo: documentos até exportação

| Passo | Percurso esperado | O que o código faz hoje e onde verificar | Condição de avanço e diferença remanescente |
|---|---|---|---|
| 1. Entrar e abrir atendimento | Usuária autenticada, cartório autorizado, compra e venda identificada. | `AtendimentoViewSet.tenant`, `get_queryset` e `perform_create` filtram cartório e registram autoria [C01]. A tela usa chaves de consulta com atendimento, usuária e cartório [C02]. | Existe controle de vínculo ao cartório. Ainda não há permissão profissional específica de confirmar/homologar distinta da associação ao cartório. |
| 2. Definir cenário e padrão | Registrar cenário coberto e versão do modelo homologado, sem pedir formulário extenso. | Abertura não exige cenário estruturado. O modelo pode ser carregado depois, em Minuta; seus marcadores adicionam campos exigidos [C03] [C04]. | Falta contrato de cenário/aplicabilidade e configuração profissional versionada. A estrutura enviada não é modelo integral homologado. |
| 3. Receber documentos | Guardar original, identificar arquivo e permitir consulta. | `anexos` aceita PDF, TXT UTF-8, PNG/JPG, valida formato e até 10 MB; deduplica por SHA-256 dentro do atendimento e guarda conteúdo no banco [C05] [C06]. | Arquivo recebido não significa documento identificado, suficiente ou válido para o ato. Não há classificação documental estruturada vinculada às pessoas e ao imóvel. |
| 4. Ler páginas | Extrair texto e preservar erros, canais e versões. | PDF nativo e OCR Windows local, até 40 páginas de PDF e 10 páginas de OCR por arquivo; falhas ficam em revisão. TXT é uma unidade de texto, não página física. Releitura cria nova versão [C07] [C08] [C09]. | Existe leitura técnica, não entendimento documental. Erro/OCR não pode ser convertido em certeza. A confirmação genérica do arquivo não resolve isoladamente cada trecho afetado. |
| 5. Propor informações | Cada proposta aponta campo, objeto, fonte, leitura e trecho. | `extrair_rotulos` encontra linhas explicitamente rotuladas. `conferir` monta candidatos com mensagem ou arquivo/página/versão/canal/trecho. `analisar_mensagem` é simulação local, não IA semântica [C10] [C11]. | Não há associação estruturada e persistente da proposta a uma pessoa, papel, documento específico ou imóvel. Texto livre continua dependendo de interpretação humana. |
| 6. Associar objetos | Separar pessoa, papel, instrumento de representação, imóvel e parcelas sem fusões. | A ficha tem campos textuais como vendedores, compradores, representação, certidões e consultas [C03] [C06]. | Esta ligação por objetos está ausente no atendimento. Os modelos legados de partes/processos não estão conectados a esse percurso [C12]. |
| 7. Complementar pela conversa | Perguntas curtas; respostas informadas ficam distintas das confirmadas. | Mensagens persistentes, envio idempotente, orientação local e diálogo de resposta. Texto não reconhecido gera pendência por mensagem. Resposta cria mensagem e revisão de campo [C13] [C14] [C15]. | Existe conversa operacional; não há investigação semântica. Uma revisão de mensagem pode encerrar sua pendência sem o servidor comprovar que todos os trechos foram tratados nos objetos corretos. |
| 8. Conferir e resolver | Mostrar evidências, divergências e efeitos da decisão; apenas escrevente decide. | Conferência compara valores dos mesmos campos; respostas exigem assinatura da pergunta, versão esperada, justificativa e confirmação. Revisões e decisões são preservadas [C10] [C14] [C16]. | Falta modelo persistente de pendência por dado/objeto e dependências. Comparação do bloco inteiro não distingue pessoas, fatos, temporalidade ou versões de negociação. |
| 9. Revisar modelo | Selecionar versão homologada e cláusulas aplicáveis, separadas dos fatos. | Modelo por atendimento tem versão, autoria e aprovação explícita; biblioteca não transfere aprovação automaticamente. Estrutura das imagens pode ser carregada como rascunho [C04] [C17] [C18]. | Aprovação de texto existe. Homologação de cenário, regras documentais e condições de cada cláusula ainda não estão modeladas. |
| 10. Preparar minuta | Preencher apenas dados confirmados, rastreáveis e sem bloqueios em modelo aprovado. | `preparar` exige conferência sem pendências, modelo aprovado, valores confirmados e marcadores resolvidos; substitui literalmente. `snapshot` vincula versão aos dados, anexos, mensagens e decisões [C19]. | O preenchimento funciona. Muitos campos ainda pedem o texto completo da cláusula à escrevente. Regex de fatos fixos não garante segurança semântica de redação arbitrária. |
| 11. Revisar e editar | Conferir texto e fontes, corrigir preservando versões. | Edição cria nova minuta com base, autora e motivo; comparação literal e consulta de fontes disponíveis. Edição não altera ficha. Revisão final exige confirmar texto, dados e fontes e registra hash do texto salvo [C20] [C21]. | Alterações manuais não são automaticamente vinculadas a novos dados/fontes. A revisão final é declaração humana, não auditoria semântica do conteúdo. |
| 12. Exportar | Exportar a versão atual, revisada, compatível com as fontes e visualmente homologada. | Endpoint revalida estado, recusa versão desatualizada ou sem revisão final e produz DOCX/PDF do texto salvo. Exportadores acrescentam identificação de minuta e metadados [C22] [C23]. | Exportação técnica existe. A aparência é genérica e não foi demonstrada como equivalente ao modelo profissional enviado. |

Alteração de fonte, resposta, decisão ou modelo pode desatualizar a minuta. Conversa e consulta histórica devem continuar disponíveis durante o bloqueio. O objetivo final desta fase termina na **minuta revisada exportável**; não inclui assinatura eletrônica, pagamento, protocolo ou execução de consultas externas.

## 3. Funcionalidades existentes, parciais e ausentes

Legenda: **existente** significa mecanismo identificado no código, dentro do alcance descrito; **parcial** significa mecanismo presente com lacuna relevante ao objetivo; **ausente no fluxo** significa que não foi encontrada integração funcional nesse percurso, mesmo que haja módulos legados com nomes relacionados.

| Capacidade | Situação | Evidência e limite |
|---|---|---|
| Criar/listar/reabrir atendimento de compra e venda | Existente | Endpoints, modelo e tela [C01] [C02] [C06]. |
| Três áreas principais e conversa persistente | Existente | Abas, mensagens e preservação ao alternar painéis [C02] [C13]. Texto ainda não enviado não é mensagem salva. |
| Recepção, original e páginas de anexos | Existente | Anexo e leitura versionada [C05] [C06] [C07]. |
| OCR local com avisos e regiões | Existente | WinRT em português, posições e limites [C08]. Depende do Windows e do idioma instalado; não certifica leitura. |
| Extração de fatos de documentos livres | Ausente no fluxo | O reconhecimento atual é por rótulos explícitos [C10] [C11]. OCR extrai texto, não fatos. |
| Simulação de propostas sem provedor | Existente | Função local e endpoint com `modo=simulacao_local` e origem [C11]. |
| Fonte literal e separação extraído/informado/confirmado | Parcial | Candidatos de documentos e mensagens são distintos; revisão confirma valores [C10] [C16]. Não há registro autônomo persistente de toda proposta nem associação por objeto. |
| Várias evidências para um mesmo dado | Parcial | Conferência agrega candidatos; revisão admite uma mensagem ou uma página [C10] [C16]. Falta relação persistente decisão → propostas/evidências aceitas e rejeitadas. |
| Pessoas e papéis do atendimento | Ausente no fluxo | Vendedores/compradores são texto; `Parte` e `ProcessoParte` são legados sem vínculo ao `Atendimento` [C03] [C06] [C12]. |
| Representante, representado e instrumento separados | Ausente no fluxo | Há apenas bloco textual de representação e pergunta orientadora [C03]. |
| Imóvel, titularidade e aquisição estruturados | Parcial | Campos separados por assunto, todos textuais; sem identidade de imóvel ou titular vinculado [C03] [C06]. |
| Negociação, parcelas e pagamentos separados | Parcial | Preço/pagamento/quitação são texto. Apenas comparação numérica conservadora de preço; sem coleção de parcelas, cálculo da soma ou estados próprios do pagamento [C03] [C10]. |
| Pendências e divergências | Parcial | Calculadas a cada conferência; decisões persistem por chave e assinatura [C10] [C14]. Não são objetos com alvo, tipo, dependências e resolução estruturada. |
| Revisão e histórico de campos | Existente | Revisões incrementais com autoria, motivo e controle de versão [C06] [C16]. Não equivale a histórico por pessoa/documento individual. |
| Dados novos reabrem conferência e desatualizam minuta | Parcial | Assinaturas de candidatos e snapshot [C10] [C19]. Não há grafo de dependências para determinar os dados afetados por texto livre ou interpretação nova. |
| Configuração profissional de cenário e requisitos | Ausente no fluxo | Campos, perguntas e regra de ao menos um anexo estão no código [C03] [C10]. Marcadores configuram preenchimento, não suficiência jurídica. |
| Modelo versionado com aprovação por atendimento | Existente | `ModeloAtendimento`, biblioteca e ação de aprovação [C04] [C17]. |
| Modelo profissional integral das imagens | Parcial | `BASE_REFERENCIA` preserva estrutura e coloca blocos em variáveis; `REFERENCIA.aprovado=False` [C18]. Ainda não é transcrição integral homologada. |
| Seleção segura de cláusulas condicionais | Parcial | Condicionais apenas para representação/observações e marcadores; bloqueio lexical de certos fatos fixos [C19]. Não há catálogo homologado de condições e fatos necessários. |
| Minuta preenchida e versões editadas | Existente | Preenchimento literal e novas versões [C19] [C20]. Qualidade profissional depende da configuração e do conteúdo confirmado. |
| Revisão final e exportação da versão atual | Existente | Hash do texto e bloqueios no endpoint [C21] [C22]. |
| Formatação profissional homologada | Parcial | DOCX/PDF A4, fonte e margens genéricas; não reproduzem automaticamente o layout das imagens [C23]. |
| Isolamento entre cartórios | Parcial quanto à garantia completa | Filtro e autorização no atendimento, objetos relacionados e chaves de cache por contexto [C01] [C02]. Falta auditoria abrangente das novas relações propostas e prova de integridade entre elas. |
| Permissão exclusiva para a escrevente confirmar/homologar | Ausente como autorização específica | `IsAuthenticated` e participação no cartório; `can_access_tenant` consulta vínculo, sem papel profissional nesse caminho [C01] [C24]. |
| Concorrência e repetição de requisições | Parcial | Transações, bloqueio do atendimento, versões esperadas, assinaturas e `client_id` [C04] [C14] [C19] [C20]. Concorrência real de múltiplas conexões em PostgreSQL não foi demonstrada; SQLite não oferece o mesmo bloqueio por linha [C25]. |
| Bloqueio de provedores externos | Existente no caminho local inspecionado; garantia global parcial | OCR e simulação são locais [C07] [C08] [C11]. Há rotas/integrações legadas fora desse percurso [C26]; não afirmar isolamento de rede de toda a aplicação sem auditar esse limite. |

### 3.1 Lacunas que orientam a execução

**L01 — Identidade e associação.** A unidade atual é a chave textual do campo, não a pessoa, o papel, a ocorrência documental ou o imóvel. Comparar nomes dentro de um bloco não permite concluir identidade nem associar procurador e representado [C03] [C06].

**L02 — Cadeia de evidências.** Uma revisão pela ficha pode apontar página, canal, versão e trecho literal; uma resposta à pergunta cria mensagem de resposta como sua origem. Nesse segundo caminho, a decisão guarda assinatura do conjunto de candidatos, mas não uma lista explícita das propostas documentais aceitas/rejeitadas. A origem original pode permanecer disponível no atendimento sem compor uma relação direta e completa até a minuta. A edição manual da minuta também não cria automaticamente essa relação [C14] [C16] [C20].

**L03 — Incerteza semântica.** `sem_dado` reconhece apenas algumas expressões; trecho existente e valor confirmado não provam interpretação. Linhas rotuladas podem conter dúvida, negação, previsão ou fato relativo a outra pessoa. O código não resolve isso semanticamente [C10] [C11].

**L04 — Revisão genérica de fonte.** A decisão sobre um arquivo ou mensagem pode fechar sua pendência por justificativa e confirmação. O servidor não exige que cada trecho não interpretado esteja ligado a dado resolvido ou descarte explícito. Falha técnica permanece nos avisos, mas falta granularidade para impedir uso de cada dado afetado [C10] [C14].

**L05 — Fatos em texto fixo.** `validar_fatos_fixos` é uma barreira lexical, com falsos positivos e paráfrases não detectadas. Não é contrato de cláusula nem comprovação de acontecimentos; não deve ser tratada como garantia suficiente [C19].

**L06 — Configuração profissional incompleta.** Cinco campos são exigidos por padrão, outros por marcadores e há bloqueio se não existir anexo. Essas são regras técnicas atuais, não requisitos documentais homologados. A estrutura da referência exige resposta de representação e vários blocos sem modelar aplicabilidade de cenário [C03] [C10] [C18].

**L07 — Autoridade profissional e concorrência.** Não há distinção específica entre membro do cartório e responsável habilitada a confirmar/homologar neste fluxo. Proteções de concorrência precisam ser provadas no banco de execução escolhido, inclusive corrida entre confirmar, reler, gerar e exportar [C01] [C24] [C25].

**L08 — Artefato profissional.** Uma minuta de textos fictícios colocados nos marcadores prova o encadeamento técnico, mas não comprova que documentos fictícios representativos produziram qualificações e cláusulas corretas. O formato exportado também precisa de comparação visual e aprovação [C18] [C23] [C27].

O conteúdo de anexos é `BinaryField` e mensagens/revisões são texto no banco deste atendimento [C06]. Não transferir para esse caminho a afirmação do README ou do modelo legado de que todos os dados já são tokens de cofre. Manter apenas dados fictícios nesta fase; requisitos de proteção e retenção para dados reais dependem de definição própria, fora da presente autorização de implementação.

## 4. Estrutura proposta — ainda não implementada

### 4.1 Objetos, relações e reaproveitamento

Todos os objetos abaixo precisam de identidade estável, `cartorio_id`, `atendimento_id` quando aplicável, autoria, datas e versão. Toda relação deve ser validada no servidor para pertencer ao mesmo cartório e atendimento; não basta filtrar a lista na interface. Alterações relevantes produzem versões/eventos, em vez de substituir silenciosamente o conteúdo anterior.

| Objeto proposto | Conteúdo e relações mínimos | Base existente e mudança necessária |
|---|---|---|
| Atendimento e cenário | Cartório, título, responsável; versão da configuração profissional e do modelo escolhidos; cobertura do caso confirmada. | Reaproveitar `Atendimento`; acrescentar referências explícitas sem transformar título em especificação jurídica [C06]. |
| Pessoa do atendimento | ID próprio; dados de identificação como afirmações com fontes; grafias alternativas preservadas. Sem união automática por nome/CPF aparente. | Avaliar `Parte` para reaproveitamento compatível; seu contrato de tokens não atende sozinho a afirmações locais e fontes. Não integrar serviços externos apenas para reutilizá-lo [C12]. |
| Participação/papel | Vínculo pessoa ↔ atendimento, papel explícito e confirmado; uma pessoa pode ter mais de um papel. Dados conjugais são vínculos próprios quando relevantes ao cenário. | Conceito de `ProcessoParte` pode orientar o vínculo; não reaproveitar IDs nem papéis como se `Processo` e `Atendimento` já fossem o mesmo objeto [C12]. |
| Representação | Representante, representado, papel exercido, instrumento-fonte, trechos pertinentes e decisão profissional de adequação. | Substituir associação implícita no bloco `representacao` por vínculos verificáveis. Não interpretar poderes como decisão automática. |
| Documento | Original, hash, tipo proposto/confirmado, referência, emissor/data quando informados; vínculos explícitos com zero ou mais pessoas, imóveis ou eventos. Indefinição de vínculo gera pendência. | Reaproveitar `AnexoAtendimento`; separar arquivo recebido de classificação e uso documental [C06]. |
| Leitura e evidência | Documento + página/unidade + versão da leitura + canal/método + trecho literal + localização quando disponível; ou mensagem + trecho/posição. Manter falha e texto original. | Reaproveitar páginas e regiões OCR; tornar referências de evidência imutáveis e reutilizáveis por propostas e decisões [C06] [C08] [C16]. |
| Imóvel | ID próprio; descrição literal, identificadores, localização, titularidade e aquisição como afirmações; vínculos com titulares e documentos. | Reaproveitar conteúdo dos campos sem misturar vários bens em uma string. Começar apenas com a quantidade homologada; detectar caso fora da cobertura. |
| Negociação | Vínculo ao imóvel e participantes; versões de preço, moeda e condições; parcelas com IDs, valor e vencimento quando explicitamente informados. | Preservar preço e pagamento já registrados como histórico. Soma de parcelas pode ser cálculo determinístico, exibindo entradas e resultado; não preencher parcela ou data ausente. |
| Evento de pagamento/consulta/declaração | Objeto e participante a que se refere; natureza do evento; informação planejada, declarada ou evidência recebida; fonte e confirmação específica. | Separar negociação futura de acontecimento. Receber comprovante não comprova por si só a interpretação nem autenticidade; consulta não realizada não tem resultado negativo presumido. |
| Proposta/afirmação | Caminho do atributo + alvo por ID; valor literal extraído/informado; eventual valor normalizado separado; origem; uma ou mais evidências; resultado de associação/interpretação. | Persistir candidatos hoje calculados/transitórios. Nunca preencher `pessoa_id` ou `imovel_id` por suposição [C10] [C11]. |
| Confirmação/decisão | Autora, data, motivo; propostas/evidências aceitas e rejeitadas; valor decidido; objeto alvo e versões examinadas. Correção é nova afirmação da escrevente, não alteração da extração original. | Evoluir revisões/decisões existentes. Confirmar um dado não confirma todos os campos de um documento [C06] [C14]. |
| Pendência | ID; tipo; alvo(s); evidências em conflito; leitura/versões envolvidas; pergunta; escopo do bloqueio; estado, responsável e decisão de resolução. | Reaproveitar cálculo da conferência e histórico de decisões; persistir identidade, dependências e resolução verificável [C10]. |
| Configuração e cláusula homologadas | Versão por cartório/cenário; requisitos condicionais; texto fixo; marcadores tipados; condições de inclusão; fatos que precisam de evidência; aprovação profissional. | Evoluir modelo/biblioteca sem herdar aprovação de uma escritura antiga. Modelo de redação fica separado dos documentos de prova [C17] [C18]. |
| Minuta/revisão/exportação | Texto imutável da versão; configuração/modelo; IDs das afirmações e decisões utilizadas; dependências e revisão final do texto. | Reaproveitar `MinutaAtendimento`, base editada, snapshot e revisão final. Associar trechos preenchidos às decisões/fontes, inclusive após edição [C19] [C20] [C21]. |

### 4.2 Estados que precisam permanecer separados

Evitar um único status tentando representar origem, certeza e autorização ao mesmo tempo:

| Dimensão | Estados propostos e regra |
|---|---|
| Origem | `extraida_documento` ou `informada_escrevente`; confirmação é registro separado, não troca da origem. |
| Associação | `nao_associada`, `proposta`, `confirmada`, `ambigua`. Apenas associação confirmada pode alimentar atributo de pessoa/imóvel no texto. |
| Interpretação | `nao_revisada`, `duvidosa`, `aceita`, `rejeitada`. Aceitação não atesta autenticidade do documento. |
| Leitura | `extraida`, `parcial`, `falhou`, `substituida`; erro e versão anterior permanecem no histórico. Revisão humana registra sua própria evidência/decisão sem alterar o resultado técnico passado. |
| Aplicabilidade | `a_decidir`, `aplicavel`, `nao_aplicavel`, com decisão da escrevente vinculada ao cenário e motivo. Campo vazio e “não se aplica” não são equivalentes. |
| Confirmação | `pendente`, `confirmada`, `reaberta`, `substituida`. Mudança em evidência dependente reabre o dado afetado. |
| Pendência | `aberta`, `resolvida`, `reaberta`, `substituida`, sempre com causa e decisão; não desaparecer por uma mensagem mais recente. |

### 4.3 Exemplo de rastreabilidade e bloqueio

Exemplo inteiramente fictício: o documento D1, unidade/página 1, leitura 2, contém literalmente “Comprador: PESSOA BETA FICTÍCIA”. A proposta P1 preserva esse valor e trecho; seu vínculo à pessoa B e ao papel comprador é proposto, não assumido. Uma mensagem M1 atribuindo outro papel abre pendência Q1 sobre a associação. Só a decisão R1 da escrevente, referenciando D1/leitura 2 e M1, define o registro aceito. A minuta V1 referencia R1 e suas evidências.

Se houver leitura 3 ou nova evidência relevante, Q1 pode reabrir e V1 fica desatualizada. O sistema não apaga a leitura 2, não decide identidade pela grafia e não usa o dado afetado em nova minuta. Uma frase literal extraída corretamente, mas atribuída à pessoa errada, deve reprovar o teste.

## 5. Próximas etapas e critérios verificáveis de conclusão

As etapas abaixo são propostas de execução. Nenhuma foi implementada por este diagnóstico. A conclusão deve ser registrada neste documento com arquivos alterados, testes executados, resultados e limites remanescentes. Não marcar uma etapa concluída apenas porque existe tela ou texto de exemplo.

### Etapa 2 — cenário e contrato do modelo a homologar

Dependência: decisões P01–P07 da seção 6. Reaproveitar referência recebida, campos e modelo atuais.

Critérios de conclusão:

1. Cenário coberto, quantidade de participantes/imóveis e tratamento de representação registrados em versão identificável, com aprovação da escrevente e exemplos fora da cobertura.
2. Modelo integral conferido, com cada trecho classificado como fixo, variável, condicional ou afirmação de acontecimento. Rasuras são variáveis sem valor recuperado; a página faltante já foi recebida.
3. Requisitos documentais e regras de aplicabilidade têm fonte profissional, condição explícita e estado de homologação; nenhum padrão técnico é apresentado como imposição jurídica.
4. Um conjunto fictício representativo tem resultados esperados aprovados antes da execução: pessoas/papéis, imóvel, fontes, dúvidas, cláusulas e minuta esperada. Não basta usar “TEXTO FICTÍCIO” em todos os blocos.
5. Caso sem homologação ou fora da cobertura permanece pendente; selecionar uma referência não registra aprovação automática.

Evidência exigida: configuração/modelo versionados e matriz de casos esperados aprovados. Lacunas tratadas: L05, L06 e L08.

### Etapa 3 — objetos e cadeia de evidências

Dependência: contrato de cenário da etapa 2. Reaproveitar atendimento, anexos, páginas, mensagens, revisões e decisões.

Critérios de conclusão:

1. Pessoas, papéis, relações de representação, documentos, imóvel e negociação possuem identidades e vínculos separados; nenhuma fusão ocorre sem decisão humana.
2. Propostas extraídas e informações da escrevente são persistidas sem sobrescrever texto literal. Normalização, quando usada, fica em atributo separado.
3. Cada confirmação referencia propostas/evidências e versões analisadas; a origem do arquivo não se perde quando a confirmação é enviada pela conversa.
4. Associação a objeto de outro atendimento/cartório é recusada no servidor em criação, leitura, alteração e reutilização de referência.
5. Histórico anterior é preservado. Registros textuais legados entram como conteúdo a revisar, sem associação automática a pessoas e imóveis.

Evidência exigida: testes com homônimos, mesma pessoa em dois papéis, procurador/representado distintos, dois documentos de pessoas diferentes e tentativa de vínculo cruzado. Lacunas: L01 e L02.

### Etapa 4 — documentos e propostas locais verificáveis

Dependência: objetos/evidências da etapa 3 e tipos documentais homologados na etapa 2. Continuar usando leitura/OCR e respostas simuladas locais.

Critérios de conclusão:

1. Cada proposta permite abrir arquivo, unidade/página, leitura, canal e trecho literal; mensagens fornecem ID e trecho correspondente. Página desconhecida permanece desconhecida, sem número inventado.
2. Arquivo ilegível, leitura parcial, página ausente, trecho ambíguo ou dúvida de associação produzem pendência no dado/objeto afetado. Falha não recebe resultado fictício de sucesso.
3. Propostas não confirmam pessoas, papéis, acontecimentos nem alteram minuta. Resposta simulada é identificada na tela, API e relatório de teste.
4. Teste com trecho correto e interpretação errada é rejeitado pelo resultado esperado, mesmo que a validação literal passe.
5. Interceptação de rede comprova ausência de envio a provedores externos no percurso e em seus fallbacks; falha local não aciona integração remota.

Evidência exigida: casos fictícios de PDF nativo, imagem, OCR discordante, releitura e falha técnica, com propostas e pendências esperadas. Lacunas: L02, L03 e L04. Interpretação automática real de documentos não será declarada implementada por passar nesta etapa simulada.

### Etapa 5 — conversa, confirmação e resolução de pendências

Dependência: etapas 3 e 4. Reaproveitar conversa, próximo passo e diálogos curtos; sem nova área principal.

Critérios de conclusão:

1. Pergunta identifica assunto e objeto, mostra fontes e permite manter pendente. Resposta sem confirmação continua informada e bloqueada quando necessária ao cenário.
2. Divergência exige decisão explícita e justificada sobre evidências aceitas/rejeitadas. “Revisei o arquivo” não fecha automaticamente dúvidas individuais.
3. Somente a permissão profissional definida em P09 pode confirmar ou resolver; outra usuária autenticada do cartório recebe recusa para essas ações.
4. Mensagem posterior não esconde dúvida anterior. Nova evidência relevante reabre decisões dependentes, preserva histórico e invalida a minuta afetada.
5. Identificador repetido com mesmo conteúdo não duplica resposta; identificador reaproveitado com conteúdo diferente é recusado. Duas decisões concorrentes sobre a mesma versão não sobrescrevem uma à outra.

Evidência exigida: roteiro completo de diálogo e testes de estados, permissões, idempotência e dependências. Lacunas: L03, L04 e L07.

### Etapa 6 — preenchimento seguro do modelo profissional

Dependência: modelo homologado da etapa 2 e dados/decisões das etapas 3–5. Reaproveitar versões, snapshot e preenchimento literal.

Critérios de conclusão:

1. Minuta usa exatamente a versão de modelo/configuração aprovada e as afirmações confirmadas, associadas aos objetos corretos, sem pendência ativa nas dependências.
2. Cada cláusula condicional tem condição e dados identificáveis. Falta de decisão de aplicabilidade bloqueia; o sistema não escolhe a variante pelo exemplo.
3. Pagamento combinado, pagamento declarado como realizado, evidência de comprovante, quitação, consulta e assinatura permanecem distintos. Não surgem acontecimentos por estarem no texto do modelo.
4. Dado ausente, leitura substituída, ambiguidade e marcador pendente impedem preparação. Nenhuma referência normativa ou cláusula é completada por conhecimento presumido do sistema.
5. Cada trecho preenchido permite consultar afirmação, decisão e fontes. Edição manual conserva versão anterior e exige identificar alterações factuais ou mantê-las pendentes até revisão específica.
6. Comparação com a minuta esperada homologada passa quanto a conteúdo e associação, sem misturar pessoas, documentos ou imóvel. Aprovação de um cenário não libera outro.

Evidência exigida: comparação literal/estruturada com resultado esperado e casos negativos de fatos do modelo, cláusula indevida, associação trocada e fonte nova. Lacunas: L01, L02, L05, L06 e L08.

### Etapa 7 — revisão, exportação e verificação integral local

Dependência: etapa 6; permissões e banco de execução definidos em P09–P10. Reaproveitar revisão final, DOCX/PDF e testes existentes.

Critérios de conclusão:

1. Roteiro da escrevente percorre abertura → anexos → leitura → complementos → dúvidas → decisões → modelo → minuta → revisão final → Word/PDF, mantendo as três abas principais.
2. Arquivos exportados contêm o corpo da versão salva correta, com todos os blocos, caracteres e páginas esperados. Acréscimos de identificação de minuta/metadados são previstos no padrão de saída aprovado.
3. Inspeção visual de Word e PDF pela escrevente aprova legibilidade e formatação; não copiar selo, manifesto, assinatura ou código de validação do documento antigo.
4. Versão sem revisão final, desatualizada ou com bloqueio não é exportada. Alteração concorrente durante preparação/revisão/exportação não produz arquivo válido ligado a estado incompatível.
5. Testes reais de múltiplas conexões no banco escolhido demonstram comportamento de corrida e recuperação, sem perda silenciosa; testes sequenciais de versão não substituem essa prova.
6. Tentativas entre cartórios/atendimentos são recusadas em todas as relações do percurso. Verificação de rede mantém o limite sem provedor externo; nenhuma chave aparece em interface, relatório ou log de teste.
7. Relatório distingue testes simulados, falhas, itens não testados e homologação profissional. Os erros de compilação/checagem que afetem a entrega do fluxo estão resolvidos ou explicitamente bloqueiam sua liberação.

Evidência exigida: execução dos casos T01–T16 abaixo, artefatos fictícios revisados, evidência visual e resultados de isolamento/concorrência. Lacunas: L07 e L08, além da regressão das anteriores.

### 5.1 Casos de aceitação a preservar

Estes casos são especificação das próximas etapas; não foram executados neste diagnóstico.

| ID | Entrada/situação fictícia | Resultado verificável esperado |
|---|---|---|
| T01 | Caso completo dentro do cenário homologado | Minuta e exportação correspondem ao resultado aprovado e às fontes corretas. |
| T02 | Duas pessoas com nomes semelhantes e papéis diferentes | Nenhuma fusão ou troca de qualificações; dúvida de identidade bloqueia a associação. |
| T03 | Procurador e representado em documentos diferentes | Relações explícitas, instrumento e decisão profissional preservados; papéis não trocados. |
| T04 | Documento sem identificação suficiente de pessoa/imóvel | Proposta sem associação, pendência visível e dado bloqueado. |
| T05 | Página ilegível/ausente ou PDF protegido | Falha preservada; pedido de conferência/cópia, sem valor presumido. |
| T06 | Texto nativo e OCR discordam | Ambos os canais visíveis, sem seleção automática; decisão humana específica. |
| T07 | Trecho literal correto usado para pessoa/papel/fato errado | Caso reprovado; literalidade não basta para aceitar o dado. |
| T08 | “Pagamento previsto” e depois comprovante apresentado | Previsão não vira pagamento concluído; evidência e declaração humana são registros distintos. |
| T09 | Duas fontes com preços diferentes ou soma de parcelas divergente | Pendência com valores, fontes e cálculo rastreável quando aplicável; nenhuma escolha automática. |
| T10 | Resposta informada sem confirmação e nova mensagem genérica | A pendência anterior permanece até decisão explícita. |
| T11 | Nova leitura/fonte depois da confirmação e minuta | Decisões afetadas reabertas; versão antiga preservada e exportação atual bloqueada. |
| T12 | Modelo antigo contém quitação, consulta negativa ou assinatura | Acontecimento não migra ao caso novo sem dados e decisão específicos. |
| T13 | Caso fora do cenário, cláusula sem condição decidida ou configuração não homologada | Pendência profissional e bloqueio; sem adaptação automática de texto. |
| T14 | Usuária sem vínculo, vínculo de fonte cruzado ou usuária sem permissão de confirmar | Recusa no servidor, sem leitura indevida ou alteração. |
| T15 | Duas confirmações/leituras/gerações concorrentes e tentativa de exportar estado antigo | Uma versão consistente; requisição obsoleta recusada, sem sobrescrita ou exportação incompatível. |
| T16 | Repetição de envio e exportação Word/PDF após edição | Sem duplicação; nova edição exige revisão própria; conteúdo e aparência conferidos. |

## 6. Decisões profissionais da escrevente

O recebimento das imagens e o esclarecimento de que as tarjas ocultam dados do exemplo estão registrados. A imagem complementar resolveu a lacuna entre o item 6 e o encerramento. Isso autoriza o trabalho de adaptação solicitado, mas não é evidência de homologação integral da configuração profissional no produto.

| ID | Decisão necessária | Registro esperado e efeito no fluxo | Estado identificado |
|---|---|---|---|
| P01 | Qual cenário inicial cobrir: participantes, quantidade de imóveis, representação e variantes de negociação? | Delimitação e exemplos fora da cobertura; define quando interromper e encaminhar à revisão. | Referência tem procuração; cobertura geral não homologada. |
| P02 | Quais documentos são usados em cada condição e como avaliar suficiência/atualidade? | Tipo, condição, dados a conferir e critério aprovado, com versão e autoria profissional. | Lista do exemplo não estabelece exigência geral. |
| P03 | Que informação pode vir por mensagem e quem é seu declarante? | Atributos, autoria, fonte e necessidade de confirmação/documento no cenário. | Perguntas gerais existem; política por atributo pendente. |
| P04 | Qual é a redação integral aprovada, incluindo correções da adaptação? | Texto e versão homologados; classificação de cada cláusula e marcador. | Estrutura parametrizada disponível; transcrição integral não homologada. |
| P05 | Quais condições autorizam cada cláusula e quais acontecimentos precisam de declaração específica? | Condições explícitas, evidências e decisões, sem defaults de pagamento/consulta/assinatura. | Condicionais profissionais ainda não configuradas. |
| P06 | Como tratar divergências de identidade, estado civil, titularidade, descrição e representação? | Critérios de encaminhamento e decisão da escrevente; software apresenta fontes sem decidir adequação jurídica. | Não deduzir do exemplo. |
| P07 | Como distinguir condições, pagamento declarado, comprovante, quitação e pendências de negociação? | Vocabulário, estados e texto aprovado para cada situação, incluindo ausência/não aplicabilidade. | Há campos textuais separados, sem contrato profissional completo. |
| P08 | Qual conteúdo e aparência tornam a minuta útil em Word/PDF? | Modelo de saída aprovado, metadados permitidos, fonte/margens/quebras e critérios visuais. | Exportação genérica implementada; homologação visual pendente. |
| P09 | Quem pode informar, confirmar, resolver divergências e homologar modelos no cartório? | Permissões profissionais explícitas e responsável pela aprovação; nenhuma inferência só por vínculo ao cartório. | Controle específico não identificado no atendimento. |
| P10 | Quem aprova o teste fictício e qual ambiente local sustentará o teste concorrente? | Casos esperados, responsável pelo aceite e banco/ambiente documentados com apoio técnico. | Resultados técnicos históricos existem; aceite profissional integral não demonstrado. |

Nenhum prazo de certidão, exigência tributária, consulta obrigatória, adequação de procuração ou cláusula legal foi definido por este diagnóstico. Referências normativas visíveis na escritura são conteúdo do exemplo até revisão profissional de vigência e aplicabilidade. Decisões pendentes devem constar na configuração, não ser completadas por conveniência técnica.

## 7. Evidências existentes e conclusão da Etapa 1

### 7.1 O que os testes existentes ajudam a comprovar

- Atendimento, fontes, versões, bloqueios e exportação têm testes em `test_atendimentos` [C28].
- Estrutura da referência, ativação de campos, propostas com origem, divergência e percurso com arquivo fictício têm testes em `test_modelo_referencia` [C27].
- Simulação sem provedor, ausência de confirmação automática e escopo da mensagem têm testes em `test_interpretacao_ia` [C29].
- Texto livre pendente, fonte manual e barreira lexical são cobertos em `test_fluxo_principal_local` [C30].
- OCR, canais e releitura têm testes, alguns dependentes do OCR nativo disponível; revisão final e invalidação de exportação têm suíte própria [C31].

Os registros da rodada anterior informam 90 testes de regressão aprovados e, após inclusão de um caso, seis testes específicos do modelo aprovados. Esses conjuntos se sobrepõem; não representam 96 testes distintos. ESLint passou nos arquivos alterados naquela rodada; a checagem TypeScript geral apontava problemas em outras partes do projeto. **Não houve nova execução nesta etapa documental**, nem prova de concorrência em PostgreSQL, validação semântica real, homologação profissional ou nova inspeção visual. Existência de teste no repositório não equivale a teste recém-executado.

### 7.2 Critério de término desta etapa

Etapa 1 concluída documentalmente quando este arquivo contiver: fluxo completo, classificação com referências, estrutura proposta, critérios por etapa e decisões da escrevente; todas as referências locais verificadas; nenhuma nova funcionalidade implementada. A etapa seguinte deve começar pelo contrato profissional e pelos casos esperados, reaproveitando os mecanismos existentes.

| Etapa | Estado na emissão deste documento | Evidência |
|---|---|---|
| 1 — diagnóstico | Documento produzido; referências verificadas na entrega | Este arquivo, versão 1.0. |
| 2 — cenário/modelo | Planejada; depende de decisões profissionais | P01–P07 e critérios da seção 5. |
| 3 — objetos/evidências | Planejada; há componentes reaproveitáveis | L01–L02. |
| 4 — propostas locais | Planejada; leitura e simulação já existentes | L02–L04. |
| 5 — conversa/pendências | Planejada; conversa e conferência já existentes | L03–L04 e L07. |
| 6 — preenchimento profissional | Planejada; preenchimento literal já existente | L01–L02 e L05–L08. |
| 7 — verificação integral/exportação | Planejada; exportadores e revisão já existentes | L07–L08. |

## 8. Referências ao código

As referências abaixo são atalhos para arquivos locais e linhas verificadas, seguidas dos símbolos que fundamentam o diagnóstico.

- [C01] — AtendimentoViewSet: autenticação, cartório, listagem e criação.

- [C02] — AtendimentoPage: contexto, conversa e três abas.

- [C03] — CAMPOS, campos_exigidos, campos_ativos e PERGUNTAS.

- [C04] — modelo_minuta: referência disponível, aprovação e versão esperada.

- [C05] — anexos: validação, limites, deduplicação e leitura.

- [C06] — Modelos de atendimento, fontes, revisões, decisões e minutas.

- [C07] — extrair_pdf, ler_pdf e ler_imagem: leitura e falhas.

- [C08] — reconhecer e executar_ocr: OCR Windows e regiões.

- [C09] — reler_anexo: versão de leitura e preservação de páginas.

- [C10] — extrair_rotulos, orientar_conversa, conferir e sem_dado.

- [C11] — analisar_mensagem: simulação local por rótulos.

- [C12] — ProcessoParte: vínculo legado com Processo e Parte.

- [C13] — mensagens: persistência e idempotência.

- [C14] — responder: assinatura, versão, confirmação e decisão.

- [C15] — PerguntasConferencia: próximo passo, fontes e resposta curta.

- [C16] — RevisaoDadoSerializer e AtualizarDadoSerializer: origem e limites.

- [C17] — ModeloReutilizavel e ModeloAtendimento: aprovação e versões.

- [C18] — BASE_REFERENCIA e REFERENCIA: adaptação e fontes visuais.

- [C19] — validar_fatos_fixos, validar_modelo, snapshot e preparar.

- [C20] — editar_minuta e comparar_minutas: texto e versões históricas.

- [C21] — revisar_minuta: revisão final vinculada ao texto.

- [C22] — exportar_minuta: estado atual, revisão e geração.

- [C23] — word e pdf: conteúdo, identificação de minuta e layout.

- [C24] — UserProfile.can_access_tenant: vínculo de acesso.

- [C25] — Seleção de PostgreSQL ou fallback SQLite, sem leitura do arquivo de credenciais.

- [C26] — Rotas legadas de IA/workflows fora do percurso de atendimento.

- [C27] — Testes da referência e do arquivo fictício.

- [C28] — Testes de atendimento, fonte, bloqueios, versões e exportação.

- [C29] — Testes de simulação sem provedor e escopo.

- [C30] — Testes de texto livre, fonte manual e fatos fixos.

- [C31] — Testes de OCR, canais e releitura.

Referências complementares dos mesmos mecanismos:

- [Parte legado](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/partes/models.py:8>).
- [Origem e validação ao salvar ficha](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:547>).
- [Origem individual da proposta simulada](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:593>).
- [Biblioteca por cartório e publicação de modelos](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:185>).
- [Hash e registro da revisão final](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/revisao_final.py:4>).
- [Testes da revisão final](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_revisao_final.py:6>).

[C01]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:36>
[C02]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-web/src/app/atendimentos/[id]/page.tsx:21>
[C03]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/ficha.py:4>
[C04]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:222>
[C05]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:445>
[C06]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/models.py:7>
[C07]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/leitura_anexos.py:17>
[C08]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/ocr_local.py:37>
[C09]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:521>
[C10]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/conferencia.py:34>
[C11]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/interpretacao_ia.py:26>
[C12]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/models.py:292>
[C13]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:613>
[C14]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:392>
[C15]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-web/src/components/atendimentos/PerguntasConferencia.tsx:8>
[C16]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/serializers.py:69>
[C17]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/models.py:183>
[C18]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/modelo_referencia.py:3>
[C19]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/redacao.py:14>
[C20]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:289>
[C21]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:330>
[C22]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/views.py:357>
[C23]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/exportacao.py:13>
[C24]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/profiles/models.py:41>
[C25]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/config/settings.py:112>
[C26]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/config/urls.py:42>
[C27]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_modelo_referencia.py:9>
[C28]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_atendimentos.py:33>
[C29]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_interpretacao_ia.py:8>
[C30]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_fluxo_principal_local.py:6>
[C31]: <C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_ocr_atendimentos.py:36>


## 9. Execução — Etapa 2: ficha estruturada de compra e venda

### 9.1 Resultado implementado

Ficha detalhada acessível na aba **Conversa**, pelo botão **Ficha detalhada: pessoas e negócio**. Mantidas as três áreas principais. As seções 1–8 continuam como diagnóstico histórico anterior a esta implementação; as ausências descritas ali devem ser confrontadas com este registro de execução.

- Pessoa com UUID próprio, sem deduplicação por nome ou CPF. Campos separados de nome, CPF, tipo/número do documento e órgão emissor; grupos curtos de identificação, qualificação e contato. Nacionalidade, profissão, estado civil informado, nascimento, naturalidade, filiação, regime informado e endereço são campos técnicos disponíveis, sem obrigatoriedade jurídica presumida.
- Papéis no negócio são registros próprios vinculados explicitamente à pessoa. Uma pessoa pode ter mais de um papel. Cônjuge e representante são relações direcionadas entre duas pessoas distintas, independentes dos papéis. Nome e estado civil não criam relações.
- Imóvel separado, com descrição, matrícula/referência, registro, localização e histórico informado. Cada negociação é vinculada explicitamente ao imóvel e separa preço, moeda, condições combinadas, situação do pagamento, declaração, comprovante e quitação. Nenhum desses campos preenche outro automaticamente.
- Campos adicionais de qualificação podem ser configurados na versão do modelo, em **Minuta → Revisar modelo → Campos adicionais de qualificação das pessoas**. Salvar cria nova versão, sem herdar aprovação; biblioteca preserva a lista. Campo retirado do modelo continua disponível no histórico dos registros que já o utilizaram.
- Vínculos de um registro são imutáveis para manter a história da associação escolhida. Correção de vínculo é explícita: registrar desativação do registro incorreto e criar a associação correta. Não há exclusão destrutiva de histórico.

### 9.2 Histórico e fontes

Reaproveitada `RevisaoDadoAtendimento`, acrescentando alvo estruturado, valor original, rótulo do campo no momento do registro e eventual revisão legada de origem. Cada pessoa/objeto tem sua própria sequência por campo. A restrição de unicidade antiga continua para revisões sem objeto; revisões estruturadas têm unicidade por objeto/campo/versão.

Valores originais são preservados sem normalização silenciosa. Correção é nova revisão, com valor revisado, situação, autora, data e justificativa. Confirmação exige ações explícitas sobre o dado e a conferência de sua fonte; validação técnica não confirma o dado.

Fontes admitidas por dado:

1. Informação expressa da escrevente, salva também como mensagem de origem, sem confirmação automática.
2. Mensagem do mesmo atendimento, com trecho literal.
3. Página do anexo, com versão de leitura, canal texto/OCR e trecho literal; o valor original deve estar no trecho. Correção humana pode divergir no valor revisado, sem reescrever o original.
4. Revisão ampla antiga, selecionada explicitamente com trecho; a revisão original e sua origem anterior continuam acessíveis.

Leitura substituída conserva a confirmação histórica, mas a consulta retorna fonte desatualizada, confirmação não atual e situação efetiva reaberta. Nova gravação a partir dessa leitura é recusada. Fonte de outro atendimento/cartório e trecho inexistente são recusados.

CPF recebe somente aviso matemático/de formato, preservando a entrada. A resposta explicita `identidade_comprovada=false`, inclusive quando os dígitos são consistentes. Nenhuma consulta externa de CPF foi acrescentada.

### 9.3 Migração do conteúdo antigo

Migrações `0014` e `0015`: criam estrutura e restrições; preservam valor original de cada revisão antiga e acrescentam um marcador de conteúdo legado por atendimento que já possuía revisões. A `0016` preserva também o motivo de criação dos novos objetos; registros anteriores sem esse motivo continuam identificados como tal, sem preenchimento inventado. IDs, autores, datas, situações antigas, fontes e números de versão permanecem. Nenhuma pessoa, relação, imóvel ou negociação é criada a partir da interpretação do texto antigo. Nenhuma confirmação antiga se transforma em confirmação de nova pessoa.

A ficha apresenta **Conteúdo antigo para revisão**, com todas as versões. Os blocos amplos continuam consultáveis e editáveis no acesso secundário **Conteúdo antigo e blocos de redação**. Qualquer aproveitamento em um registro detalhado exige escolha expressa do objeto, campo, revisão e trecho, seguida de revisão humana. Backup de segurança local do banco foi preservado antes da aplicação das migrações no servidor local.

### 9.4 Concorrência, isolamento e limite da redação

A nova API `GET/POST /api/v1/atendimentos/{id}/ficha-detalhada/` reutiliza autorização de cartório e atendimento. Todas as referências de pessoa, imóvel, fonte e revisão de origem são validadas no servidor. Tipos incompatíveis de vínculo são recusados. O modelo usado no formulário deve continuar sendo a versão atual ao salvar.

Gravação em lote é atômica; campo obsoleto cancela todo o lote, inclusive mensagens de origem. Eventos com `client_id` e hash permitem repetir a mesma operação sem duplicar registros/revisões. Conteúdo ou autora diferentes com o mesmo identificador são recusados.

No SQLite, a transação reserva o escritor antes de ler as versões. Sobreposição de escritores recebe conflito sem alteração parcial; nova tentativa revalida a versão. Em outros bancos, mantém bloqueio da linha do atendimento. O teste de concorrência desta entrega foi realizado com duas conexões SQLite sobrepostas; não constitui teste de concorrência PostgreSQL.

Objetos, revisões e eventos estruturados entram na assinatura do estado da minuta. Sem registros detalhados, o contrato de assinatura antigo é preservado, inclusive após a migração do marcador de legado; a migração sozinha não desatualiza minutas antigas sem alteração de dados. Os leitores antigos de campos amplos filtram revisões sem objeto, impedindo agregar nomes de pessoas ao texto de vendedores/compradores por coincidência de chave. **A montagem dos registros detalhados no modelo pertence à etapa de redação e não foi implementada aqui. Enquanto houver registros detalhados, a geração/exportação pelo fluxo antigo fica bloqueada com explicação explícita.** Criar uma ficha estruturada não autoriza ignorá-la e exportar só os blocos antigos. Uma resposta genérica na conversa não remove esse bloqueio.

### 9.5 Como testar na interface

1. Abra um atendimento TESTE no cartório fictício e entre em **Conversa → Ficha detalhada: pessoas e negócio**.
2. Crie duas pessoas e informe nomes, inclusive iguais se quiser testar homônimos. Confira IDs distintos e campos agrupados. Salve primeiro como informado; abra origem/histórico e depois faça uma confirmação humana explícita em nova versão.
3. Em **Papéis no negócio**, escolha explicitamente a pessoa e registre o papel. Acrescente outro papel à mesma pessoa. Em **Relações entre pessoas**, escolha as duas pessoas e informe cônjuge ou representante; confira a direção. A ficha não deduz o vínculo.
4. Crie um imóvel. Em **Preço e pagamento**, selecione o imóvel, registre preço e condições futuras e observe que comprovante/quitação continuam vazios. Nenhum valor de situação de pagamento é escolhido automaticamente.
5. Em um campo, escolha mensagem, página do documento fictício ou conteúdo antigo como fonte. Copie o trecho literal e mantenha o original separado do valor corrigido. Teste trecho inexistente e leitura substituída: o salvamento deve ser recusado.
6. Em **Minuta → Revisar modelo**, acrescente campo de qualificação particular e salve uma versão. Confira o campo na pessoa; depois retire-o em outra versão e verifique que o histórico anterior permanece.
7. Abra a mesma pessoa/campo em duas janelas. Salve em uma e tente salvar a versão antiga na outra: deve haver conflito, sem sobrescrita. Repetir uma requisição com mesmo identificador não deve duplicar.
8. Consulte o conteúdo antigo e confira que textos ambíguos permanecem inteiros, sem pessoas repartidas ou relações criadas automaticamente. A minuta antiga deve ficar desatualizada/bloqueada ao introduzir dados detalhados.

### 9.6 Verificação e limitações

- 107 testes passaram na regressão, incluindo 16 da ficha estruturada. Cobertura nova: várias pessoas, homônimos, papéis múltiplos, relações explícitas, imóvel/negociação/pagamento separados, fontes documentais/mensagens/legado, confirmação, CPF, histórico, modelo configurado, gravação atômica, repetição, versão obsoleta, isolamento, migração e dois escritores SQLite sobrepostos.
- Após o ajuste final da orientação para não tratar mensagens geradas pela ficha como texto livre não interpretado, os 51 testes de ficha, atendimento e conversa foram reexecutados e passaram. Estes testes se sobrepõem à regressão anterior, não são 51 casos adicionais.
- Migrações sem alterações de esquema pendentes na checagem. Teste de migração preserva conteúdo ambíguo, ID, versão, situação, autora/data e vínculo de fonte, sem criar pessoas.
- Interface local verificada em atendimento exclusivamente fictício: criação de pessoa, grupos curtos, registro informado sem confirmação automática, reabertura após recarga e histórico com original, revisado, mensagem e autoria. Um aviso de estrutura HTML introduzido no componente foi corrigido durante essa verificação.
- A checagem TypeScript geral ainda encontra erros fora dos arquivos alterados; a interface geral também apresenta um aviso de hidratação em `ProtectedRoute` na recarga. Não foi tratado como funcionalidade desta etapa. Não há alegação de compilação global limpa.
- Não há interpretação semântica de documentos, dedução de pessoas/relações, prova de identidade, integração externa, homologação jurídica, cálculo de parcelas ou composição automática da minuta a partir dos novos objetos. Campos disponíveis/opções são vocabulário técnico de registro, não regras profissionais homologadas.
- Permissão profissional distinta do vínculo ao cartório e validação de concorrência PostgreSQL continuam pendentes das etapas próprias. Esta entrega garante a autoria autenticada usada pelo fluxo existente, não inventa uma habilitação profissional.

Arquivos principais da execução:

- [Modelos e revisões reutilizadas](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/models.py>).
- [Serviço da ficha, fontes e transações](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/ficha_estruturada.py>).
- [Campos e configuração de qualificação](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/ficha_estruturada_schema.py>).
- [Migração estrutural](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/migrations/0014_eventofichaatendimento_objetofichaatendimento_and_more.py>).
- [Preservação do legado](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/migrations/0015_preservar_ficha_legada.py>).
- [Formulários da ficha](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-web/src/components/atendimentos/FichaDetalhada.tsx>).
- [Campos adicionais do modelo](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-web/src/components/atendimentos/CamposQualificacaoModelo.tsx>).
- [Testes da ficha, concorrência e migração](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_ficha_estruturada.py>).


## 10. Execução — Etapa 3: propostas e cadeia de evidências

### 10.1 O que foi implementado

Esta entrega complementa os objetos da ficha e a cadeia de evidências da Etapa 3 proposta no diagnóstico, com parte da infraestrutura local prevista para a Etapa 4. Não homologa cenários, requisitos documentais ou cláusulas, não interpreta documentos semanticamente e não libera a composição da minuta.

Foram adicionadas propostas persistentes e decisões humanas versionadas. Cada proposta preserva valor original, trecho literal, rótulo, arquivo/página/leitura/canal/linha ou mensagem de origem, método local e destinos de campo sugeridos pelo rótulo. A identificação do arquivo/mensagem é estável; os destinos não identificam uma pessoa ou imóvel. Nenhuma pessoa, papel ou relação é criada, deduplicada ou escolhida pela extração.

A extração usa exclusivamente rótulos disponíveis na ficha/modelo, como Nome, CPF, RG, Preço e Condições de pagamento. A expressão ampla “Vendedores: pessoa A e pessoa B” não é repartida em nomes. Linhas livres são contadas como não interpretadas e permanecem acessíveis no contexto original. Preserva-se o texto capturado após os dois-pontos, inclusive espaços; eventual correção é feita no valor revisado, sem modificar o original.

Um mesmo arquivo ou mensagem pode ser processado novamente sem duplicar a mesma proposta da mesma linha, canal e leitura. Cada pedido aceita até 200 propostas; ultrapassar o limite ou o tamanho de trecho cancela toda a operação, sem resultado parcial apresentado como sucesso. Avisos técnicos de leitura/OCR continuam visíveis. Não há SDK de provedor, fallback externo ou cobrança de IA nesse percurso.

### 10.2 Decisão, associação e histórico

A escrevente seleciona a proposta e escolhe explicitamente o registro e o campo na ficha detalhada. São exigidos vínculo de fonte exato e confirmação expressa de que a proposta pertence àquele registro/campo. Rótulo incompatível com o tipo de registro é recusado. Compatibilidade de rótulo não comprova identidade da pessoa: homônimos e interpretação do contexto continuam dependendo da escrevente.

- Salvar o dado como informado gera decisão **associada, sem confirmação** e mantém a proposta pendente.
- Confirmar fonte, associação e dado gera decisão **aceita**, vinculada à revisão exata, ao objeto, à autora, à data e ao motivo. A revisão mantém sua página/mensagem original; a confirmação não a substitui por uma mensagem sem referência ao arquivo.
- **Não usar esta proposta** exige motivo e gera decisão de rejeição, sem apagar a proposta nem o histórico. Se uma decisão aceita ainda sustenta o dado atual, é necessário revisar esse dado antes de rejeitar a fonte. Reconsideração humana posterior é nova decisão, não exclusão da anterior.
- Uma proposta já associada a um registro não pode ser transferida silenciosamente a outra pessoa. A revisão anterior precisa ser tratada antes de reutilizar a fonte em outra associação.
- Cada decisão exige a versão que estava aberta no formulário. Versão desatualizada ou leitura substituída recebe conflito. Repetição com mesmo identificador não duplica decisões/revisões; lote de campos continua atômico.
- Nova leitura preserva a proposta e a aceitação histórica, mas reabre sua situação efetiva e impede nova aceitação daquela leitura antiga. Extração da leitura nova cria proposta própria. Revisão posterior do campo pode substituir o uso da proposta antiga, preservando a cadeia histórica.

O histórico da ficha informa os IDs das propostas que sustentam cada revisão e permite abrir sua fonte. O painel **Propostas com fonte** mostra decisões, objetos e revisões vinculados. O botão **Abrir fonte e contexto** consulta sob demanda o texto completo preservado da página/canal ou da mensagem; não mostra só o trecho como se ele bastasse para interpretar o dado. Leituras históricas são identificadas, sem página ou conteúdo inventados.

### 10.3 Interface e contrato local

Mantidas **Conversa, Documentos e Minuta**:

1. Em **Documentos**, cada arquivo possui **Guardar propostas locais para revisão**, utilizando a versão de leitura exibida. A resposta distingue propostas, linhas não interpretadas e problemas de leitura.
2. Nas opções da mensagem, **Propostas locais da mensagem → Guardar propostas para revisão** preserva as propostas e mantém o aviso de que não é IA real.
3. Em **Conversa → Ficha detalhada → Propostas com fonte**, a escrevente abre o contexto, seleciona uma proposta, escolhe o registro/campo e registra sua decisão. Seleção de proposta sozinha não escolhe uma pessoa.
4. Original e trecho da proposta ficam preservados; somente o valor revisado pode ser corrigido. Para opções controladas, a escrevente escolhe explicitamente a alternativa aplicável, sem normalização semântica automática.
5. **Decisões e histórico** mostra quem aceitou/associou/rejeitou e por quê. **Não usar esta proposta** mantém a evidência e registra o descarte, sem aprovar automaticamente o restante do arquivo.

API reutilizando autorização e isolamento do atendimento:

- `GET/POST /api/v1/atendimentos/{id}/propostas-dados/`: consulta, extração local e rejeição versionada.
- `GET /api/v1/atendimentos/{id}/propostas-dados/{proposta}/fonte/`: contexto da fonte exata, inclusive leitura histórica.
- `POST /api/v1/atendimentos/{id}/ficha-detalhada/`: gravação da revisão com proposta, versão da decisão e conferência explícita da associação.

A migração `0017` adiciona tabelas de propostas e decisões, sem transformar conteúdo antigo em dados confirmados. O backup local anterior foi verificado e a migração foi aplicada no servidor local. Propostas e decisões passam a integrar a assinatura da minuta quando presentes. Propostas pendentes, apenas associadas ou reabertas acrescentam bloqueio na conferência, que não pode ser removido por uma resposta genérica do fluxo antigo.

### 10.4 Verificações e limites

A regressão passou com **119 testes**, incluindo **12 testes de propostas**. Após a consulta adicional de contexto, os 12 testes específicos foram reexecutados e passaram. Foram verificados: literalidade e preservação de espaços; mensagem e página/leitura/canal; ausência de provedor; ausência de associação/confirmação automática; duas fontes com nomes iguais sem fusão; atributo incompatível; associação explícita; cadeia até a revisão; rejeição/reconsideração com histórico; decisão antiga recusada; leitura substituída; canais nativo/OCR separados; isolamento de arquivo/proposta/contexto/decisão; repetição sem duplicação e rollback integral ao exceder o limite.

Na interface local, um atendimento exclusivamente fictício foi usado para enviar mensagem rotulada, guardar a proposta, escolher explicitamente a pessoa e o campo, confirmar associação/fonte/dado e consultar a decisão ligada à revisão. Nenhum dado real foi utilizado nesse teste. ESLint passou nos arquivos alterados; a checagem TypeScript geral continua falhando em outras partes do projeto, sem erros reportados nesses arquivos durante a verificação.

Limites que permanecem:

- A leitura é por rótulos e a associação depende da escrevente. Trecho literal, CPF consistente e clique de confirmação não comprovam autenticidade nem garantem decisão profissional correta.
- Não há classificação documental completa, cobertura de texto livre, exigência jurídica deduzida, interpretação de procuração ou homologação semântica de um cenário profissional. Documentos ilegíveis e trechos não interpretados continuam exigindo revisão do original.
- O mecanismo completo de pendências por dado/objeto e dependências semânticas pertence à etapa seguinte; existem bloqueios conservadores globais e situações efetivas para proposta/leitura. Uma revisão de arquivo não confirma todos os seus dados.
- Cada revisão desta entrega parte de uma fonte primária; várias fontes e decisões permanecem no histórico. Não há composição automática de múltiplas evidências corroborantes em uma única revisão nem montagem da minuta a partir desses objetos.
- A redação estruturada permanece bloqueada conforme a Etapa 2. A próxima entrega técnica deve completar pendências e diálogo por dado/objeto antes de liberar qualquer preenchimento profissional.
- A autorização profissional distinta de vínculo ao cartório e testes reais em PostgreSQL continuam pendentes das etapas próprias. As transações desta entrega reutilizam o bloqueio/versionamento já testado no SQLite.

Arquivos principais:

- [Propostas e decisões persistentes](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/models.py>).
- [Extração local, contexto lógico e decisões](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/propostas_dados.py>).
- [Associação às revisões existentes](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/ficha_estruturada.py>).
- [Migração 0017](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/apps/processos/migrations/0017_propostadadoatendimento_decisaopropostaatendimento_and_more.py>).
- [Painel de propostas e decisões](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-web/src/components/atendimentos/FichaDetalhada.tsx>).
- [Propostas de documentos](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-web/src/components/atendimentos/AnexosConversa.tsx>).
- [Propostas de mensagens](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-web/src/components/atendimentos/InterpretacaoMensagem.tsx>).
- [Testes da cadeia de evidências](<C:/Users/Erick Grotz/Documents/Codex/2026-10-23/bai/outputs/notarius/apps/notarius-api/tests/test_propostas_dados.py>).

## 11. Etapa 4 — pendências por registro e revisão específica

### 11.1 O que foi implementado

Reaproveitados atendimento, ficha detalhada, revisões imutáveis, propostas, decisões, modelo versionado e controle de alterações concorrentes. `PendenciaFichaAtendimento` preserva identidade, alvo, campo, contexto, assinatura, versão, resolução e situação aberta/resolvida/reaberta; `HistoricoPendenciaFicha` acrescenta autora, data, motivo e contexto de cada alteração. O histórico não é apagado ao corrigir o dado. GET calcula a situação atual sem escrever; POST de atualização registra mudanças de estado. Alterações oficiais de ficha, propostas, modelo, mensagens e leituras sincronizam o histórico.

- Cada campo informado, extraído, divergente, ilegível ou com fonte/dependências desatualizadas tem pendência própria. Sua confirmação exige revisão daquele registro/campo; uma resposta genérica do fluxo antigo é recusada. Corrigir uma pessoa não resolve pendências de outra.
- Propostas têm pendências individuais. Associar sem confirmar continua pendente. Uma linha com proposta acompanha a decisão exata dessa proposta; as demais linhas da mensagem continuam separadas. A orientação da conversa deixa de apresentar uma linha já tratada como texto sem destino, sem ocultar outras linhas.
- Cada página da leitura atual exige revisão de seu destino. Propostas da página devem ser decididas individualmente; vinculação exige revisões atuais e confirmadas e abrange todos os campos que ainda usam a página. Desconsiderar uma fonte em uso é recusado. Arquivo sem páginas legíveis só pode ser explicitamente desconsiderado ou substituído; nenhuma leitura é presumida.
- A escrevente pode registrar dúvida adicional em um campo e registro específicos, com motivo. Resolver exige seleção da revisão atual confirmada do mesmo campo/registro e conferência expressa da dúvida. Mudar essa revisão reabre a dúvida, conservando a decisão anterior.
- Alterar uma pessoa ou imóvel explicitamente vinculado invalida a conferência dependente de papel, relação ou negociação. A revisão anterior e seu valor original permanecem preservados. Não há dedução de parentesco, representação ou titularidade.
- Decisões exigem assinatura e versão da pendência aberta, identificador de requisição e motivo. Decisão desatualizada recebe conflito; repetição idêntica não duplica o registro. Os acessos continuam limitados ao cartório e atendimento autorizados.

### 11.2 Configuração profissional e interface

O modelo versionado aceita `campos_obrigatorios_ficha` e `dependencias_campos_ficha`, inicialmente vazios. Requisitos documentais, cláusulas e exigências jurídicas não foram predefinidos pelo sistema. As dependências configuráveis são entre campos do mesmo registro; ciclos, campos inexistentes, tipos inválidos e duplicações são recusados. Dependências entre registros são exclusivamente os vínculos técnicos já escolhidos pela escrevente. A captura ocorre após salvar todos os campos do lote para evitar invalidar imediatamente uma decisão do próprio lote.

Em **Minuta → modelo**, a seção **Requisitos e dependências para homologação profissional** permite escolher campos e dependências, removê-los e salvar nova versão com aprovação explícita. Configuração e campos adicionais seguem na biblioteca de modelos. A existência desses controles não significa que algum cenário profissional foi homologado.

Em **Conversa → Pendências por registro e histórico**, a escrevente consulta o alvo e o motivo, abre fonte/contexto e histórico, registra dúvida ou decide sobre fontes. Pendências automáticas orientam a revisão na ficha; não oferecem encerramento genérico. Não foi criada quarta aba principal. O botão do próximo passo abre esse painel quando existe pendência por registro.

API: `GET/POST /api/v1/atendimentos/{id}/pendencias-ficha/`, operações `atualizar`, `abrir` e `resolver`. A migração `0018_modeloatendimento_campos_obrigatorios_ficha_and_more` foi aplicada localmente após cópia SQLite consistente e verificação de integridade. Os eventos de pendências passam a integrar a assinatura da minuta quando existentes, sem alterar hashes legados sem registros novos. O backup local inclui as novas tabelas.

### 11.3 Como testar e evidências

Usar somente atendimento fictício:

1. Criar duas pessoas na ficha e informar seus nomes sem confirmar. Abrir o painel: deve existir pendência distinta para cada registro. Confirmar apenas uma na ficha: só sua pendência encerra, mantendo histórico.
2. Registrar dúvida sobre o nome de uma pessoa. Tentar resolver sem revisão confirmada ou com revisão de outra pessoa: deve recusar. Selecionar a revisão correta e registrar conferência/motivo: encerra. Alterar o nome posteriormente: a mesma pendência reabre.
3. Criar papel vinculado explicitamente à pessoa; confirmar o papel. Alterar um dado da pessoa: a conferência do papel deve exigir nova revisão, sem modificar o valor original.
4. Enviar mensagem com duas linhas sem interpretação. Desconsiderar apenas uma com motivo: a outra continua aberta. Para linha rotulada, guardar proposta e decidir sobre ela; conferir que as outras linhas continuam visíveis.
5. Anexar TXT fictício rotulado. Tentar encerrar a revisão da página com propostas pendentes ou desconsiderar página em uso: deve recusar. Decidir propostas, confirmar os dados e vincular a página às revisões atuais.
6. Configurar no modelo um campo exigido e uma dependência, salvar e aprovar nova versão. Conferir a nova pendência; alterar o campo de origem da dependência e verificar reabertura. Tentar dependência circular: deve recusar.
7. Abrir duas versões da mesma pendência; decidir em uma e tentar salvar a outra: deve receber conflito. Tentar acessar a pendência por outro atendimento/cartório: deve recusar.

A regressão passou com **125 testes**. Após acrescentar cobertura de configuração, página e cartório, passaram **15 testes específicos**: nove de pendências e seis de backup. A regressão inclui concorrência SQLite, migração com preservação de hashes legados, isolamento e cadeia de evidências das etapas anteriores. ESLint passou nos seis arquivos alterados da interface e no componente de configuração; TypeScript geral permanece com erros preexistentes em outras áreas, sem erros reportados nos arquivos desta etapa. A abertura de dúvida e seu histórico foram verificados na interface local com pessoa e atendimento explicitamente fictícios; evidência em `.local/qa-pendencias-etapa4.png`. Não foram enviados dados a provedores externos.

### 11.4 Limites e próxima entrega

- Continua sendo processamento local de rótulos e decisões humanas, sem IA semântica real. Não classifica integralmente documentos livres, não comprova identidade, autenticidade, pagamento, consulta ou assinatura.
- Dependências configuradas não representam um sistema jurídico completo. A escrevente ainda define escopo, relações, campos relevantes, exigências documentais, cláusulas e regras de cada modelo; nenhuma dessas decisões foi homologada automaticamente.
- Não há perfil profissional distinto do acesso autenticado ao cartório nesta etapa. Testes de concorrência foram realizados em SQLite; PostgreSQL continua sem validação real.
- Pendências por registro aplicam-se ao caminho estruturado. Atendimentos exclusivamente legados conservam o comportamento anterior até revisão explícita/migração; conteúdo ambíguo não é dividido automaticamente.
- O bloqueio técnico de redação estruturada permanece mesmo quando todas as dúvidas forem resolvidas. Não há liberação de minuta por blocos que ignore pessoas e negócios separados. A próxima etapa deve vincular campos e blocos ao modelo profissional aprovado, verificar pendências abertas/reabertas no momento da geração e exportação e produzir rastreabilidade de cada preenchimento. O fluxo completo até exportação ainda não está concluído.

Referências de implementação: `apps/notarius-api/apps/processos/pendencias_ficha.py`, `dependencias_ficha.py`, `ficha_estruturada.py`, `conferencia.py`, `redacao.py`, `models.py`, `serializers.py`, `views.py`, `tests/test_pendencias_ficha.py`; interface em `apps/notarius-web/src/components/atendimentos/PendenciasFicha.tsx`, `PerguntasConferencia.tsx`, `RegrasRevisaoModelo.tsx` e `MinutaPreparada.tsx`.

## 12. Etapa 5 — vinculação ao modelo e preenchimento estruturado

### 12.1 O que funciona

O caminho estruturado agora preenche literalmente um modelo aprovado a partir de registros e revisões escolhidos explicitamente. Reutiliza preparação, versões de minuta, comparação, edição humana, revisão final e exportadores Word/PDF. Não foi introduzido provedor externo, geração livre de cláusulas ou declaração automática de pagamento, consulta ou assinatura.

O modelo versionado pode configurar `registros_minuta`: posições com identificador, rótulo, tipo e vínculos. Exemplo técnico: posição `vendedor1`, tipo `pessoa`, marcador `{{vendedor1.nome}}`. Cada posição aponta para um único registro; vários participantes usam posições separadas, sem concatenar blocos antigos ou juntar homônimos. Uma posição de papel exige referência à posição da pessoa; relação exige as duas pessoas; negociação exige o imóvel. A escolha de registros deve corresponder exatamente aos vínculos reais da ficha. O rótulo “vendedor” sozinho não prova papel ou identidade.

A vinculação do atendimento é independente da configuração reutilizável do modelo. `VinculacaoMinutaAtendimento` mantém versões imutáveis, modelo exato, autora, data, registros, exclusões individuais e motivo. A biblioteca preserva posições e vínculos do padrão, sem transportar IDs de pessoas ou imóveis do caso de origem. No caso novo, é preciso escolher registros e aprovar o modelo novamente.

- Todo registro ativo deve estar vinculado a uma posição ou explicitamente fora daquela minuta, com motivo individual. Alterar um registro excluído exige revisar novamente sua destinação. Excluir do texto não apaga suas pendências; o bloqueio conservador da conferência continua valendo.
- A revisão da vinculação exige modelo, versão, assinatura da ficha aberta e conferência explícita. Nova tentativa idêntica é idempotente; versão ou ficha desatualizada recebe conflito. A reserva de escrita SQLite precede as leituras da transação; outros bancos usam bloqueio da linha do atendimento.
- Os marcadores usados passam a exigir o campo no registro vinculado, produzindo pendência individual quando ausente, sem exigir o mesmo campo de todas as pessoas. Não são exigências legais: são entradas necessárias ao texto que a escrevente aprovou.
- Cada preenchimento exige revisão atual confirmada, valor conhecido, fonte/leitura e dependências atuais. Todas as pendências abertas ou reabertas continuam impedindo preparação, revisão final e exportação. Não existe caminho de resposta genérica que dispense a vinculação.
- O texto não normaliza nomes, valores, datas ou condições por suposição. Preserva o valor revisado literalmente, inclusive espaços. Marcadores desconhecidos, campos não configurados, mistura de marcadores antigos/estruturados e marcadores ainda presentes nos valores são recusados. Preenchimento acima de 150.000 caracteres é recusado sem truncamento nem gravação parcial.
- Cada marcador preserva registro, campo, revisão/versão, valor original/revisado, fonte, trecho, confirmação, propostas associadas, dependências, modelo e vinculação. As ocorrências no texto preparado têm bloco e posições inicial/final, permitindo verificar que o trecho corresponde ao valor salvo.
- Edição humana mantém as fontes da versão de base; a API e a interface informam que as posições de inserção não correspondem automaticamente ao texto editado. A edição não confirma novos fatos nem altera a ficha. Exige nova revisão final daquela versão.
- Mudança de dado, documento/leitura, modelo, decisão ou vinculação invalida a assinatura da minuta anterior. Exportação verifica novamente dados, pendências, versão mais recente e revisão final do texto exato. Reaproveitados os mesmos exportadores, sem reescrita por IA. Comparação entre versões também inclui campos estruturados.

### 12.2 Interface e como testar

Mantidas as áreas **Conversa, Documentos e Minuta**. A pendência de vinculação na Conversa abre a área Minuta.

1. Em **Minuta → Revisar modelo → Posições e marcadores da ficha detalhada**, configurar posições, tipos e vínculos. Escolher os campos e posicionar seus marcadores nos trechos adequados do padrão profissional. Substituir os marcadores antigos antes de salvar o modelo estruturado. Revisar o texto inteiro e aprovar explicitamente uma nova versão.
2. Em **Vincular ficha ao modelo**, escolher o registro exato para cada posição. Conferir pessoas, papéis, relações e imóvel da negociação; justificar cada registro que ficará fora. Registrar motivo e conferência da vinculação. O histórico anterior permanece disponível.
3. Voltar à ficha/conversa para confirmar os campos e resolver cada pendência, inclusive destinos de páginas e propostas. Não se aceita aprovação de arquivo inteiro como confirmação de todos os campos.
4. Usar **Preparar minuta** e **Conferir dados utilizados**. Comparar o texto com valores, fontes, página/leitura/canal e trechos. A minuta fica salva como versão imutável; uma segunda preparação sem mudanças reutiliza a versão existente.
5. Conferir integralmente o texto salvo e registrar a revisão final da versão. Só então baixar Word/PDF. Alterar um dado ou fonte e tentar exportar a versão anterior: deve recusar. Preparar outra versão, comparar, revisar e exportar novamente.

API adicionada: `GET/POST /api/v1/atendimentos/{id}/vinculacao-minuta/`. Configuração incorporada aos endpoints existentes de modelo e biblioteca. Migração `0019_modeloatendimento_registros_minuta_and_more`, aplicada localmente após cópia SQLite consistente verificada por integridade. O backup local inclui vinculações. A migração não divide conteúdo legado nem transfere confirmações para novos registros. A compatibilidade dos hashes legados sem dados estruturados continua coberta por regressão.

### 12.3 Evidências

A regressão passou com **142 testes**. A cobertura nova inclui múltiplas pessoas, imóvel/negociação, literalidade e ocorrências repetidas, confirmação/fonte, dúvidas manuais, vínculo de papel com pessoa incorreta recusado, registro não destinado, exclusão alterada, modelo alterado, dados alterados, leitura substituída, idempotência, histórico, isolamento, bloqueio de fatos fixos e exportação após revisão final. A concorrência de dois escritores SQLite preserva uma única versão da vinculação. O teste de exportação lê o DOCX e verifica a correspondência do corpo com o texto salvo; o PDF é reaberto e seu texto é conferido. Após o ajuste final do limite de preenchimento, passaram os 15 testes específicos da etapa, incluindo esse limite.

Na interface local, atendimento **TESTE FICTÍCIO — minuta estruturada etapa 5 (respostas simuladas)** percorreu documento TXT fictício, proposta com leitura/página/trecho, mensagem de condições, revisões simuladas, revisão da unidade de texto, escolha explícita de pessoa/imóvel/negociação e preparação da minuta. O texto preservou a previsão de pagamento e não a transformou em pagamento realizado. A seção de dados utilizados apresentou a cadeia até o documento/mensagem. Os downloads permaneceram bloqueados na tela enquanto a revisão final não havia sido registrada. A exportação após revisão foi validada nos testes automatizados, com respostas humanas simuladas. Evidência visual: `.local/qa-minuta-estruturada-etapa5.png`.

ESLint passou nos arquivos de interface alterados. TypeScript geral ainda falha em outras áreas já existentes do projeto, sem erros reportados nos arquivos desta etapa. Nenhuma resposta de teste foi apresentada como homologação profissional ou IA real.

### 12.4 Limitações e decisões que continuam com a escrevente

- O padrão profissional completo das imagens ainda depende de homologação: posições, campos, qualificações, documentos exigidos, cláusulas aplicáveis, vínculos e redação de cada cenário. A demonstração local é fictícia e não é uma escritura aprovada para uso real.
- O preenchimento é literal e por posições explícitas. Não há composição automática de qualificação de várias pessoas, flexão de gênero/número, pluralização, seleção semântica de cláusulas ou repetição automática de blocos. Para vários participantes, configurar posições e texto específicos. Cada bloco não vazio do modelo estruturado é incluído; não há condição jurídica implícita de representação/observações.
- Os marcadores estruturados aceitam os campos disponíveis na ficha e as qualificações adicionais configuradas. Uma informação necessária sem campo configurado exige adequação explícita da estrutura; não deve ser copiada como fato fixo do exemplo nem inserida por suposição. O legado permanece disponível para revisão, sem mistura automática com os registros novos.
- O bloqueio de declarações fixas de pagamento, quitação, consultas e assinaturas é lexical e conservador, reaproveitando a proteção existente. Pode bloquear títulos ou formulações legítimas e não compreende todas as paráfrases. A escrevente deve revisar o texto fixo integralmente e separar fatos do caso em dados confirmados com fonte. Aprovação, literalidade e validação de CPF não comprovam veracidade, identidade ou autenticidade.
- Edições livres do texto exigem revisão integral. A rastreabilidade das inserções automáticas pertence ao preenchimento de base; o sistema não inventa evidência para texto acrescentado manualmente.
- O perfil profissional distinto do vínculo de acesso ao cartório e a validação em PostgreSQL continuam pendentes. Os testes atuais usam SQLite e dados fictícios. Não há autorização nesta entrega para dados reais ou envio a provedores externos.

Próxima etapa proposta: homologar um cenário profissional de compra e venda com a escrevente, configurar seu modelo completo e executar o roteiro de ponta a ponta com documentos fictícios correspondentes. Essa homologação deve revelar campos ou decisões ainda ausentes, sem tratá-los como exigências jurídicas universais nem ampliar funcionalidades periféricas.

Arquivos centrais: `apps/notarius-api/apps/processos/redacao_estruturada.py`, `redacao.py`, `conferencia.py`, `pendencias_ficha.py`, `models.py`, `serializers.py`, `views.py`, `comparacao_minutas.py`, `backup_local.py`; testes em `apps/notarius-api/tests/test_redacao_estruturada.py`. Interface: `apps/notarius-web/src/components/atendimentos/PosicoesModelo.tsx`, `VinculacaoMinuta.tsx`, `MinutaPreparada.tsx` e `PerguntasConferencia.tsx`.

## 13. Etapa 6 — dois cenários preparados para revisão profissional

### 13.1 Escopo escolhido e entrega

À pergunta sobre qual cenário homologar primeiro, a resposta nesta conversa foi **“Preparar os dois para comparação”**. Foi autorizada a preparação de participação direta e representação por procuração. Essa escolha não é aprovação dos modelos, suficiência documental ou homologação jurídica de qualquer variante.

Reaproveitados ficha, propostas, leitura local de TXT, fontes, relações, pendências, modelos, vinculação, revisões e exportação. Não foram introduzidos novos tipos de registro, abas, exigências jurídicas, cláusulas automáticas ou provedores externos. Nesta rodada, a implementação é a preparação reproduzível dos cenários e sua cobertura de testes; a homologação continua com a escrevente.

Material concreto para revisão: [Comparação para a escrevente](homologacao-compra-venda/COMPARACAO_PARA_ESCREVENTE.md), com links para os dois atendimentos, rascunhos completos, arquivos fictícios e tabela das seções da referência ainda não cobertas.

| Variante local | Material e organização | Estado verificado |
|---|---|---|
| Participação direta — `0a9ff6f1-9bbd-54c7-81f9-d032d55b4f5d` | 2 pessoas, 2 papéis, imóvel e negociação; 6 TXT + mensagem; 27 propostas | Modelo rascunho, zero revisões de dados, zero vinculações de minuta, zero minutas |
| Com procuração — `a8ed8261-ef71-5eac-bb03-5226c7588f45` | Mesma base fictícia; procurador e relação representante→vendedor separados; 8 TXT + mensagem; 38 propostas | Modelo rascunho, zero revisões de dados, zero vinculações de minuta, zero minutas |

Os mesmos nomes e valores fictícios foram usados como base comparável, com IDs distintos nos atendimentos. Não houve fusão de pessoas ou compartilhamento de fonte entre os casos. A variante direta omite o bloco de representação como proposta de teste; isso não confirma ausência de representação em qualquer caso real. A variante com procuração não atesta validade, suficiência ou poderes do instrumento.

Os rascunhos cobrem qualificação individual, papéis, imóvel, titularidade/aquisição/ônus informados, preço e condições. As qualificações e condições são sintéticas. CPF, documento e matrícula estão explicitamente identificados como fictícios e sem validade. Não foram copiados dados rasurados, assinaturas, selos, resultados de consulta ou fatos da escritura enviada. A abertura, as declarações, tributo, certidões, consultas, requerimentos e encerramento profissional ainda exigem definição e campos adequados; não foram preenchidos por suposição nem ocultados como se estivessem completos.

### 13.2 Preparação segura e como testar

`cenarios_homologacao.py` define as duas variantes e seus resultados esperados propostos. O comando `preparar_homologacao_compra_venda` exige cartório identificado como fictício e usuária que já tenha acesso a ele. Reutiliza os contratos existentes do atendimento, registra origem da preparação no histórico e não confirma campo, fonte, modelo, vinculação ou revisão final. As fontes são TXT literais e mensagem, sem IA real ou OCR apresentado como leitura de certidão autêntica.

Cada atendimento é preparado em transação, com identificação estável por versão/cartório/variante. Falha desfaz a preparação daquele atendimento. Repetição retorna o manifesto inicial e preserva as decisões feitas posteriormente: não apaga revisões nem redefine o modelo aprovado. O manifesto representa o momento da preparação inicial, não o estado atual. Material local alterado é preservado; o comando recusa sobrescrita. Nenhuma migração ou alteração de cobrança/chave foi necessária.

Roteiro da escrevente:

1. Abrir a comparação e os dois atendimentos. Comparar primeiro as fontes e a direção da representação, depois os rascunhos em **Minuta → Revisar modelo**.
2. Revisar a organização proposta dos registros. Em **Conversa → Ficha detalhada**, associar cada proposta ao registro/campo correto, conferindo o contexto e a fonte; confirmar somente após revisão.
3. Resolver pendências de páginas, dados e instrumento. Trecho literal ou mesma grafia do nome não garante associação correta. Não usar revisão genérica para aprovar dados de todo o arquivo.
4. Homologar a redação e completar as seções profissionais ainda ausentes antes de aprovar o modelo. Vincular registros e preparar somente depois dessa revisão. O aplicativo permanece bloqueado enquanto o modelo e os dados não forem revisados.
5. Conferir a minuta, revisar a versão final e exportar Word/PDF. Este passo foi simulado apenas no banco isolado dos testes; os atendimentos locais não foram aprovados para demonstrá-lo.

### 13.3 Verificação e limites

Passaram **oito testes novos**, sendo sete executados em conjunto e um teste adicional do comando/material. Cobrem: preparação sem decisões humanas fabricadas; repetição após revisões preservando o histórico; participação direta e procuração de ponta a ponta; texto/ocorrências/fontes correspondentes; DOCX com corpo igual ao texto salvo; PDF reaberto; instrumento não confirmado impedindo geração; novo preço divergente bloqueando sem sobrescrever a confirmação anterior; nomes iguais com fontes de outro atendimento recusadas; cartório não fictício ou não autorizado recusado; falha desfazendo criação; preservação de material local editado. As respostas de confirmação, aprovação e revisão final desses testes são explicitamente simuladas e nunca aplicadas aos dois atendimentos locais.

O comando foi executado e repetido no cartório fictício existente. As contagens e os modelos em rascunho foram conferidos no banco e na interface local; **Preparar minuta** permaneceu desabilitado nas duas variantes. Evidências visuais em `.local/qa-homologacao-direta-etapa6.png` e `.local/qa-homologacao-procuracao-etapa6.png`. A verificação Django passou e não há migração pendente. Não houve alteração da interface nem nova execução de verificações globais da interface nesta rodada.

**Homologação profissional não concluída.** O texto completo da escritura de referência ainda não está representado pelos campos e rascunhos disponíveis. A comparação lista as lacunas concretas e as decisões que dependem da escrevente: redação a manter/substituir; pessoas, qualificações e relações aplicáveis; documentos por variante; conferências do instrumento; campos das demais seções e condições de cada cláusula. Não se deve transformar essas propostas em exigências jurídicas universais nem preencher lacunas copiando acontecimentos do exemplo. Também permanecem os limites anteriores sobre validação de identidade/autenticidade, edição manual, perfil profissional e PostgreSQL.

Próximo passo dependente de decisão humana: a escrevente revisar os dois rascunhos e indicar os ajustes e campos profissionais da tabela de lacunas. Só após essas definições será possível configurar o cenário completo e registrar sua homologação; a preparação dos dois casos e os testes técnicos não substituem essa decisão.

Referências novas: `apps/notarius-api/apps/processos/cenarios_homologacao.py`, `management/commands/preparar_homologacao_compra_venda.py`, `apps/notarius-api/tests/test_cenarios_homologacao.py` e o material em `docs/homologacao-compra-venda/`.

## 14. Etapa 7 — dados do ato e complementos com fonte e âmbito próprios

### 14.1 Trabalho executado

O pedido de avançar autorizou completar a infraestrutura dos campos faltantes; não foi tratado como homologação dos rascunhos. Reaproveitados objetos da ficha, revisões, fontes, propostas, pendências, vínculos imutáveis, modelo e exportadores. Mantidas **Conversa, Documentos e Minuta**, sem provedor externo, alteração de cobrança ou exposição de chave.

Adicionados dois tipos opcionais:

- **Ato:** abertura, data informada, local, serventia, referência e encerramento. Não recebe data, local ou fatos automaticamente. Não aceita pessoa/imóvel como vínculo de criação; seu âmbito é o atendimento.
- **Complemento:** categoria, assunto, conteúdo, referência e situação informada, em registros separados por documento, consulta, declaração ou assunto. Na criação, a escrevente escolhe explicitamente âmbito de atendimento, pessoa, imóvel ou pessoa+imóvel. Vínculos estrangeiros, incompatíveis ou ausentes são recusados e não podem ser transferidos silenciosamente depois.

As categorias disponíveis organizam declaração, transmissão, DOI, tributo, certidão/documento, consulta, requerimento, despesas ou outro assunto. São opções de classificação, não documentos/cláusulas juridicamente obrigatórios. Situação informada é distinta da confirmação da revisão: previsão ou declaração de realização não significa serviço executado pelo sistema, documento autenticado ou fato comprovado.

Categoria e situação são necessárias para interpretar um complemento criado, como integridade técnica do registro. Não são exigências legais nem uma nova lista documental. A pendência distingue essa classificação de campos exigidos pelo modelo. “A esclarecer” mantém bloqueio. Cada conteúdo conserva fonte e confirmação próprias; classificar/revisar arquivo não confirma todos os campos.

A classificação e a situação passam a integrar as dependências técnicas do conteúdo. Alterá-las reabre a conferência afetada; valores e confirmações históricas não são sobrescritos. Dependências configuráveis continuam no modelo; ciclos entre elas e as dependências técnicas são recusados. Mudanças de pessoa/imóvel vinculado também exigem revisão. Campos/opções novos não foram preenchidos em atendimentos antigos nem repartiram textos legados.

### 14.2 Modelos e proteção contra mistura

O editor de posições oferece ato e complemento. Cada posição de complemento exige **categoria esperada** e vínculos explícitos. A vinculação verifica categoria atual confirmada e âmbito exato: consulta não pode preencher tributo; complemento de uma pessoa não pode virar geral nem pertencer a outra pessoa por omissão/troca de vínculo. Essas verificações são compatibilidade técnica com a configuração, sem julgamento de validade jurídica ou suficiência da fonte.

Em **Minuta → Revisar modelo → Estruturas complementares para revisar**, há duas referências não homologadas, com e sem procuração. Cobrem posições de abertura/data/local/serventia, seções individuais de declarações, transmissão, informação de DOI, tributo, documento do imóvel, consultas por pessoa, requerimento, encerramento e despesas. A declaração de quitação usa seu campo separado já existente na negociação. Vários documentos/consultas precisam de posições e registros separados; não há agregação ou cláusula condicional inferida.

Carregar só modifica o rascunho no editor: não grava modelo, cria objetos, preenche campos ou aprova conteúdo. A caixa de aprovação continua desmarcada. As referências preservam as âncoras das imagens e página original não identificada; são fonte da organização proposta, não evidência de acontecimentos em outro atendimento. Não são transcrição integral profissional aprovada. Os dois casos da etapa 6 permanecem preservados.

Material para revisão: [Guia e dois rascunhos ampliados](homologacao-compra-venda/estruturas-complementares/LEIA_PRIMEIRO.md). Os arquivos `.txt` e `.json` correspondentes contêm texto/posições/categorias e identificação explícita de não homologação. Não foi preenchido fato do exemplo rasurado, consultada base externa ou declarada assinatura/recolhimento.

### 14.3 Concorrência e histórico

Foi corrigida uma lacuna encontrada na revisão: conferir apenas a versão do campo permitia capturar uma classificação/pessoa vinculada nova após uma confirmação iniciada em contexto antigo. A ficha agora devolve `contexto_assinatura` por campo; o formulário envia a assinatura que estava aberta. O servidor reserva a escrita e valida todos os contextos do lote antes da primeira revisão. Contexto divergente ou ausente para campo dependente recebe conflito e não grava o lote. Os campos sem dependências preservam compatibilidade com pedidos antigos; campos dependentes exigem o contexto atual.

O lote de categoria, situação e conteúdo valida o contexto inicial e captura as dependências finais após suas gravações, sem invalidação imediata de sua própria confirmação. Repetição idempotente preserva a decisão anterior. Histórico, isolamento e bloqueios de exportação permanecem. A assinatura da minuta continua sendo invalidada por mudança de dados/decisões/fontes/vinculação.

A migração `0020_alter_objetofichaatendimento_tipo` acrescenta as opções de tipo e não migra fatos/valores. Foi aplicada localmente após cópia SQLite consistente com integridade verificada. Objetos, campos, histórico e configurações novos já são incluídos pelo backup existente. Não há migração adicional pendente.

### 14.4 Como testar e evidências

1. Em **Conversa → Ficha detalhada**, criar dados do ato e conferir que não surgem data, local ou confirmação automáticos. Os demais grupos não devem receber esses dados.
2. Criar complemento sem escolher âmbito ou sem a pessoa/imóvel exigido pela escolha: deve recusar. Registrar complementos distintos para documentos, consultas e declarações de pessoas diferentes; conferir fonte, trecho, revisão e vínculo de cada um.
3. Classificar e informar categoria/situação/conteúdo sem confirmar: mantém pendências. “A esclarecer” não libera geração. Confirmar os campos individualmente após revisão.
4. Carregar referência complementar no editor e cancelar: nenhum modelo ou objeto deve ser criado. Ajustar uma versão segundo as decisões profissionais e aprovar explicitamente antes de vincular/preparar.
5. Tentar vincular consulta à posição de tributo, ou complemento de uma pessoa à posição geral/outra pessoa: deve recusar.
6. Alterar categoria, situação ou pessoa/imóvel após confirmação: conteúdo exige nova revisão e minuta anterior não exporta. Tentar salvar formulário aberto antes da alteração: conflito, sem perda do histórico nem gravação parcial.
7. Após pendências resolvidas e modelo aprovado, preparar, conferir texto/dados/fontes, revisar a versão final e exportar. Os testes usam respostas humanas simuladas; não são homologação real.

A regressão completa passou com **161 testes**, incluindo **10 novos testes de ato/complementos**. Cobertura nova: ausência de valores/criação automática; âmbito explícito e isolamento; classificação incerta; dependências e ciclos; confirmação em lote; reabertura sem sobrescrita; contexto aberto desatualizado recusado; categoria/âmbito incompatíveis no modelo; duas referências válidas e não aprovadas sem escrita no GET; preenchimento com fonte e Word/PDF só após revisão final; invalidação posterior. Os 53 testes estruturados/propostas/novos campos também passaram em execução específica anterior à regressão completa.

Na interface local foi criado atendimento exclusivamente fictício `178a7f69-c2f9-59ae-a8fb-79898c594a7e`. Criado um complemento geral vazio e salva apenas sua categoria como **informada**, com motivo explícito de resposta simulada. Conferidos no banco: categoria `consulta` em situação de revisão `informado`, zero modelos aprovados e zero minutas. Não houve consulta efetuada, dado confirmado ou homologação. Carregamento da referência com procuração foi verificado no editor, com aprovação desmarcada, sem salvar modelo ou criar seus registros. Evidência em `.local/qa-complementos-etapa7.png`.

ESLint passou nos arquivos alterados da interface; a checagem TypeScript global mantém erros em outras áreas, sem erros reportados nesses arquivos. Durante a inspeção foram corrigidas chaves repetidas entre componentes do editor e uma seleção sem opções durante carregamento. A revisão geral do restante da interface não foi ampliada para além do fluxo solicitado.

### 14.5 Limites e decisão profissional pendente

Os campos agora permitem representar as seções, mas a redação profissional integral, os documentos aplicáveis, os poderes do instrumento e as condições de cada cláusula continuam dependendo da escrevente. As referências ampliadas são estruturas para revisão, não escrituras prontas ou juridicamente homologadas. O sistema não classifica livremente fontes, autentica documentos, valida poderes ou executa consultas. O bloqueio de fatos fixos continua lexical e limitado; edição manual exige revisão integral e não recebe evidência inventada.

Propostas anteriores preservam seus destinos e decisões originais. Se um campo novo não constar dos destinos de uma proposta antiga, a escrevente pode revisar diretamente a fonte literal na ficha e tratar expressamente a proposta anterior; não há reclassificação automática silenciosa. Continua sem perfil profissional separado do acesso ao cartório e sem teste real em PostgreSQL. Dados reais e provedores externos seguem fora do escopo autorizado.

Referências centrais: `apps/notarius-api/apps/processos/ficha_estruturada_schema.py`, `ficha_estruturada.py`, `dependencias_ficha.py`, `pendencias_ficha.py`, `redacao_estruturada.py`, `modelo_complementar.py`, `models.py`, `views.py`; `apps/notarius-api/tests/test_complementos_ato.py`; interface em `FichaDetalhada.tsx`, `PosicoesModelo.tsx`, `MinutaPreparada.tsx`, `RegrasRevisaoModelo.tsx` e `VinculacaoMinuta.tsx`.

## 15. Fechamento 1/2 — homologação profissional iniciada, não concluída

O pedido de próxima etapa iniciou a revisão profissional, primeira das duas etapas finais estimadas. Não foi interpretado como aprovação dos modelos, dados ou cláusulas. Foram lidos os dois rascunhos ampliados, o mapa da escritura e as decisões pendentes, preservando o material anterior.

Constatação concreta: os rascunhos atuais são estruturas de campos, com títulos como “Qualificação informada” e campos de conteúdo ainda sem redação profissional fixa. Não equivalem à transcrição integral da escritura enviada. A base da redação precisa ser definida pela escrevente antes de adaptar/homologar seu texto; dados rasurados e acontecimentos do exemplo não serão completados ou reaproveitados como fatos.

Preparada [Ficha de revisão profissional](homologacao-compra-venda/REVISAO_PROFISSIONAL.md), com os dois textos, suas identificações SHA-256, a diferença em relação à referência, decisões pendentes e critérios de encerramento da homologação. À primeira definição sobre a base da redação, a resposta nesta conversa foi: **“O padrão ainda será definido pela escrevente”**. Essa decisão foi registrada em 24/10/2026; não autoriza adotar automaticamente a escritura enviada ou os rascunhos como padrão aprovado. A homologação permanece pendente até a escrevente definir o texto e as condições aplicáveis às duas variantes. A adaptação da redação dependente dessa definição e a validação final do cenário homologado aguardam essa entrada profissional.

Verificação proporcional: consulta somente de leitura dos dois atendimentos fictícios da comparação, ambos com zero modelos aprovados, zero revisões confirmadas e zero minutas. Os rascunhos foram identificados pelos bytes dos arquivos. Nenhum código funcional, dado ou modelo foi alterado nesta rodada; os 161 testes da etapa anterior não foram reexecutados nem apresentados como homologação profissional. Nenhuma consulta jurídica, provedor externo ou alteração de cobrança foi realizada.

Limite atual: somente a escrevente pode decidir a base, redação, aplicabilidade, documentos e conferências profissionais, conforme as regras do usuário. A etapa permanece em revisão e não deve ser marcada concluída enquanto essas definições e a aprovação da versão exata não forem registradas. Depois disso segue o fechamento 2/2: validação final de ponta a ponta do cenário homologado, com dados fictícios e respostas simuladas identificadas.

## 16. Ensaio técnico integral independente da definição profissional

O usuário pediu continuidade após informar que o padrão ainda será definido pela escrevente. Foi executado o trabalho independente dessa definição: validar tecnicamente as duas variantes com todas as posições dos rascunhos ampliados. Não foram adaptadas ou aprovadas a redação profissional, condições de cláusulas ou documentos do cenário real. O fechamento 1/2 permanece pendente; este ensaio não substitui o fechamento 2/2 da versão que vier a ser homologada.

Implementado `apps/notarius-api/tests/test_validacao_integral_local.py`, reutilizando a preparação, os contratos da API e as respostas simuladas dos testes anteriores. O ensaio cria os registros adicionais de ato/complementos em banco de teste separado, adiciona fontes TXT fictícias e uma declaração fictícia de ausência de quitação, associa propostas explicitamente e mantém um conteúdo de consulta divergente embora o trecho literal esteja disponível. Geração permanece bloqueada, inclusive após aprovação e vinculação simuladas. Só depois de decisão humana simulada específica e revisão da unidade de texto o roteiro prossegue.

O percurso completo cobre **45 marcadores na participação direta e 56 com procuração**. Confere registro/revisão/fonte/trecho, propostas e confirmação de cada inserção, página/leitura dos TXT, e correspondência das posições de ocorrência com o valor salvo. Não mistura procurador, representado, comprador, imóvel ou complementos de pessoas distintas. A situação de pagamento continua previsão; consultas não realizadas, despesas/tributos previstos e minuta sem assinatura não são convertidos em acontecimentos concluídos.

Antes da revisão final simulada, exportação é recusada. Após revisar a versão exata, Word e PDF são produzidos e reabertos: corpo do DOCX corresponde ao texto salvo; todos os valores usados são localizados no texto extraído do PDF, normalizando espaços/quebras de linha. Uma troca simulada de versão de leitura em fonte do teste bloqueia nova geração e exportação antiga. Não foi executado OCR real, consulta externa ou provedor de IA; o construtor do provedor é monitorado no teste e não é chamado.

A validação evidenciou cálculos duplicados de dependências/serialização durante leitura de ficha, histórico e pendências. Foram removidas duplicações **dentro da avaliação atual**, sem cache global ou entre alterações. A ficha calcula o contexto por campo uma vez e serializa cada revisão uma vez para atual/histórico; pendências reaproveitam as dependências que acabaram de calcular; o preenchimento verifica a confirmação efetiva da revisão serializada. Continuam as mesmas exigências de versão/contexto, confirmação, fonte/leitura e registro vinculado. Na ficha fictícia medida, houve **96 → 50 consultas ao banco**, com assinatura da resposta completa idêntica antes/depois. Isso não é benchmark de produção/PostgreSQL nem garantia de tempo.

**Verificações concluídas:** 161 testes de regressão passaram; o novo teste integral, contendo ambas as variantes e verificações negativas/positivas, também passou após o ajuste. Total de 162 testes nas duas execuções. A primeira execução integral anterior ao ajuste também havia passado. Não houve alteração da interface nem nova migração. Não foram reexecutadas verificações de interface sem mudança correspondente.

Como repetir e detalhes: [Relatório de validação técnica integral](homologacao-compra-venda/VALIDACAO_TECNICA_INTEGRAL.md), incluindo comando de teste, percurso, critérios e limites. Arquivos de implementação alterados: `ficha_estruturada.py`, `pendencias_ficha.py` e `redacao_estruturada.py`, exclusivamente na reutilização de leituras/cálculos equivalentes. Medições locais de referência em `.local/qa-consulta-before.json` e `.local/qa-consulta-after.json`.

Limites: os testes usam rascunhos estruturais, dados sintéticos e respostas simuladas. Nenhuma aprovação simulada foi aplicada aos atendimentos comparativos locais; a definição do padrão continua aguardando a escrevente. A formatação profissional deve ser revisada visualmente e o ensaio repetido com o modelo exato após homologação. Permanecem os limites anteriores de identidade/autenticidade, interpretação livre, autorização profissional específica e PostgreSQL. Não se declara concluída a homologação nem liberado o uso de dados reais ou provedores externos.

## 17. Etapa 3 solicitada — documentos vinculados à ficha

Esta é a **Etapa 3 de documentos vinculados**, conforme a solicitação atual, e não uma nova aprovação da seção 10 ou dos modelos profissionais. Reaproveitados upload, hash e binário original, extração nativa, OCR local, páginas e versões de leitura. A interface continua em Conversa, Documentos e Minuta.

### 17.1 Entrega e referências

- `apps/processos/organizacao_anexos.py`, modelos `OrganizacaoAnexoAtendimento` e migração `0021`: decisões append-only de finalidade, tipo livre definido pela escrevente e vínculos explícitos com IDs de pessoa/imóvel. Vínculos admitem páginas específicas, todas as páginas por escolha explícita, vários destinatários e atendimento geral sem pessoa/imóvel. Nenhum nome ou estado civil determina associação.
- `views.py`, rota `anexos/{id}/organizacao/`: histórico, autora, motivo, leitura e versão; controle otimista, repetição idempotente e reserva do atendimento antes da decisão. IDs externos ao atendimento são recusados, inclusive entre casos do mesmo cartório.
- `OrganizarAnexo.tsx` e `AnexosConversa.tsx`: filtros por finalidade/tipo/destinatário, formulário agrupado, IDs curtos para distinguir homônimos, abrangência por página e histórico de correções. O formulário conserva a versão aberta, recusando sobrescrita após atualização concorrente.
- `ficha_estruturada.py`, `serializers.py`, `dependencias_ficha.py` e `propostas_dados.py`: cada uso de página registra a versão de organização conferida. Confirmar exige tipo, finalidade de caso, destinatário e página compatíveis. Referência de redação/arquivo desconsiderado não fornece dados à ficha, mesmo com trecho literal. Propostas anteriores permanecem no histórico, identificadas como referência/desconsideradas. Corrigir classificação ou substituir leitura reabre os usos antigos, preservando seus valores, fontes e confirmações históricas; exige nova conferência para uso atual.
- `conferencia.py`, `pendencias_ficha.py` e `redacao.py`: documentos pendentes geram perguntas próprias; referências ficam fora da conferência comprobatória e extração de propostas. Fontes antigas não podem sustentar a minuta atual. Mudanças de organização alteram a assinatura usada pela preparação/exportação, exigindo atualização e revisão correspondente.
- `leitura_anexos.py`, `ocr_local.py`, `PaginaLeitura.tsx`: cobertura atual informa total identificado, unidades processadas, páginas sem texto, leitura incerta e limites explícitos de 40 páginas, OCR em 10 páginas, texto de 50.000 caracteres e regiões OCR. Falha/tempo/senha permanecem problemas de leitura; ausência de texto não representa inexistência do fato. Os códigos de limite recebem descrição simples na tela.
- `backup_local.py`: a nova tabela integra a contagem opcional de backup, preservando compatibilidade com cópias anteriores. Migração local aplicada após cópia SQLite verificada em `.local/migration_safety/antes-documentos-vinculados.sqlite3`. Nenhum anexo antigo foi classificado automaticamente.

### 17.2 Como testar

No atendimento **TESTE FICTÍCIO — documentos vinculados etapa 3** (`9e828e2a-9bef-4321-b0d0-94f7624c4161`), abrir Documentos. Há duas pessoas de nomes próximos, um imóvel e dois anexos fictícios. Os dados foram apenas informados, sem confirmações, aprovação profissional ou minuta. O PDF tem somente a página 1 vinculada à pessoa ALFA por decisão de teste expressamente simulada; as demais páginas aguardam revisão. O TXT foi separado como referência de redação por decisão simulada na interface.

1. Abrir **Classificar e vincular documento** no PDF, consultar o histórico e adicionar a segunda pessoa explicitamente à página 2; não selecionar todas as páginas por conveniência.
2. Usar os filtros de destinatário/tipo/finalidade e conferir os IDs diferentes. Verificar que o arquivo de referência tem extração de propostas bloqueada e não admite fonte para preencher os dados do caso.
3. Abrir **Conferir leitura** e comparar com **Baixar original**. Para falha/limite, usar arquivos fictícios próprios; o total desconhecido deve continuar desconhecido. Página com texto não é garantia de leitura integral.
4. Com duas sessões abertas, salvar uma correção e tentar salvar a versão antiga na outra: deve recusar e manter a primeira decisão. Ler novamente o PDF: preservar original/páginas antigas e exigir reavaliação dos vínculos e usos de fontes.

Automação em `tests/test_organizacao_anexos.py`: PDF multipágina, várias pessoas, nomes próximos, vínculos conjuntos/pessoa/imóvel e por página, original/binário/hash preservados, finalidade de referência, reclassificação que reabre dado já confirmado, leitura nova com páginas antigas preservadas, limites de página/OCR, idempotência, versão antiga e isolamento. Fixtures anteriores foram atualizadas somente no banco de teste para registrar decisões de classificação **simuladas e explícitas**, sem liberar esses comportamentos automaticamente no produto.

### 17.3 Critérios e limites

Concluído funcionalmente quando a escrevente consegue classificar/corrigir cada arquivo e sua abrangência, distinguir os participantes pelo registro, consultar o histórico, manter dúvidas pendentes e observar bloqueio de fonte incompatível/antiga na preparação e exportação. Classificar não confirma valores, identidade, autenticidade, interpretação ou cumprimento de exigência jurídica. Requisitos documentais, modelos e cláusulas continuam configuração a homologar.

O tipo é um rótulo humano por arquivo; PDFs que reúnem tipos distintos podem receber um rótulo coletivo, com destinatários separados por página. Não há separação automática de arquivos, inferência de titularidade ou interpretação semântica por IA. Limites da leitura atual ficam no anexo; páginas históricas mantêm texto/OCR/limites individuais, sem um novo painel de comparação de leituras nesta etapa. Anexos antigos sem metadados não ganham total presumido. A revisão visual completa e a resolução de páginas incertas continuam com a escrevente. Testes locais SQLite não substituem validação de concorrência PostgreSQL.

### 17.4 Verificações da entrega

- Os 7 testes específicos de organização passaram após o último ajuste, incluindo truncamento explícito do texto nativo. Comando na raiz: `.venv/Scripts/python.exe apps/notarius-api/manage.py test tests.test_organizacao_anexos --noinput`.
- Passaram os 17 testes reunindo organização, OCR e resumo; passaram também os 20 testes de cenários/propostas, cobrindo ambas as variantes, geração e exportação com decisões simuladas. O teste antigo de transcrição TXT passou após informar explicitamente versão de organização zero para fonte ainda não classificada, sem confirmação.
- ESLint passou nos componentes de atendimento e bibliotecas alteradas. A checagem global TypeScript continua recusada por erros fora deste fluxo (módulos antigos de documentos/HITL, tipagens de Grid, Cypress, entre outros); não apontou erro nos arquivos de atendimentos/ficha/propostas desta entrega. Não se declara o build global integralmente validado.
- Migração sem alterações de modelo pendentes; verificação de espaços do diff sem erros. A tela local foi exercitada: referência fictícia salva com extração bloqueada; PDF fictício vinculado apenas à pessoa e página escolhidas; nomes próximos apresentados com IDs distintos. Captura local: `.local/qa-documentos-vinculados-etapa3.png`.
- Auditoria do caso fictício: 2 pessoas, 1 imóvel, 2 arquivos, 2 decisões simuladas de classificação, **zero dados confirmados, zero modelos aprovados, zero minutas**. Nenhum envio a provedor externo, consulta, pagamento ou assinatura foi executado.
- A regressão ampla executou 168 testes: 164 passaram, incluindo o ensaio integral das duas variantes; quatro fixtures antigas falharam por não informar a nova versão/classificação da fonte. Três já tinham sido corrigidas e verificadas em execução focada enquanto a regressão ainda usava os módulos carregados anteriormente; a quarta foi atualizada para classificar explicitamente o documento sintético do cenário. Não foi removido o bloqueio do produto. O reteste final dos quatro módulos (`test_modelo_referencia`, `test_ocr_atendimentos`, `test_resumo_revisao`, `test_organizacao_anexos`) passou integralmente: **23 testes**, incluindo os quatro antes recusados e o novo teste de vínculo conjunto/imóvel. Cobertura combinada: **169 testes distintos**, em execuções complementares; não se registra uma única execução global final limpa. Evidências locais: `.local/etapa3-regression.log`, `.local/etapa3-reteste-final.log`, `.local/etapa3-documentos-final.log` e `.local/etapa3-cenarios.log`.

## 18. Etapa 4 solicitada — extração documental estruturada, sem chamadas externas

Preparada a integração de análise dos textos dos documentos para **propor dados à ficha detalhada**. Não há IA real funcionando nesta entrega: o adaptador real tem construtor de requisição e parser de resposta preparados, com transporte ausente e bloqueio incondicional. A rota normal não invoca sequer seu método de análise. O provedor simulado é código exclusivo do pacote de testes, com guarda adicional de contexto/banco de teste; nenhum parâmetro HTTP, chave configurada ou opção de cobrança o ativa no uso normal.

Reaproveitados `PropostaDadoAtendimento`, decisões humanas da ficha, fontes/páginas, classificação documental, `PendenciaFichaAtendimento` e assinatura de preparação/exportação. Não foi conectado o serviço antigo de geração por microsserviços, que contém fallback próprio e não pertence ao fluxo autorizado. A extração local por rótulos permanece uma operação separada e claramente identificada, sem ser chamada como fallback da análise documental.

### 18.1 Contratos e limites

Contratos Pydantic fechados e estritos em `apps/processos/contratos_documentais.py`, versão `documental_v1`. Campos extras, coerções de tipos, confirmação sugerida pelo provedor e campos não configurados são recusados.

| Estrutura | Conteúdo obrigatório |
| --- | --- |
| Pedido HTTP | `client_id`; documentos com `documento_id`, `leitura_versao` e `organizacao_versao` esperadas. Provedor e resposta não são aceitos no pedido. |
| Entrada montada pelo servidor | Atendimento e assinatura do contexto; registros com seus IDs/tipos e vínculos humanos existentes; campos configurados, rótulos e opções permitidas; unidades de leitura. Não inclui referências de redação. |
| Unidade de entrada | ID estável da página/canal/linha, texto literal completo da linha, situação/limites da leitura, destinatários de página escolhidos pela escrevente e sinal de instrução suspeita. Páginas sem texto continuam como unidades vazias para revisão. |
| Fonte | Documento, ID e número da página, versão da leitura, versão da organização e canal (`texto` ou `ocr`). |
| Proposta | Fonte completa, trecho, início/fim Unicode na unidade (fim exclusivo), valor literal, tipo de registro/campo, registro sugerido, pessoa/imóvel relacionado e associação `sugerida` ou `incerta`. Não há campo de confirmação. |
| Saída | Versão e assinatura do contexto; exatamente uma resposta por unidade enviada, com propostas e/ou dúvidas explícitas. Sem unidade omitida, repetida ou adicionada. |

Limites técnicos desta versão: até **5 documentos**, **200 unidades**, **100.000 caracteres totais**, **4.000 caracteres por linha/trecho/valor**, **200 propostas no lote**, **10 propostas e 10 dúvidas por unidade**, resposta de até **500.000 bytes**, até 200 registros e 500 campos no contexto. Os limites são controles técnicos, não requisitos jurídicos. A operação é recusada por inteiro quando ultrapassados; não trunca nem completa silenciosamente o conteúdo. O limite anterior de upload TXT continua em 50.000 caracteres por arquivo. Conjuntos maiores exigem seleção menor/divisão autorizada dos arquivos; esta versão não faz paginação automática de análise.

### 18.2 Validação, associações e dúvidas

`analise_documental.py` monta as referências exclusivamente a partir do atendimento/cartório autenticados, verifica classificação de caso e versões atuais e recusa referências de redação/arquivos desconsiderados. Texto nativo e OCR divergentes permanecem canais distintos. O provedor recebe cópia do contrato: modificar essa cópia não altera a entrada que o servidor usa para validar a evidência.

O servidor confere cada página, canal, versão, intervalo e trecho; exige valor literalmente contido no trecho, campo configurado e opção literal exata para campos enumerados. Um valor existente no texto pode continuar semanticamente errado: a validação **não prova interpretação, negação, identidade, autoria ou titularidade**. O contexto completo da unidade permanece junto da proposta e visível na ficha.

Uma sugestão de pessoa/imóvel só é mantida quando tipo/ID são compatíveis e a classificação humana da página tem destinatário exclusivo. Havendo vários destinatários, a associação é retirada, fica sem vínculo e gera dúvida; a afirmação original do provedor é preservada separadamente para auditoria. Referências inexistentes, pessoas de outro caso, tipo incompatível e associação automática a registro de papel/relação/negociação são recusados. Papéis e relações podem ter valores propostos, mas seus registros devem permanecer sem associação até escolha humana. Não se deduz cônjuge, representante ou papel por nome/estado civil.

Todos os valores divergentes para o mesmo registro/campo são conservados como propostas e geram dúvida; valores já informados ou confirmados não são sobrescritos. Registros sem vínculo não são agrupados por nome para comparar fatos. Propostas e dúvidas continuam bloqueando a redação pelo mecanismo existente. A IA não cria pessoas, papéis, relações, imóveis, revisões de dados nem decisões de confirmação.

Instruções de documentos são tratadas como dados. O pedido preparado separa instrução do sistema e JSON documental e não fornece ferramentas, consultas ou navegação. Há sinalização conservadora de alguns padrões suspeitos; unidades sinalizadas só admitem dúvidas. **Essa sinalização não é um detector completo de ataques**, e uma literalidade válida não transforma ordem maliciosa em dado verdadeiro. A barreira principal é o contrato fechado, a conferência de fonte/registro, a ausência de autoridade para alterar a ficha e a revisão humana obrigatória.

Dúvidas são persistidas pelo mecanismo de pendências, com fonte/contexto/histórico. Apenas a escrevente as resolve, com motivo e confirmação específica; para vincular uma dúvida, as revisões devem ser atuais, confirmadas e usar trecho dessa mesma unidade/página. Trocar leitura/classificação invalida propostas antigas **sem encerrar automaticamente as dúvidas**. Dúvida de análise histórica com fonte substituída exige decisão explícita de não usar aquela análise; a decisão não valida fatos nem libera dados afetados da ficha.

### 18.3 Atomicidade e provedor preparado

`POST /api/v1/atendimentos/{id}/analise-documental/` aceita somente o pedido acima. `GET` informa indisponibilidade e histórico das análises aceitas do próprio atendimento, com `Cache-Control: no-store`. Retornos: pedido inválido/referência de redação `400`; fonte inacessível `404` ou cartório não autorizado `403`; contexto/versão concorrente `409`; resposta inválida/recusa/incompleta `422`; provedor bloqueado/falha/timeout `503`.

Todo lote é validado antes de gravar. A persistência reserva o atendimento e remonta o contexto: documento, classificação, ficha ou modelo alterado durante a análise provoca recusa completa. Análise, propostas e pendências são gravadas na mesma transação; falha após criação das propostas desfaz tudo. Repetição bem-sucedida com mesmo identificador/autora/pedido retorna o resultado histórico sem nova análise; a validade atual das fontes deve ser consultada nas propostas. Falhas não geram análise parcialmente aceita nem correção automática da resposta.

`AnaliseDocumentalAtendimento` conserva entrada, resposta original que passou no contrato e resultado validado, assinatura, autoria e identificação de simulação. Campos novos de proposta guardam a análise e evidência estruturada. Migração `0022`, tabela incluída no inventário opcional de backup; cópia SQLite verificada antes de aplicar a migração em `.local/migration_safety/antes-extracao-documental-estruturada.sqlite3`. O banco de uso local não recebe as simulações dos testes.

`provedor_documental.py` prepara JSON Schema estrito e envelope Responses, sem persistência no provedor (`store: false`) e sem ferramentas; não contém transporte de envio. O parser offline recusa status incompleto/erro/recusa, saídas de ferramenta, mensagens inesperadas, JSON com chaves repetidas e contrato inválido. A preparação segue a [documentação oficial de Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs). Isso não constitui integração real homologada: compatibilidade do modelo configurado, SDK/transporte, autorização e comportamento real ainda precisarão de validação numa fase expressamente autorizada. Não houve consulta a chave, alteração de cobrança ou chamada ao provedor real.

### 18.4 Como testar e limitações

Na raiz do projeto:

```powershell
.venv/Scripts/python.exe apps/notarius-api/manage.py test tests.test_analise_documental --noinput
```

`tests/provedor_documental_simulado.py` contém respostas fictícias, sem transporte, acessíveis somente no contexto/banco dos testes. Os testes incluem sucesso sem escrita na ficha; papéis/pessoas/imóveis trocados; valor inventado; campo/opção inválida; fonte inexistente/canal/versão errada; omissões/duplicações; resposta vazia/recusa/incompleta; limites; instrução maliciosa; conflito de valores; várias páginas/OCR/página vazia; isolamento; idempotência; alteração durante análise; modificação da cópia de entrada; rollback após falha de persistência; confirmação/resolução por ação humana simulada; invalidação de fonte sem fechamento automático de dúvida.

No uso local, abrir Documentos mostra que a análise por IA está bloqueada e que a operação por rótulos é separada. Não há botão para ativar simulação no atendimento normal. Essa entrega valida a integração e seus limites com respostas fictícias, **não demonstra interpretação de documentos reais por IA**. Não detecta toda omissão semântica: cada unidade exige proposta ou dúvida, mas a decisão sobre conteúdo incompleto/negado, vínculo e interpretação pertence à escrevente. O padrão profissional continua aguardando definição/homologação; nenhum requisito documental ou jurídico novo foi aprovado pelo sistema.

### 18.5 Evidências de verificação

- **57 testes de integração passaram** na execução final (`.local/etapa4-verificacao-final.log`): 21 do contrato/adaptador documental e os testes existentes de propostas, pendências, interpretação local e organização de anexos. Os casos incluem a regra final de que fonte substituída não encerra dúvida sem decisão humana, bem como validação dos limites após acrescentar dúvidas derivadas pelo servidor.
- **69 testes de regressão passaram** (`.local/etapa4-regressao.log`): ficha, concorrência SQLite, migração do legado até `0022`, redação estruturada, atendimento/exportação e backup. Total: 126 testes nas duas execuções. Não foi necessário repetir o ensaio profissional integral de ambas as variantes, nem se declara um novo ensaio integral com provedor real.
- ESLint passou nos componentes de atendimento e biblioteca de propostas alterados. A checagem TypeScript global permanece com os erros anteriores fora do fluxo, sem erros apontados nas pastas de atendimento/bibliotecas verificadas. Django `check`, verificação de migrações pendentes e de espaços do diff sem erros.
- Verificação adicional da rota normal no caso fictício da etapa 3: `GET` informa indisponibilidade; `POST` válido retorna `503`, sem invocar o adaptador real, sem fallback e com as mesmas contagens de dados/propostas/minutas. **Zero análises documentais no banco de uso local**, antes e depois. Evidência em `.local/etapa4-bloqueio-normal.json`. As análises simuladas ficaram exclusivamente nos bancos descartáveis de teste.
- A conferência visual desta etapa **não foi concluída**: duas tentativas de abertura da página pelo navegador integrado terminaram sem conectar a janela. Não há nova captura visual e não se usa a captura da etapa 3 como prova da etapa 4. A indicação textual de IA bloqueada foi adicionada ao componente Documentos; a apresentação visual deve ser conferida manualmente ao abrir o aplicativo. Esse limite não altera as verificações automáticas do contrato/servidor.

## 19. Etapa 5 solicitada — comparação conservadora entre fontes

Comparação determinística dos dados já estruturados e vinculados, reaproveitando propostas, revisões da ficha, classificação de anexos, pendências e histórico. **Não há provedor de IA nem preferência automática por documento, mensagem ou ficha.** O texto original continua salvo; a representação normalizada existe apenas na resposta da comparação e no retrato das evidências consideradas na decisão.

### 19.1 Vínculos explícitos e fontes consideradas

`comparacao_fontes.py` agrupa exclusivamente por **ID do registro e chave do campo**, nunca por semelhança de nome, CPF ou endereço. Cada registro conserva seu tipo e seus vínculos humanos com pessoa/imóvel; negociações diferentes não são unificadas só por apontarem para o mesmo imóvel. Conteúdo legado amplo continua fora da comparação até haver derivação humana explícita para um registro detalhado, com cadeia de fonte preservada. Arquivo de referência de redação não passa a comprovar dados.

São exibidos o valor atual da ficha, evidências documentais/mensagens usadas explicitamente em suas revisões e propostas cujo registro/campo foi identificado pela escrevente. Trechos/valores distintos da mesma página permanecem separados. Revisões repetidas da mesma evidência literal são representadas por seu último uso; o histórico anterior continua disponível. Edições manuais antigas da própria ficha permanecem no histórico, sem criar automaticamente várias pessoas ou novas fontes concorrentes. Propostas rejeitadas saem da comparação ativa, preservando sua rejeição e justificativa no histórico.

Nova operação `associar` em `propostas-dados/`: escolhe **registro e campo**, exige justificativa, confirmação específica da associação, versão da decisão e, para documento, versão da organização. Não cria revisão de dado nem confirma o valor. Confere tipo/campo, cartório/atendimento, original atual e destinatários da página; impede uso de registro desativado e correção silenciosa de proposta que ainda sustenta dado atual. Correções de vínculo geram nova decisão versionada. A migração `0023` acrescenta campo escolhido e organização conferida à decisão de proposta; decisões antigas com revisão continuam identificadas pela chave dessa revisão, sem nova associação inventada.

`GET /api/v1/atendimentos/{id}/comparacao-fontes/` entrega grupos e fontes **sem vínculo**, com `Cache-Control: no-store`. Sugestão de pessoa/imóvel da análise documental não é vínculo humano e não entra automaticamente em grupo. Documento com titularidade/classificação alterada ou leitura substituída fica marcado como incerto, preservando os IDs/versionamentos originais; não é transferido para outra pessoa por nome. A comparação numérica/textual exclui evidências de vínculo, leitura ou formato incertos e as mantém visíveis para revisão.

### 19.2 Normalização e categorias

Política técnica versionada: `comparacao_conservadora_v1`. Não substitui interpretação, identidade, autenticidade ou regra jurídica homologada.

| Informação | Comparação e limites |
| --- | --- |
| Nome e texto livre | Unicode NFC, espaços e caixa para comparação. Preserva acentos, pontuação, ordem, abreviações e negações. `José` e `Jose` não são unificados. Nomes semelhantes não vinculam registros. |
| CPF | Aceita a forma de 11 dígitos ou a máscara padrão, retirando apenas separadores reconhecidos na representação de comparação. Formato/dígitos inconsistentes recebem aviso próprio e não são usados para concluir igualdade/divergência. CPF matematicamente consistente **não comprova identidade**. |
| RG/documento e matrícula | Mantém zeros iniciais e pontuação; não cria uma gramática jurídica universal para documento/registro. `AB-001` e `AB001`, ou `00123` e `123`, permanecem diferentes. Matrícula isolada não identifica automaticamente o imóvel. |
| Preço | Reconhece números inteiros/formatos brasileiros com fração de duas casas, mantendo a indicação explícita de moeda. `R$ 1.000,00` e `R$ 1000,00` têm representação equivalente. Não inventa moeda para valor sem indicação. Formato ambíguo como `1.234` sem indicação suficiente fica não comparável, sem adivinhar convenção. O valor salvo/exportado continua o original, nunca o decimal normalizado. |
| Pagamento e opções de campos | Conserva previsão, declaração de realização e negações como valores diferentes. Ajusta só espaços/caixa na representação de comparação; não converte condição, declaração ou modelo em pagamento efetuado, consulta ou assinatura. Opções são as do campo configurado. |

Categorias separadas e acumuláveis: **ausente no registro**, **formato/dígitos inconsistentes**, **leitura incerta/substituída**, **vínculo incerto/desatualizado**, **valores divergentes**. Divergência automática exige ao menos dois valores comparáveis diferentes do mesmo registro/campo; texto ilegível não é tratado como fato divergente. Marcação humana de divergência permanece sinalizada. Ausência de valor/leitura não significa inexistência do fato.

Campo opcional explicitamente ausente, sem outra evidência relevante, não se transforma em nova exigência. Obrigações de preencher vêm somente da configuração do modelo ou de seus marcadores efetivamente vinculados. Quando uma conferência anterior precisa ser encerrada para campo opcional ausente, admite decisão humana justificada de manter o campo sem uso, considerando todas as evidências. Essa decisão não declara inexistência do fato. Se a configuração/modelo passar a exigir o campo, a conferência reabre e a dispensa anterior não o libera para redação.

### 19.3 Resolução, histórico e minuta

As diferenças entram no mecanismo existente como pendências de `comparacao_fontes`. Para resolvê-las, a escrevente deve conferir o conjunto atual, selecionar **a revisão atual confirmada daquele registro e campo**, justificar a escolha e identificar todas as evidências consideradas, inclusive as não escolhidas. Se preferir outro valor, deve corrigi-lo/confirmá-lo na ficha primeiro, preservando fonte e original; o comparador não copia uma alternativa por conta própria. Dado escolhido ausente/inválido, revisão de outra pessoa/campo, conjunto incompleto de evidências e assinatura/versão antiga são recusados. Campo obrigatório não admite a decisão de mantê-lo ausente e sem uso.

A resolução conserva autora, justificativa, revisão/valor escolhidos (ou decisão específica de não usar campo opcional), IDs e retrato das evidências com originais, representação normalizada, arquivo/mensagem, página, leitura, canal, trecho e vínculos/versionamentos. O histórico da pendência mostra as fontes consideradas na decisão. Não confirma nem rejeita outras propostas individualmente; as demais pendências do atendimento continuam exigindo suas decisões específicas.

Nova evidência vinculada, valor corrigido, fonte reclassificada, releitura ou alteração da regra do modelo modifica o contexto da conferência e reabre a decisão anterior quando ela já não cobre o conjunto atual. Leitura/associação antiga não é aceita automaticamente. As assinaturas existentes de documentos, mensagens, revisões, decisões e histórico desatualizam a minuta e bloqueiam preparação/exportação; resolver a comparação **não revalida uma versão antiga da minuta**. O bloqueio é conservador por atendimento: não se altera outro atendimento/cartório, nem se tenta provar que mudança em um campo seria irrelevante para a minuta inteira.

### 19.4 Como testar na interface

Abrir **TESTE FICTÍCIO — comparação de fontes etapa 5** (`34bf4acb-c3ef-4494-ad34-fae5bc4e96a6`) → **Conversa → Pendências por registro e histórico → Comparar fontes por registro**.

O cenário contém duas pessoas de nomes próximos, imóvel e negociação fictícios; quatro grupos de diferenças (CPF, matrícula, preço e situação de pagamento); e uma mensagem de nome deixada **sem vínculo mesmo coincidindo com o segundo participante**. Dados e associações são expressamente simulados no roteiro: **zero dados confirmados, zero modelos aprovados, zero minutas**. Não houve análise de IA nem chamada externa para preparar o cenário.

1. Conferir as fontes lado a lado: original, valor considerado e representação técnica separados, com suas situações/fontes. Em tela estreita os cartões são empilhados.
2. Na fonte sem vínculo, usar **Identificar registro e campo para comparar**. Nenhuma pessoa vem pré-selecionada; conferir ID/registro, campo e justificativa. O vínculo não confirma o valor. Vínculos já registrados podem ser revistos com justificativa e proteção de versão.
3. Abrir **Ver conferência e registrar decisão** em um grupo divergente. Corrigir/confirmar o dado na ficha quando necessário, selecionar sua revisão válida e marcar todas as evidências consideradas antes de registrar a decisão. O servidor repete as verificações, mesmo se a interface for contornada.
4. Acrescentar fonte fictícia com outro valor e vinculá-la explicitamente ao mesmo registro/campo. A conferência anterior deve reabrir e a minuta anterior deve ficar desatualizada. Repetir com leitura nova para verificar preservação da página e decisão históricas. Uma fonte de outra pessoa/imóvel não pode ser incluída por semelhança de nome.

Implementação de tela: `ComparacaoFontes.tsx` e extensão de `PendenciasFicha.tsx`, preservando as três áreas principais. Estado e consultas são isolados por atendimento, usuário e cartório. Os painéis usam a mesma ficha atualizada dos formulários, conservam os tokens abertos para detectar concorrência e mostram o histórico da decisão com evidências. Cópia SQLite verificada antes da migração em `.local/migration_safety/antes-comparacao-fontes.sqlite3`.

### 19.5 Verificações e limites remanescentes

- **49 testes passaram** na bateria final de comparação, pendências, propostas e redação estruturada (`.local/etapa5-entrega-final.log`), incluindo 13 testes novos de comparação com múltiplas verificações de CPF, nome, RG/documento, matrícula, preço e pagamento; equivalência apenas de formato; não associação por nome; evidência original preservada; trechos diferentes da mesma página; derivação legada com arquivo/página/leitura visíveis; categorias de incerteza; registro de decisão com todas as evidências; ausência opcional versus exigência configurada; reabertura após evidência/releitura; isolamento e versões; minuta antes exportável recusada com `409` depois de nova fonte.
- **82 testes de regressão passaram** (`.local/etapa5-regressao-final.log`): contrato/provedor documental bloqueado, ficha/concorrência SQLite/migração até `0023`, atendimento/exportação, organização de anexos e backup. Total das duas baterias: **131 testes**. Fixtures antigas foram ajustadas para selecionar a regra de campo correta entre as novas pendências e usar preço fictício numérico em teste que anteriormente usava o texto `VALOR FICTÍCIO`; a comparação não foi afrouxada para aprovar esse texto como preço. O teste de exportação foi corrigido para esperar a recusa de versão `409`, em vez de erro genérico `400`.
- ESLint dos componentes alterados, Django `check`, migrações pendentes e verificação de espaços do diff sem erros. Checagem TypeScript global mantém erros anteriores fora das pastas verificadas de atendimento; não se declara build global limpo.
- Tela exercitada no navegador local: fonte de nome sem vínculo apesar de coincidir com pessoa cadastrada; preço e pagamento com valores originais/representações em duas colunas; distinção de informação e proposta ainda não confirmadas. Captura própria desta etapa: `.local/qa-etapa5-fontes.png`. Cenário fictício auditado em `.local/etapa5-caso-ficticio.json`: quatro grupos divergentes, uma proposta sem vínculo, zero dados confirmados, zero modelos aprovados e zero minutas. Nenhum provedor externo foi invocado.

Limitações: comparação dos valores estruturados explicitamente vinculados, não interpretação integral de documentos livres. Não identifica todas as contradições semânticas nem valida identidade, autenticidade, titularidade ou cumprimento jurídico. Variações de formato fora da política suportada exigem revisão, sem reescrever o original. Rejeições de propostas e outras dúvidas continuam separadas da decisão da comparação; não há aprovação coletiva implícita. Minuta e requisitos profissionais continuam dependentes do modelo e das decisões a homologar pela escrevente. Concorrência real PostgreSQL e validação de produção permanecem fora desta prova local.


## 20. Etapa 6 solicitada — conversa orientada pelas pendências

### 20.1 Entregue e reaproveitado

A conversa usa o mesmo conjunto de conferências, propostas, vínculos documentais e ficha detalhada das etapas anteriores. `conversa_orientada.py` reúne um roteiro determinístico em `GET /api/v1/atendimentos/{id}/roteiro-conversa/`, sem provedor: informa quantas mensagens, documentos, propostas, pessoas e imóveis foram recebidos, todas as pendências ainda abertas e a próxima tarefa. Recebimento não significa leitura suficiente, interpretação correta ou confirmação. A interface identifica a orientação como **local por regras, sem IA real**.

`conferencia.py` acrescenta destino explícito às perguntas: ID de pendência, registro, campo, proposta, mensagem, arquivo/página, trecho e tarefa. A ordem inicia pela organização e leitura documental, depois revisão de propostas/campos e vinculação ao modelo. Perguntas resolvidas não entram nessa lista; alteração de evidência pode reabri-las pelas regras já existentes. Os contadores incluem o histórico recebido, inclusive mensagens corrigidas; não representam quantidade de dados válidos.

`PerguntasConferencia.tsx` encaminha a pergunta para o arquivo e a página corretos em `AnexosConversa.tsx`, para um formulário curto de campo em `FichaDetalhada.tsx`, para a pendência específica em `PendenciasFicha.tsx`, ou para a aba Minuta. Não pré-seleciona pessoa por nome nem escolhe vínculo de proposta incerta. A ação **Acrescentar participante** abre criação curta de pessoa com ID próprio; os dados e papéis são preenchidos separadamente. Conteúdo livre continua usando apenas a interpretação local explícita existente; trechos desconhecidos e tarefas de análise preservam o texto literal e oferecem conferência manual. Não há chat de IA livre nesta etapa.

### 20.2 Correção de respostas e proteção das fontes

A ação **Opções desta mensagem → Corrigir esta resposta** registra outra mensagem, com autora, justificativa e referência à original, em `POST /mensagens/{id}/corrigir/`. A original não é editada nem apagada. Migração `0024` adiciona vínculo único para impedir bifurcação de correções; a cadeia pode continuar corrigindo a última resposta. Identificador de envio torna repetição idêntica idempotente e rejeita seu reaproveitamento com outro conteúdo/autora. Reserva de escrita do atendimento, transação e tratamento de disputa SQLite preservam a proteção existente contra concorrência.

Uma mensagem corrigida deixa de ser fonte atual. `dependencias_ficha.py`, `ficha_estruturada.py`, a ficha legada e `propostas_dados.py` recusam seu uso como fonte vigente. Revisões e propostas anteriores continuam visíveis no histórico; seus valores não são substituídos pela correção. Os dados afetados voltam à revisão e a minuta anterior perde atualidade. A comparação conserva também a evidência antiga com indicação de fonte desatualizada. A análise documental verifica o contexto das mensagens antes de aplicar qualquer resultado: uma correção durante a análise causa recusa integral, sem propostas parciais.

### 20.3 Rascunhos e retomada

Os três painéis continuam montados durante a navegação. O corpo da página e as consultas são separados por atendimento, usuária e cartório. O novo `lib/rascunhoSessao.ts` guarda rascunhos em `sessionStorage` da **mesma aba do navegador**, com chave desses três identificadores, validação e limite de tamanho. Falha de armazenamento/recuperação aparece em aviso; não há truncamento silencioso.

São recuperáveis após recarregar: mensagem ainda não enviada e sua tentativa idempotente; correção não enviada; campos/criação da ficha; texto do modelo e motivo; edições por versão de minuta. Os rascunhos da ficha conservam modelo, versão do campo, assinatura de contexto e versões de fonte/proposta originais: retomá-los não autoriza sobrescrever alteração concorrente. Rascunhos de campos distintos são preservados separadamente. As marcações de confirmação de dado, fonte, associação e aprovação de modelo **não são restauradas**. Um campo cujo rascunho tinha situação desejada “confirmado” exige novamente as marcações antes de salvar.

Mensagens e versões efetivamente salvas continuam no servidor e podem ser retomadas com nova sessão autenticada. Rascunhos locais não são dados confirmados, histórico do servidor ou backup; normalmente se encerram ao fechar a aba e não sincronizam entre navegadores/dispositivos. Formulários auxiliares de decisões mantêm estado ao trocar de aba, mas a recuperação após recarregar cobre os editores principais enumerados acima. As únicas áreas principais permanecem **Conversa, Documentos e Minuta**.

### 20.4 Roteiro verificável na interface

Usar o atendimento **TESTE FICTÍCIO — comparação de fontes etapa 5** (`34bf4acb-c3ef-4494-ad34-fae5bc4e96a6`), reaproveitado como prova local, sem aprovar dados/modelos reais.

1. Em Conversa, conferir os totais recebidos, a indicação “sem IA real”, a próxima tarefa e **Ver todas as pendências**. Uma pergunta de página deve abrir o documento certo por **Conferir página do documento**, preservando o original. **Registrar revisão manual desta fonte** abre diretamente a pendência daquela página; a decisão permanece sujeita às propostas, revisões e evidências exigidas pelo servidor.
2. Escrever sem enviar, alternar Documentos/Minuta/Conversa e recarregar. O texto deve reaparecer; a quantidade de mensagens salvas não deve aumentar.
3. Usar **Acrescentar participante**, informar motivo de teste e criar. Conferir o ID separado e campos ausentes. Preencher um campo sem salvar, usar **Guardar rascunho e voltar**, recarregar e **Retomar rascunho … sem confirmar**. Valor/motivo devem voltar, confirmações desmarcadas. **Descartar só este rascunho local** não apaga dados salvos.
4. Abrir as opções de uma mensagem fictícia e registrar correção com motivo. Conferir a original e a nova no histórico. Campo que usava a original exige revisão explícita; nenhum dado deve mudar de valor sozinho. Duas tentativas de corrigir a mesma mensagem não podem gerar ramos concorrentes.
5. Em Minuta, alterar um rascunho fictício sem salvar/aprovar, voltar, recarregar e reabrir **Revisar modelo**. Texto/motivo devem voltar sem aprovação. Uma versão anterior desatualizada não pode ser exportada por retomar seu rascunho.
6. Trocar para outro atendimento/cartório autorizado e conferir que o rascunho anterior não aparece. Ao voltar ao mesmo contexto na mesma aba, ele continua disponível.

A prova visual acrescentou o registro vazio de pessoa `4c9a2297-a4fa-4e30-b9af-7d9673c7b217`, com justificativa explícita de teste. Também registrou uma mensagem explicitamente fictícia e sua correção justificada, preservando a original. Foram auditadas 13 mensagens, 1 documento, 5 propostas, 3 pessoas, 1 imóvel e 21 pendências; zero dados confirmados, modelos aprovados, minutas e análises documentais no cenário local (`.local/qa-etapa6-auditoria.json`). Rascunhos locais não foram usados para confirmar a ficha ou aprovar modelo. O cenário continua bloqueado pelas suas pendências reais de teste; não foi artificialmente completado para a demonstração.

### 20.5 Verificações e limites

`tests/test_conversa_orientada.py` cobre recebimento e destino por ID, incerteza explícita, preservação literal de espaços, correção aditiva/idempotente, disputa de correções, recusa entre atendimentos/cartórios, nova sessão autenticada, invalidação de fonte confirmada sem reescrita, proposta histórica de mensagem corrigida, mudança de conversa durante análise e percurso com **provedor simulado exclusivo do banco de testes** até revisão final e exportação Word. Confirmações e modelo usados nessa prova são explicitamente simulados; não homologam o padrão profissional.

O ensaio integral antigo usa originalmente CPFs inválidos e preço com prosa para demonstrar dados fictícios. A comparação conservadora passou a bloquear corretamente essas entradas. O teste de exportação integral agora prepara apenas no banco de testes CPFs sintéticos com dígitos matematicamente consistentes e preço numérico, preservando os avisos fictícios. O ensaio também registra a decisão específica das comparações que abriram durante a interpretação divergente: corrigir e confirmar um campo não encerra automaticamente essa conferência. Não se alterou a comparação, a preparação local dos cenários ou a exigência de revisão humana. Consistência de CPF não comprova identidade.

Resultados finais desta etapa:

- Bateria ampliada inicial: **148 testes**, com 147 casos passando e duas falhas de subcasos no único ensaio integral antigo (`.local/etapa6-regressao.log`). As correções descritas acima foram feitas exclusivamente na preparação e nas decisões simuladas desse teste, sem afrouxar o produto.
- Bateria final de conversa e propostas: **20 testes passaram**, incluindo os **8 novos testes de conversa** (`.local/etapa6-conversa-final.log`). Inclui acesso da mesma usuária a dois cartórios autorizados, com leitura/correção cruzadas recusadas por `404`.
- Repetição do ensaio integral: **1 teste passou com as duas variantes**, participação direta e procuração, revisão final, Word/PDF com o texto salvo e bloqueio após releitura (`.local/etapa6-integral-final.log`). O percurso adicional com provedor simulado está entre os oito novos testes. Entre as baterias, foram cobertos **151 testes distintos**; não se trata de uma execução única com 151 casos.
- Django `check` e verificação de migrações sem problemas; diff sem erros de espaço. ESLint dos componentes de atendimento e bibliotecas alteradas sem erros ou avisos. Nos dois contêineres de layout/cabeçalho, zero erros e três avisos anteriores de variáveis/importações sem uso. TypeScript não apontou erros nas áreas alteradas; a checagem global ainda acusa erros anteriores em outras telas e Cypress, registrados em `.local/etapa6-types.log`. Não se declara build global limpo.
- Navegador local: troca de abas e recarga preservaram mensagem, campo, modelo e correção não enviada; as confirmações de campo/fonte e aprovação não voltaram marcadas. Outro atendimento ficou sem os rascunhos deste caso; voltar ao contexto original os recuperou. Foram exercitados criação de participante com ID próprio, abertura da página correta, acesso direto à decisão manual e correção mantendo a original. Nenhuma decisão foi registrada na pendência de página durante a prova visual. Evidência adicional: `.local/qa-etapa6-revisao.png`.

Cópia SQLite anterior à migração, verificada por integridade: `.local/migration_safety/antes-conversa-orientada.sqlite3`. Migração aplicada e serviço local reiniciado. Capturas: `.local/qa-etapa6-rascunho.png` e `.local/qa-etapa6-conversa.png`. Ajuste mínimo de encolhimento dos contêineres do layout/cabeçalho permite acomodar os formulários na janela estreita, sem alterar as áreas ou ações do fluxo.

Limites: orientação determinística, sem interpretação livre ou provedor externo; simulado apenas em testes, sem fallback normal. A minuta profissional continua dependente do texto e das regras a homologar pela escrevente. Não foram criadas exigências jurídicas/documentais. Reabrir conferência e desatualizar minuta continua conservador no atendimento inteiro. Concorrência de produção/PostgreSQL e sincronização de rascunhos entre dispositivos não foram demonstradas nesta etapa.


## 21. Etapa 7 solicitada — minuta baseada na ficha detalhada

### 21.1 O que foi reaproveitado e ampliado

O preenchimento por posições da ficha, seus vínculos, exigências configuradas, histórico imutável de modelos/minutas, edição manual, comparação, revisão final e Word/PDF já existiam. Foram preservados. A ampliação usa o texto versionado do próprio modelo, inclusive quando copiado para a biblioteca: não há outro repositório paralelo de regras nem migração de banco nesta etapa.

`blocos_minuta.py` acrescenta uma gramática restrita e limitada, sem Jinja, Python, eval, chamadas externas ou redação de IA. `redacao_estruturada.py` valida e preenche as posições; `pendencias_ficha.py` e `comparacao_fontes.py` reconhecem também referências de condições e de repetições, incluindo campos exigidos que não aparecem literalmente no texto final. `redacao.py` mantém a barreira conservadora contra possíveis afirmações de acontecimentos no texto fixo e recusa diretivas em modelo legado por blocos amplos.

As posições de pessoas, papéis, relações, imóveis, negociação, ato e complementos continuam explicitamente vinculadas a registros do atendimento, com seus tipos e vínculos conferidos. Não se deduz papel, representação, cônjuge, identidade ou titularidade por nome, estado civil ou ordem de documentos. A lista de repetição escolhe posições na ordem desejada; não pesquisa pessoas nem agrupa participantes automaticamente por nomes/papéis. Duas posições da mesma repetição não podem apontar para o mesmo registro.

### 21.2 Contrato de blocos e interrupções

As diretivas ficam preservadas na versão do padrão e desaparecem do texto preenchido. Marcadores repetidos comuns continuam funcionando. A forma de configuração técnica é:

```text
{% repetir qualificacao vendedor1,vendedor2 %}Nome informado: {{item.nome}}
{% fim %}

{% se previsao {"campo":"negocio.situacao_pagamento","permitidos":["previsto","declarado_realizado"],"incluir":["previsto"]} %}TEXTO FICTÍCIO PARA REVISÃO: {{negocio.condicoes}}{% fim %}
```

O segundo exemplo ilustra a gramática, não valida opções do campo nem define cenário profissional: somente os valores aplicáveis à ficha e ao padrão homologado podem ser utilizados. O modelo fictício executável entregue admite apenas `previsto` para a condição de pagamento; trocar para `declarado_realizado` interrompe a preparação. Não afirma pagamento, consulta ou assinatura. Os papéis vendedor/comprador também são controlados por condições explícitas daquele exemplo.

- **Repetir:** identificador único e até 60 posições explícitas distintas, todas do mesmo tipo; o corpo usa ao menos um marcador `item.campo`. A referência é expandida para cada posição real, mantendo a ordem e a fonte individual. Não há cardinalidade ilimitada nem descoberta automática de participantes.
- **Se:** identificador único, campo `posição.campo`, lista literal de alternativas do cenário e subconjunto que inclui o bloco. O campo precisa estar confirmado, com fonte/dependências atuais. Valor confirmado dentro das alternativas, mas fora do subconjunto de inclusão, omite somente aquele trecho e registra o resultado. Valor fora das alternativas **interrompe a operação inteira para decisão da escrevente**; ausência e leitura/vínculo incertos não são interpretados como condição falsa. `a_esclarecer` e `pendente` não são alternativas aprovadas.
- **Limites:** até 60 blocos, 20 alternativas por condição, 500 caracteres por alternativa, 3.000 referências expandidas e 150.000 caracteres de saída. Chaves duplicadas, tipos errados, identificadores/campos/posições inexistentes, comandos desconhecidos, fechamento ausente, blocos aninhados e estouro de limite são recusados, sem truncamento ou minuta parcial. As diretivas de abertura/fechamento são reservadas e não podem ser inseridas como comandos provenientes de dados do caso.

Nesta primeira gramática a condição compara **um campo, de forma literal e exata**. Não há expressões livres, flexão automática de gênero/número, conjunções lógicas ou blocos aninhados. Casos que dependam disso precisam de variante explícita e revisão profissional, sem texto gerado para completar a lacuna. Conservadoramente, **todos os campos citados no modelo precisam estar confirmados, inclusive os de blocos omitidos**. Posições opcionais ou referências desconhecidas não são silenciosamente dispensadas. A escrevente define o cenário e as exigências; essas limitações não constituem regras jurídicas.

### 21.3 Separação e rastreabilidade

Texto fora dos blocos pertence ao padrão fixo versionado e exige revisão profissional integral. Valores variáveis vêm das revisões confirmadas da ficha; condições e destinos vêm da configuração expressamente aprovada pela escrevente, jamais da IA. As cláusulas/declarações aplicáveis precisam ser fornecidas pela profissional e colocadas em blocos com a condição pertinente. Não se utiliza o modelo como prova de fatos. A barreira lexical de acontecimentos é mantida, inclusive no conteúdo de blocos condicionais/repetidos; ela é conservadora e **não identifica juridicamente toda cláusula ou contradição no texto fixo**. A homologação deve classificar e revisar esse conteúdo; não se promete validação jurídica automática.

Cada dado utilizado conserva original, valor revisado, revisão/versão, registro/tipo, fonte literal, arquivo/mensagem/página/leitura, confirmação humana, dependências e IDs de modelo/vinculação. Inserções repetidas acrescentam identificador da repetição, posição e índice; os intervalos no texto final são verificáveis. O dado que controla uma condição conserva também identificador do bloco, configuração, valor confirmado, resultado incluído/omitido e versão do modelo. Dado usado apenas como condição aparece como tal, sem inserção literal fictícia. Valores verificados apenas para exigir completude de bloco omitido não são apresentados como inserções na minuta.

A edição manual continua criando versão própria, preservando o retrato de fontes e decisões da base. A interface avisa que decisões e intervalos pertencem ao preenchimento de base e não validam semanticamente o texto editado. A comparação literal detecta mudanças no texto e no retrato dos dados/decisões. Revisão final expressa continua obrigatória antes de exportar a versão salva; alteração de fonte/dado/modelo desatualiza a minuta e impede reutilizar aprovação anterior.

### 21.4 Modelo fictício e lista objetiva para a escrevente

O padrão profissional **continua não homologado**, conforme decisão anterior da usuária. `modelo_ficticio_estruturado.py` entrega somente uma demonstração marcada **MODELO FICTÍCIO DE TESTE — SEM VALIDADE PROFISSIONAL**, com duas pessoas, dois papéis, imóvel, negociação, repetição e condições de papéis/pagamento. Não é transcrição da escritura, minuta profissional completa, lista de exigências legais nem fonte comprobatória. Não foram inventadas cláusulas para completar a entrega.

Antes de uso profissional, a escrevente precisa fornecer ou aprovar:

1. **Redação integral do padrão** e identificação da versão/responsável por homologá-la. Partes rasuradas das imagens não podem ser reconstruídas por suposição.
2. **Cenários cobertos:** participação direta, representação, quantidade de pessoas/imóveis e demais variações aceitas. Definir quando interromper e exigir outra variante, sem presumir poderes ou relações.
3. **Posições e vínculos:** quem ocupa cada posição, como se relacionam pessoas/papéis/imóvel/negociação e a ordem exata das repetições. Definir a destinação dos registros fora da minuta com decisão expressa.
4. **Campos de qualificação e exigências do modelo:** campos obrigatórios, requisitos documentais e dependências a homologar. Consistência de CPF não comprova identidade; o sistema não cria exigência jurídica por conta própria.
5. **Cada cláusula/declaração condicional:** texto integral aprovado, campo que a controla, alternativas do cenário e alternativas que permitem incluí-la. Outros valores devem interromper; falta de leitura/informação não significa inexistência do fato.
6. **Separação entre padrão e acontecimentos:** identificar o que é apenas estrutura fixa e o que exige dado do caso e fonte expressamente confirmada, especialmente pagamento/quitação, consultas e assinaturas. Não deixar acontecimentos do exemplo no texto fixo.
7. **Tratamento das exceções não expressáveis nesta gramática:** variantes necessárias para múltiplas condições, posições opcionais e concordância/redação. Não há preenchimento livre para contornar a falta de configuração.
8. **Critérios e responsabilidade da revisão final:** conferência de dados, fontes, decisões de blocos, edição manual, comparação e autorização de uso da versão exportada.

### 21.5 Como testar

Abrir **TESTE FICTÍCIO — minuta com condições e repetições etapa 7** (`367a49e7-1954-428d-a11d-62c20906a55f`). É um atendimento novo de demonstração no cartório fictício, sem alterar as provas anteriores. Contém seis registros separados, oito campos informados com mensagens de origem, **zero dados confirmados, zero modelos aprovados e zero minutas**. Auditoria em `.local/qa-etapa7-caso.json`.

1. Em **Minuta → Revisar modelo**, conferir o aviso fictício e o modelo v1 em rascunho. **Preparar minuta** permanece bloqueado.
2. Expandir **Blocos condicionais e repetições explícitas**. O formulário permite escolher posição/campo/alternativas, texto fornecido para revisão ou posições em ordem para repetição. Acrescentar altera apenas o rascunho e desmarca aprovação; salvar exige motivo e nova versão. **Carregar modelo fictício com condições e repetições** também apenas altera o rascunho, sem confirmar dados nem aprovar modelo.
3. Nas provas automatizadas isoladas, simular revisão explícita dos dados/modelo/vínculos. Conferir que nomes próximos, papéis, imóvel e pagamento não são trocados; condições verdadeiras incluem seu trecho, alternativas falsas previstas omitem e registram o motivo; valores fora do cenário, papel trocado ou campo sem confirmação interrompem sem salvar versão parcial.
4. Em uma minuta preparada de teste, abrir **Conferir dados utilizados** para fontes, repetições e decisões. Editar, comparar, revisar e exportar: o arquivo deve conter o texto da versão salva, e a rastreabilidade da base continua identificada. Releitura/correção não pode revalidar uma minuta antiga.

A interface foi exercitada no navegador local: seleção explícita de posição, inclusão de bloco fictício apenas no rascunho, aprovação desmarcada e preparação bloqueada. O rascunho adicional de QA foi descartado sem modificar o modelo v1 salvo. Evidências visuais: `.local/qa-etapa7-blocos.png` e `.local/qa-etapa7-minuta.png`.

### 21.6 Verificações e limites remanescentes

- **89 testes passaram** na bateria de blocos, redação estruturada, comparação entre fontes, pendências, revisão final, comparação de minutas, biblioteca e atendimento (`.local/etapa7-regressao.log`).
- **12 testes novos passaram** na bateria final específica (`.local/etapa7-blocos-final.log`), incluindo contrato inválido/malicioso, limites de configuração, repetição por IDs, nomes próximos, papéis trocados, fonte/condição confirmada, omissão registrada, valor fora do cenário, mesma pessoa duplicada na repetição, campos exigidos mesmo em bloco omitido e exemplo fictício sem aprovação automática. O percurso com edição/comparação/revisão/Word/PDF conserva as decisões de blocos e o texto salvo. Entre as baterias são **92 testes distintos**, pois a primeira já continha nove dos novos testes.
- ESLint dos componentes de atendimento e DTO alterados sem erros/avisos; Django `check`, verificação de migrações e espaços do diff sem erros. TypeScript não apresentou erros nas áreas de atendimento alteradas; a checagem global mantém erros anteriores fora desse fluxo, registrados em `.local/etapa7-types.log`. Não se declara build global limpo.
- Nenhuma migração foi necessária; o serviço local foi reiniciado com o código atualizado. Os testes usam exclusivamente banco isolado e decisões explicitamente simuladas, sem homologação profissional nem provedor externo.

Limites: gramática restrita e verificações locais, sem IA real, interpretação jurídica ou autenticação de fatos/documentos. Ainda não existe padrão profissional homologado. Não há regra automática que reconheça toda cláusula ou garanta a correção de texto fixo; a redação integral, classificação de trechos e regras de aplicação dependem da escrevente. As restrições de condições simples, participantes explícitos e completude de campos estão expostas no formulário e neste documento.


## 22. Etapa 8 solicitada — teste integrado da função principal

### 22.1 Percursos, resultados e distinção das provas

`tests/test_funcao_principal_integrada.py` acrescenta nove percursos fictícios e um teste de rótulos/isolamento. Foram percorridos: compra e venda simples; vários vendedores e vários compradores em subcasos separados; cônjuge explicitamente informado sem inferência por estado civil; representação com dúvida e decisão humana simulada; dois preços documentais divergentes; PDF com página sem texto e falha simulada de OCR; condição de pagamento ausente; pagamento futuro sem quitação; e correção depois de preparar, editar, revisar e exportar a minuta.

Cada percurso concluído utiliza upload, original preservado, classificação expressa, propostas do provedor simulado exclusivo do banco de testes, associação e confirmação simuladas, revisão de páginas, perguntas/bloqueios, vinculação ao modelo fictício, retomada com novo cliente autenticado, preenchimento literal/rastreável, edição com motivo, comparação, revisão final e exportação Word/PDF com conferência do texto salvo. A divergência inclui proposta local por rótulo explicitamente vinculada à negociação a partir de documento organizado no imóvel. Não houve escolha de valor por IA. A página sem texto não foi recuperada: a cópia sem uso nos dados só deixou de bloquear após decisão humana simulada de não utilizá-la, sem declarar inexistência de fato.

**143 testes passaram** na bateria final (`.local/etapa8-regressao-final.log`): integração, conversa, blocos, redação, comparação entre fontes, pendências, anexos, análise documental bloqueada, atendimentos, ficha, isolamento, versões, migração e concorrência SQLite. São dez testes novos entre os 143, incluindo os nove percursos; o caso com múltiplos participantes tem dois subcasos. O primeiro ensaio de divergência encontrou erro no próprio roteiro: tentou classificar documento na negociação e recebeu 404. O roteiro passou a usar vínculo documental no imóvel e associação da proposta ao campo da negociação; a proteção não foi afrouxada.

Não se apresenta essa prova como decisão da escrevente, homologação profissional ou IA real. Aprovações/confirmações e revisão final positivas foram simuladas em banco isolado. O provedor real permanece bloqueado, sem chamada externa ou fallback silencioso. Não se alteraram cobrança, credenciais ou chave de API.

### 22.2 Inspeção da interface e correções

A navegação local examinou as três áreas, participantes múltiplos, leitura parcial, fonte/preço divergente e abertura/reabertura dos atendimentos, usando janela estreita. Foram corrigidos:

- Rótulos de pessoas, papéis, relações, imóveis e negociação: `rotulos_ficha.py` usa exclusivamente valores salvos e vínculos explícitos por ID. Nomes registrados e pessoa/imóvel vinculados aparecem na ficha, conversa, pendências, comparação e seletor da minuta, conservando o identificador. Rótulo não confirma identidade nem cria relações. Menus quebram nomes longos em linhas, sem cortá-los horizontalmente.
- Em `VinculacaoMinuta.tsx`, a usuária escolhe primeiro cada posição; os motivos de exclusão só aparecem para registros que sobram depois das escolhas completas. Salvar exige todas as posições, motivos necessários, confirmação da revisão e modelo aprovado. Nenhuma seleção automática foi introduzida.
- Em `AnexosConversa.tsx`, o botão que apenas fechava a leitura foi renomeado de “Voltar à conversa” para **Fechar leitura**, correspondendo à sua ação real.
- No carregamento inicial, havia diferença entre HTML do servidor e primeira renderização do cliente: um estilo global aparecia onde a área protegida esperava a tela de espera. `providers/ThemeProvider.tsx` instala esse estilo global após a primeira renderização compatível, sem suprimir avisos ou modificar autenticação. O servidor da interface foi reiniciado para carregar a alteração; o HTML inicial passou a não conter aquele estilo global e a recarga observada deixou de mostrar o erro.
- O roteiro antigo em `docs/teste-escrevente/ROTEIRO.md` foi marcado como histórico e aponta ao roteiro vigente, evitando instruções contraditórias sobre OCR e revisão final.

Django `check`, verificação de migrações e espaços do diff sem erros. Não houve migração. ESLint dos componentes/bibliotecas alterados e do provedor de tema sem erros/avisos; a checagem TypeScript das áreas alteradas não apontou erros. A checagem global ainda mantém problemas anteriores fora do fluxo de atendimento (`.local/etapa8-types.log`); não se declara build global limpo. Evidências visuais em `.local/qa-etapa8-participantes.png`, `.local/qa-etapa8-leitura.png` e `.local/qa-etapa8-divergencia.png`.

### 22.3 Material entregue e exercícios locais

- **Roteiro curto para a mãe/escrevente:** `docs/teste-integrado-etapa8/ROTEIRO_PARA_MAE.md`, com sete tarefas e orientação para parar/anotar dúvidas em vez de liberar botões por tentativa.
- **Relatório completo:** `docs/teste-integrado-etapa8/RELATORIO_ETAPA8.md`, com matriz dos cenários, falhas/correções, distinção entre simulações e verificações locais, catálogo dos exercícios e avaliação real pendente.
- **Documentos inteiramente fictícios:** `docs/teste-integrado-etapa8/arquivos/`. Os TXT têm nomes/valores de teste; o PDF tem uma página de texto e uma página deliberadamente em branco. Não representam amostra real de documento ilegível ou exigência notarial.
- **Nove atendimentos de demonstração**, títulos `TESTE FICTÍCIO 8.01` a `8.09`, no cartório fictício existente. Catálogo e auditoria final: `.local/etapa8-catalogo.json` e `.local/etapa8-auditoria-final.json`. Total: 25 documentos e 25 propostas locais por rótulos; zero dados confirmados, zero modelos aprovados, zero minutas, zero análises de IA e zero vinculações de minuta salvas pelo agente nesses exercícios.

O início recomendado é o atendimento simples `caefe3c0-5620-49d1-9d8c-6c95e1260f3f`. O relatório contém os nove links. O exercício de correção deve ser preparado/revisado expressamente pela usuária antes da correção acompanhada; não foi fabricada aprovação no banco local para fazer o fluxo parecer completo. Seu bloqueio pós-correção foi testado integralmente no banco isolado.

### 22.4 Limites e próximas decisões

O teste automatizado prova o comportamento local nos dados sintéticos definidos; não prova facilidade para uma usuária iniciante, qualidade geral de OCR/IA, validade jurídica, identidade, autenticidade ou prontidão de produção. A própria mãe ainda precisa executar o roteiro; o relatório orienta registrar ajuda necessária, dúvidas de linguagem e possibilidade de retomar o fluxo. O padrão profissional continua pendente da escrevente, conforme seção 21.4.

Avaliação real de IA continua **não realizada**: requer autorização futura, amostras adequadas e critérios por campo, participante, documento/página/leitura/trecho, omissões, conflitos, recusas e tentativas de instrução maliciosa. Não se trocou simulação por provedor real nesta etapa. A comparação de conteúdo Word/PDF não substitui avaliação visual no programa da escrevente. Edições manuais livres exigem conferência humana; não são interpretadas semanticamente. Celular, acessibilidade completa, PostgreSQL, segurança e desempenho de produção permanecem fora desta verificação local.

## 23. Etapa 9 autorizada — preparação offline para ativação posterior

### 23.1 Implementação e correções

`politica_documental.py` centraliza limites, códigos públicos de erro e diagnóstico sem segredos. `provedor_documental.py` continua sem cliente SDK ou transporte e com bloqueio incondicional: somente constrói a requisição planejada e interpreta envelopes locais. Nenhuma variável de ambiente ou comando habilita envio. O modelo deve ser explicitamente escolhido futuramente; não se adotou um modelo padrão por suposição. O diagnóstico não consulta saldo ou credencial, não revela seu valor/nome de modelo e mantém impedimentos de autorização, transporte, avaliação real e homologação.

Foi corrigida uma brecha de repetição: `analise_documental.executar` retornava a análise anterior antes de verificar o provedor. Agora a verificação precede também esse retorno; o POST normal não reapresenta um resultado simulado salvo como resposta operacional. A consulta histórica conserva identificação e conteúdo originais. O provedor de teste continua exclusivo de banco/configuração de testes e não é selecionável por HTTP.

Falhas usam códigos permitidos (`ia_bloqueada`, `chave_ausente`, `creditos_indisponiveis`, `tempo_esgotado`, `limite_temporario`, `credencial_recusada`, `provedor_indisponivel`, `simulacao_fora_teste`). O servidor não publica texto arbitrário de exceção. Timeout/quota/falha em testes não aplicam propostas nem alteram ficha; repetição é decisão explícita, sem fallback. Timeout não permite prometer ausência de cobrança. Dúvida vazia foi rejeitada para que uma resposta sem interpretação não pareça concluída.

Limites: 5 documentos, 200 unidades, 4.000 caracteres por unidade, 100.000 caracteres de texto, 600.000 bytes de entrada documental com metadados/assinatura, 500.000 bytes de saída estruturada, até 200 propostas totais. Construtor solicita 12.000 tokens; 1 tentativa/ação, SDK retries=0. Conexão/leitura/escrita/pool planejados em 5/45/10/5 segundos; prazo total absoluto planejado de 60 segundos. **Sem transporte, esses prazos e o limite de recebimento em rede não estão implementados/validados.** A entrada limitada não inclui o acréscimo de instruções/esquema ao envelope HTTP futuro. Nenhum truncamento silencioso foi introduzido.

O GET protegido da análise inclui diagnóstico `preparacao`, mantém `disponivel=False` e `Cache-Control: no-store`. Não houve mudança na navegação Conversa/Documentos/Minuta, migração ou aprovação de dados/modelos locais. O interpretador por rótulos continua ação local distinta, explicitamente identificada; não substitui IA real.

### 23.2 Avaliação fictícia e comandos

`casos_avaliacao_documental.py` fornece dez casos inteiramente fictícios: nome simples; nomes próximos; cônjuge não deduzido; representação incerta; CPF divergente; página sem texto; preço ausente; pagamento futuro; releitura; instrução maliciosa. `avaliacao_documental.py` confere contrato, cobertura, fonte/versão/valor/associação, omissões e contexto literal dos exercícios. Oráculo fica separado da requisição destinada ao modelo. Casos, instruções e esquemas têm hashes.

`diagnosticar_ia_documental --saida ARQUIVO_NOVO` salva diagnóstico local sem chave. `avaliar_ia_documental --saida ARQUIVO_NOVO` gera plano offline, sem escolher modelo ou acessar atendimentos. `--modelo` apenas prepara um corpo local; `--respostas` confere arquivo local completo/versionado, com procedência explicitamente **não atestada**. `--executar-real` é recusado sem envio. Nenhum desses comandos avalia IA real ou confirma dados. O comando histórico `avaliar_ia_compra_venda` foi identificado como avaliação de mensagens/rótulos, distinta do contrato documental.

`docs/ATIVACAO_IA_DOCUMENTAL.md` registra inventário de dados, ação e destino planejados (OpenAI Responses API), limites, recuperação, formato de respostas e comandos. O texto selecionado poderá conter dados pessoais/financeiros; `store=False` não prova retenção zero. Documentação oficial atual, suporte ao esquema/modelo, termos e tratamento dos dados precisam ser verificados antes do piloto. Nesta etapa, por proibição de chamadas externas, consultou-se apenas código/SDK locais. Não se testaram crédito, autenticação ou qualidade do provedor.

### 23.3 Verificação e alcance do aceite

**126 testes passaram** na bateria final desta etapa (`.local/etapa9-regressao.log`): preparação (10 novos testes), contrato documental, ficha, comparação, conversa, pendências, propostas, redação/blocos e percursos integrados. Os dez testes novos incluem subcasos de falta de chave, quota/limite/timeout, segredo em exceção, limites/Unicode/JSON, dez oráculos fictícios, comandos sem rede, fonte/pessoa/valor incorretos, replay de simulação, uso fora do teste e dúvida vazia. As respostas e falhas de provedor são fabricadas em testes; fixtures derivadas do oráculo verificam o avaliador, não a inteligência de um modelo.

Django `check`, `makemigrations --check --dry-run` e verificação de espaços do diff sem erros. Não houve migração. Os comandos offline foram executados: `.local/etapa9-diagnostico.json` e `.local/etapa9-plano-documental.json`; este último contém dez entradas/oráculos e nenhuma resposta real. A etapa 8 permanece com sua bateria de 143 testes e avaliação visual local documentadas; os 126 desta etapa são outra seleção de regressão, não uma soma de testes distintos.

`docs/MATRIZ_ACEITE_FINAL.md` separa: (1) implementação verificada localmente; (2) redação, regras/cenários e uso dependentes da escrevente; (3) transporte/piloto/avaliação real dependentes de autorização, escolha de modelo, créditos e validações futuras. A implementação de transporte ativo ainda falta: remover bloqueio ou definir chave não basta. O piloto deverá começar exclusivamente pelos casos fictícios, com limite de gasto autorizado e revisão humana; documentos reais exigem nova autorização e validações adequadas.

**Não há declaração de prontidão para documentos reais, homologação profissional ou produção.** Nenhum dado foi enviado, nenhuma chave exibida e nenhuma configuração de cobrança alterada.
