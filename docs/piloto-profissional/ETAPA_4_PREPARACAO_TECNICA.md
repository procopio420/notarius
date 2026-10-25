# Etapa 4 — preparação técnica e limites do ensaio

25/10/2026. Continuação autorizada pelo usuário. Mantidas as pendências profissionais das etapas 2 e 3. Entrega: `ROTEIRO_ETAPA_4.md`, revisão do percurso de documentos e execução de regressões locais com documentos fictícios. Não foi aberto caso real, não houve aprovação automática ou envio externo.

## Verificações do percurso

| Item da etapa 4 | Evidência técnica e alcance |
|---|---|
| Recebimento e original | `views.py`, ações `anexos`/`download_anexo`: preservam bytes e filtram atendimento/cartório; download usa `Cache-Control: no-store`. Testes de organização comparam bytes enviados, armazenados e baixados. |
| Acesso restrito | `AtendimentoViewSet.tenant`/`get_queryset` verificam vínculo ao cartório; arquivo/página pertencem ao atendimento. Testes verificam isolamento; isso não audita a conta Windows, disco, banco, backup ou downloads já salvos. |
| Leitura/OCR | `test_ocr_atendimentos` cobre indisponibilidade/timeout sem texto inventado, discordância, limite e releitura. Testes de OCR nativo em PNG/JPG/PDF misto são condicionados à disponibilidade do OCR pt-BR local; distinguir execução de eventual teste pulado no resultado final. |
| Identificação explícita | `organizacao_anexos.py` e testes: destinatários por página; nome semelhante não autoriza vínculo; referência de redação não pode fornecer dados do caso. |
| Fontes e divergências | Testes integrados preservam evidências/preços conflitantes, fonte por página e versão; escolha/associação exigem decisão explícita simulada somente no banco de teste. |
| Modelo, edição e desatualização | Testes integrados percorrem modelo fictício, posições, preparação, edição com motivo e correção posterior, bloqueando versão antiga. Não provam redação profissional ou preenchimento do padrão enviado integralmente. |
| Interface | Leitura dos componentes existentes confirma ações de leitura, original e organização. O roteiro usa Conversa, Documentos e Minuta. Não foi realizada nova sessão visual no navegador ou teste de usabilidade com a escrevente nesta rodada. |
| Exportação | Nos testes integrados, download só segue revisão final fictícia; correção bloqueia versão antiga. Conferência do caso profissional e apresentação Word/PDF não foram realizadas e continuam na etapa 5. |

Nenhuma dificuldade nova de interface foi comprovada nesta rodada; não se alterou interface por suposição. Problemas observados na futura sessão devem ser registrados pelo roteiro e corrigidos antes de considerar o atendimento real concluído.

## Execução

Seleção: `manage.py test tests.test_organizacao_anexos tests.test_ocr_atendimentos tests.test_funcao_principal_integrada --noinput`. **23 testes passaram em 73,980 segundos, sem testes pulados.** Os dois testes condicionados ao OCR nativo local foram executados, incluindo PNG/JPG e PDF misto fictícios. Isso comprova disponibilidade e comportamento nesses arquivos, não qualidade geral do OCR. Verificação de sistema sem problemas.

Essa seleção tem casos já existentes; não representa testes novos nem repete a bateria completa de todas as etapas. Respostas de IA, aprovações, confirmações e decisões positivas dos percursos integrados são simuladas explicitamente em banco isolado. Nenhum resultado equivale ao acompanhamento pela escrevente.

Verificação adicional de acesso: **3 testes passaram em 1,106 segundos**, da classe `tests.test_atendimentos.AtendimentoTests`: `test_requires_authentication`, `test_cannot_read_or_write_another_tenant` e `test_anexos_are_scoped_and_empty_image_stays_uncertain`. Incluem recusa de download em outro atendimento/cartório e imagem vazia mantendo incerteza. Total desta rodada: **26 testes aprovados**, sem testes pulados. `git diff --check` sem erros. Não se declara auditoria do equipamento ou segurança de produção.

## Pendências para o atendimento real

1. **Etapa 2 / escrevente:** revisar/corrigir e aprovar redação, declarações, condições e concordâncias.
2. **Etapa 3 / escrevente e desenvolvimento:** confirmar cenário e requisitos, adaptar a configuração provisória e conectar redação profissional aprovada às posições/condições.
3. **Etapa 4 / usuário:** definir pessoas com acesso e verificar armazenamento, banco, backups/recuperação e equipamento local. A cópia privada das imagens não demonstra esse aceite operacional.
4. **Etapa 4 / escrevente:** executar roteiro acompanhada; conferir fontes, dúvidas e decisões sem confirmação pelo agente.

**Estado:** preparação técnica da etapa 4, sem atendimento real executado ou homologado. Não iniciar etapa 5 automaticamente.
