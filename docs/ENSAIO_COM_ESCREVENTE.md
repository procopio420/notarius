# Ensaio acompanhado e escopo dos serviços

Registro da preparação técnica de 07/11/2026. O teste de uso da Mary segue o
[roteiro do piloto com casos reais](ROTEIRO_PILOTO_COMPRA_VENDA.md#teste-de-uso-da-mary).

## O que podemos ensaiar hoje

Compra e venda pelo fluxo manual, em exercício fictício separado. Já existe um
exercício com vinte anexos, fontes de 46 campos e três versões de minuta.
Conferência atual dos arquivos aprovou integridade e correspondência do texto
salvo com Word/PDF; isso não aprova profissionalmente a redação.

1. Seguir [a abertura do exercício separado](piloto-profissional/ROTEIRO_ETAPA_4_FICTICIO.md).
   O endereço normal usa outro banco; não misturar dados reais no exercício.
2. Examinar uma pessoa, um documento e o trecho que sustenta cada dado.
3. Ver a correção do preço e comparar as versões da minuta.
4. Ensaiar edição e revisão, identificando qualquer aprovação como simulada.
5. Abrir as exportações no programa que a escrevente usa e anotar cortes,
   redação inadequada, concordâncias e informações faltantes.
6. Fechar e reabrir o atendimento; conferir se o trabalho foi salvo.
7. Registrar dificuldades sem colocar dados pessoais nos relatórios do projeto.

Para reproduzir o ensaio técnico, comece pela minuta pronta e confira o percurso
e o padrão antes de explorar o preenchimento dos 46 campos.
Não clicar em análise de IA esperando resposta: o envio permanece bloqueado.

## Situação dos serviços solicitados

| Serviço | Evidência atual | Preparação que ainda falta |
| --- | --- | --- |
| Compra e venda | Fluxo local próprio, modelo candidato e exercício completo | Decisão da escrevente sobre redação/cenário, caso real e validação da IA posterior |
| Procurações | Há esquemas legados para veículo/ad judicia e representação em compra e venda | Escolher o tipo de procuração, obter padrão autorizado, criar fluxo próprio e testes; representação numa venda não equivale a emissão de procuração |
| Doações | Sem fluxo específico identificado no piloto | Padrão autorizado, cenário, campos/vínculos e condições definidos com a escrevente; implementação e exercício fictício |
| Inventários | Sem fluxo específico identificado no piloto | Padrão autorizado, cenário, entidades/vínculos e condições definidos com a escrevente; implementação e exercício fictício |

O atendimento atual tem `tipo_ato=compra_venda` fixo e a ficha inclui papéis de
vendedor/comprador. Não usar esse cadastro como se já fosse um inventário ou
doação. Os esquemas antigos de procuração não estão homologados nem disponíveis
pela API restrita do piloto. Não foi criado um seletor que ofereça serviços sem
seu fluxo implementado.

## Preparação de cada serviço novo

A escrevente fornece ou identifica um modelo completo que possa ser usado,
preferencialmente sem dados pessoais para os ensaios. Ela define qual situação
o modelo atende, participantes, vínculos, condições de inclusão/omissão das
cláusulas e decisões que exigem revisão. Essas escolhas não serão tratadas como
regras universais. Não é necessário reenviar o padrão de compra e venda existente.

Para cada um: adaptar a ficha e a minuta, preservar fontes e histórico,
configurar bloqueios de dados pendentes, gerar exercício fictício e conferir
Word/PDF. Só oferecer o serviço para uso acompanhado após esse percurso. Isso
é configuração de modelos de documento; não é treinamento/fine-tuning da IA.

## IA e orçamento

Saldo e chave são preparativos de conta, não comprovação de integração.
`ProvedorReal.analisar` permanece bloqueado e o perfil local desativa geração.
Nada nesta preparação valida a chave, saldo/acesso ao modelo ou resposta externa.

Teto de testes preparado: **US$ 0,50 no total**, dez tentativas pequenas com
reserva conservadora de US$ 0,05 cada. Até 32.000 bytes por pedido e 4.000 tokens
de saída. Não há repetição automática nem devolução da reserva por falha.
[Detalhes e limitações](LIMITE_TESTES_IA.md).

Quando o usuário pedir para testar: implementar a conexão protegida pelo
orçamento, validar primeiro com transporte falso e começar com um único caso
fictício. Conferir fontes, pessoa correta, omissões, divergências e consumo antes
de ampliar. Não iniciar uma bateria completa automaticamente. Documentos reais
exigem autorização de conteúdo e destino, além da conferência profissional.

## Limites da prontidão

A checagem TypeScript do fluxo de atendimentos e componentes importados passou
com configuração temporária local que mantém as opções estritas do projeto.
A checagem global falhou em módulos legados e testes com dependências ausentes;
isso permanece pendente e não foi escondido alterando a configuração de build.
O ambiente é de desenvolvimento local, sem liberação de produção ou multiusuário.

Testes locais não gastam tokens da API. O roteiro automatizado
`scripts/conferir-prontidao-offline.py` bloqueia conexões e clientes OpenAI e
exercita o banco de testes fictício. Os resultados desta rodada ficam em
[continuidade do piloto](CONTINUIDADE_PILOTO_REAL.md).

Não há garantia de que o primeiro teste real vá passar: autenticação, rede,
compatibilidade do esquema e qualidade de interpretação ainda dependem dele.
O ensaio acompanhado pode começar pelo percurso manual já disponível.
