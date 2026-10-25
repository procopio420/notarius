# Etapa 16 — revisão geral do atendimento

Funciona localmente, sem chamada a provedor de IA. A decisão sobre a API permanece adiada.

Abra o atendimento e clique em **Revisão geral do atendimento** para conferir pendências, último registro de cada campo, situação, versão, autor, motivo e origem. Quando documental, a fonte informa arquivo, página, versão da leitura e canal OCR/texto. A tela reúne também os anexos e a revisão manual da leitura atual, modelo e última minuta.

Um campo pode ter registro confirmado anteriormente e uma pendência atual. A tela mantém ambos visíveis e alerta que a confirmação anterior não resolve novas divergências. Consultar o resumo não cria revisões nem libera preparação ou exportação.

**Atualizar resumo** consulta os dados novamente. Durante atualização ou falha, o resultado anterior não é apresentado como atual. A consulta é montada em transação e verifica mudanças no conjunto de dados e na última minuta; ao detectar conflito, exige nova consulta.

**Baixar resumo TXT** salva os valores, fontes, motivos, documentos, pendências, modelo, minuta e data da consulta. Não inclui arquivos originais nem o corpo da minuta. O arquivo pode conter dados sensíveis e exige os mesmos cuidados do atendimento. É uma fotografia dos registros: alterações futuras não atualizam a cópia.

Não é minuta, aprovação do ato, prova de autenticidade ou checklist jurídico completo. Confira os documentos e a minuta integralmente.

## Verificação

69 testes Django passaram (65 anteriores e quatro novos). Foram verificados atendimento vazio sem escrita, coerência com as travas de preparação, divergência nova que desatualiza minuta, fontes literais, documento pendente de revisão, isolamento por cartório e conflito durante a consulta. ESLint passou nas páginas/componentes de atendimento e cliente da API. A tela foi conferida no navegador usando somente dados fictícios.
