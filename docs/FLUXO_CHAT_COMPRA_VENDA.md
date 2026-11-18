# Entrada por documentos e conversa

08/11/2026. Fluxo solicitado: nome do atendimento, serviço (somente escritura de
compra e venda), seleção conjunta de documentos e orientação opcional; Continuar
abre uma conversa, sem ficha técnica como tela principal.

## Implementação entregue

- `NovoAtendimento`: seleção múltipla, até vinte arquivos por envio e 10 MB por
  arquivo. Cria o atendimento uma vez, envia os arquivos em sequência e salva a
  orientação. Falha parcial preserva o atendimento e oferece retomar os pendentes
  ou abrir a conversa salva. Criação de resultado ambíguo não é repetida por botão
  sem voltar à lista. Arquivos idênticos usam a deduplicação do servidor existente.
- `ChatAtendimento`: mensagens persistidas pelo endpoint existente, rascunho de
  sessão e identificador idempotente. Anexos, leitura local e arquivos sem texto
  aparecem na conversa. Novos arquivos podem ser anexados pelo clipe.
- Assistente explicitamente identificado como **local**: mensagens fixas de
  orientação e resumo calculado a partir da leitura disponível. Não são respostas
  de modelo nem uma conversa de IA funcional. Nenhuma frase livre é aplicada à
  ficha, tratada como confirmação ou usada para resolver divergência.
- Transcrição literal em TXT disponível para conferência, com título e aviso de
  que não é minuta. Texto nativo e OCR divergentes são preservados separadamente.
  Leitura parcial/vazia e limites exigem revisão; não se afirma integridade de
  leitura, identidade das pessoas ou concordância de nomes/endereços.
- Quando já existe uma minuta salva, a conversa mostra um cartão com a versão e
  um resumo de situação. **Abrir minuta** abre a mesma janela de edição usada em
  **Revisão e ajustes**.
- Ficha, fontes, pendências, modelo, versões e exportação Word/PDF continuam em
  **Revisão e ajustes**. O componente anterior foi reaproveitado em
  `FerramentasDoAtendimento`, com seus callbacks e guardas. Seu rascunho tem chave
  de sessão separada do compositor principal para evitar sobrescrever texto.

## Verificações

TypeScript do fluxo e ESLint dos arquivos alterados aprovados. Quatro verificações
locais do resumo/TXT cobrem arquivo vazio, OCR/leitura parcial, limites e texto
não confiável preservado literalmente. Nada chama clientes de IA.

No navegador, criado exercício identificado como fictício: dois TXT com nomes e
preços distintos e PDF em branco, enviados juntos. A conversa exibiu três anexos,
identificou o PDF sem texto e não declarou que os nomes/preços estavam corretos.
Orientação inicial e segunda mensagem permaneceram após recarregar. Download TXT
real conferido por conteúdo: ambos os preços literais, aviso e página sem texto.
Preparação da minuta continuou bloqueada; ficha e revisão permaneceram acessíveis.
Viewport de 390 px sem transbordamento horizontal do documento.

O exercício criado pelo agente foi removido por ID e título exatos ao final,
com cópia local de recuperação e conferência de chaves estrangeiras. O atendimento
do usuário foi preservado. Capturas e material fictício ficam em `.local/chat-qa/`.

Compilação isolada do frontend móvel passou; o build informa ausência de config
ESLint na cópia, por isso a validação de lint foi executada separadamente na origem
e passou. Não se declara build global de módulos legados aprovado.

## Pendências explícitas

IA permanece bloqueada, sem chamadas, gastos ou uso de documentos reais no provedor.
O registro local de orçamento continua com zero reservas consumidas. A integração
real ainda precisa ser implementada e validada depois, com autorização para o
primeiro teste fictício, dentro do teto acumulado de US$ 0,50.

Faltam comparação semântica efetiva entre documentos, respostas de IA às dúvidas
e preparação automática do candidato a minuta. Não apresentar o fluxo local como
se isso já funcionasse. Para a fase futura: toda proposta precisa de fonte, trecho
e destinatário explícito; dúvida gera pergunta, nunca preenchimento adivinhado.
As decisões profissionais e aprovação do padrão continuam com a escrevente.

Prévia móvel temporária renovada por duas horas, com login, lista restrita de
rotas, bloqueio de arquivos privados, API de IA desligada e encerramento pelo
controlador local. O endereço/horário corrente ficam no arquivo privado
`.local/mobile-link.json`; não integra uma implantação de produção.

## Cartão e editor da minuta no chat

- **Preparar minuta** ou a mensagem “Prepare a minuta” usa o gerador local com
  a assinatura atual do atendimento. Se já houver uma versão atual, a mensagem
  abre essa versão. O servidor exige modelo aprovado e dados conferidos, e
  revalida pendências, versão e fontes antes de gravar. A conversa indica o que
  impede a preparação e mantém a versão anterior disponível para consulta.
- **Abrir minuta** mostra o texto, busca e edição de parágrafos em uma janela
  que ocupa a tela inteira no celular. Salvar cria uma versão no mesmo histórico
  de **Revisão e ajustes**. As versões ficam disponíveis para reabertura e
  comparação dentro do Notarius.
- Se outra edição for salva primeiro, o servidor recusa sobrescrever a versão
  mais nova. A edição digitada continua aberta e pode ser retomada na mesma aba
  quando o armazenamento da sessão estiver disponível. A comparação abre entre
  a versão de origem da edição e a versão mais recente.
- O resumo do cartão informa se o texto foi preenchido a partir do modelo, se
  recebeu edição manual ou se ficou desatualizado.

### Validação do cartão e do editor

Com banco fictício separado e IA externa desligada, a API confirmou login,
bloqueio por pendências, preparação, edição, reabertura das duas versões,
comparação do texto e resposta 409 ao editar sobre a versão anterior. Passaram
14 testes focados, o lint dos componentes envolvidos e a checagem de tipos
do fluxo de atendimentos. A compilação com Webpack terminou e o build global
parou no lint de outros módulos.

O teste no navegador passou após iniciar o ensaio pelo PowerShell. No caso
fictício, “Prepare a minuta” abriu a v1 no chat. Busca, inserção de parágrafo e
salvamento produziram a v2, que reabriu com o texto editado após recarregar a
página. O histórico preservou a v1 e a comparação mostrou a edição.

Em duas abas, a segunda salvou a v3. A primeira recebeu o conflito, preservou
o texto digitado, comparou v2 com v3 e permitiu retomar a edição local após
fechar a janela. O editor ocupou toda a largura de 390 px sem rolagem horizontal.
Um segundo caso fictício exibiu as pendências e manteve o botão de preparação
desabilitado.

Para abrir o ensaio no Windows, execute
`./scripts/testar-cartao-minuta-local.ps1` no PowerShell, na raiz do repositório.
O script cria um banco fictício novo e usa as portas locais 3012 e 8012. Quando
o Next indicar que está pronto, use o endereço e a conta fictícia exibidos na
janela. Mantenha o terminal aberto durante a conferência.

## Etapa 3 — conferência automática de anexos na conversa

A escrevente recebe um resumo das sugestões assim que a conversa carrega os
anexos, inclusive em atendimentos antigos. A API autenticada do cartório lê
somente as versões atuais, com os mesmos rótulos da extração local de propostas.
Cada sugestão mostra o arquivo, a página, a versão, o canal, a linha e o trecho
literal. A conversa atualiza o resumo após novo envio, inclusive parcial.

- Compara por campo e destinatário já vinculado à página. Nomes semelhantes,
  páginas com destinatários ambíguos e dados pessoais sem vínculo exigem que a
  escrevente confira a origem. Valores diferentes de negociação sem vínculo
  geram uma pergunta sobre a negociação a que se referem.
- Distingue coincidência, divergência, possível divergência e necessidade de
  conferência. Leitura incerta, ausência, formato inválido, versões de leitura
  substituídas e documentos de referência ou desconsiderados recebem o
  tratamento correspondente. Condições previstas, situação do pagamento e
  quitação são campos separados.
- Cada trecho permite abrir a leitura na página correspondente. A extração de
  propostas para a ficha, o vínculo, a rejeição e a confirmação continuam
  disponíveis no percurso de revisão existente. O resumo é somente leitura e
  as guardas do servidor para gerar minuta continuam aplicadas.
- A conversa prevê carregamento, ausência de campos reconhecidos, análise
  parcial, erro com nova tentativa e exibição responsiva de trechos. A etapa usa
  leitura local por rótulos, inclusive OCR já disponível. Interpretação de
  documentos sem rótulos reconhecíveis e ativação de IA externa ficam fora do
  escopo. A configuração padrão do piloto permanece com IA externa desligada.

### Validação local da etapa 3

Em 12/11/2026, a seleção `tests.test_comparacao_anexos tests.test_atendimentos`
passou com 35 testes no perfil `config.settings_piloto`. No navegador, dois TXT
fictícios foram anexados juntos a um atendimento isolado que estava pronto
para gerar minuta. A conversa atualizou o resumo após o envio, mostrou os
preços de R$ 100,00 e R$ 200,00 como possível divergência e pediu a confirmação
do destinatário dos nomes. Cada preço manteve arquivo, página, linha e versão
da leitura. O botão de fonte de `beta.txt` abriu a leitura com o trecho de
R$ 200,00. O envio reabriu pendências e desabilitou **Preparar minuta**.
O ensaio usou um banco fictício separado e manteve a IA externa desligada.

### Ensaio com prints

O OCR pt-BR do Windows foi exercitado pela API com PNG fictício cortado,
borrado e em branco. Os três ficaram pendentes de conferência, sem confirmar
campos ou habilitar a minuta. Dois prints legíveis exibiram preços distintos
como **Possível divergência**, com arquivo, página e trecho de OCR. Cada trecho
continuou marcado como leitura incerta. `Situação do pagamento: previsto` e
`Quitação: não declarada` apareceram em campos distintos. O ensaio usou a
leitura local e a comparação por rótulos.

Em 12/11/2026, cinco prints gerados para o ensaio passaram pelo OCR local.
Foram enviados somente os textos extraídos e metadados fictícios ao provedor
controlado. Na primeira chamada, os seis valores passaram pelo validador,
mas o modelo deixou pessoa e imóvel sem associação. As instruções passaram
a distinguir incerteza de leitura de vínculo exclusivo informado. Na segunda
chamada, as seis sugestões passaram com seus trechos literais e fontes. Nome
e descrição vieram com os destinatários esperados, os dois preços divergentes
permaneceram separados e a situação prevista não virou quitação. O print em
branco gerou dúvida sem proposta. O ensaio foi independente do banco e da
interface, sem aplicar sugestões nem liberar IA no piloto real. Passaram 34
testes locais de análise documental, OCR, comparação e transporte.

O cartão da minuta mostra as fontes registradas para os campos efetivamente
inseridos. O detalhe reúne arquivo, página, trecho e versão da leitura, com
acesso à fonte, ou identifica mensagem e registro manual. A situação do
pagamento aparece em separado da declaração de quitação. Para uma minuta
editada, as fontes são identificadas como pertencentes à versão de base.

## Ensaio integrado — da divergência à exportação

O teste `test_attachment_conflict_requires_new_review_before_export` parte de
uma minuta fictícia revisada e exportável. Dois anexos com preços diferentes
reabrem a conferência, bloqueiam nova geração e invalidam a exportação da
versão anterior. Após a conferência explícita dos documentos e a decisão
sobre o preço, a API gera uma nova versão e preserva o texto anterior no
histórico. A nova versão só pode ser exportada depois de uma nova revisão.
O teste compara o corpo do Word com a minuta salva e verifica no PDF o preço
escolhido e a ausência do preço divergente. O ensaio roda no banco de testes,
com revisão simulada pela API e sem envio ao provedor de IA.

## IA no chat
Enviar uma nova mensagem chama a IA quando o endpoint autenticado informa que o chat está habilitado. A mensagem é salva antes da análise. Respostas da IA ficam registradas separadamente, identificadas por mensagem de origem; atualizar respostas faz somente GET e não consome uma nova análise. Histórico de até dez mensagens, texto das páginas atuais e citações literais verificadas. A geração de minuta continua pelo modelo aprovado, fora da redação livre do chat. O teto de testes é acumulado e bloqueia novos envios ao ser atingido. Nenhuma análise é disparada só por abrir ou recarregar o atendimento.

A conversa distingue consulta de disponibilidade, falha na consulta e modo
local. Se a mensagem for salva e a resposta ficar sem confirmação, o botão
**Atualizar respostas** permanece disponível mesmo que a consulta ainda não
encontre respostas. O aviso desaparece quando a resposta correspondente é
encontrada. O teste com transporte simulado verificou que um anexo recebido
durante a análise invalida a resposta anterior, preserva o registro da falha
e não dispara novo envio ao consultar ou repetir a solicitação original.

No navegador, uma falha simulada na análise deixou a mensagem salva. A primeira
consulta voltou vazia e o botão continuou disponível. Uma consulta posterior
encontrou a resposta fictícia persistida e removeu o aviso. Quando a consulta
de disponibilidade passou a falhar, uma nova mensagem foi salva sem pedido
de análise, mesmo com um estado anterior de IA conectada em cache. Após a
recuperação da consulta, uma nova mensagem recebeu a resposta do provedor
simulado e o histórico reapareceu após recarregar. O registro de requisições
confirmou que atualizar e recarregar usaram somente GET e que a mensagem
enviada durante a falha não foi analisada posteriormente. O ensaio usou
banco isolado, sem chamadas externas.
