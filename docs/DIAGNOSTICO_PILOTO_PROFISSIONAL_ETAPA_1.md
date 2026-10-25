# Piloto profissional — diagnóstico da etapa 1

25/10/2026. PR #2 de `evgrotz/notarius`, branch `codex/plano-piloto-profissional`, base inspecionada `75b2857`. Escopo: diagnóstico técnico, sem parametrizar padrão, configurar cenário ou iniciar caso real. As etapas 2 a 6 não foram executadas.

Foram lidos a orientação inicial do plano, `EXECUCAO_FLUXO_PRINCIPAL.md`, `REVISAO_ETAPAS_1_A_8_E_PROXIMOS_PASSOS.md`, a conclusão da etapa 9 na seção 23 do documento de execução e `MATRIZ_ACEITE_FINAL.md`. O arquivo `ETAPA_9_OCR_LOCAL.md` pertence à numeração histórica de OCR; não é o relatório da preparação offline do ciclo principal.

## 1. O que reaproveitar

| Estrutura existente | Evidência no código | Alcance e limite |
|---|---|---|
| Ficha por objetos, revisões e fontes | `apps/notarius-api/apps/processos/ficha_estruturada.py` (`alterar`, `consultar`) e `ficha_estruturada_schema.py` | Pessoas, papéis, relações, imóvel, negociação, ato e complementos separados. Dado informado/extraído não equivale a confirmado; confirmação pode perder atualidade. |
| Documentos, originais, leitura e vínculos por página | `organizacao_anexos.py` (`permite`, `validar_fonte`, `salvar`) e fluxo de anexos/OCR documentado no relatório principal | Finalidade de referência de redação não pode comprovar fatos do caso. Classificação, destinatário e versão precisam ser conferidos. OCR não interpreta nem comprova autenticidade. |
| Propostas, comparação, pendências e conversa | `analise_documental.py`, `comparacao_fontes.py`, `pendencias_ficha.py`, `dependencias_ficha.py`, `conversa_orientada.py` | Reutilizar rastreabilidade, conflitos e perguntas por dado/objeto. Extração local por rótulos e respostas fabricadas de teste não demonstram interpretação geral de documentos. |
| Modelo, posições e vínculos explícitos | `redacao_estruturada.py` (`validar_configuracao`, `conferir_vinculos`, `preencher`) | Posição exige objeto do tipo correto e vínculos consistentes. Registros excedentes exigem exclusão justificada. Não associar por nome parecido. |
| Cláusulas condicionais e repetições | `blocos_minuta.py` (`plano`, `referencias`, `expansoes`) | Condições literais, posições e ordem explícitas; sem blocos aninhados ou expressões livres. Configuração técnica não representa aprovação profissional. |
| Biblioteca, versões, edição, comparação, revisão e exportação | Fluxo registrado nas seções 21–23 do documento de execução e componentes `BibliotecaModelos`, `MinutaPreparada`, `ComparacaoMinuta`, `RevisaoFinalDaMinuta` | Preservar modelo/versão, autoria, motivos, fontes e desatualização. Exportação genérica não comprova fidelidade visual ao padrão profissional. |
| Interface em Conversa, Documentos e Minuta | `apps/notarius-web/src/app/atendimentos/[id]/page.tsx` e componentes de atendimentos | Reaproveitar a navegação. Configuração técnica dos marcadores deve ser preparada pelo desenvolvimento e revisada pela escrevente. |

## 2. Ajustes necessários, sem implementá-los nesta etapa

| Área | Ajuste a preparar quando houver material/decisão | Dependência e limite atual |
|---|---|---|
| Texto do modelo | Inventariar texto fixo, marcadores, declarações específicas, blocos condicionais e repetições; registrar versão e origem do padrão. | Falta padrão profissional integral autorizado e revisão da transcrição. Não completar rasuras nem transportar fatos do exemplo. |
| Campos | Mapear cada trecho variável ao campo existente; definir obrigatoriedade, alternativas e dependências aprovadas. Campos adicionais de qualificação já são configuráveis. | `validar_regras` permite requisitos por tipo/campo e dependências dentro do mesmo tipo; não é um motor geral de regras condicionais entre objetos. Só propor extensão se o cenário aprovado exigir. |
| Vínculos e ordem | Definir posições de vendedores/compradores, relações, representação, imóvel e negociação, inclusive exclusões e ordem de redação. | Modelo suporta até 60 posições e repetições explícitas; não há repetição ilimitada automática. Determinar quantidades cobertas e quando parar para decisão humana. |
| Condições e cenário | Especificar alternativas que incluem/omitem cada cláusula e casos fora do escopo. Separar preço, pagamento previsto, pagamento declarado e quitação. | Blocos condicionais já recusam alternativa fora do cenário configurado; isso não constitui homologação integral de um cenário ou checklist documental profissional. |
| Documentos e fontes | Aprovar quais documentos/páginas sustentam cada informação e como tratar falta, divergência, ilegibilidade e leitura antiga. | Classificação manual existente não verifica suficiência documental profissional. Lista de exigências não deve ser inferida do exemplo. |
| Interface | Após mapear o padrão, conferir rótulos compreensíveis, ordem de preenchimento, seleção explícita de participantes e perguntas para dúvidas; usar o roteiro da etapa 8 com a escrevente. | Ainda falta observação de uso por ela. Não declarar defeito de usabilidade sem esse ensaio nem acrescentar telas periféricas. |
| Saída | Definir apresentação exigida e conferir Word/PDF no programa/equipamento usados pela escrevente. | Exportadores atuais são genéricos; eventuais ajustes de layout dependem do padrão e da comparação posterior. |
| Operação local e acesso | Antes de receber dados reais, verificar usuários autorizados, armazenamento dos originais/banco, cópias de segurança e recuperação no equipamento escolhido. | Controles locais e testes de isolamento não equivalem a auditoria de segurança/produção. Os erros globais de TypeScript documentados anteriormente continuam uma pendência a verificar antes de empacotar/publicar; não foram reavaliados aqui. |

Não é necessário substituir a arquitetura. A primeira intervenção prevista é configurar o que já existe; a necessidade de novos campos ou mudanças estruturais só poderá ser fechada depois do mapeamento do padrão completo.

## 3. Material e decisões pendentes

**Da escrevente:**

1. Padrão completo, legível, com todas as páginas e autorização de uso/adaptação; esclarecer rasuras e indicar a versão de referência. Original com dados reais deve ficar fora do Git.
2. Escolher um primeiro cenário restrito: participantes, relações/representação, imóvel e condições de pagamento cobertos; definir situações que obrigam a interromper e consultar.
3. Aprovar campos, fontes/documentos necessários, declarações e condições de cada cláusula, distinguindo informação ausente, não aplicável e fato confirmado.
4. Aprovar redação, ordem dos participantes e apresentação; acompanhar a revisão do primeiro caso e registrar dúvidas de uso. Essas aprovações ainda não existem como resultado desta etapa.

**Do usuário:** organizar a entrega privada do material autorizado, combinar a participação da escrevente e indicar equipamento/programa e pessoas com acesso ao piloto. Antes de dados reais, decidir e verificar o armazenamento/acesso/backup local. Solicitar expressamente a próxima etapa quando desejar prosseguir. Créditos de IA não são requisito deste diagnóstico ou da parametrização manual; IA externa permanece adiada e depende de autorização específica futura.

## 4. Critérios de aceite para o primeiro caso real acompanhado

Estes são critérios propostos para revisão da escrevente, não aceites já obtidos:

1. Antes de abrir o caso: padrão integral autorizado, versão parametrizada revisada/aprovada e cenário restrito definido; acessos e armazenamento local conferidos. Material real, banco, credenciais e exportações reais fora do Git; nenhum envio externo autorizado por este plano.
2. Cada pessoa, papel, relação, imóvel e negociação identificado por registro próprio; associação documental/página e posições da minuta explicitamente revisadas. Sem vínculo por semelhança de nome e sem fatos herdados do padrão.
3. Todo dado usado tem origem identificável e confirmação atual da escrevente. Ausências, divergências, ilegibilidade e dúvida de associação permanecem pendentes até decisão explícita com justificativa; caso fora do cenário para.
4. Pagamento futuro não produz quitação, e consultas, assinaturas ou declarações não são tratadas como realizadas sem informação específica confirmada.
5. Minuta usa a versão aprovada, posições e cláusulas aplicáveis; a escrevente confere o texto e as fontes. Correção relevante deve desatualizar a versão anterior, exigir nova revisão e preservar histórico.
6. Word/PDF correspondem ao texto salvo e à versão revisada: nomes, números, valores, acentos, ordem, cláusulas e apresentação conferidos. A escrevente aprova o conteúdo/apresentação no programa utilizado; verificação técnica não declara validade jurídica.
7. Registrar percurso, ajuda necessária, problemas e decisões sem dados pessoais no relatório versionado. Resultado permanece limitado a um caso acompanhado; não representa homologação geral ou avaliação de IA.

## 5. Evidências, verificações e encerramento

Inspeção estática do código e documentação na base indicada; provedor real verificado em `ProvedorReal.analisar`: bloqueio incondicional `ia_bloqueada`. `preparar_requisicao` apenas constrói dados locais; não envia. Não se alterou configuração para remover avisos ou bloqueios.

Verificação automatizada desta rodada: **33 testes passaram em 22,525 segundos**, com `manage.py test tests.test_preparacao_documental.PreparacaoOfflineTests tests.test_blocos_minuta tests.test_redacao_estruturada --noinput`, em banco de testes isolado. A verificação de sistema não apontou problemas. `git diff --check` sem erros. Esses testes usam dados/respostas fictícios e não avaliam IA real, documentos reais, aparência do Word/PDF ou uso pela escrevente. As baterias históricas de 143 e 126 testes não foram repetidas integralmente nesta rodada.

Arquivos alterados nesta etapa: este diagnóstico e o registro de acompanhamento em `PLANO_PILOTO_PROFISSIONAL.md`. Sem alteração de implementação, banco operacional, configurações, credenciais ou documentos reais. Sem homologação profissional e sem execução das etapas seguintes.

**Resultado:** diagnóstico técnico entregue; adaptação e aceite profissional permanecem pendentes do material e das decisões acima. Aguardar nova solicitação.
