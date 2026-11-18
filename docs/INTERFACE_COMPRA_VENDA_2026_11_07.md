# Interface simplificada de compra e venda

Revisão de 07/11/2026 solicitada pelo usuário. Alterações apenas na interface do
fluxo de atendimentos, sem mudança no banco, regras de aprovação ou integração de IA.

- Cabeçalho próprio compacto, sem sidebar vazia, busca sem função, notificações
  fictícias ou menus sem ação. Cartório e saída da conta continuam funcionais.
- Lista com busca automática por título, filtros de situação e acesso direto aos
  casos. Criação em diálogo, sem formulário permanente ocupando a página.
- Atendimento organizado em Dados do caso, Documentos e Minuta. Próxima pendência
  destacada; ficha em largura útil; conversa/anotações, resumo e opções avançadas
  recolhidos e disponíveis, com rascunhos e callbacks de fontes preservados.
- Documentos com envio destacado e instruções detalhadas recolhidas. Avisos reais
  de falha, leitura incerta, fontes e revisões permanecem disponíveis.
- Minuta com três etapas e revisão/exportação explícitas. Aprovação de modelo,
  conferência de fontes, atualidade de versão e revisão final continuam exigidas.
- Tema local em verde floresta e fundo claro, tipografia legível, marca serifada,
  espaçamento responsivo e foco visível; sem imagens/fontes de serviço externo.

Verificação desta rodada: TypeScript específico do fluxo e ESLint dos oito arquivos
alterados aprovados. A checagem TypeScript global já tinha falhas legadas e não é
declarada aprovada. Nenhum teste de backend foi repetido para estas mudanças visuais.

Conferência no navegador com a conta local existente: listagem, busca sem resultados
e limpeza, diálogo de criação (sem salvar registro), abrir/fechar ficha, abas de
documentos/minuta e preparação bloqueada sem aprovação. Layout conferido em 1280
e 390 pixels, sem transbordamento horizontal do documento na tela estreita.
Viewport temporário restaurado ao final. Nenhum atendimento, dado ou aprovação
foi criado/alterado nesses ensaios; nenhum arquivo foi enviado ou baixado.

Não houve chamada à API de IA nem consumo de créditos. Capturas ficam em `.local`,
fora do Git. O fluxo continua um piloto acompanhado; o novo visual não homologa
redação profissional nem ativa serviços além de compra e venda.
