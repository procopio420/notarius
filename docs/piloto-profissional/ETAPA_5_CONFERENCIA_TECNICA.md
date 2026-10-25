# Etapa 5 — conferência técnica com amostra fictícia

25/10/2026. Continuação autorizada pelo usuário. **Não houve minuta profissional real revisada/aprovada pela escrevente.** Esta rodada verifica tecnicamente os mecanismos de edição/exportação com texto fictício e preserva as pendências anteriores. Não inicia a etapa 6, não ativa IA e não declara validade jurídica.

## O que foi conferido

Foram acrescentados dois testes em `apps/notarius-api/tests/test_exportacao_piloto.py`. Usam o exportador da aplicação com nomes explicitamente fictícios, acentos, referência numérica com zeros, valor monetário sintético, caracteres literais `<`, `>` e `&`, linha em branco e 65 linhas numeradas para forçar paginação.

- **Word:** igualdade de todas as linhas do corpo salvo, inclusive linha em branco e caracteres literais, após os três parágrafos de identificação adicionados pelo exportador. Dimensões A4 verificadas com tolerância para a unidade interna do Word.
- **PDF:** comparação do corpo inteiro e sua ordem, após retirar cabeçalho, metadados e rodapés conhecidos e normalizar espaços/quebras de linha de extração. A normalização não comprova preservação de espaços múltiplos ou linhas em branco; esses aspectos não devem ser tratados como equivalência literal de layout.
- **Regressões:** revisão final, edição, comparação entre versões, bloqueio de download desatualizado/não autorizado, caractere não suportado recusado sem substituição silenciosa, paginação longa e regras do cenário provisório.
- **Cláusulas/repetições:** casos fictícios de bloco omitido, repetição em posições explícitas e edição/exportação preservando rastreabilidade; isso não decide quais cláusulas profissionais são aplicáveis.

O exportador insere título, aviso de minuta, versão, modelo, tipo de edição e data; esses elementos não fazem parte do corpo salvo e foram tratados separadamente na comparação. A apresentação é genérica; não reproduz cabeçalhos, selos, manifesto ou assinatura da referência enviada. O horário dos metadados do exportador utiliza `America/Sao_Paulo`, como já implementado; esta rodada não homologa essa escolha para o equipamento/cenário da escrevente nem alterou a configuração.

## Inspeção visual

Amostras geradas com os exportadores reais da aplicação a partir da fixture fictícia, sem banco operacional. Arquivos intermediários em `.local/piloto-etapa5/`, fora do Git:

- `amostra-ficticia.docx` e `amostra-ficticia.pdf`;
- `texto-salvo-ficticio.txt`;
- três imagens `pdf-pagina-1.png` a `pdf-pagina-3.png`, renderizadas com Poppler.

As três páginas do PDF foram abertas e inspecionadas: A4, texto legível, acentos e caracteres literais visíveis, sem sobreposição/corte; numeração e rodapés presentes, sequência das linhas e marcador final preservados. Trata-se de inspeção da amostra técnica, sem equivalência visual ao padrão profissional ou aprovação no programa da escrevente.

Tentativa de renderizar Word com `render_docx.py` não concluiu: `LibreOffice soffice.exe was not found on PATH`. O runtime fornecido não disponibiliza o conversor neste Windows. Não se utilizou o aplicativo pessoal de escritório nem se instalou software no computador para contornar isso. **Word validado por conteúdo/estrutura, mas inspeção visual do Word continua pendente.** Os intermediários de QA não são apresentados como documentos profissionais finais.

## Execução e limites dos testes

A primeira seleção executou 20 testes em 45,465 s: 19 passaram e um teste novo de dimensão A4 falhou por comparar 21 cm com a conversão interna de 21,000861 cm. O teste foi corrigido para comparação aproximada com duas casas decimais; não houve alteração no exportador nem no conteúdo. O teste corrigido e três casos adicionais pertinentes de blocos passaram na verificação final: **4 testes em 3,776 s**. Portanto, **23 testes distintos aprovados ao final das duas seleções**, sem somar a repetição do teste corrigido como teste novo. Verificação de sistema e `git diff --check` sem problemas.

As aprovações/decisões exercitadas nos testes são simuladas em banco isolado. Não houve revisão final feita pelo agente em atendimento real, mudança de implementação de produção, credenciais ou envio externo. As amostras não contêm fatos da escritura enviada.

## Pendências para concluir profissionalmente

| Responsável | O que falta |
|---|---|
| Escrevente | Aprovar/corrigir a redação da etapa 2 e o cenário/regras da etapa 3. |
| Usuário e escrevente | Conferir condições locais e executar o atendimento acompanhado da etapa 4. |
| Escrevente | Rever o conteúdo e as fontes da versão exata do caso; decidir cláusulas, nomes/papéis, números, valores e concordâncias. |
| Desenvolvimento e escrevente | Comparar os Word/PDF do caso aprovado com o texto salvo, conferir aparência no programa utilizado e resolver divergências; inspeção visual do Word ainda não feita nesta rodada. |

**Estado:** conferência técnica fictícia documentada; etapa 5 profissional pendente. IA real continua bloqueada, sem créditos/modelo/autorização presumidos. Aguardar nova solicitação.
