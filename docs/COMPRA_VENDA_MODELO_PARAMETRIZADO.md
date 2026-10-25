# Estrutura da escritura no fluxo local

## O que foi implementado

A referência recebida agora está disponível em **Minuta → Revisar modelo → Usar estrutura da escritura enviada**. Carregar a estrutura preenche apenas o editor do modelo. Ao salvar como rascunho, os blocos entram na ficha e nas perguntas da conversa, mantendo a preparação bloqueada até as respostas e a aprovação explícita da versão do modelo.

É uma adaptação parametrizada da estrutura das imagens, não uma transcrição integral homologada. Os títulos e a ordem dos blocos acompanham a referência; o conteúdo de cada cláusula variável deve ser informado e conferido no caso. Dados, resultados de consultas, afirmações e referências normativas do exemplo não foram inseridos como texto fixo.

Os campos foram separados em abertura, vendedores, compradores, representação, imóvel, titularidade, aquisição, ônus, preço, pagamento, quitação, transmissão, declarações de cada lado, DOI, tributo, certidões, consultas, declarações específicas das partes, requerimentos, encerramento e despesas. Os campos exigidos são determinados pelos marcadores do modelo salvo. Isso é uma regra do fluxo de preenchimento, não uma lista de exigências legais.

Cada bloco usado pelo modelo precisa estar preenchido e confirmado. “Não se aplica”, ausência de consulta ou inexistência de declaração devem ser registrados expressamente pela escrevente quando forem a situação do caso. O sistema não escolhe essas respostas. A representação, usada no corpo desta estrutura, entra na posição prevista e não é repetida ao final como bloco condicional.

Os modelos anteriores continuam funcionando com os campos que já utilizavam. Novos campos só aparecem na ficha quando exigidos pelo modelo ou quando possuem histórico. Mudanças no modelo preservam versões e atualizam ficha, perguntas e estado da minuta. Novas evidências divergentes reabrem a conferência.

## Como testar

1. Abra um atendimento fictício novo na interface local existente.
2. Em **Minuta → Revisar modelo**, carregue a estrutura da escritura enviada. Registre um motivo de teste e salve como rascunho, sem aprovação.
3. Em **Documentos**, anexe `teste-escrevente/04-estrutura-referencia-ficticia.txt`. Esse arquivo tem textos de teste claramente fictícios, sem documentos ou dados de clientes.
4. Compare original e leitura; registre a revisão manual do arquivo.
5. Na **Conversa**, responda às perguntas, confira cada trecho e confirme as respostas de teste. Experimente deixar uma sem confirmação: ela deve continuar pendente. Não é necessário preencher todos os campos em um formulário inicial.
6. Volte a **Minuta**. Mesmo com as respostas completas, o rascunho do modelo ainda deve impedir a preparação. Revise e aprove explicitamente a versão **para o teste fictício**.
7. Prepare a minuta. Compare todos os blocos com os textos confirmados. Não devem existir marcadores, dados do exemplo original ou resultados de consulta criados automaticamente.
8. Envie outra fonte fictícia com `Consultas: RESULTADO FICTÍCIO DIVERGENTE`. Confira a pendência com arquivo, página, leitura e trecho; a minuta anterior deve ficar desatualizada.
9. A revisão final e a exportação continuam vinculadas à versão atual, como no fluxo anterior.

## Limitações

- Leitura local por rótulos e respostas simuladas, sem interpretação semântica real ou envio a provedor externo.
- Os novos campos são blocos textuais separados, não coleções estruturadas por participante, documento ou imóvel. A escrevente precisa identificar cada pessoa, papel e fonte na redação confirmada. Não há associação automática.
- Conteúdo profissional integral, aplicabilidade das cláusulas e referências normativas precisam de revisão da escrevente. Carregar uma referência não registra aprovação.
- A barreira para afirmações no texto fixo continua lexical e limitada. Não garante detectar todas as paráfrases e pode exigir revisão de texto legítimo.
- Não houve teste visual desta alteração nem validação de concorrência em PostgreSQL. A checagem TypeScript geral continua com erros em outras partes do projeto.

## Verificação realizada

A regressão passou com 90 testes Django. Depois da inclusão do percurso pelo arquivo fictício, os seis testes específicos do modelo passaram, cobrindo estrutura sem aprovação herdada, exigência dos novos blocos, preparação literal, fontes documentais, nova divergência e vínculo de propostas simuladas à mensagem. ESLint passou nos arquivos de interface alterados; não foram reportados erros de TypeScript nesses arquivos na checagem global. Não há migração de banco pendente. Os testes não homologam conteúdo profissional nem qualidade semântica de IA.
