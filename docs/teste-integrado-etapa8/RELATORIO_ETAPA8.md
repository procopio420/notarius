# Notarius — teste integrado da função principal

Data: 25/10/2026. Escopo: documentos → propostas → vínculos → perguntas → confirmação humana → preenchimento → edição → revisão final → Word/PDF → correção/desatualização. Todo o conteúdo utilizado é fictício. Não foram enviados dados a provedores externos, alterada cobrança ou exibida chave de API.

## Resultado

Passaram **143 testes** na bateria final (`.local/etapa8-regressao-final.log`), incluindo **10 testes novos**: nove percursos integrados e uma verificação de rótulos/isolamento. O percurso com múltiplos participantes executa subcasos de vários vendedores e de vários compradores. A bateria inclui também conversa, blocos da minuta, redação, comparação entre fontes, pendências, organização de anexos, contrato documental/provedor bloqueado, atendimento/exportação, ficha, migração e concorrência SQLite. Não equivale a homologação notarial, medição de qualidade de IA ou teste com uma escrevente real.

## Matriz dos cenários integrados

| Cenário | O que foi verificado | Resultado |
|---|---|---|
| Compra e venda simples | Originais TXT preservados; upload; classificação explícita; proposta simulada sem escrever na ficha; confirmação simulada com fonte; leitura/revisão de página; vinculação; recarga; preenchimento; edição; comparação; revisão final; Word/PDF | Passou |
| Mais de um vendedor ou comprador | Subcasos separados, IDs próprios, nomes próximos, papéis explicitamente ligados à pessoa, ordem de repetição e origem por campo | Passou |
| Cônjuge informado | Estado civil/nome não criam relação. Relação é criada explicitamente com os dois IDs. Cônjuge não se torna comprador/vendedor automaticamente | Passou |
| Representação com dúvida | Dado do instrumento fica informado, há pendência humana e a minuta bloqueia. Retomada somente após confirmação e decisão específicas simuladas, sem atestar poderes jurídicos reais | Passou |
| Documentos divergentes | Preços de R$ 100.000,00 e R$ 120.000,00 ficam separados; associação expressa; divergência visível; nenhum valor escolhido pelo sistema; decisão simulada e revisão da comparação com evidências | Passou |
| Página sem leitura/parcial | PDF sintético com segunda página em branco e falha de OCR simulada; cobertura exposta; preparação bloqueada. Retomada apenas após decisão humana simulada de não utilizar a cópia sem uso nos dados | Passou, não demonstra recuperação de uma página ilegível |
| Informação ausente | Condição de pagamento requerida fica inexistente na ficha; pergunta específica e bloqueio. Não se sintetiza resposta. Só informação explicitamente fornecida permite continuar | Passou |
| Pagamento futuro | Situação permanece previsto; não cria quitação; mudança para outra situação fora do modelo fictício interrompe a preparação | Passou |
| Correção após minuta/revisão | Primeiro prepara/edita/revisa/exporta; depois corrige mensagem de origem. Original preservada, pendência reaberta, dado não reescrito sozinho e download da versão antiga recusado | Passou |

Em todos os percursos concluídos, os testes fazem edição com motivo, comparam versões, exigem revisão final antes do download e conferem o texto do Word/PDF contra a versão salva. As fontes dos dados e as decisões dos blocos continuam vinculadas à versão de base após edição. Alterações manuais livres não são semanticamente validadas pelo sistema.

## O que foi simulado

- Provedor `simulado_documental_teste_v1`, exclusivo de teste e banco isolado, com resposta determinística sobre nomes explicitamente rotulados. Não mede compreensão de documentos livres.
- Decisões, confirmações, aprovação do modelo fictício, revisão de páginas, resolução de conflitos e revisão final executadas pelo código dos testes, com justificativas que as identificam como simulações. Não são decisões da escrevente real.
- Falha de OCR no teste de página parcial. A segunda página é intencionalmente em branco; não é uma amostra real de documento danificado.
- Redação fictícia, sem validade profissional e sem reconstruir os trechos rasurados das imagens enviadas.

## O que foi verificado localmente de fato

- Execução dos endpoints Django e persistência/histórico/transações no ambiente de testes, processamento de TXT/PDF sintéticos, conferência dos arquivos exportados com leitores locais e bloqueios por versão/fonte/pendência.
- Navegação no navegador local das três áreas e dos formulários, incluindo vários participantes, cobertura de leitura parcial e comparação dos preços divergentes, com foco em reduzir códigos difíceis para a usuária. A prova visual não confirmou dados nem aprovou modelos.
- Nove atendimentos de demonstração no cartório fictício, com documentos e propostas locais por rótulos, todos sem dados confirmados, sem modelos aprovados e sem minutas. Catálogo auditado em `.local/etapa8-catalogo.json` e `.local/etapa8-auditoria-final.json`: 25 documentos, 25 propostas e zero confirmações, aprovações, minutas, análises de IA ou vinculações de minuta salvas pelo agente.
- O PDF de demonstração na pasta `arquivos` tem texto na primeira página e segunda página em branco. O processamento do navegador/servidor é local; seus avisos devem ser lidos, sem tratar página sem texto como prova de inexistência de fato.

## Falhas encontradas e correções

1. **Rótulos pouco claros na escolha dos registros.** O seletor mostrava papel, código e função, mas não a pessoa vinculada. Com vários vendedores, isso dificulta uma escolha consciente. Agora ficha, conversa e seletor recebem rótulos com o nome registrado e vínculo expresso, mantendo ID para distinguir registros. Os rótulos não confirmam identidade nem criam relações. Nomes longos passam a quebrar em linhas no seletor, para evitar corte na janela estreita. Há teste com dois papéis vendedor e pessoas de nomes próximos, além de recusa entre cartórios autorizados.
2. **Motivos de exclusão prematuros.** Ao abrir a vinculação, apareciam motivos para todos os registros antes de escolher as posições. Agora a tela pede primeiro as escolhas e mostra motivos apenas para o que realmente sobrar. Salvar também exige todas as posições, motivos individuais necessários e modelo aprovado. O servidor mantém suas verificações; nada é escolhido automaticamente.
3. **Erro no próprio roteiro de teste de divergência.** A primeira execução tentou classificar documento diretamente na negociação e recebeu 404. O roteiro foi corrigido para vincular o documento ao imóvel e associar a proposta de preço à negociação. A restrição do produto foi preservada; não é falha de isolamento corrigida no produto. A repetição individual passou e a bateria final passou integralmente.
4. **Botão de leitura com destino enganoso.** “Voltar à conversa” apenas fechava a leitura e mantinha a aba Documentos. Foi renomeado para **Fechar leitura**, sem alterar dados ou decisões. A aba Conversa continua sendo a navegação explícita.
5. **Aviso recuperável ao abrir o atendimento.** O HTML inicial continha um estilo global do tema onde o primeiro carregamento do cliente esperava o indicador de espera. A inicialização do estilo global passou a ocorrer após a primeira renderização compatível, sem suprimir avisos ou contornar autenticação. Após reiniciar o servidor de interface para eliminar o pacote anterior em memória, o HTML inicial não contém esse estilo e a recarga do atendimento não exibiu o erro. O restante do tema e a proteção de acesso foram preservados.
6. **Roteiro antigo com instruções desatualizadas.** Foi marcado como histórico e apontado para o roteiro atual; não se orienta mais que OCR inexiste nem que exportação dispense revisão final.

## Exercícios disponíveis para acompanhamento

| Nº | Cenário fictício | Navegador local |
|---|---|---|
| 1 | Compra e venda simples | [Abrir exercício](http://localhost:3002/atendimentos/caefe3c0-5620-49d1-9d8c-6c95e1260f3f) |
| 2 | Vários vendedores e compradores | [Abrir exercício](http://localhost:3002/atendimentos/e4b8d048-dd6d-459f-987c-76eefab7c204) |
| 3 | Cônjuge explicitamente informado | [Abrir exercício](http://localhost:3002/atendimentos/2d173f29-9250-497a-ba22-5da9bc13618b) |
| 4 | Representação com dúvida humana | [Abrir exercício](http://localhost:3002/atendimentos/082fe1ff-715a-47db-9fbb-e7b3581c1dda) |
| 5 | Documentos com preços divergentes | [Abrir exercício](http://localhost:3002/atendimentos/346fcc78-6574-4147-8b0f-71cd1ed08b26) |
| 6 | Documento com página sem leitura | [Abrir exercício](http://localhost:3002/atendimentos/42574ea7-d691-494b-bbaf-0ac321997a9f) |
| 7 | Condição de pagamento ausente | [Abrir exercício](http://localhost:3002/atendimentos/5624471a-321d-4d7f-8218-48e0b2452892) |
| 8 | Pagamento futuro sem quitação | [Abrir exercício](http://localhost:3002/atendimentos/d50a11c5-e8cf-4660-af1f-66f82feab1b9) |
| 9 | Correção após minuta — exercício acompanhado | [Abrir exercício](http://localhost:3002/atendimentos/94a5e65a-5b1e-4891-8fef-1422f14010d2) |

Os nove exercícios no navegador estão deliberadamente pendentes. Confirmar/aprovar no banco local é uma ação da escrevente durante o exercício. Não foi criada uma minuta artificialmente aprovada só para parecer que o percurso passou. O cenário 9 deve ser preparado/revisado pela usuária antes da correção acompanhada; seu bloqueio após correção já foi percorrido integralmente no teste automatizado isolado.

Evidências visuais da inspeção: `.local/qa-etapa8-participantes.png`, `.local/qa-etapa8-leitura.png` e `.local/qa-etapa8-divergencia.png`. As confirmações ficaram desmarcadas e decisões não foram salvas durante a inspeção.

Verificações de código: Django `check` e migrações sem problemas; ESLint das áreas alteradas sem erros/avisos; TypeScript sem erros nessas áreas, mantendo erros globais anteriores fora delas. Não se declara build global limpo.

## Avaliações ainda pendentes

- Sua mãe realizar o [roteiro curto](ROTEIRO_PARA_MAE.md): medir dificuldade, tempo, necessidade de ajuda, linguagem, entendimento de fonte/pendência e revisão. A inspeção do agente não comprova facilidade para uma usuária iniciante.
- Homologação do texto profissional e dos cenários/requisitos pela escrevente, conforme seção 21.4 do documento único de execução. Exigências jurídicas e documentais não foram inventadas.
- Avaliação real de IA com autorização e amostras apropriadas: precisão por campo, pessoa/papel/imóvel correto, página/leitura/trecho, omissões, divergências, recusas, injeções maliciosas e interrupção por incerteza. Nenhuma chamada real foi realizada nesta etapa. O provedor real continua bloqueado e não há fallback silencioso.
- Qualidade de OCR com documentos fictícios degradados representativos; o PDF em branco e o erro simulado não medem essa qualidade. Autenticidade, identidade, poderes de representação, titularidade e veracidade não são comprovados pelo sistema.
- Revisão visual dos arquivos no Word/PDF usados pela escrevente, acessibilidade completa, outros dispositivos, produção/PostgreSQL, segurança e desempenho de produção. Nesta etapa foi conferido o conteúdo salvo/exportado, não houve certificação de aparência editorial ou prontidão para produção.
- Checagem TypeScript global: mantém erros anteriores fora das áreas de atendimento verificadas, registrados em `.local/etapa8-types.log`; não se declara build global limpo.

Critério para continuar: testes fictícios sem dados presumidos nem confirmação automática, pendências visíveis, fontes e histórico preservados; depois validar o roteiro com a escrevente e homologar o padrão. O resultado atual é um fluxo local testado, com decisões profissionais e IA real ainda pendentes.
