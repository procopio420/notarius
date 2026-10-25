# Interface simplificada do atendimento

A tela foi reorganizada após o teste visual do usuário, priorizando navegação simples e legibilidade para a escrevente.

- Três abas com nomes diretos: **Conversa**, **Documentos** e **Minuta**.
- A conversa abre por padrão, com o campo de mensagem acessível e sem a sequência anterior de botões de organização/modelo/resumo/testes.
- Em telas largas, **Próximo passo** e **Dados do atendimento** ficam ao lado da conversa; em telas menores, ficam abaixo.
- Organização e feedback ficam recolhidos em **Mais opções**.
- Opções de uma mensagem e detalhes técnicos da leitura ficam recolhidos, sem retirar suas funções.
- Texto principal de 17 px, botões com alvo de pelo menos 44 px, títulos claros e formulários com mais espaço.
- A ficha tem uma única lista de campos, em cartões, sem repetir os campos em uma lista de pendências separada.
- Os painéis permanecem montados ao alternar abas. A mensagem digitada não é apagada ao navegar entre Conversa, Documentos e Minuta. Isso não é salvamento de rascunho: recarregar/sair ainda pode perder texto não enviado.
- O botão de envio orienta quando a mensagem será salva. As regras de confirmação, revisão final e bloqueio de minuta permanecem no servidor e não foram alteradas.

## Verificação

ESLint passou nos componentes e páginas de atendimento. A checagem TypeScript não apontou erros nos arquivos de atendimento alterados; a checagem global ainda encontra erros anteriores em outras telas/Cypress.

No navegador foram verificados: tela estreita e tela larga, abas por clique/teclado, preservação de mensagem não enviada ao trocar de aba, abertura dos documentos pelo próximo passo, acesso à ficha sem listas duplicadas, opções recolhidas e abertura de uma minuta fictícia já revisada. O rascunho temporário usado no teste foi apagado sem envio. Nenhum dado do atendimento do usuário foi salvo ou alterado nesta verificação.
