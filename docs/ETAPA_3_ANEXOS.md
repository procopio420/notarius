# Etapa 3 — anexos e leitura literal

## Experiência

A conversa é a tela principal. A ficha extensa deixou de ocupar uma coluna permanente. **Revisar informações** abre os dados em pop-up. Mensagens e trechos documentais abrem uma pergunta curta para escolher o campo; a revisão ocorre em um formulário separado, preservando o histórico.

**Anexar arquivo** recebe um arquivo por vez, até 10 MB. Formatos: PDF, TXT UTF-8, PNG e JPG. Downloads passam pela API autenticada e pelo vínculo com o cartório. O conteúdo original fica no banco, sem URL pública de mídia. Arquivos iguais no mesmo atendimento são identificados por SHA-256 e não duplicados. O armazenamento no banco é apropriado para este piloto local, mas exige backup e revisão de capacidade antes de ampliar o uso.

## Leitura

- PDF com texto: extração literal por página usando pypdf, até 40 páginas.
- TXT: texto literal em uma unidade de leitura, até 50.000 caracteres.
- PDF sem texto, protegido por senha, corrompido, com leitura esparsa ou sinais de leitura incompleta: pendente de revisão.
- Imagens: recebidas, mas pendentes de OCR. Não há OCR implementado nesta entrega.
- Páginas com objetos de imagem/formulário são sinalizadas conservadoramente para revisão, mesmo que parte do texto esteja disponível.
- O processo de leitura de PDF é isolado em subprocesso com limite de tempo; falhas não são substituídas por conteúdo inferido.

O texto extraído não garante leitura integral nem autenticidade. Não há chamada a modelo externo nem preenchimento/confirmacão automática de campos nesta etapa. Interpretar, comparar documentos e formular perguntas automáticas faz parte da etapa 4.

## Evidências

Ao vincular um trecho à ficha, a revisão registra arquivo, número da página, trecho literal, autor e motivo. A API exige que o trecho exista no texto extraído e que a página pertença ao mesmo atendimento. Mensagem e documento não podem ser declarados simultaneamente como uma única origem. Uma edição humana continua identificada como informação ou confirmação da escrevente.

## Testes

Doze testes de API aprovados, cobrindo a base anterior e também PDF textual e misto, PDF corrompido/protegido, UTF-8 inválido, tipo/tamanho, origem literal, download idêntico ao original, duplicação e acesso entre atendimentos/cartórios. Django check e migrações sem alterações pendentes. Não houve erros TypeScript nos arquivos desta entrega; erros anteriores em outras áreas continuam fora deste escopo.

No navegador foram conferidos anexos fictícios, o alerta da página sem texto e o vínculo de um trecho do PDF a um campo não confirmado. Nenhum anexo pessoal enviado na conversa foi inserido no projeto ou na base.
