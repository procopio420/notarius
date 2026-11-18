# Controle de gastos e teste real — 08/11/2026

O transporte explícito `ProvedorTesteControlado` chama o registro persistente de orçamento antes de abrir conexão. Teto acumulado US$ 0,50; reserva de US$ 0,05 por tentativa, inclusive falhas. Sem repetição automática. Registro ausente/corrompido ou teto atingido bloqueia. Somente gpt-6-luna, texto, 32 KB de envelope, saída até 4.000 tokens, sem ferramentas e sem armazenamento de respostas na API. O limite vale somente para esse transporte, não para outras aplicações na conta.

A autorização desta sessão substituiu a proibição anterior de executar teste externo. Foram usadas apenas entradas fictícias embutidas; nenhum atendimento ou arquivo de cliente foi enviado. A chave foi carregada apenas em memória, sem impressão ou registro do segredo.

Resultado: seis tentativas locais reservadas, cinco respostas com contagem de uso; uma tentativa sem resposta/uso foi mantida no orçamento conservador. 17.101 tokens informados. Estimativa pelas tarifas padrão sem desconto de cache: US$ 0,0028421 (aproximadamente US$ 0,003, não comprovante de cobrança). Reservado: US$ 0,30; teto inalterado US$ 0,50. Nenhuma reserva foi devolvida ou reiniciada.

Na rodada após ajuste de instruções, nome simples e página sem texto passaram. Pagamento futuro foi rejeitado pela validação de evidência. Nenhuma resposta inválida foi aplicada, nenhum modelo aprovado automaticamente e nenhum dado do banco operacional foi modificado. Uma resposta anterior também foi rejeitada por referência literal inválida; houve ajuste para preservar contexto completo. Metadados de raciocínio da Responses são ignorados sem serem tratados como fonte; chamadas de ferramentas continuam recusadas.

O teste de integração local cobre nove jornadas, incluindo upload, revisão, preparação, exportação, divergências, pagamento futuro e alteração após revisão. Essas jornadas usam provedor simulado, portanto NÃO comprovam um fluxo completo com IA real. O transporte pago foi validado separadamente. O chat público continua com IA desativada; `provedor_do_ambiente` ainda seleciona o provedor bloqueado. Não está homologado para trabalho real.

Evidências privadas: `.local/resultado-teste-ia*.json` e `.local/orcamento-ia.sqlite3`. Relatórios contêm somente respostas fictícias e uso. O executável `scripts/testar-ia-controlada.py` recusa repetir quando seu relatório já existe. Não apagar registros para liberar mais testes.

Fontes de protocolo e tarifa consultadas: https://developers.openai.com/api/docs/models/gpt-6-luna e documentação oficial Responses. Limites de bytes e saída mantêm cada tentativa muito abaixo da reserva; orçamento local não substitui conferência de cobrança do provedor.

## Chat com IA ativado — 08/11/2026
O endpoint autenticado `chat-ia` usa GPT-6 Luna, somente o texto extraído localmente dos anexos do atendimento, versões atuais das páginas e até dez mensagens recentes com respostas anteriores. Não lê imagens por visão nem consulta fontes externas. O envelope completo acima de 32 KB é bloqueado sem truncamento ou envio parcial. Cada citação retornada é conferida literalmente no texto da página, sem depender de índices calculados pelo modelo. Respostas recusadas/incompletas ou citações inválidas não são exibidas como análise válida. Não há confirmação automática de ficha, aprovação de modelo ou redação livre de minuta por IA.

Uma resposta persistente por mensagem impede novo envio pago em recarga, consulta e repetição do mesmo pedido. A resposta processando/falha fica registrada; não existe repetição automática. O caminho usa o mesmo orçamento acumulado de US$ 0,50, sem reinicializar o registro anterior. Reservado após o teste real adicional: US$ 0,35. Restam no máximo três pequenas tentativas neste orçamento. A reserva é uma margem local, não o gasto cobrado.

O perfil `config.settings_piloto` roda no ambiente `real` e bloqueia o chat externo mesmo se o arquivo privado `.local/chat-ia-habilitado` existir. O transporte também recusa ambiente real ou indefinido antes de acessar a chave ou reservar orçamento. O teste do chat externo usa o banco descartável do Django, com ambiente fictício explícito. O arquivo de ativação é considerado somente nesse ambiente. `store=false`, sem ferramentas.

Validação: quatro testes novos offline (persistência/replay, orçamento, acesso a mensagem de outro caso, citação literal/recusa), teste real integrado em banco descartável com documento fictício e pagamento futuro passou, sem confirmar dados. A API respondeu que pagamento previsto não demonstra quitação e citou o texto. Tipos, lint dos arquivos alterados e build de produção passaram; a cópia isolada não contém configuração de lint e essa etapa foi executada separadamente no projeto. A suíte ampliada teve dois testes de subprocesso inicialmente limitados pelo ambiente; os dois passaram na reexecução com acesso ao leitor local. Nenhuma chamada adicional paga nessa reexecução.

Backup antes da migração: `.local/antes-chat-ia.sqlite3`. Migração 0025 aplicada. Link HTTPS temporário renovado, login e status IA conectada conferidos pelo navegador. Mensagens antigas não foram reenviadas à IA automaticamente. Não constitui homologação para trabalho real.

## Revalidação estruturada com prints fictícios — 12/11/2026

Duas chamadas controladas validaram texto de OCR local de cinco prints
inteiramente fictícios. A primeira encontrou os valores, mas deixou os dois
vínculos exclusivos sem sugestão. Após esclarecimento das instruções, a
segunda retornou seis propostas com valores, fontes e associações esperados,
além de uma dúvida para o print em branco. O servidor validou as propostas
com o contrato documental. O ensaio não carregou casos do banco operacional.
O orçamento acumulado ficou em US$ 0,45 reservados de US$ 0,50. A reserva é
um limite conservador, não a cobrança. Evidências em `.local/teste-ia-prints/`.
