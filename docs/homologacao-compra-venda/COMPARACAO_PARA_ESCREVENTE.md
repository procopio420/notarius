# Compra e venda — dois cenários fictícios para comparação

Preparação de 24/10/2026. **Aguardando revisão profissional. Nenhum modelo foi homologado, nenhuma fonte foi confirmada e nenhuma pessoa foi identificada por estes arquivos.**

Atualização técnica da etapa 7: agora existem campos de ato e complementos separados, com [dois rascunhos ampliados para revisão](estruturas-complementares/LEIA_PRIMEIRO.md). Os atendimentos e rascunhos preparados abaixo foram preservados; essa ampliação não homologa nem aplica automaticamente as novas seções.

A escolha nesta conversa foi preparar as duas variantes para comparação. Isso define o material de teste, não aprova a redação, os documentos necessários nem as condições jurídicas de qualquer variante. Os dados são propositalmente fictícios e os identificadores contêm letras e avisos de invalidade.

## Comparação concreta

| Item | Participação direta | Com procuração |
|---|---|---|
| Atendimento local | [Abrir cenário direto](http://localhost:3002/atendimentos/0a9ff6f1-9bbd-54c7-81f9-d032d55b4f5d) | [Abrir cenário com procuração](http://localhost:3002/atendimentos/a8ed8261-ef71-5eac-bb03-5226c7588f45) |
| Base comum | Uma pessoa vendedora fictícia, uma compradora fictícia, um imóvel inexistente e preço fictício | Mesma base e mesmos textos fictícios, em registros independentes do outro atendimento |
| Pessoas | Vendedor e comprador em registros separados | Vendedor, comprador e procurador em registros separados |
| Papéis no negócio | Registros próprios de vendedor e comprador, vinculados explicitamente às pessoas | Os mesmos papéis, sem transformar o procurador em vendedor |
| Relação de representação | Não foi criada para esta variante de teste; isso não estabelece ausência de representação em caso real | Registro separado: procurador como primeira pessoa, vendedor como segunda, tipo `representante_de` |
| Instrumento e limites | Não entram no texto desta variante | Campos próprios, vinculados a `FICTICIO-representacao.txt`; não atestam poderes ou suficiência |
| Imóvel e negócio | Registro de imóvel separado de preço, condições e situação do pagamento | Mesma separação; a negociação aponta para seu imóvel, sem compartilhar registro com o outro atendimento |
| Pagamento | Mensagem diz previsão futura; situação `previsto` | Mesma mensagem fictícia; a procuração não altera a situação do pagamento |
| Material recebido | 6 arquivos TXT + 1 mensagem; 27 propostas locais | 8 arquivos TXT + 1 mensagem; 38 propostas locais |
| Leitura | Texto literal local; cada TXT é uma unidade de texto, não página física de certidão | Mesmo procedimento. Não houve OCR de documento real nem interpretação de procuração por IA |
| Estado inicial | Modelo rascunho; nenhum dado, vínculo de minuta ou revisão final confirmado | Mesmo estado, inclusive instrumento sem confirmação |
| Rascunho para comparar | [Modelo direto](direta/modelo-rascunho.txt) | [Modelo com procuração](procuracao/modelo-rascunho.txt) |

Os nomes iguais nas duas variantes são uma base de comparação. Não provam que duas fontes pertencem à mesma pessoa, e o software não funde os registros. Toda proposta conserva arquivo/mensagem, leitura, unidade de texto, linha, canal e trecho literal. A associação e confirmação continuam dependendo da escrevente.

## O que estes rascunhos cobrem

Os textos usam posições explícitas para qualificação, papéis, imóvel, titularidade/aquisição/ônus informados, preço e condições. A variante com procuração acrescenta pessoa representante, relação, instrumento e limites informados. A presença desses campos no rascunho não valida seu conteúdo nem estabelece um requisito jurídico.

Os textos completos a conferir são os dois arquivos `modelo-rascunho.txt` acima. Nenhuma condição ou cláusula foi escolhida por interpretação automática. A situação conjugal escrita nos arquivos é apenas um dado sintético do teste: não determina participação de cônjuge e não cria relação entre pessoas.

## Diferenças em relação à escritura enviada

Referência de leitura preservada em `docs/COMPRA_VENDA_REFERENCIA_IMAGENS.md`; o modelo estruturado do exemplo anterior é uma adaptação para revisão, não uma transcrição integral aprovada. Dados rasurados não foram recuperados nem substituídos por suposição.

| Trecho da referência | Situação nos dois rascunhos | Decisão profissional pendente |
|---|---|---|
| Abertura, data, local e serventia | Não preenchidos com dados do exemplo | Definir campos e texto exatos; não presumir ocorrência do ato |
| Qualificação e situação conjugal | Campos fictícios individuais, sem cônjuge deduzido | Quantidade de pessoas, qualificação necessária e participação conforme o cenário |
| Representação por procuração | Só na segunda variante, com fonte fictícia própria | Quem representa quem, instrumento, poderes, limites, verificações e redação aplicável |
| Item 1: imóvel e titulação | Campos estruturados propostos para os dados do imóvel | Descrição literal, titularidade, aquisição, ônus e fontes efetivamente aceitos |
| Item 2: negócio e pagamento | Preço, condições e situação separados | Forma de pagamento, declarações aplicáveis e texto específico; não aproveitar quitação do exemplo |
| Declarações, transmissão e DOI | Não copiadas como fatos fixos | Quais declarações foram prestadas e qual redação/campo corresponde a cada fonte |
| Item 6: tributo | Não preenchido com guia, valor ou recolhimento do exemplo | Campos, documentos e distinção entre previsão, guia apresentada e recolhimento informado |
| Item 7: certidões e consultas | Nenhuma consulta ou certidão real foi presumida | Quais documentos se aplicam e quais consultas foram efetivamente efetuadas, com suas fontes |
| Itens 8 e 9: declarações e requerimentos | Não copiados nem deduzidos | Conteúdo aplicável, quem declarou/requereu e fonte de cada afirmação |
| Item 10, emolumentos e encerramento | Nenhuma leitura, assinatura ou cobrança presumida | Texto compatível com a fase de minuta e informações realmente confirmadas |
| Manifesto, selos e validação | Não reproduzidos | Não reutilizar assinatura, código, link ou selo do caso antigo |

Essas lacunas impedem considerar os rascunhos como o modelo profissional completo. Os campos estruturados disponíveis ainda não cobrem todas as seções da referência; não se deve contornar isso copiando os fatos antigos para texto fixo. A inclusão de campos e regras adicionais deve partir das decisões da escrevente.

## Roteiro de revisão na interface

1. Abrir cada atendimento e comparar os arquivos na aba **Documentos**. Não tratar TXT fictício como certidão ou procuração autêntica.
2. Em **Conversa → Ficha detalhada → Propostas com fonte**, conferir a fonte completa, escolher a pessoa/registro/campo e revisar o valor. Os registros criados são uma proposta de organização do teste, não dados confirmados.
3. Conferir os papéis e, na segunda variante, a direção da relação: procurador → vendedor. Não trocar nome de procurador com nome do representado.
4. Confirmar somente os dados efetivamente revisados; resolver divergências, dúvidas e destinos das páginas individualmente. A validade formal de CPF não comprova identidade.
5. Em **Minuta → Revisar modelo**, definir o padrão adequado, completar as seções profissionais e salvar nova versão após revisão. Os modelos preparados permanecem em rascunho.
6. Em **Vincular ficha ao modelo**, escolher cada registro, conferir os vínculos e justificar registros fora do texto. Preparar a minuta somente após as pendências e a aprovação do modelo.
7. Conferir dados usados e texto inteiro. Revisar a versão final antes de baixar Word/PDF. Alterações posteriores exigem nova preparação e revisão.

Os testes automatizados executam essas decisões com respostas simuladas em banco de teste isolado. Essas respostas não são aplicadas aos dois atendimentos locais e não são aprovação da escrevente.

## Respostas que permitem avançar

A escrevente pode responder nesta conversa, sem dados reais:

1. Quais trechos dos dois rascunhos devem ser mantidos, corrigidos ou substituídos pela redação profissional?
2. Para cada variante, quais pessoas, qualificações, relações e documentos devem ser tratados no primeiro cenário homologado?
3. Na procuração, quais informações e conferências do instrumento precisam constar da ficha e do texto?
4. Qual redação e quais campos devem atender às seções ainda não cobertas na tabela acima?
5. Quais condições autorizam cada cláusula e quais fatos devem exigir fonte/declaração específica antes de entrar no texto?

Preparar ambos, aprovar tecnicamente os testes e receber as imagens são atos distintos de homologar profissionalmente o cenário. Esta comparação permanece **não homologada** até decisões explícitas da escrevente.

## Material e repetição segura

Os subdiretórios `direta/` e `procuracao/` contêm os arquivos fictícios, mensagem e rascunho de cada variante. `manifesto-ficticio.json` preserva o retrato da preparação inicial e resultados esperados propostos; não é um relatório do estado atual nem uma decisão de associação dos dados. O estado atual deve ser consultado nos atendimentos.

A preparação é idempotente e preserva decisões posteriores: repetir o comando não redefine os dados, não reaprova modelos e não cria novos atendimentos para a mesma versão do cenário/cartório. Arquivos de material alterados anteriormente são preservados, com recusa de sobrescrita. Somente cartório identificado como fictício e usuária que já tenha acesso a ele podem preparar esses cenários.
