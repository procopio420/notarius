# Entrega do piloto local acompanhado

Integração das etapas operacionais 2 a 4, solicitada em 25/10/2026. Continuação do fluxo existente de compra e venda; não é homologação profissional ou instalação de produção.

## Resultado

O ambiente local passa a ter perfil próprio, início/encerramento, acesso autenticado por cartório, seleção explícita de banco e backup/restauração sem sobrescrita. A configuração do piloto não expõe mídia pública ou módulos legados de envio externo; a IA documental continua bloqueada. Logs da interface deixam de imprimir objetos que podem conter credenciais, e sessão inválida permite novo login.

O padrão parametrizado e o cenário provisório foram reunidos em candidato com 20 posições, 46 referências e mapa dos 23 blocos anteriores. A interface oferece revisão simples e permite carregar, salvar e retomar rascunho, sem aprovação automática. Fontes, confirmações, destinatários e decisões profissionais continuam explícitos.

Um atendimento inteiramente fictício foi concluído por API HTTP local e interface, em banco separado: 20 originais preservados, correção de preço e dependências, três versões de minuta, edição, comparação, revisão final simulada e downloads Word/PDF. Os arquivos finais têm duas páginas cada, com conteúdo conferido e apresentação inspecionada localmente. Foram corrigidos título órfão no PDF, borda/espaçamento do Word e horário dos metadados.

## Operação e revisão

- [Iniciar, encerrar, fazer backup e restaurar](OPERACAO_PILOTO_LOCAL.md).
- [Revisão do padrão pela escrevente](piloto-profissional/REVISAO_PADRAO_ACOMPANHADO_V2.md).
- [Repetir o exercício fictício](piloto-profissional/ROTEIRO_ETAPA_4_FICTICIO.md).
- [Implementação, evidências, limitações e retomada](CONTINUIDADE_PILOTO_REAL.md).

## Integração sem publicação

O workflow CI/CD existente permitia publicação de imagens e deploy a partir da main. A integração passa a exigir `workflow_dispatch` e a opção booleana `publicar_ambiente=true` para esses jobs; o padrão é falso. Push e PR continuam configurados para testes. O workflow separado de release por tag não foi acionado. Nenhum ambiente foi publicado, segredo de infraestrutura consultado ou proteção de branch removida.

Não integram o commit: `.local`, banco operacional ou de exercício, anexos, credenciais, segredos de sessão, backups, logs, instalador/extração do LibreOffice, screenshots e exportações. O índice é conferido antes do envio. As referências a caminhos locais na documentação não incluem seu conteúdo privado.

## Validação e limites

**86 testes passaram em 263,320 segundos**, sem testes pulados, na regressão conjunta desta integração:

```text
manage.py test tests.test_piloto_local tests.test_backup_local tests.test_atendimentos tests.test_exportacao_piloto tests.test_padrao_piloto tests.test_pacote_piloto_profissional tests.test_cenario_piloto_provisorio tests.test_redacao_estruturada tests.test_blocos_minuta --settings=config.settings_piloto --noinput
```

Execução em banco isolado com dados fictícios. Log privado `.local/pr-piloto-regressao.log`. Resultados por etapa e demais comandos estão na continuidade; suas contagens se sobrepõem e não devem ser somadas aos 86. A configuração YAML também foi conferida: publicação/deploy dependem de evento manual e opção explícita, com padrão falso.

As verificações locais de Django, migrações, ESLint dos arquivos alterados e espaços do diff passaram. TypeScript global continua com problemas anteriores fora das áreas alteradas. Há workflows legados que usam actions/upload-artifact@v3 desativado e podem falhar na preparação; isso não equivale a um resultado dos testes. Não se declara suíte global ou CI integralmente aprovado.

O padrão profissional permanece não aprovado. Aprovação e revisão do exercício são simuladas e não se transferem para um caso real. Ainda dependem da escrevente a redação/cenário/aplicabilidade, documentos/fontes do caso e revisão final; a apresentação deve ser conferida no programa usado por ela. O DOCX desta etapa foi renderizado com LibreOffice local, não com Microsoft Word. Persistem os limites de desenvolvimento, SQLite sem criptografia em repouso, backup de até 512 MiB, ausência de auditoria integral do equipamento e qualidade de OCR real não avaliada por este ensaio TXT.
