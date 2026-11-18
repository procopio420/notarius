# Compra e venda, editor e integração do Luna

Entrega de 18/11/2026 para integração na `main` de `procopio420/notarius`.

## Fluxo entregue

O atendimento reúne conversa, anexos e cartão da minuta. O editor permite abrir,
buscar, editar, formatar, salvar e reabrir o texto, comparar versões e consultar
a fonte dos dados. O layout adapta o editor ao celular. O perfil do piloto usa
usuário e senha com uma conta individual vinculada ao ambiente pelo servidor.

A estrutura de compra e venda reproduz a sequência das quatro páginas do
documento de referência. O preenchimento substitui os campos variáveis. O
cenário conserva as qualificações e cláusulas desse modelo específico. Outros
regimes de bens, participantes ou formas de representação exigem revisão do
modelo e das cláusulas aplicáveis.

As sugestões documentais guardam arquivo, página, versão de leitura e trecho.
A conferência do servidor exige evidência literal e mantém alternativas
divergentes visíveis. Pagamento previsto e declaração de quitação têm tratamento
próprio. Campos sem evidência ficam pendentes no rascunho.

No editor, as declarações do caso podem ser conferidas individualmente e salvas
em uma nova versão. Cada confirmação registra autor, motivo e assinatura das
fontes. Mudanças dos anexos reabrem as declarações na preparação seguinte.
Confirmar declarações e editar texto salvo são operações locais.

O salvamento protege contra edição concorrente e repetição do mesmo pedido.
As versões anteriores continuam disponíveis. A revisão final pertence à versão
salva e exige resolver as pendências. Uma nova edição precisa de nova revisão.
As exportações Word, PDF e PDF/A partem do texto salvo.

## IA e dados reais

O teste de uso da Mary será com casos e documentos reais de compra e venda.
Os ensaios técnicos e testes automatizados usam dados fictícios em bancos
separados, conforme as instruções em `AGENTS.md`.

O perfil operacional permanece com Qwen3 local. A integração de minutas com
GPT-6 Luna exige chave, organização, projeto, região, ambiente e referência
da autorização de envio na configuração privada do servidor. Essa liberação
continua pendente. O chat externo tem uma guarda independente e permanece
bloqueado no ambiente real, inclusive se a opção global do chat estiver ligada.

O provedor de minutas envia apenas texto das páginas classificadas como fontes
do caso que exigem inferência. A requisição usa `store: false`, sem ferramentas,
redirecionamentos ou proxies herdados do ambiente. A chave fica no servidor.
Os anexos e as versões já salvos continuam disponíveis quando a API falha.

Em 15/11, a configuração privada foi vinculada ao projeto Notarius na região
Global e a chave existente respondeu ao teste técnico. O painel mostrou
compartilhamento para treinamento desativado. A conta não apresentou confirmação
de retenção zero. A retenção padrão de monitoramento pode incluir conteúdo por
até 30 dias, com exceções previstas pelo provedor.
[Controles de dados da OpenAI](https://developers.openai.com/api/docs/guides/your-data).

O teto de US$ 0,50 documentado nos ensaios antigos se aplica ao transporte de
teste controlado e ao chat que usa esse orçamento. A integração de minutas tem
limites de texto, saída e prazo por pedido. O limite mensal total de R$ 100 ainda
precisa de controle operacional próprio antes da ampliação do serviço.

## Evidência anterior com GPT

O ensaio técnico isolado da integração retornou 22 de 22 campos esperados do
Luna, além dos 137 campos extraídos pelos rótulos. Após 14 confirmações simuladas,
o texto correspondeu ao modelo preenchido. Word e PDF de quatro páginas
preservaram esse texto. Um segundo caso exibiu dois preços e manteve a quitação
pendente. Foram duas chamadas pagas, estimadas em US$ 0,0016 no total. O relatório
privado está em `.local/ensaio-escritura-fiel/resultado-ensaio-gpt-revisao.json`.
Esse resultado corresponde aos documentos inventados do ensaio.

## Instalação e operação

As migrações `0025`, `0026` e `0027` acrescentam a resposta persistente do chat,
a formatação e a assistência da minuta. Faça backup do banco antes de aplicá-las
em outra instalação. As novas colunas têm valores padrão para registros antigos.
O iniciador verifica migrações pendentes antes de abrir os serviços.

O Qwen e seu executável ficam na pasta privada `.local/ia-minuta`. O código
versionado contém o iniciador. O acesso HTTPS pelo mesmo Wi-Fi está disponível
pelos scripts de rede e depende de instalar o certificado local no dispositivo.
O procedimento está no [manual de operação](OPERACAO_PILOTO_LOCAL.md).

O merge integra código e documentação. Hospedagem pública, compra de serviços,
publicação de imagens e ativação do envio externo têm procedimentos próprios.
Os jobs de deploy do CI continuam exigindo acionamento manual explícito.

## Verificações desta integração

Foram descobertos 154 testes. Passaram 153 em 145,467 segundos e um teste pago
foi pulado deliberadamente. A execução usou bancos fictícios isolados, bloqueou
conexões de rede e não consumiu a API. Uma primeira tentativa foi interrompida
após travar nos subprocessos de leitura sob restrições do ambiente. A execução
final abaixo foi realizada com acesso ao OCR local do Windows.

```powershell
.\.venv\Scripts\python.exe scripts\conferir-prontidao-offline.py tests.test_orcamento_documental tests.test_transporte_controlado tests.test_chat_ia tests.test_comparacao_anexos tests.test_minuta_openai tests.test_modelo_referencia tests.test_atendimentos tests.test_blocos_minuta tests.test_redacao_estruturada tests.test_ocr_atendimentos tests.test_organizacao_anexos tests.test_piloto_local tests.test_exportacao_piloto tests.test_funcao_principal_integrada tests.test_preparacao_documental tests.test_analise_documental
```

O log local está em `.local/pr-editor-luna-regressao.log`. A seleção cobre
isolamento de contas, persistência, replay, edições concorrentes, modelo de
referência, declarações, falhas da API, OCR e exportação.

ESLint dos arquivos TypeScript alterados passou sem avisos. O TypeScript
restrito ao fluxo de atendimentos passou. Para reproduzi-lo, salve o conteúdo
abaixo em `.local/tsconfig-conferencia-piloto.json` e execute
`node apps/notarius-web/node_modules/typescript/bin/tsc -p .local/tsconfig-conferencia-piloto.json`.

```json
{
  "extends": "../apps/notarius-web/tsconfig.json",
  "compilerOptions": { "incremental": false },
  "include": [
    "../apps/notarius-web/next-env.d.ts",
    "../apps/notarius-web/src/app/atendimentos/**/*.tsx",
    "../apps/notarius-web/src/components/atendimentos/**/*.tsx"
  ],
  "exclude": ["../apps/notarius-web/node_modules"]
}
```

`manage.py check`, `makemigrations --check --dry-run --noinput` e
`migrate --check` passaram no perfil `config.settings_piloto`. A sintaxe dos
scripts PowerShell e do proxy Node foi conferida. `git diff --cached --check`
passou. A busca nos conteúdos do índice por chaves de provedores e chaves
privadas não encontrou ocorrências. O ZIP dos exemplos corresponde byte a byte
aos arquivos da pasta do kit.

## Limitações conhecidas

- A revisão profissional da redação, das fontes e da aplicabilidade das cláusulas
  cabe à Mary. O teste dela com casos reais ainda depende da realização por ela.
- A leitura local de imagens usa OCR do Windows. Páginas cortadas, borradas ou
  ilegíveis exigem conferência do original.
- A comparação literal e o formato do CPF são verificados. A minuta não faz
  consulta cadastral automática à Receita Federal.
- Negrito, itálico e sublinhado são preservados no editor e no histórico. As
  exportações usam a apresentação padrão do exportador.
- O exportador inclui metadados e perfil de cor para PDF/A-2b. A conformidade
  completa ainda precisa de validação independente com ferramenta especializada.
- O TypeScript global tem erros nos módulos legados e no Cypress. A checagem
  restrita ao fluxo de atendimentos e seus componentes importados passou.
- O CI remoto legado já apresentou falhas de infraestrutura nas PRs anteriores,
  incluindo ações descontinuadas e configuração ausente de detecção de segredos.
  Os resultados desta PR serão verificados antes do merge.

## Material para ensaios técnicos

`documentos-ficticios-teste/` e o ZIP correspondente contêm seis imagens
sintéticas, instruções e prompts de geração. Os CPFs repetidos são
intencionalmente inválidos. O kit tem lacunas e pagamento previsto para exercitar
pendências. O banco do piloto da Mary, os originais reais, a chave da API, os
backups e os relatórios privados ficam nas pastas ignoradas pelo Git.
