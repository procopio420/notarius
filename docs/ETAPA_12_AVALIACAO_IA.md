# Etapa 12 — avaliação da interpretação da IA

## O que foi implementado

Uma bateria versionada de 14 mensagens inteiramente fictícias e um comando de avaliação. O comando não lê banco de atendimentos, documentos ou dados pessoais. O modo padrão apenas valida os casos localmente; o modo explícito `--executar` envia esses casos à API da OpenAI e pode gerar custo.

Os casos cobrem identificação e troca de papéis, nome sem papel, preço explícito/incerto/contraditório, pagamento futuro ou negado, representação não comprovada, pronome ambíguo, instrução maliciosa na mensagem, imóvel literal, caractere duvidoso em valor e proibição de calcular fatos não informados.

O avaliador confere valor esperado por campo e evidência literal. Também exige dados explícitos nos casos positivos e encaminhamento de dúvidas nos casos incertos. Uma resposta vazia falha em todos os casos desta bateria. Não basta devolver um texto que exista na mensagem: trocar vendedor por comprador também reprova.

A régua é deliberadamente estrita e usa respostas literais previamente definidas. Um resultado reprovado precisa de inspeção humana: pode revelar falha do modelo ou uma formulação válida não prevista na régua. Não afrouxe o teste automaticamente para obter aprovação.

## Resultado desta entrega

- 54 testes Django passaram: os 47 anteriores e sete testes do avaliador.
- Os 14 casos foram validados localmente, sem chamada externa.
- Relatório local em `.local/etapa12-avaliacao-local.json`.
- **O modelo real não foi avaliado: a chave da API continua ausente.**

## Executar no PowerShell, a partir da raiz do projeto

Validação local sem envio:

```powershell
& .venv/Scripts/python.exe apps/notarius-api/manage.py avaliar_ia_compra_venda --saida .local/avaliacao-local-nova.json
```

Depois de configurar a chave no servidor, avaliação real somente dos exemplos fictícios:

```powershell
& .venv/Scripts/python.exe apps/notarius-api/manage.py avaliar_ia_compra_venda --executar --repeticoes 3 --saida .local/avaliacao-real-nova.json
```

A execução real acima faz até 42 solicitações, sequencialmente. O comando não repete chamadas automaticamente e interrompe a bateria na primeira falha de provedor/resposta rejeitada. Não sobrescreve relatórios. Use um nome novo a cada execução.

O relatório registra modelo configurado, data, hashes dos casos, prompt e schema, respostas fictícias e erros por caso/repetição. Um alias de modelo pode mudar no provedor; para comparações reprodutíveis, configure uma versão fixa compatível, quando disponível.

Estados:

- `nao_executada`: somente validação local; nenhuma evidência sobre qualidade do modelo.
- `aprovada_nestes_casos`: todos os casos e repetições executados passaram nesta régua.
- `reprovada`: ao menos um erro semântico/omissão foi detectado; comando termina com erro.
- `inconclusiva`: houve falha ou rejeição de resposta; execução parcial, comando termina com erro.

Nenhuma dessas etapas aprova automaticamente dados, ficha, minuta ou uso profissional. A escrevente ainda precisa revisar os exemplos e acrescentar casos representativos do trabalho dela. A avaliação de documentos completos e o modelo profissional da escritura continuam pendentes.

## Próximo passo necessário

Configurar a chave localmente e executar a bateria real com dados fictícios. Corrigir e revisar eventuais falhas antes de ampliar para análise de documentos. Não enviar a chave por chat nem armazená-la no frontend ou no Git.
