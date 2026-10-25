# Etapa 5 — modelo revisável e preparação literal

O atendimento dispõe de **Revisar modelo**, **Preparar minuta** e **Abrir minuta**. A edição do modelo e a prévia abrem em pop-ups, mantendo a conversa como tela principal.

## Modelo

A base fornecida é uma estrutura inicial sem dados pessoais nem cláusulas jurídicas inventadas. Não é uma transcrição integral do exemplo enviado nem um padrão completo aprovado do cartório. A escrevente deve inserir o texto aplicável, revisar e aprovar explicitamente a versão usada no atendimento. Não foi conferida a atualidade de cláusulas legais do exemplo.

O corpo principal exige os marcadores vendedores, compradores, imóvel, preço e pagamento. Representação e observações têm blocos separados que entram apenas com dados confirmados. Não há conclusão automática sobre pagamento efetuado, consultas realizadas, assinaturas ou outras ocorrências.

Cada salvamento cria uma versão imutável do modelo, com autor, data, justificativa e estado de aprovação. A caixa de aprovação começa desmarcada e é desmarcada ao alterar o texto. Uma nova versão não aprovada revoga a possibilidade de gerar com a versão anterior.

## Preparação

A API valida pendências, revisão dos documentos, versão atual do modelo e confirmação dos campos. Os valores são inseridos literalmente, sem chamada externa a um modelo de linguagem. Marcadores desconhecidos ou ainda presentes nos dados bloqueiam o preenchimento. Os blocos opcionais são tratados explicitamente.

A minuta preserva o texto, a versão do modelo e uma cópia dos dados usados, com revisões e origens. Alterações posteriores em mensagens, dados, documentos, decisões ou modelo marcam versões anteriores como desatualizadas. Repetir a preparação sem mudanças não duplica a versão. A prévia permite consultar os dados utilizados e versões anteriores.

Endpoints do atendimento: GET/POST `modelo-minuta/`, GET/POST `minuta-preparada/`. O POST de preparação exige a assinatura do estado visto pelo cliente; alteração concorrente retorna 409. A autorização segue o cartório do atendimento.

## Validação e limites

26 testes aprovados na suíte de atendimentos, incluindo bloqueios, aprovação do modelo, preenchimento literal, blocos condicionais, versões, reenvio, alteração dos dados, origem, marcadores inválidos e controle de acesso. Django check e migrações passaram. Os arquivos desta entrega não apresentaram erros no filtro TypeScript; permanecem erros anteriores em outras áreas.

Pela interface, um modelo inteiramente fictício passou de rascunho para aprovado em um atendimento de teste e gerou uma minuta com dados fictícios. O modelo real da escrevente não foi aprovado automaticamente nem foram incorporados dados dos documentos enviados na conversa.

Edição da minuta, salvamento das alterações manuais e exportação em Word/PDF são a etapa 6. Interpretação semântica geral de documentos e OCR continuam fora desta entrega; não há alegação de uma IA notarial completa nem de documento pronto para lavratura.
