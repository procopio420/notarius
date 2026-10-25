> **Roteiro histórico — não usar como instrução atual.** Para o exercício integrado vigente, use [Roteiro curto para a escrevente](../teste-integrado-etapa8/ROTEIRO_PARA_MAE.md). O texto abaixo foi preservado como histórico e contém passos anteriores ao OCR local, à ficha detalhada e à revisão final obrigatória.

# Teste acompanhado da escrevente

Este teste avalia navegação, perguntas, revisão, salvamento e exportação. Use somente os exemplos fictícios desta pasta. O protótipo ainda não interpreta integralmente documentos livres e não está liberado para atendimentos reais.

Abra http://localhost:3002 neste computador e use a conta de teste informada na conversa. O computador e os dois servidores precisam estar ligados. A conta de teste não tem permissão de administração e está em um cartório fictício separado.

## Percurso principal

1. Abra **Atendimentos** e crie um atendimento com título que comece por TESTE.
2. Escreva uma mensagem e envie. Volte à lista, reabra o atendimento e confira se a mensagem continua lá.
3. Use **Anexar arquivo** e envie **01-dados-ficticios.txt**. Abra **Conferir leitura** e compare o texto com o arquivo original.
4. Registre a conferência manual do arquivo, descrevendo que é um teste fictício. Não confirme um arquivo que não abriu ou não conseguiu conferir.
5. Responda às perguntas. O botão **Usar este valor para revisar** apenas preenche a resposta. Confira o texto e só então marque a confirmação. Se deixar sem confirmar, a pergunta deve continuar pendente.
6. Abra **Revisar modelo**. A base é uma estrutura inicial; no teste, mantenha o aviso de documento fictício. Salve primeiro como rascunho e confira que **Preparar minuta** fica bloqueado. Depois aprove explicitamente o modelo fictício, com motivo de teste.
7. Prepare a minuta e compare vendedores, compradores, imóvel, preço e pagamento com os dados confirmados. Não deve aparecer nenhum fato novo.
8. Abra **Editar minuta**, acrescente uma frase de teste e tente sair sem salvar. Escolha **Continuar editando** e confira que o texto foi mantido.
9. Informe o motivo e salve uma nova versão. Recarregue, reabra e confira a alteração. A versão anterior deve continuar disponível.
10. Baixe Word e PDF. Abra os dois, confira os dados, acentos, quebras de página e a frase adicionada. Avalie a aparência do Word no programa que você usa; ela ainda não foi inspecionada visualmente pelo agente neste ambiente.

## Testes de interrupção

1. Depois de preparar a minuta, envie **02-preco-divergente.txt**. O sistema deve exibir os dois preços com suas origens, marcar a minuta anterior como desatualizada e bloquear a exportação.
2. Abra a pergunta do preço e escolha **Manter pendente**. Nenhum valor deve ser escolhido ou confirmado automaticamente.
3. Responda sem marcar confirmação. A resposta deve ficar no histórico e continuar pendente.
4. Para continuar o exercício, confira ambos os exemplos e confirme explicitamente uma escolha fictícia, com justificativa. A seleção não torna o documento real nem comprova o preço.
5. Prepare outra versão. Confira que as versões antigas continuam disponíveis para consulta, sem exportação como versão atual.
6. Envie **03-informacao-nao-identificada.txt**. O sistema deve pedir conferência humana, sem extrair fatos inexistentes.
7. Se quiser testar um escaneamento, use somente uma imagem fictícia. O protótipo deve informar que precisa de OCR e não inventar seu conteúdo. OCR ainda não está implementado.

## Como registrar um problema

Para cada ocorrência, anote: número da tarefa; ação realizada; o que esperava; o que aconteceu; se conseguiu continuar; captura da tela sem dados pessoais. Use FEEDBACK.md para registrar. Também anote quais palavras e perguntas ficaram difíceis de entender.

O teste passa quando nenhum dado aparece inventado, as pendências não desaparecem sem confirmação, o histórico é preservado e os arquivos exportados reproduzem a versão salva. Ganho de tempo com documentos reais só poderá ser medido depois da interpretação documental e da validação do modelo profissional.

## Atualização: OCR local

Imagens PNG/JPG e páginas digitalizadas de PDF agora têm leitura OCR local no Windows. A proposta de texto precisa ser comparada com a imagem; nenhuma leitura confirma os dados automaticamente. Veja ../ETAPA_9_OCR_LOCAL.md para percurso e limites.

## Atualização: revisão final antes do download

Antes de baixar Word ou PDF, abra a minuta e use **Registrar revisão final da vN**. Confira texto, dados e fontes e registre o motivo. Cada versão nova precisa de sua própria revisão; registros antigos não liberam minutas desatualizadas. Consulte ../ETAPA_17_REVISAO_FINAL.md.

## Registrar dificuldade durante o teste

Use **Registrar feedback do teste**, dentro do atendimento. Escolha onde aconteceu e descreva os passos, o resultado e o que esperava, sem dados pessoais. O relato fica salvo no caso e pode ser baixado em TXT. Ele não corrige a ficha nem confirma dados da minuta. Consulte ../ETAPA_19_FEEDBACK_TESTES.md.
