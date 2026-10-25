# Etapa 19 — feedback dos testes dentro do atendimento

Funciona localmente, sem IA externa ou envio automático a terceiros.

## Usar com a escrevente

1. Dentro do caso, clique em **Registrar feedback do teste**.
2. Escolha onde aconteceu: conversa, anexos, ficha, modelo, minuta, exportação ou outra parte.
3. Classifique como erro, dúvida ou sugestão.
4. Descreva o que fez e o que aconteceu. Opcionalmente informe o que esperava.
5. Clique em **Registrar relato**. O formulário só é limpo após confirmação do salvamento. Se falhar, mantém o texto; o reenvio idêntico usa o mesmo identificador e não duplica o registro.
6. Consulte **Relatos salvos** ou use **Baixar relatos TXT** para obter uma cópia local.

Evite incluir dados pessoais dos documentos. Não são anexadas imagens, documentos, conversas ou textos completos da minuta automaticamente. O contexto registrado pelo servidor contém somente assinatura do conjunto de dados, versão do modelo/minuta e quantidade de pendências na consulta.

O relato guarda autoria e data. A redação original é preservada; para corrigir ou complementar, registre outro relato identificando o anterior. Nesta entrega não há estados de triagem, edição/exclusão ou envio ao suporte. O histórico é por atendimento, acessível apenas no cartório correspondente.

## Separação dos dados do ato

Feedback não é mensagem da conversa, fonte de dados, correção de ficha ou decisão de conferência. Não muda nem confirma valores e não altera a assinatura dos dados da minuta. Se houver informação incorreta, corrija-a nos fluxos próprios da ficha/modelo/minuta. Um feedback de erro não bloqueia automaticamente o caso nem significa que o problema foi resolvido.

## Backup

O banco inteiro já inclui os relatos no backup criptografado. A ferramenta agora também apresenta a contagem de feedbacks quando a tabela existe, mantendo compatibilidade com cópias anteriores que ainda não tinham esse recurso.

## Verificação

83 testes Django passaram: persistência/reenvio, rejeição de conteúdo vazio/excessivo e categorias inválidas, isolamento por cartório/atendimento/autoria no reenvio, contexto calculado pelo servidor e preservação da assinatura dos dados. O teste adicional de backup confirma preservação dos relatos e leitura de cópias antigas.

ESLint passou nos componentes, páginas de atendimento e cliente da API. Um relato explicitamente fictício foi salvo e consultado no navegador, com modelo/minuta v1 e nenhuma pendência no contexto. Não houve chamada à IA externa.
