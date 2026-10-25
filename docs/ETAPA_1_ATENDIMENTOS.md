# Etapa 1 — atendimentos de compra e venda

## Entrega

- `/atendimentos`: criação e lista de atendimentos do cartório selecionado.
- `/atendimentos/[id]`: histórico persistente e envio de mensagens da escrevente.
- API `/api/v1/atendimentos/` e `/api/v1/atendimentos/{id}/mensagens/`.
- Mensagens registram autor, data e identificador de reenvio. O mesmo identificador e texto não criam mensagens duplicadas.
- O acesso exige autenticação e vínculo com o cartório. Os atendimentos são compartilhados entre usuários autorizados do mesmo cartório.
- O formulário só limpa a mensagem após confirmação do servidor; texto ainda não enviado não é salvo.

O menu Atendimentos e o botão Novo Processo da Inbox abrem a lista nova. Os registros antigos de Processo continuam separados; esta entrega não os converte nem os exclui.

## Validação

Executar, em `apps/notarius-api`, com o Python do ambiente virtual:

```
python manage.py migrate
python manage.py test tests.test_atendimentos --noinput
python manage.py runserver 127.0.0.1:8002 --noreload
```

Quatro testes cobrem persistência, reenvio, conteúdo inválido, autenticação e isolamento entre cartórios. `manage.py check` também passou.

No navegador foram criados um atendimento e duas mensagens fictícias, seguida de saída para a lista, reabertura e recarregamento completo. O histórico foi restaurado. Não houve erros TypeScript nos arquivos desta entrega; a verificação global continua falhando por problemas anteriores em outras áreas do projeto.

## Limites

Não há resposta de IA, extração de campos, pendências estruturadas, anexos ou geração de minuta nesta etapa. Não foram incorporados dados dos documentos enviados na conversa. A base local é SQLite; não há implantação remota nem backup automatizado nesta entrega.
