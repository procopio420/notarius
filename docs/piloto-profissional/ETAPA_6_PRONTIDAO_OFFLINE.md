# Etapa 6 — conferência offline antes da autorização

25/10/2026. O usuário pediu continuação após a etapa 5. O plano exige confirmação de créditos e autorização específica para iniciar testes externos. Essas condições ainda não foram informadas; foi solicitada confirmação ao usuário. Esta rodada não interpreta “continue” como autorização de gasto ou envio de documentos.

## Resultado concreto

Foram executados os comandos existentes `diagnosticar_ia_documental` e `avaliar_ia_documental`, sem modelo escolhido, com proteções locais de teste que impedem conexão por socket, construção de clientes SDK e consulta ao banco operacional. As duas operações terminaram e verificações locais passaram:

- diagnóstico mantém `disponivel=false`;
- plano contém dez casos fictícios embutidos, sem consultar documentos/atendimentos;
- hashes do plano correspondem aos casos/instruções/esquemas atuais;
- nenhum modelo foi escolhido e nenhuma requisição planejada foi preenchida;
- nenhuma instância dos clientes síncrono/assíncrono do SDK foi criada;
- nenhuma consulta ao banco foi feita dentro da execução protegida dos comandos;
- avaliação real permanece `nao_executada`.

Arquivos locais fora do Git: `.local/piloto-etapa6/diagnostico-0bd93153.json` e `.local/piloto-etapa6/plano-0bd93153.json`. O diagnóstico não valida a credencial ou saldo e não expõe seu valor. Não foram impressos segredos, alterados créditos/cobrança ou feita tentativa de autenticação externa.

Casos preparados: nome simples, nomes próximos, cônjuge não deduzido, representação incerta, CPF divergente, página sem texto, preço ausente, pagamento futuro, releitura corrigida e instrução maliciosa. São entradas e oráculos locais, não respostas de IA nem prova de qualidade de um modelo.

## O que ainda precisa ser implementado

`ProvedorReal.analisar` continua recusando a operação incondicionalmente. Não há transporte real ou comando de execução externa disponível. Definir chave, modelo ou acrescentar crédito não ativa a IA.

Após autorização, será necessário implementar e testar o transporte previsto em `docs/ATIVACAO_IA_DOCUMENTAL.md`: destino fixo, validação de credencial sem exposição, uma tentativa, sem fallback, limites de recebimento, prazo absoluto/cancelamento, erros seguros e preservação transacional. Essa implementação não foi iniciada nesta rodada condicionada à autorização, nem o bloqueio foi removido.

## Condições para prosseguir

1. Usuário confirma créditos/acesso e autoriza chamadas pagas somente com casos fictícios, informando teto de gasto. Não enviar chave pelo chat.
2. Escolher modelo explicitamente e conferir documentação oficial, compatibilidade e condições do provedor antes da implementação/ativação. Não foi recomendado modelo ou preço nesta conferência offline.
3. Implementar transporte e validá-lo primeiro com transporte falso; só depois executar um caso fictício autorizado e conferir resultado/consumo antes de ampliar.
4. Documentos reais continuam sujeitos a nova autorização específica, incluindo conteúdo e destino, além das aprovações profissionais e condições locais pendentes.

As etapas 2 a 5 mantêm suas pendências: aprovação da redação/cenário pela escrevente, atendimento real acompanhado, controles locais e conferência profissional/visual no Word. Não são substituídas por uma campanha de IA fictícia.

**Estado:** prontidão offline conferida; ativação e avaliação real da etapa 6 pendentes. Nenhuma chamada de IA ou gasto de API nesta rodada. Somente documentação alterada; não foi repetida a bateria funcional já aprovada, pois não houve mudança de implementação.
