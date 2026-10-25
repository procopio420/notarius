# Validação técnica integral dos rascunhos

24/10/2026 · dados fictícios · **não é homologação profissional**.

O usuário informou que o padrão ainda será definido pela escrevente. Esta rodada verifica o funcionamento técnico dos rascunhos existentes, independentemente dessa decisão. A redação profissional e a validação final da versão que vier a ser homologada continuam pendentes.

Estado da rodada: **verificações técnicas aprovadas nos rascunhos existentes**. Passaram 161 testes de regressão e um novo teste integral com duas variantes, totalizando 162 testes nas duas execuções. As aprovações de modelo/dados/revisão final do teste são simuladas; nenhum padrão profissional foi homologado.

## Cenários verificados

| Variante | Campos efetivamente inseridos no texto | Organização |
|---|---:|---|
| Participação direta | 45 | Pessoas, papéis, imóvel, negociação, dados do ato e complementos separados |
| Com procuração | 56 | Mesma organização, mais procurador, relação, instrumento e limites informados |

Os valores são sintéticos, com nomes, referências e identificadores explicitamente fictícios. A data é um texto fictício; não é preenchida com a data corrente. Tributos/despesas usam previsão sem recolhimento; consultas usam situação não realizada; encerramento identifica minuta sem assinatura. Não há inferência de pagamento, consulta, autenticidade ou validade de instrumento.

## Percurso exercitado

1. Criar os cenários em banco de teste isolado. Reaproveitar os contratos de atendimento, arquivos TXT, mensagem, propostas e fontes existentes.
2. Acrescentar os registros de ato e complementos de cada posição do rascunho. Cada complemento recebe categoria, âmbito e fonte individuais.
3. Informar os dados com valores originais e trechos preservados. Associações, confirmações, aprovação do modelo, vinculação e revisão final são **respostas simuladas exclusivamente no teste**, identificadas nos motivos.
4. Manter o conteúdo de uma consulta marcado como divergente, embora o trecho exista literalmente. Conferir que a minuta permanece bloqueada antes e depois da aprovação simulada do modelo. O teste introduz essa dúvida explicitamente; não simula um sistema de IA que a tenha descoberto.
5. Registrar uma nova decisão simulada para esse conteúdo, mantendo original, fonte e histórico. Rever a unidade de texto e preparar a minuta somente após as pendências resolvidas.
6. Conferir todos os marcadores: registro correto, revisão, confirmação, proposta, mensagem ou arquivo, página/leitura e trecho. Para cada ocorrência no corpo, verificar que o trecho inserido corresponde ao valor salvo.
7. Conferir que a variante direta não inclui procurador e que a variante com procuração mantém representante e representado separados.
8. Tentar exportar antes da revisão final: bloqueio. Registrar revisão final simulada da versão exata e exportar DOCX/PDF.
9. Reabrir o DOCX e comparar seu corpo com o texto salvo. Reabrir o PDF e procurar todos os valores inseridos, normalizando espaços e quebras de linha da extração. Isso não substitui inspeção visual profissional da formatação.
10. Simular substituição da versão de leitura de uma fonte no banco de teste. Conferir que nova geração e exportação da versão antiga ficam bloqueadas. Essa alteração não representa OCR real ou consulta externa.

## Ajuste de leituras repetidas

A inspeção encontrou cálculo repetido das mesmas dependências para exibir revisão atual, histórico e pendência. Foram removidas duplicações dentro da mesma avaliação:

- A ficha calcula o contexto por campo uma vez em cada consulta e serializa cada revisão uma vez para atual/histórico.
- A pendência usa as dependências que acabou de calcular para apresentar aquela revisão e a validade de suas referências.
- O preenchimento usa a situação efetiva da revisão serializada, sem refazer a mesma confirmação por outro caminho.

Não há cache global, entre requisições ou entre fases de gravação. Controle de contexto aberto, versões, reserva de escrita, fonte/leitura, identidade dos registros e confirmação humana permanecem necessários.

Na ficha fictícia de referência usada para medir a consulta, houve **96 → 50 consultas ao banco**, com assinatura da resposta completa idêntica antes/depois. É uma medição local de uma ficha, não uma promessa de tempo ou desempenho em produção/PostgreSQL. Os testes de regressão e o ensaio integral foram reexecutados com o ajuste e passaram.

A primeira execução integral anterior ao ajuste também passou. A execução repetida com o ajuste concluiu as duas variantes, e a regressão confirmou histórico, concorrência, isolamento, fontes e bloqueios existentes. Não houve mudança da interface ou nova migração nesta rodada.

## Limites que permanecem

O roteiro usa rascunhos de estrutura e textos sintéticos. Não aprova redação, aplicabilidade de cláusula, conjunto documental, poderes, identidade ou autenticidade. Nenhuma aprovação simulada deste teste é aplicada aos atendimentos locais preparados para a escrevente. Não há IA semântica real nem provedor externo nesse percurso.

Após a escrevente definir e homologar o padrão, o mesmo roteiro deverá ser executado novamente com a configuração exata e resultados esperados por ela revisados. A conclusão técnica dos rascunhos não encerra essa etapa profissional.

Reprodução local pelo ambiente Python existente: `manage.py test tests.test_validacao_integral_local --noinput`, a partir de `apps/notarius-api`. O teste utiliza banco separado; não é comando de aprovação de modelos no aplicativo. A regressão dos demais módulos é registrada no documento único de execução.
