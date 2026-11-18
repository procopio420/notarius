# Roteiro técnico da escritura de compra e venda

A referência deste ciclo é a escritura de compra e venda enviada. O Notarius usa
a estrutura da escritura como modelo e reserva os campos variáveis
para os dados do atendimento. Os ensaios técnicos usam exemplos fictícios em
ambiente separado.

## Teste de uso da Mary

Mary sempre testa o Notarius com casos e documentos reais de compra e venda no
ambiente do piloto. Ela confere os documentos, as fontes dos dados e a minuta
gerada. O resultado do teste de uso é registrado depois da revisão dela.
A liberação do envio de dados reais ao GPT depende da configuração e da
autorização do projeto da API do piloto.

## Etapas técnicas

| Etapa | Entrega técnica |
|---|---|
| 1. Modelo da escritura de compra e venda | Usar `referencia-imagens-v4` com a redação fixa das quatro páginas e campos separados para os dados do caso. |
| 2. Cartão e editor no chat | Abrir, buscar, editar, formatar, salvar, reabrir e comparar versões sem sobrescrever edição concorrente. Negrito, itálico e sublinhado foram validados no navegador em uma nova versão da minuta fictícia. |
| 3. Prints no rascunho | Percurso local validado no navegador, do envio dos prints à abertura da fonte no cartão. As seis sugestões da análise por IA também foram reproduzidas em um banco fictício, exibidas na ficha, revisadas e usadas em uma minuta técnica de ensaio. |
| 4. Ajustes por conversa | O chat já propõe alterações para campos pendentes com fonte documental. O navegador validou aviso de campo afetado, valor anterior, novo valor com fonte, confirmação, nova minuta e reabertura da versão anterior. |
| 5. Preparação técnica | Ensaio fictício aprovado. Após reiniciar e restaurar o backup, o anexo, o modelo, a origem do preço, as duas minutas, a formatação e a revisão simulada foram recuperados. Uma conta sem vínculo não abriu o atendimento, o anexo ou a minuta. O envio externo permaneceu bloqueado. |
| 6. Ampliação | Isolamento verificado entre dois ambientes fictícios usando a mesma estrutura de compra e venda. Novos atos ficam para um ciclo com referências próprias. |

## Abrir o modelo no Notarius

Em um atendimento, abra **Revisão e ajustes → Minuta → Revisar modelo**.
Em um atendimento novo, o editor começa pela estrutura da escritura enviada.
Use **Carregar modelo de compra e venda** para retomá-la quando houver
outra estrutura aberta. Salvar como rascunho cria uma versão. A origem
`referencia-imagens-v4` fica indicada na descrição inicial do modelo.

O modelo mantém abertura, qualificação, representação, imóvel, título, ônus,
preço, pagamento, quitação, transmissão, declarações, DOI, tributo, certidões,
consultas, requerimentos, encerramento e despesas. Pagamento e quitação
usam campos separados. Um campo referenciado e ainda sem dado confirmado
aparece nas pendências.

## Ensaio local

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar-cartao-minuta-local.ps1 -EscrituraCompleta
```

O comando cria um banco fictício separado, importa o [anexo de ensaio](teste-escrevente/04-estrutura-referencia-ficticia.txt),
gera a minuta de demonstração e imprime o endereço e a conta de teste.
A confirmação das fontes e a aprovação da versão são simuladas dentro desse
banco para exercitar o fluxo. No atendimento, use **Abrir minuta** e
**Fontes da minuta** para conferir os campos, os trechos e o histórico.

A minuta de ensaio contém qualificação das partes, matrícula, descrição do
imóvel, preço, parcelas, declarações e encerramento. O preço é de R$ 120.000,00,
dividido em duas parcelas de R$ 40.000,00 e R$ 80.000,00. A quitação fica para
depois do recebimento integral, e o encerramento registra a assinatura como
prevista. Os campos guardam a página e o trecho do anexo fictício.

Em **Abrir minuta → Editar minuta**, selecione um trecho e aplique **Negrito**,
**Itálico** ou **Sublinhado**. A prévia mostra os estilos. **Salvar nova versão**
guarda a formatação com a minuta, inclusive se só os estilos mudarem.
**Comparar versões** informa se houve mudança de formatação. Word e PDF
continuam exportando o texto com a apresentação padrão desses formatos.

No ensaio da etapa 3, dois PNG fictícios com preços de R$ 100.000,00 e
R$ 120.000,00 foram anexados pelo chat. O OCR exibiu os dois trechos e a
minuta ficou bloqueada até a conferência. Depois de classificar e revisar
os prints, foi escolhida a fonte B. A nova versão usou R$ 120.000,00 e o
cartão abriu a página e o trecho selecionados. O navegador usou OCR e
comparação locais, sem chamada a provedor externo.

Em um segundo caso fictício, a resposta estruturada da IA já validada foi
reproduzida sem nova chamada. O servidor conferiu novamente os trechos do OCR
e os vínculos do caso. No navegador, foram exibidas as seis propostas, a
origem e os destinatários sugeridos. A proposta de nome foi aberta e confirmada
na ficha. As demais decisões foram simuladas pela API, incluindo a escolha de
R$ 120.000,00. A minuta técnica foi aberta no navegador com pessoa, imóvel,
preço e situação prevista, mantendo separada a declaração de quitação. Esse
caso usa um modelo curto para testar os campos estruturados. O ensaio principal
usa o modelo completo de compra e venda.

Na etapa 4, use um pedido como **“Use o preço do print C”** ou o botão
**Revisar ajustes dos anexos**. O chat mostra os campos pendentes da minuta
e os candidatos documentais. A fonte citada no pedido recebe destaque e as
alternativas continuam visíveis. Escolha a fonte, confira a proposta, registre
o motivo e confirme a decisão antes de preparar uma nova versão. Pedidos de
nome sem indicar a parte geram uma pergunta. O fluxo local trabalha com campos
pendentes e trechos reconhecidos. A edição livre segue disponível no editor.

Para repetir a verificação de acesso, persistência e restauração, execute
`./.venv/Scripts/python.exe scripts/verificar-piloto-local.py`. O roteiro cria
um banco e uma cópia recuperada em `.local/verificacao-piloto/`. As decisões,
a revisão final e a senha interativa do backup são simuladas para o ensaio.

O ensaio de isolamento prepara dois atendimentos com a mesma estrutura e
dados fictícios diferentes. Cada conta vê seu atendimento e seu modelo da
biblioteca. O servidor recusa abrir o atendimento, o anexo, a ficha, o modelo
e a minuta do outro ambiente, inclusive o download Word. Também recusa trocar
de ambiente por cabeçalho ou aplicar no próprio atendimento uma referência da
biblioteca alheia. As verificações são repetidas após reiniciar e restaurar o
backup. A medição de tempo e retrabalho depende do teste de uso posterior.
