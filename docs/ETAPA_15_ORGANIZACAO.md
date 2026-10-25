# Etapa 15 — organização e busca de atendimentos

Disponível sem IA externa.

## Uso

- Na lista, busque pelo título e selecione a situação. Clique em **Buscar** para aplicar os dois filtros. **Limpar filtros** volta a mostrar todos os atendimentos do cartório.
- Dentro do caso, abra **Organizar atendimento** para alterar o título ou a situação: **Em andamento**, **Aguardando informação** ou **Pausado**.
- Informe um motivo. O histórico mostra autor, data, versão, título anterior/novo e situações anterior/nova.
- Retome um caso pausado escolhendo **Em andamento**. Nenhum dado é apagado.

Situação é organização do trabalho, não aprovação documental, conclusão do ato ou avaliação jurídica. Pausar não bloqueia consulta ou edição e não altera a ficha, o modelo ou a minuta. As travas de conferência e exportação continuam independentes. Mudanças apenas de título/situação não invalidam o conteúdo da minuta.

A alteração usa uma versão própria do cadastro para impedir sobrescrita quando duas pessoas organizam o mesmo atendimento. Em conflito, a tela pede atualizar antes de tentar novamente. Não há exclusão ou arquivamento nesta etapa.

Os filtros da lista não afetam o acesso a um atendimento por endereço direto; o isolamento por cartório continua obrigatório em ambos. Atendimentos antigos recebem situação inicial **Em andamento** pela migração 0011.

## Validação

65 testes Django passaram, incluindo pausa/retomada, preservação de mensagens e assinatura dos dados da minuta, histórico, rejeição de versão antiga, campos inválidos e isolamento de busca/histórico entre cartórios. ESLint passou nas páginas/componentes de atendimento e cliente da API.

No navegador, o caso fictício inicial foi marcado **Aguardando informação**, o histórico foi reaberto e a busca combinada por título/situação retornou somente esse caso. Nenhuma API externa foi chamada.
