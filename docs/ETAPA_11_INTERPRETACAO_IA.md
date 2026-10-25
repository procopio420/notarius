# Etapa 11 — integração de interpretação por IA

> Atualização de 24/10/2026: a integração externa descrita abaixo foi substituída por **simulação local por rótulos**, inclusive no comando de avaliação. O endpoint não instancia cliente OpenAI e ignora a antiga autorização de envio. Nenhuma configuração de chave é necessária para este fluxo. As instruções antigas abaixo são histórico e não devem ser executadas nesta fase. Consulte `FLUXO_PRINCIPAL_LOCAL.md`.

## Entrega e estado atual

Cada mensagem salva tem a ação **Analisar mensagem com IA**. O diálogo mostra exatamente o texto a enviar, identifica a OpenAI como destinatária e exige autorização. Esta solicitação não envia anexos, histórico, dados da ficha nem modelos de escritura.

A API usa Responses com saída estruturada. O servidor aceita somente os sete campos atuais, limita tamanho e quantidade de propostas e verifica se cada trecho existe literalmente na mensagem e se o valor existe dentro desse trecho. Trecho inválido, recusa, resposta incompleta, JSON inválido ou falha do provedor interrompem toda a análise. Erros externos não são devolvidos ao navegador.

As propostas não alteram ficha, confirmações ou minutas. O botão de revisão abre a mensagem original na ficha, onde a escrevente escolhe o campo e registra sua decisão. Resultados da análise são temporários no diálogo; não constituem histórico de decisões. As decisões efetivas continuam versionadas na ficha.

**Não há chave OpenAI configurada no ambiente local.** A integração e as proteções foram verificadas com respostas simuladas; qualidade semântica e chamada real ainda não foram validadas. Sem chave, a tela informa a indisponibilidade e mantém a revisão manual.

## Configuração no computador

No arquivo local `apps/notarius-api/.env`, configure `OPENAI_API_KEY` com uma chave da sua conta da API, `AI_MODEL_VERSION` com o modelo autorizado (o padrão existente é `gpt-4o-mini`) e `AI_GENERATION_ENABLED=True`. Não coloque a chave no frontend, Git ou mensagens de chat. Reinicie o backend após configurar. A conta precisa ter acesso ao modelo e condições de uso da API.

A chamada usa o endpoint oficial https://api.openai.com/v1, timeout de 30 segundos, nenhuma repetição automática e `store=False`. Isso não significa ausência de retenção pelo provedor; revise as condições e controles da conta antes de enviar dados reais. Por enquanto use mensagens fictícias.

## Teste acompanhado após configurar

1. Escreva uma mensagem fictícia com um vendedor explicitamente identificado, preço e uma condição ainda incerta.
2. Abra a análise, confira o texto e autorize o envio.
3. Compare cada proposta ao contexto: a validação literal não comprova a relação entre pessoa, papel e fato.
4. Confira que condições e incertezas não viraram fatos. Se houver erro, feche a análise e mantenha a pendência.
5. Abra a revisão manual; a IA não deve confirmar nem gerar minuta por conta própria.

A IA pode omitir informações ou atribuir incorretamente um trecho literal a um campo. A validação implementada reduz invenções de texto, mas não garante interpretação correta. Ainda faltam avaliação semântica com casos representativos, extração assistida de documentos completos e homologação profissional do modelo.

## Verificação

47 testes Django passaram: 41 anteriores e seis de integração, validação literal, recusa/falha, chave ausente, autorização e isolamento por atendimento. Os testes do provedor são simulados. ESLint passou nas páginas/componentes de atendimento e cliente da API.

Referência usada: [Structured Outputs — OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs).
