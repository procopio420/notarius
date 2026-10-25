# Próximo ciclo — piloto profissional de compra e venda

Plano recuperado da conversa, posterior às etapas 1 a 9 do fluxo principal. Estas seis etapas são um novo ciclo; não renumeram nem substituem o trabalho concluído.

## Como executar no outro chat

Leia a orientação inicial e execute somente uma etapa por solicitação. Comece pela etapa 1. Ao terminar, registre aqui evidências, arquivos alterados, verificações e limitações; aguarde a próxima solicitação. Não marque uma etapa concluída quando faltar material ou decisão da escrevente. Não execute nem ative a IA externa ao receber apenas este plano.

Prompt curto: `Leia docs/PLANO_PILOTO_PROFISSIONAL.md, siga a orientação inicial e execute somente a etapa 1 do novo ciclo. Informe o resultado, os testes pertinentes e o que depende de mim ou da escrevente.` Nas solicitações seguintes, substitua o número da etapa.

## Acompanhamento

| Etapa | Objetivo | Situação |
|---|---|---|
| 1 | Diagnóstico da adaptação profissional | Diagnóstico técnico entregue; material e decisões profissionais pendentes (ver registro abaixo) |
| 2 | Parametrizar padrão autorizado | Preparação v1 entregue; revisão/correções e aprovação da escrevente marcadas como pendentes; usuário autorizou avançar à etapa 3 |
| 3 | Configurar primeiro cenário | Configuração técnica provisória preparada; hipótese e regras profissionais aguardam confirmação da escrevente |
| 4 | Percorrer atendimento acompanhado | Depende de padrão aprovado e revisão dos controles de dados |
| 5 | Conferir minuta e exportações | Depende da revisão da escrevente |
| 6 | Ativar e avaliar IA real | Adiada até autorização específica e créditos |

O PR foi aberto com somente o plano; as execuções posteriores estão registradas abaixo. Os arquivos versionados não contêm documentos reais nem dados pessoais do exemplo. O provedor documental real continua bloqueado. A conferência manual do piloto não comprova a qualidade da IA.

### Registro da etapa 3 — configuração provisória, 25/10/2026

- O usuário autorizou expressamente avançar à etapa 3 mantendo pendências da etapa 2. Revisão/correções e aprovação da redação pela escrevente ficam **pendentes**, sem serem declaradas concluídas.
- [Configuração executável provisória](piloto-profissional/cenario-provisorio-v1.json) e [relatório](piloto-profissional/ETAPA_3_CENARIO_PROVISORIO.md): participação direta, uma pessoa vendedora, uma compradora, um imóvel, pagamento previsto; hipóteses de teste ainda não homologadas. Seis posições, vínculos explícitos, campos exigidos provisoriamente, dependências e três blocos condicionais. Não contém dados do exemplo nem uma minuta profissional integral.
- Configuração reutiliza o contrato existente, sem novo motor ou importação automática. Mantém `aprovado=false`. Somente o banco isolado dos testes recebeu aprovação simulada para exercitar o caminho positivo; banco operacional e decisões profissionais intactos.
- **37 testes passaram em 61,843 s**, incluindo seis novos em `tests.test_cenario_piloto_provisorio`, quatro do pacote e 27 de blocos/redação. Testados pagamento previsto sem quitação, nomes iguais com IDs separados, troca de vínculo recusada, pagamento fora do domínio bloqueado, campo obrigatório ausente e revisão de dependências após correção de preço.
- Verificações de sistema, migrações e diff sem problemas. Arquivos desta etapa: configuração JSON, relatório, testes novos e este plano. Sem alteração de código de produção, configuração do ambiente, banco operacional ou IA externa.
- **Etapa 3 profissional permanece pendente** da confirmação/substituição da hipótese pela escrevente, aprovação de campos/documentos/regras e conexão da redação profissional aprovada. Fora do cenário: interromper para decisão humana; o mecanismo não interpreta juridicamente uma exclusão justificada. Não declarar bloqueio semântico universal.
- Etapa 4 não iniciada; aguardar nova solicitação.

### Atualização da etapa 2 — preparação v1, 25/10/2026

#### Verificação técnica adicional autorizada, sem aceite humano

- A pedido do usuário, executado somente o trabalho independente de decisões profissionais. [Relatório](piloto-profissional/VERIFICACAO_TECNICA_SEM_ACEITE_HUMANO.md).
- Quatro novos testes em `apps/notarius-api/tests/test_pacote_piloto_profissional.py` validam o pacote entregue: contrato/guardas reais, recusa de quitação fixa, persistência/reabertura como rascunho e bloqueio de geração mesmo com campos fictícios completos enquanto não aprovado.
- **57 testes passaram em 38,003 s**: pacote, ficha, redação estruturada, blocos e preparação documental. Banco isolado, dados fictícios; sem chamadas externas. Django `check`, verificação de migrações e `git diff --check` sem problemas.
- Alterações desta rodada: testes novos, relatório técnico e este registro. Sem mudanças de código de produção, modelo, configurações, banco operacional ou decisões profissionais. Preparação técnica verificada; aprovação da escrevente e configuração do cenário continuam pendentes. Não houve avanço automático à etapa 3.

- O usuário confirmou documento completo/ordenado e tarjas somente em dados sensíveis; autorizou prosseguir com o contexto e consulta de referências. Não se solicita retirada das tarjas nem revelação dos dados pessoais. Pendências anteriores de integralidade e texto de cláusula oculto foram resolvidas por esse esclarecimento.
- [Redação parametrizada v1](piloto-profissional/REDACAO_PARAMETRIZADA_V1.md): fórmulas candidatas detalhadas por seção, parâmetros, confirmações e condições; concordâncias de outorgante/outorgado, vendedor/comprador, gênero, quantidade e cargo, sem dedução pelo nome. Texto adaptado identificado, sem importar cláusulas de modelos externos.
- [Pacote técnico v1](piloto-profissional/modelo-v1.json): versão, origem e objeto de modelo com os 23 campos existentes, `aprovado=false`, sem posições, obrigatoriedades ou dependências configuradas. Fórmulas factuais ficam no documento de revisão, não embutidas como fatos fixos. Sem importação em biblioteca/atendimento.
- Verificação específica do arquivo v1 pelo `SalvarModeloSerializer`, `redacao.validar_modelo` e `validar_fatos_fixos`: passou; 23 campos cobertos, delimitadores aceitos, aprovação falsa e cenário vazio. Busca de CPF, valores monetários e datas do exemplo nos dois novos arquivos sem ocorrências; revisão manual sem transferência de dados pessoais. Sem gravação no banco. Os seis testes registrados abaixo são da rodada v0; não foram repetidos ou apresentados como nova bateria.
- Consulta pública ao art. 215 em fonte oficial para terminologia, sem enviar documento/dado pessoal à pesquisa, sem extrair novos requisitos jurídicos. Fonte e limite registrados no relatório. `git diff --check` sem erros.
- **Preparação técnica entregue para revisão. Etapa 2 ainda aguarda decisão da escrevente**, como exige a orientação inicial; não houve aprovação automática, liberação para caso real ou avanço à etapa 3. Abaixo fica o histórico v0, superado onde menciona falta de páginas/texto legível.

### Histórico parcial da etapa 2 — v0, 25/10/2026

- Material: cinco imagens enviadas pelo usuário; originais preservados em pasta privada fora do repositório. Leitura visual, sem reconstruir tarjas, consultar links ou enviar a provedor externo.
- Entrega para revisão: [rascunho parametrizado](piloto-profissional/modelo-v0.txt) e [mapa de texto/dados, confirmações, condições e dúvidas](piloto-profissional/REVISAO_MODELO_ETAPA_2.md). Só títulos e estrutura segura como texto fixo candidato; fatos, declarações e resultados ficam variáveis. Não se declara transcrição integral.
- Verificações: 23 marcadores conferidos contra os campos existentes, delimitadores íntegros e rascunho sem CPF, e-mail, links, valores ou datas do exemplo; **6 testes de `tests.test_modelo_referencia` passaram em 9,422 s**, em banco isolado. Verificação de sistema sem problemas e `git diff --check` sem erros. Testes fictícios verificam o mecanismo existente, não homologam este padrão ou as cláusulas.
- Arquivos alterados: este plano, `docs/piloto-profissional/modelo-v0.txt` e `docs/piloto-profissional/REVISAO_MODELO_ETAPA_2.md`. Nenhuma mudança de código, banco operacional, aprovação, biblioteca, regras ou cenário.
- **Etapa 2 não concluída:** faltam texto fixo legível onde há tarjas, confirmação da integralidade/ordem, autorização da escrevente e revisão de redação/aplicabilidade. O rascunho não foi carregado como modelo aprovado. Aguardar revisão; etapas 3 a 6 não executadas.

### Registro da etapa 1 — 25/10/2026

- Relatório: [Diagnóstico da adaptação profissional](DIAGNOSTICO_PILOTO_PROFISSIONAL_ETAPA_1.md), com reaproveitamento, ajustes, material/decisões pendentes e critérios propostos para o primeiro caso acompanhado.
- Base inspecionada: `75b2857`, branch `codex/plano-piloto-profissional`, confirmada como origem do PR #2 de `evgrotz/notarius`. Lidos os documentos da orientação inicial e a conclusão da etapa 9 na seção 23 de `EXECUCAO_FLUXO_PRINCIPAL.md`.
- Verificação nesta rodada: **33 testes passaram**, em banco de testes isolado, com `manage.py test tests.test_preparacao_documental.PreparacaoOfflineTests tests.test_blocos_minuta tests.test_redacao_estruturada --noinput` (22,525 s); verificação de sistema sem problemas e `git diff --check` sem erros. São testes fictícios/offline; não comprovam IA real ou aceite profissional.
- Arquivos alterados: este plano e `docs/DIAGNOSTICO_PILOTO_PROFISSIONAL_ETAPA_1.md`. Sem mudanças de implementação ou configuração; sem dados reais ou envio externo.
- Pendências: padrão integral autorizado, esclarecimento de rasuras, cenário/participantes, campos/fontes, condições das cláusulas e apresentação aprovados pela escrevente; usuário organiza entrega privada, acompanhamento e condições de operação local.
- Diagnóstico técnico entregue, **sem marcar adaptação ou homologação profissional como concluída**. Etapas 2 a 6 não executadas; aguardar nova solicitação.

## Prompts de cada etapa

### Orientação inicial

```text
Vamos adaptar o Notarius existente para um piloto acompanhado de compra e venda com documentos reais.

Não recomece nem substitua a arquitetura. Leia primeiro:
- docs/EXECUCAO_FLUXO_PRINCIPAL.md
- docs/REVISAO_ETAPAS_1_A_8_E_PROXIMOS_PASSOS.md
- O relatório da etapa 9, se já estiver concluído.

Reaproveite ficha detalhada, documentos, fontes, propostas, comparação, pendências, conversa, modelos, versões e exportação.

Regras:
- Não inventar fatos, cláusulas, vínculos ou exigências jurídicas.
- Toda informação deve ter origem identificável.
- Proposta extraída não significa dado confirmado.
- Dúvidas e divergências dependem da escrevente.
- Não enviar dados reais a provedores externos sem autorização específica.
- Não colocar documentos reais, dados pessoais, banco ou credenciais no Git.
- Preserve os testes fictícios: eles continuam necessários.
- Mantenha a interface simples e explique os limites reais da entrega.

Execute somente a etapa solicitada. Não acrescente funcionalidades periféricas nem declare homologação profissional por conta própria.
```

### Etapa 1 — preparar a adaptação

```text
Inspecione o estado atual do código e identifique o que falta para usar um padrão profissional de compra e venda.

Entregue:
1. O que pode ser reaproveitado.
2. Ajustes necessários no modelo, campos, vínculos e interface.
3. Lista curta do material e das decisões que precisamos obter da escrevente.
4. Critérios de aceite para o primeiro caso real acompanhado.

Não altere configurações para simplesmente remover avisos ou liberar bloqueios. Não declare a análise por IA funcional sem verificar a implementação e seus testes reais.
```

### Etapa 2 — transformar o padrão dela em modelo

```text
Com o modelo profissional autorizado e disponibilizado pela escrevente, prepare sua versão parametrizada.

Separe:
- Texto fixo do padrão.
- Dados das pessoas e do imóvel.
- Condições do negócio.
- Declarações que dependem de confirmação específica.
- Cláusulas condicionais e suas condições de aplicação.

Não copie os fatos do exemplo para atendimentos novos. Não reconstrua partes ilegíveis ou rasuradas. Registre dúvidas para decisão da escrevente.

Guarde o documento original e o material com dados reais fora do Git. Apresente a adaptação para revisão dela antes de marcar o modelo como aprovado. Se o material estiver ausente, informe exatamente o que falta.
```

### Etapa 3 — configurar o primeiro cenário

```text
Após as decisões da escrevente, configure o primeiro cenário de compra e venda atendido pelo modelo.

Implemente seus campos obrigatórios, posições, vínculos, dependências e condições de inclusão de cláusulas, reaproveitando a estrutura existente.

Não transforme essas escolhas em regras jurídicas universais. Situações fora do cenário devem parar para decisão humana.

Teste com dados sintéticos derivados da estrutura, sem reproduzir dados pessoais reais. Confirme que pagamento previsto não vira quitação e que participantes não são associados por semelhança de nome.
```

### Etapa 4 — preparar o atendimento real acompanhado

```text
Prepare o percurso de um caso real acompanhado pela escrevente, inicialmente com conferência manual e sem envio externo.

Verifique:
- Upload e acesso restrito aos originais.
- Qualidade e limites da leitura/OCR.
- Identificação explícita de pessoas e documentos.
- Fontes de cada dado e tratamento de divergências.
- Preenchimento do padrão aprovado.
- Revisão, edição, desatualização e exportação.

Não confirme dados nem aprove decisões profissionais no lugar dela. Corrija dificuldades de interface encontradas e mantenha pendente aquilo que não conseguiu interpretar.
```

### Etapa 5 — conferir o documento produzido

```text
Depois da revisão e aprovação da escrevente, confira tecnicamente a minuta e os arquivos Word/PDF.

Compare texto salvo e exportado, nomes, números, valores, acentos, ordem dos participantes, cláusulas incluídas/omitidas e formatação.

Preserve o histórico de correções. Alterações nos dados devem invalidar a versão anterior quando aplicável.

Registre separadamente:
- Verificações técnicas realizadas.
- Decisões aprovadas pela escrevente.
- Limitações e problemas ainda abertos.

Não coloque os arquivos reais exportados no Git nem declare validade jurídica por conta própria.
```

### Etapa 6 — ativar a IA quando eu autorizar

```text
Somente quando eu informar que disponibilizei créditos e autorizar os testes externos, revise e ative a integração real de IA.

Comece pela bateria fictícia. Verifique extração, associação correta das pessoas, fontes, omissões, divergências e interrupção por dúvida.

Antes de qualquer teste com dados reais, apresente quais documentos/textos serão enviados e a qual provedor, para minha autorização específica.

Mantenha propostas separadas de confirmações. Não use simulação como fallback no atendimento normal. Informe custo observado e falhas, sem expor credenciais.
```
