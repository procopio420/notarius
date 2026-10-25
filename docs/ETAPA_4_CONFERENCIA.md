# Etapa 4 — perguntas e conferência conservadora

## Entrega

O atendimento apresenta uma pergunta por vez, com resposta em pop-up. Uma lista opcional permite escolher outra pendência. As perguntas e respostas registradas ficam associadas no histórico. Não é necessário manter a ficha aberta.

O servidor solicita documentos ausentes, revisão humana dos anexos, preenchimento dos campos iniciais e decisão sobre divergências. Respostas sem a confirmação explícita ficam como informadas. Resolver um conflito exige resposta, motivo e confirmação. Revisões e decisões são preservadas.

O endpoint GET `/api/v1/atendimentos/{id}/conferencia/` produz a conferência atual. POST `responder/` registra a resposta com autoria e versão. POST `verificar-redacao/` retorna 409 enquanto houver pendências, e 200 somente quando os controles iniciais estão respondidos. Isso é uma verificação preliminar, não validação jurídica. A geração do novo atendimento será implementada na etapa 5 e deverá obrigatoriamente usar `exigir_pronto` antes de redigir. Os geradores antigos, separados destes atendimentos, não foram integrados por esta entrega.

## Limite importante

Esta entrega usa regras explícitas e não chama um modelo de linguagem externo. Reconhece linhas rotuladas, por exemplo `Preço: R$ 100.000,00`, `Compradores: ...`, e respostas dadas às perguntas do formulário. Não faz interpretação semântica geral de escrituras, certidões ou mensagens livres. Não é uma promessa de que todas as divergências possíveis serão detectadas. Documentos exigem revisão manual, inclusive quando há campos extraídos. Dados não identificados não são inventados.

Comparações textuais conservadoras podem pedir revisão mesmo quando a diferença é apenas uma redação diferente. Valores monetários estritamente reconhecidos são comparados com Decimal, sem ponto flutuante. Variantes ambíguas permanecem como texto.

## Proteções

- Cada candidato mostra mensagem ou arquivo, página e trecho literal.
- Documento com leitura problemática continua sinalizado mesmo após confirmação de revisão manual; a decisão humana não é apresentada como leitura automática bem-sucedida.
- Uma nova evidência reabre a pergunta. Decisões são vinculadas à versão do campo e ao conjunto de evidências, sem aprovação permanente de novas informações.
- Resposta sobre versão antiga retorna 409. Reenvio idêntico é idempotente.
- “Não sei”, “xxx” e outros marcadores de ausência não podem ser confirmados como resposta válida.
- Autenticação e vínculo com o cartório são exigidos também nos novos endpoints.

## Validação

Dezoito testes de API aprovados, incluindo toda a base anterior, comparação de valores, conflitos com duas fontes, confirmação, idempotência, reabertura após nova evidência, bloqueio e liberação preliminar, acesso e recusa de resposta desconhecida. Verificações do Django e de migrações passaram. Os arquivos desta entrega não apresentaram erros no filtro da checagem TypeScript; erros anteriores em outras áreas continuam fora do escopo.

No navegador foi aberto um atendimento com dois anexos fictícios de preços divergentes. O pop-up apresentou as duas fontes. Uma resposta não confirmada foi salva no histórico e a divergência permaneceu aberta. Nenhum dado dos anexos pessoais enviados pelo usuário foi utilizado.
