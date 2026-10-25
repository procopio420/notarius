# Etapa 2 — ficha e pendências

O atendimento agora contém conversa, ficha e lista de pendências. Os campos iniciais são vendedores, compradores, imóvel, preço, forma de pagamento, representação e observações. Esta lista não é uma declaração de suficiência documental ou jurídica.

## Uso

1. Envie uma mensagem na conversa e escolha **Usar na ficha**.
2. Escolha o campo e confira o conteúdo antes de salvar. A transcrição é manual nesta etapa.
3. Informe a situação e o motivo do registro. É possível registrar diretamente no campo, com origem manual.
4. Consulte **Origem e histórico** para ver a mensagem vinculada, motivo, autor, data e versões anteriores.

Estados: ausente, informado pela escrevente, confirmado pela escrevente, divergente e leitura incerta. Campos iniciais sem confirmação e qualquer campo informado, divergente ou incerto aparecem nas pendências. Campos opcionais ausentes não exigem confirmação. Confirmado pela escrevente não significa verificado pela IA ou por documentos.

Cada salvamento acrescenta uma revisão no banco; não substitui a anterior. A API rejeita a tentativa de salvar com uma versão antiga e referências a mensagens de outro atendimento. Endpoints disponíveis: GET/POST `/api/v1/atendimentos/{id}/ficha/`.

## Validação

- Sete testes de API aprovados: persistência das conversas, reenvio, validação, autenticação, isolamento, histórico da ficha, origem e conflito de versão.
- Interface: registro vinculado a mensagem, registro manual de preço fictício, alteração para divergente, recarregamento e consulta das duas versões anteriores.
- Django check e verificação das migrações passaram.
- Sem erros TypeScript nos arquivos de atendimentos verificados; permanecem erros anteriores em outras partes do projeto.

Não há extração automática, upload, resposta da IA ou geração de minuta nesta entrega. Não foram usados dados pessoais dos anexos. A etapa 3 adicionará os documentos e suas evidências; a etapa 4 adicionará as comparações e perguntas automáticas.
