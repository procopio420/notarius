# Etapa 17 — revisão final da minuta por versão

Antes de baixar Word/PDF, a versão atual precisa de um registro explícito de revisão final da escrevente. Funciona localmente, sem IA externa.

## Percurso

1. Prepare e abra a minuta após resolver as pendências e revisar o modelo.
2. Leia o texto completo; confira os dados usados e os documentos originais. Se necessário, edite e salve uma nova versão.
3. Clique em **Registrar revisão final da vN**.
4. Confirme separadamente que leu o texto, conferiu os dados/condições e conferiu as fontes. Registre a observação ou motivo da revisão.
5. **Registrar conferência desta versão** salva autora/autor, data e motivo vinculados ao texto exato. Só então os botões Word/PDF são liberados, se as demais condições continuarem válidas.

A confirmação é um registro de conferência humana, não assinatura, conclusão do ato, prova de autenticidade ou homologação jurídica. O sistema não confirma por conta própria que o trabalho foi efetivamente feito.

## Proteções

- Revisão vinculada a uma versão e hash do texto salvo; alteração direta dos bytes invalida a correspondência.
- Minuta nova/editada não herda a revisão anterior. O histórico da versão antiga permanece.
- Novas informações, releitura de anexo ou alteração de modelo/ficha continuam desatualizando a minuta pelo mecanismo existente. Uma revisão antiga não contorna esses bloqueios.
- Apenas a versão atual, compatível com os dados e sem pendências, pode receber a revisão final.
- Reenvio idêntico pela mesma pessoa retorna o registro anterior; tentativa de sobrescrever motivo/autoria é rejeitada.
- Acesso limitado ao atendimento/cartório. Word e PDF validam a revisão no servidor, além da trava da tela.
- A migração 0012 não aprova versões antigas automaticamente. Elas passam a precisar dessa conferência antes de um novo download.
- A revisão geral e o resumo TXT também indicam a existência ou ausência da revisão final.

## Verificação

73 testes Django passaram (69 anteriores e quatro novos). Foram verificados bloqueio sem revisão, confirmações explícitas, reenvio sem duplicação, exportação após revisão, edição sem herança, dados novos após revisão, isolamento e correspondência do hash. Os testes de Word/PDF existentes passaram após registrar a revisão final no percurso.

ESLint passou nos componentes, páginas de atendimento e cliente da API. Percurso conferido no navegador com um novo atendimento e documentos inteiramente fictícios. Não houve chamada à IA externa.
