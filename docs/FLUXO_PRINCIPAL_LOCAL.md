# Fluxo principal local — 24/10/2026

## Estado

Reaproveitados atendimento, conversa, leitura de anexos, ficha versionada, decisões de conferência, modelo aprovado por atendimento, preparação literal, revisão final e exportação já existentes. Interface mantida em Conversa, Documentos e Minuta. Não houve alteração de cobrança ou inspeção de credenciais.

O mapa `COMPRA_VENDA_MAPA_PARA_REVISAO.md` ainda registra o modelo profissional e o cenário como não homologados. A aprovação de modelos feita pelos testes é fictícia. Esta entrega não homologa modelos nem habilita interpretação semântica real.

## Mudanças

- “Simular leitura local” substitui a chamada externa. O servidor reconhece apenas rótulos explícitos e copia valores e trechos; não usa SDK de provedor nem rede. Funciona sem chave e continua local mesmo com uma chave configurada. Resultados trazem `modo=simulacao_local`, mensagem de origem e aviso. Não confirma campos nem cria minuta.
- Mensagens com linhas não reconhecidas geram pendência persistente vinculada ao texto integral e ID. Mensagens posteriores não escondem essa pendência. A escrevente precisa resolver as dúvidas, registrar os dados nos campos e confirmar a revisão da fonte com justificativa. Essa revisão não confirma automaticamente os campos. Cada mensagem nova exige sua própria revisão quando não reconhecida.
- Propostas documentais incluem arquivo, anexo, página, versão da leitura, canal e trecho literal, marcadas como extraídas. Propostas da conversa são marcadas como informadas. Confirmações continuam em registros separados, com autoria, versão e justificativa.
- Entrada manual na ficha passa a criar mensagem de origem com autor e conteúdo literal, dentro da mesma transação da revisão. O histórico não é substituído.
- Envio de mensagem e anexo passa a usar o bloqueio do atendimento já empregado em respostas, OCR e redação. Versões e assinaturas continuam impedindo decisões sobre estados antigos e uso de minuta desatualizada.
- Aprovar o modelo não libera automaticamente frases fixas reconhecidas como pagamento, quitação, consulta concluída ou assinatura. A preparação bloqueia e solicita revisão, sem reescrever cláusulas. Fatos específicos devem vir de campos e fontes confirmados.

## Teste manual com dados fictícios

1. Inicie pelo procedimento local existente em `scripts/iniciar-teste-local.ps1`. Abra `/atendimentos` na porta 3002 e crie um atendimento TESTE.
2. Anexe `docs/teste-escrevente/01-dados-ficticios.txt`. Confira original, leitura e páginas em Documentos e registre sua revisão manual.
3. Na Conversa, envie `Preço: R$ 100.000,00`. Execute “Simular leitura local”. Confira valor e trecho; a simulação deve informar que não é IA e não confirmar o dado.
4. Responda às pendências. Salve uma resposta sem confirmar: ela deve ficar informada e pendente. Confirme somente depois da conferência, com justificativa.
5. Envie uma mensagem livre, por exemplo “Ainda não identifiquei o representante”. Ela deve impedir a preparação, mesmo se os cinco campos obrigatórios já estiverem confirmados. Resolva a dúvida nos campos afetados antes de registrar a revisão da mensagem.
6. Em Minuta, revise e aprove explicitamente um modelo **fictício de teste**. Prepare a minuta e compare com campos e fontes. O texto deve ser preenchido literalmente.
7. Acrescente ao texto fixo do modelo “O preço foi pago e dou quitação”. Mesmo com aprovação, a preparação deve bloquear. Corrija o modelo; não confirme um pagamento apenas para liberar o teste.
8. Envie `02-preco-divergente.txt`. Confira as duas fontes; a minuta anterior deve ficar desatualizada, com nova preparação/exportação bloqueadas até a decisão humana. Uma resposta antiga deve receber conflito, sem sobrescrever a atual.
9. Depois da revisão final específica da versão atual, teste a exportação já existente. A revisão de uma versão antiga não libera uma versão nova.

## Limitações que permanecem

- A simulação não interpreta texto livre, pessoas, papéis ou documentos completos. A adaptação posterior da referência ampliou os campos em blocos textuais, descritos em `COMPRA_VENDA_MODELO_PARAMETRIZADO.md`; eles ainda não são cadastro estruturado de múltiplos participantes, documentos, imóveis ou parcelas. Não há associação automática entre pessoas ou bens.
- O reconhecimento de frases fixas é uma barreira lexical conservadora: não detecta todas as paráfrases e pode interromper texto que não declara um acontecimento. Não substitui a marcação e homologação profissional das cláusulas do modelo.
- Conferir manualmente uma fonte com falha de leitura registra decisão humana; não apaga o aviso nem transforma OCR em leitura comprovada. Trecho literal não prova interpretação, autenticidade ou verdade.
- Os testes de banco locais usam SQLite. Bloqueio de linha de `select_for_update` depende de PostgreSQL; esta entrega não valida concorrência real entre servidores. SQLite pode recusar escritas concorrentes por bloqueio do banco.
- A checagem TypeScript global tem erros fora dos arquivos de atendimento alterados. Não foi declarada aprovação visual da interface ou dos arquivos exportados nesta rodada.
- Sem identificação e aprovação do modelo profissional e do cenário pela escrevente, o percurso permanece um exercício fictício verificável, não uma compra e venda profissional concluída.

## Verificação desta entrega

85 testes Django passaram nas suítes de atendimento, conversa, simulação, avaliação, fluxo principal, OCR, revisão final, modelos, resumo, comparação, organização, feedback e backup. Incluem percurso fictício até minuta, reabertura de pendências, fontes manuais, isolamento e proibição de obter acontecimentos do texto fixo. Não houve alteração de esquema pendente (`makemigrations --check --dry-run`). ESLint passou nos componentes e cliente alterados. A checagem TypeScript global falhou com erros em outras telas e Cypress, sem erros reportados nos arquivos de atendimento alterados. Não houve chamada real de IA nem teste de concorrência em PostgreSQL.
