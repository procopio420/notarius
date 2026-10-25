# Etapa 14 — biblioteca de modelos do cartório

Funciona localmente, sem IA externa. Um modelo atual e aprovado pode ser publicado explicitamente como padrão reutilizável. A biblioteca é isolada por cartório.

## Publicar um padrão

1. Abra **Revisar modelo**.
2. Substitua dados específicos por marcadores. Confira todos os blocos: nomes, documentos, endereços, valores e declarações sobre um caso não devem ficar no padrão.
3. Revise e salve a versão aprovada para o atendimento de origem.
4. Reabra **Revisar modelo** e clique em **Publicar modelo salvo na biblioteca**.
5. Confira o texto salvo exibido, dê um nome sem dados pessoais e confirme a revisão antes de publicar.

O botão fica desabilitado se houver alterações de texto ainda não salvas. O servidor exige que a origem continue sendo a versão atual e aprovada no momento da publicação. Repetir a publicação da mesma origem e nome não duplica o registro.

Não há anonimização automática nem garantia de remoção de dados sensíveis: a publicação depende da revisão humana. O compartilhamento fica limitado aos usuários com acesso ao mesmo cartório, conforme o acesso já existente aos atendimentos.

## Reutilizar

1. Em outro atendimento, abra **Revisar modelo → Carregar da biblioteca**.
2. Busque pelo nome e selecione um padrão para conferir seus blocos.
3. Clique em **Carregar no editor para revisão**. A ação substitui os textos do editor, com aviso, sem salvar automaticamente.
4. Ajuste o padrão ao caso e informe o motivo. A aprovação fica desmarcada; revise antes de aprovar para o novo atendimento.
5. Salve como rascunho ou aprove explicitamente. Cada salvamento cria a versão normal do atendimento e registra a referência da biblioteca.

Não são copiados dados da ficha, participantes, documentos, decisões ou minutas do caso de origem. Texto fixo específico que alguém tenha deixado no padrão, porém, será copiado: por isso a conferência antes de publicar é indispensável.

Publicações são snapshots: versões posteriores do modelo de origem não alteram padrões já publicados. Publicar uma atualização gera outro registro; use um nome claro que identifique a revisão. Não há editor nem exclusão de publicações nesta entrega. A busca limita a 50 resultados e orienta refinar o nome quando houver mais.

A biblioteca não declara que um modelo foi homologado para qualquer cenário. A adequação profissional e a aprovação por atendimento continuam necessárias.

## Validação

61 testes Django passaram, incluindo publicação explícita, recusa de origem antiga/rascunho, reenvio sem duplicação, isolamento entre cartórios, cópia sem aprovação herdada e preservação do padrão publicado. ESLint passou nas telas e componentes de atendimento e no cliente da API. A migração 0010 adiciona a biblioteca e a referência de origem dos modelos carregados.
