# Etapa 3 — configuração provisória do primeiro cenário

25/10/2026. O usuário autorizou avançar à etapa 3 e manter o que faltou na etapa 2 como pendente. Isso autoriza preparação técnica, não substitui as decisões da escrevente nem aprova a redação. A etapa 4 não foi executada.

## Configuração entregue

Arquivo: `cenario-provisorio-v1.json`. Contém metadados de hipóteses e pendências, `aprovado: false` e um objeto `modelo` no contrato existente. A aplicação não foi alterada para importar/selecionar automaticamente esse arquivo. Nenhum atendimento operacional foi criado e nenhuma versão existente foi sobrescrita.

Hipótese restrita para testar a configuração: uma pessoa vendedora, uma compradora, participação direta, um imóvel e pagamento previsto. **Hipótese de desenvolvimento, não cenário aprovado pela escrevente.** Não foi deduzida uma preferência profissional a partir do exemplo, que contém representação. A redação produzida é rascunho técnico e não reproduz integralmente a escritura profissional.

| Elemento | Configuração executável no modelo |
|---|---|
| Posições | `vendedor`, `comprador`, `papel_vendedor`, `papel_comprador`, `bem`, `negocio`. |
| Vínculos | Cada papel aponta explicitamente para sua pessoa; negociação aponta para o imóvel. IDs reais só serão escolhidos no atendimento, nunca salvos no modelo. |
| Campos exigidos provisoriamente | Nome da pessoa; tipo do papel; descrição, matrícula e registro do imóvel; preço, situação e condições do negócio. São requisitos deste teste, não lista jurídica de documentos/qualificação. |
| Dependências | Condições dependem de preço e situação do pagamento. Revisão de quitação, se vier a existir, depende de preço, situação e condições; não é criada, exigida ou inserida na minuta por essa regra. |
| Cláusulas/trechos condicionais | Bloco vendedor aceita somente papel `vendedor`; bloco comprador somente `comprador`; previsão aceita somente situação `previsto` e inclui condições informadas. Não há fórmula de quitação ou declaração de pagamento realizado no texto. |
| Fora do domínio permitido | Condição de papel/pagamento não contemplada impede preparar minuta, sem minuta parcial. Campo obrigatório ausente bloqueia. Mudança em dado de dependência exige nova conferência. |
| Registros excedentes | O mecanismo existente exige destinação explícita de todos os registros: vínculo ou exclusão individual justificada. Não elimina participantes por nome semelhante. |

Não existe homologação automática da participação direta, limite semântico geral de cardinalidade ou verificação jurídica de exclusões. O motor valida os vínculos e alternativas configurados; não interpreta uma justificativa de exclusão como prova de que um representante/cônjuge possa ficar fora do ato. Se houver outras pessoas, representação, relações, imóveis ou fatos não cobertos, a orientação é interromper para decisão humana e revisar o cenário, não justificar exclusão para contornar a limitação. Essa orientação não é apresentada como bloqueio semântico universal implementado pelo sistema.

O cabeçalho de teste não faz concordância automática por gênero/cargo. CPF, regime, filiação e outras qualificações continuam no catálogo da etapa 2, sem terem sido escolhidos como exigências universais. Tributo, certidões, consultas, declarações, transmissão, quitação, requerimentos e encerramento profissionais não foram incluídos por suposição.

## Como foi verificado

`tests/test_cenario_piloto_provisorio.py` lê o arquivo entregue e o salva pelos endpoints existentes em banco isolado. Seis verificações:

1. Modelo é salvo não aprovado e continua bloqueado para geração.
2. Somente com aprovação/confirmações **simuladas no banco de testes**, o rascunho técnico é preenchido; pagamento previsto não cria revisão nem texto de quitação; pessoas de nomes idênticos mantêm IDs próprios.
3. Troca de pessoas sem trocar os vínculos corretos dos papéis é recusada, apesar dos nomes idênticos.
4. Pagamento `declarado_realizado`, fora do domínio provisório, bloqueia sem salvar minuta parcial.
5. Matrícula ausente bloqueia geração.
6. Correção do preço invalida a confirmação das condições dependentes e impede nova geração até revisão.

As pendências persistentes de comparação são resolvidas explicitamente no roteiro de teste somente quando as fontes fictícias estão completas, confirmadas e sem problemas. Não foram desativadas nem apagadas para fazer o teste passar. Nas execuções iniciais, dois testes positivos pararam nessas pendências; o preço também usava uma frase de teste sem formato monetário válido. Corrigiu-se o roteiro para registrar revisão explícita e usar valores monetários sintéticos, sem mudar regras de produção.

**37 testes passaram em 61,843 segundos**, com `manage.py test tests.test_cenario_piloto_provisorio tests.test_pacote_piloto_profissional tests.test_blocos_minuta tests.test_redacao_estruturada --noinput`: seis novos testes do cenário, quatro do pacote e 27 regressões de blocos/redação. Django `check`, `makemigrations --check --dry-run` e `git diff --check` sem problemas. Não houve IA, documentos reais, migração, alteração de configuração do ambiente ou aprovação profissional. Não foram conferidas redação profissional integral, usabilidade pela escrevente ou apresentação Word/PDF nesta etapa.

## Pendências preservadas

| Etapa | Pendência | Responsável |
|---|---|---|
| 2 | Revisar/corrigir redação v1, fórmulas de declaração, condições, concordâncias e aprovar versão. | Escrevente |
| 3 | Confirmar ou substituir hipótese de participação direta, quantidade de pessoas/imóveis e pagamento previsto. | Escrevente, com usuário organizando a escolha |
| 3 | Homologar campos e documentos exigidos, vínculos, exceções e casos que interrompem o cenário. | Escrevente |
| 3 | Após decisões, conectar a redação profissional às posições e condições aprovadas; completar cláusulas e ajustar testes afetados. | Desenvolvimento, dependendo das decisões anteriores |
| 4–5 | Operação local, acompanhamento do caso real e revisão de conteúdo/apresentação exportada. | Usuário e escrevente, em etapas futuras |

**Estado:** configuração provisória implementada como artefato executável pelo mecanismo existente, para ensaio fictício. Configuração profissional final pendente. Aguardar nova solicitação; não iniciar a etapa 4 automaticamente.
