# Revisão das etapas 1 a 8 e próximos marcos

Data: 25/10/2026. Revisão do checkout local enquanto a etapa 9 está sendo executada em paralelo. Não houve alteração de implementação, configuração, servidores, dados locais ou decisões profissionais nesta revisão. A etapa 9 não é declarada concluída ou validada por este documento.

## Parecer

As etapas 1 a 8 implementaram a estrutura central que faltava ao primeiro protótipo. O resultado é um fluxo local de compra e venda com ficha por objetos, fontes, pendências, modelo parametrizado, revisão e exportação. Não equivale a interpretação documental real validada nem a um produto homologado para uso profissional.

| Etapa solicitada | Evidência no código/documentação | Avaliação |
|---|---|---|
| 1 — Diagnóstico | EXECUCAO_FLUXO_PRINCIPAL.md consolida fluxo, lacunas, decisões e critérios | Documentado; preservar como referência única |
| 2 — Ficha detalhada | ficha_estruturada.py e ficha_estruturada_schema.py: pessoas, CPF/documento, papéis, relações, imóvel e negociação separados | Implementado; campos obrigatórios dependem do modelo homologado |
| 3 — Documentos e vínculos | organizacao_anexos.py e metadados/versionamento de leitura | Implementado; associação explícita e referências de redação separadas dos documentos do caso |
| 4 — Contrato documental | contratos_documentais.py, analise_documental.py e provedor_documental.py | Validação de propostas implementada; transporte/provedor real ainda bloqueado no estado inspecionado |
| 5 — Comparação | comparacao_fontes.py, pendencias_ficha.py e dependencias_ficha.py | Comparação conservadora por registro e campo; não é interpretação geral nem prova de identidade |
| 6 — Conversa | conversa_orientada.py e correção versionada de mensagens | Orientação local e perguntas ligadas às pendências; compreensão livre não demonstrada |
| 7 — Minuta detalhada | redacao_estruturada.py e blocos_minuta.py: marcadores, posições, repetições e condições explícitas | Preenchimento rastreável implementado; modelo profissional ainda não homologado |
| 8 — Integração | test_funcao_principal_integrada.py e teste-integrado-etapa8/RELATORIO_ETAPA8.md | Nove cenários sintéticos e dez testes novos; provas positivas usam decisões/provedor simulados em banco isolado |

## Limites que precisam permanecer claros

1. O ProvedorReal.analisar inspecionado recusa a chamada. Existe construtor de requisição e decodificação de resposta, mas não envio real neste estado. Acrescentar saldo, sozinho, não remove esse bloqueio. A etapa 9 precisa explicitar o que deixou preparado e o que depende de autorização posterior.
2. Os casos integrados usam, na extração simulada, nomes explicitamente rotulados. Eles exercitam o percurso e as proteções, mas não comprovam compreensão geral de RG, CPF, certidões ou matrícula.
3. A ficha tem campos de CPF/RG e outros dados. Sua obrigatoriedade e aplicabilidade não devem ser presumidas: é necessário homologar o modelo e suas regras para o cenário escolhido.
4. O modelo de demonstração está marcado como fictício. O texto profissional integral, cenários, participantes, cláusulas condicionais e critérios de revisão dependem da escrevente; imagens rasuradas não podem ser completadas por suposição.
5. O relatório da etapa 8 registra erros TypeScript globais anteriores fora das áreas verificadas. Não há evidência de build global de produção limpo. Isso precisa ser resolvido antes de publicar uma versão de produção.
6. O checkout tem muitas alterações e arquivos ainda não versionados. Ao estabilizar a etapa 9, registrar uma versão revisável no Git é um marco necessário para entrega e recuperação do código; não foi feito commit de trabalho em andamento nesta revisão.

## Próximos marcos, na ordem

### A — Aceite do fluxo com a escrevente, ainda sem IA externa

Usar o roteiro curto em teste-integrado-etapa8/ROTEIRO_PARA_MAE.md. Começar pelo caso simples e registrar onde ela precisou de ajuda, quanto tempo gastou e quais textos/campos confundiram. Depois percorrer participantes múltiplos, cônjuge, representação, divergência, leitura parcial, informação ausente, pagamento futuro e correção após minuta. Corrigir os bloqueios de uso encontrados antes de adicionar novos módulos.

Em paralelo, converter um padrão completo autorizado em modelo parametrizado e homologar o primeiro cenário com a escrevente. Conferir o Word/PDF no programa que ela realmente usa. A configuração técnica dos marcadores deve ser preparada pelo desenvolvimento; ela deve revisar conteúdo e decisões profissionais.

### B — Avaliação real da IA, quando houver decisão e autorização

Concluir e revisar a preparação da etapa 9. Quando houver créditos/autorização, ativar explicitamente o transporte real e executar primeiro casos fictícios representativos. Medir extração por campo e atribuição à pessoa/imóvel, fonte/página, omissões, dúvidas e divergências. Corrigir falhas e repetir casos afetados. Não tratar contrato JSON e trecho literal como prova de interpretação correta.

### C — Versão piloto estável

Registrar o código revisado no Git; conferir migrações e instalação reproduzível; resolver os erros de compilação necessários ao pacote final; testar backup/recuperação e o acesso no equipamento onde a escrevente trabalhará. Definir o primeiro cenário atendido, os casos que devem parar e quem responde pelos testes.

Só depois decidir implantação e uso real, com configuração operacional adequada e controle de acesso/dados. A etapa atual ainda é piloto local supervisionado; não é liberação para uso autônomo ou exposição pública.

## Evidência de testes

O relatório anterior da etapa 8 registra 143 testes aprovados em .local/etapa8-regressao-final.log. Nesta revisão, os 43 testes reexecutados de integração, comparação, conversa e blocos passaram em 138,341 segundos, em banco isolado (.local/revisao-etapas1a8-testes.log). Não foi repetida toda a bateria de 143 testes. A extração e as decisões positivas dos testes são simuladas; não foram autorizadas chamadas a provedores externos.
