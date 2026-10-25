# Verificação técnica independente de aceite profissional

25/10/2026. Solicitada pelo usuário após a preparação v1. Não configura a etapa 3: nenhum cenário, participante, documento exigido ou condição jurídica foi escolhido. Não registra aprovação da escrevente.

## Verificação do pacote efetivamente entregue

`apps/notarius-api/tests/test_pacote_piloto_profissional.py` abre `modelo-v1.json` e exercita os validadores e endpoints reais em banco isolado, sem copiar o pacote para o banco operacional. Os quatro testes novos cobrem:

1. Aceitação pelo serializer, contrato de marcadores e guarda de fatos fixos; os 23 campos existentes estão cobertos, a aprovação continua falsa e não há posições/regras profissionais configuradas.
2. Rejeição de tentativa de embutir afirmação de pagamento/quitação no texto fixo do pacote.
3. Salvamento e reabertura do pacote como rascunho, preservando conteúdo, sem aprovar ou produzir minuta.
4. Mesmo com todos os campos exigidos preenchidos/confirmados artificialmente em teste, geração continua bloqueada porque o modelo não foi aprovado. Nenhuma minuta é criada.

Os textos de preenchimento são explicitamente fictícios. Confirmações usadas no banco de teste exercitam o comportamento do sistema; não se referem ao padrão profissional nem a um caso real. Não houve extração de dados das imagens, OCR real, IA externa ou consulta ao provedor.

## Regressões pertinentes

| Área | O que a bateria verifica | Limite |
|---|---|---|
| Ficha estruturada | Pessoas com nomes iguais conservam IDs; relações explícitas; fontes/versões; preço, condição e pagamento previsto não preenchem quitação/comprovante. | Não confirma identidade ou interpretação de documento real. |
| Redação estruturada | Vínculos incompatíveis recusados; registros excluídos justificados; correção desatualiza; exportação exige revisão final. | O cenário usado é fictício e não configura o primeiro cenário profissional. |
| Blocos | Alternativas fora do cenário ou não confirmadas bloqueiam; condições/repetições respeitam posições explícitas; edição preserva histórico. | Não aprova quais condições ou cláusulas se aplicam ao padrão. |
| Preparação documental | Provedor real bloqueado, falhas preservam trabalho, simulação não vira resposta normal, comandos/avaliação offline. | Respostas e falhas fabricadas não avaliam IA real. |

## Execução e resultado

Comando: `manage.py test tests.test_pacote_piloto_profissional tests.test_ficha_estruturada tests.test_redacao_estruturada tests.test_blocos_minuta tests.test_preparacao_documental --noinput`.

**57 testes passaram em 38,003 segundos**, incluindo os quatro testes novos do pacote e 53 da seleção existente. Django `check` sem problemas; `makemigrations --check --dry-run` sem mudanças; `git diff --check` sem erros. Nenhuma migração ou ajuste de configuração. Sem mudança no texto do modelo. Não é a repetição das baterias históricas completas, nem soma de testes independentes às contagens anteriores.

## O que continua dependendo da escrevente

Revisar a redação detalhada v1, aprovar/corrigir as cláusulas e concordâncias, decidir o cenário e os requisitos, e acompanhar o primeiro caso. A aprovação humana não pode ser substituída por estes testes. A apresentação Word/PDF do padrão e a usabilidade no equipamento dela também não foram avaliadas nesta rodada.

O pacote executável continua sendo uma estrutura de blocos; as fórmulas detalhadas estão separadas para revisão. Estes testes não demonstram montagem automática dessa redação detalhada, concordância gramatical automática ou parametrização profissional homologada. Sua conexão aos objetos/regras do cenário é trabalho posterior condicionado às decisões e à solicitação da etapa 3.
