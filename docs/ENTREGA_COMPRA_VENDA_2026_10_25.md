# Entrega do fluxo de compra e venda e preparação do piloto

Data: 25/10/2026. Consolidação do trabalho local para integração na `main` de `procopio420/notarius`.

## O que foi implementado

- Atendimento com conversa orientada, ficha estruturada, participantes identificados por IDs e revisão explícita dos dados.
- Anexos organizados por documento/página, leitura local e OCR, indicação de fontes e comparação de divergências, com histórico de correções.
- Propostas de dados separadas de confirmações humanas; pendências impedem avanço indevido. Pagamento previsto não se transforma em quitação.
- Biblioteca de modelos, blocos e vínculos da minuta, comparação de versões, revisão final e exportação condicionada à revisão atual.
- Interface de atendimentos, recuperação de rascunhos na sessão, feedback do teste e backup local.
- Migrações do fluxo, testes com dados fictícios, cenários de homologação e documentação das seis etapas do piloto profissional.
- Preparação offline da análise documental com contratos, validação e avaliação simulada. O provedor documental real permanece bloqueado.

## Como conferir

O ponto de entrada é [Fluxo principal local](FLUXO_PRINCIPAL_LOCAL.md). O roteiro e o estado do piloto estão em [Plano do piloto](PLANO_PILOTO_PROFISSIONAL.md) e nos documentos de `piloto-profissional/`.

Para iniciar o ambiente já preparado no Windows, usar `scripts/iniciar-teste-local.ps1`. O roteiro utiliza dados fictícios. Não publicar banco, anexos, credenciais ou arquivos de `.local` e `.venv`.

## Limites da entrega

Esta integração entrega o desenvolvimento e sua preparação técnica; não declara homologação profissional ou prontidão de produção. Continuam pendentes a aprovação da redação/cenário pela escrevente, o acompanhamento do caso real, a conferência visual no Word e as condições de uso/backup no equipamento de destino.

IA documental externa não foi ativada nem avaliada com modelo real. Sua implementação/execução exige autorização específica, teto de gasto e testes fictícios, conforme [Ativação da IA documental](ATIVACAO_IA_DOCUMENTAL.md). Documentos reais exigem autorização própria. Os resultados históricos de testes simulados não demonstram qualidade de IA real.

## Validação desta integração

- Django `check`: sem problemas.
- Migrações: `makemigrations --check --dry-run` sem mudanças pendentes.
- ESLint dos componentes/páginas de atendimentos e bibliotecas novas: aprovado.
- TypeScript e ESLint globais: falharam em áreas fora do fluxo de atendimentos, incluindo Cypress, documentos e editor. ESLint global reportou 64 erros e 67 avisos. Esses resultados impedem declarar a interface integralmente validada.
- `git diff --check`: aprovado antes desta documentação.
- Bateria Django geral: encontrou erros de importação por ausência de `pytest` e falhas durante a execução; foi interrompida após ficar sem progresso visível. O diagnóstico com `--failfast` confirmou a dependência ausente em `tests.ai_documents.test_generate_minuta`. Não se declara aprovação da suíte completa.
- CI remoto: os jobs `pii-detection` e `API Performance Testing` falharam ainda na preparação por uso de `actions/upload-artifact@v3` desativado pelo GitHub. Esses fluxos já existiam na base e não foram alterados neste PR; essas falhas não são resultados de testes de PII ou desempenho.
- Regressão selecionada: **65 testes passaram em 76,145 segundos**, sem testes pulados, com `manage.py test tests.test_pacote_piloto_profissional tests.test_cenario_piloto_provisorio tests.test_exportacao_piloto tests.test_ficha_estruturada tests.test_redacao_estruturada tests.test_blocos_minuta tests.test_preparacao_documental --noinput`. Cobertura técnica de pacote/cenário fictício, ficha, redação/blocos, exportação e preparação offline; não substitui a suíte completa nem aceite profissional.

Os relatórios por etapa preservam comandos, resultados e limites das verificações anteriores; suas contagens não devem ser somadas como testes distintos.
