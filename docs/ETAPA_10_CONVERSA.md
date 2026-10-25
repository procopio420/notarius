# Etapa 10 — orientação na conversa

O atendimento agora apresenta a orientação ao lado do envio de mensagens, com a próxima pergunta e acesso aos formulários de revisão.

Após salvar uma mensagem, o sistema mostra os campos explicitamente identificados e os trechos que não conseguiu interpretar. As propostas preservam o texto literal e a identificação da mensagem. Nada é gravado ou confirmado na ficha sem ação da escrevente.

## Teste fictício

Envie:

```
Vendedores: PESSOA FICTÍCIA
Preço: R$ 100.000,00
Ela talvez pague depois
```

A orientação deve mostrar vendedores e preço como propostas, e a última linha como não interpretada. **Revisar este campo** abre a pergunta com as fontes; **Associar informação à ficha** permite escolher o campo manualmente. A próxima pendência continua visível. Respostas sem confirmação continuam pendentes. Novas mensagens atualizam a orientação, mantendo as anteriores no histórico.

## Limite deliberado

É orientação por regras locais, não um modelo de linguagem. Não compreende livremente frases, não atesta veracidade e não resolve dúvidas jurídicas. Mensagens em linguagem livre ficam explicitamente para interpretação humana. Não envia documentos ou mensagens a provedores externos.

O próximo avanço de interpretação livre precisa de uma integração de IA configurada, propostas estruturadas com trechos literais verificáveis e testes contra omissões, mistura de participantes e instruções presentes nos documentos. A homologação do modelo profissional continua pendente.

## Verificação

41 testes Django passaram (incluindo os 38 anteriores). Foram acrescentados casos de mensagem parcialmente interpretada, texto sem campos, instruções para confirmar indevidamente, reenvio e isolamento de cartório. ESLint passou nos componentes, páginas de atendimento e cliente da API.
