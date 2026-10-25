# Etapa 13 — comparação de versões da minuta

A decisão sobre crédito/provedor de IA foi adiada pelo usuário. Esta etapa funciona localmente, sem chave ou chamadas externas.

## Como usar

1. Abra um atendimento com pelo menos duas versões salvas da minuta.
2. Abra a minuta e clique em **Comparar versões**.
3. Escolha a versão de referência. A minuta aberta é a versão de destino, mesmo quando a referência escolhida é mais recente.
4. Confira os blocos **Removido da referência** e **Acrescentado no destino**. Marque **Mostrar também trechos sem alteração** se quiser o contexto completo.
5. Confira os registros da ficha que mudaram e as versões dos modelos utilizados.
6. Volte à minuta para continuar a revisão. A comparação não altera nenhuma versão nem libera exportação bloqueada.

A comparação é literal por linhas. Uma alteração dentro de uma linha exibe essa linha completa como removida e acrescentada. A apresentação preserva acentos, espaços, linhas e pontuação. Textos com mais de 1500 linhas em uma das versões usam blocos completos, com aviso, para limitar o custo do processamento.

As diferenças nos dados usam os snapshots salvos na preparação: se só mudou a revisão/origem/situação, a tela informa que o valor permaneceu igual. Edições manuais do texto não atualizam esses snapshots nem a ficha. A comparação não é uma checagem jurídica ou validação de veracidade.

## Validação

57 testes Django passaram (54 anteriores e três de comparação). Os novos testes verificam reconstrução exata dos dois textos, mudanças só na revisão, isolamento por atendimento/cartório e manutenção do bloqueio de exportação. ESLint passou nos componentes, páginas de atendimento e cliente da API.

## Pendências que continuam

- Decisão sobre uso e crédito da API externa, explicitamente adiada.
- Avaliação real do modelo quando houver decisão sobre o provedor.
- Revisão profissional do mapa e do modelo da escritura pela escrevente.
- Teste acompanhado de usabilidade com dados fictícios e registro dos pontos de dificuldade.
