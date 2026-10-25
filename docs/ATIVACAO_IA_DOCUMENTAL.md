# Preparação para ativação posterior da IA documental

25/10/2026 · Etapa 9 · Referência principal: `EXECUCAO_FLUXO_PRINCIPAL.md`, seção 23.

**Nenhum envio externo foi autorizado ou realizado nesta etapa. O sistema não está liberado para documentos reais.** O modo normal continua bloqueado. O adaptador real prepara uma requisição e interpreta um envelope fornecido localmente, mas **não implementa transporte de rede**. Não existe variável ou comando que o libere nesta versão. Não há confirmação de saldo, acesso, compatibilidade de modelo ou qualidade de IA real.

## Comportamento implementado

- A fábrica normal retorna `ProvedorReal`, que interrompe a análise antes de criar cliente ou consultar credenciais. Um resultado simulado salvo também não pode ser recuperado por repetição do POST normal. O histórico conserva sua identificação como simulado.
- O provedor simulado documental fica em `tests/`, exige configuração explícita e banco isolado de testes. Não é selecionável pelo pedido HTTP nem substitui falha do provedor real.
- O interpretador local por rótulos, já existente, continua uma ação distinta, identificada como local; não constitui IA real ou fallback de análise documental.
- Respostas inválidas, incompletas, recusadas, omissas ou com evidências incompatíveis interrompem a operação inteira. Propostas não confirmam nem escrevem diretamente na ficha. O contexto é conferido novamente na transação antes de salvar.
- Avisos públicos usam códigos permitidos, sem copiar texto de exceção, credenciais, cabeçalhos ou resposta bruta do fornecedor. Os testes de falha comprovam preservação e repetição explícita posterior no banco isolado.
- O GET protegido da análise inclui `preparacao`, diagnóstico offline sem valor da chave, sem nome de modelo configurado e sem consulta à conta. Essa informação não habilita envio. Documentos e rascunhos continuam disponíveis para revisão manual.

## Dados e ação de envio planejados

Destino planejado: **OpenAI Responses API**, `https://api.openai.com/v1/responses`. Modelo: **a definir explicitamente**, sem padrão escolhido pelo sistema. Um destino alternativo em `OPENAI_BASE_URL` é apontado como impedimento; o construtor planejado fixa o destino acima. Um futuro transporte deve recusar destinos alternativos, inclusive os herdados do ambiente.

A ação futura será a análise documental expressa dos documentos selecionados do atendimento (`POST /api/v1/atendimentos/{id}/analise-documental/`). **Hoje essa ação retorna bloqueio, sem envio.** Upload, releitura/OCR local, mudança de aba, conversa, preparação da minuta e exportação não acionam esse adaptador.

| Conteúdo da requisição preparada | Finalidade / cuidado |
| --- | --- |
| Texto das unidades selecionadas, inclusive texto de OCR | Pode conter nome, CPF, RG, endereço, estado civil e dados financeiros; ser fictício deve ser verificado antes do piloto. |
| IDs de atendimento/documento/página, número da página, linha, versão de leitura e classificação, canal | Vincular a resposta à fonte exata, sem usar semelhança de nomes. |
| Destinatários de página escolhidos pela escrevente; IDs/tipos dos registros e relações explícitas por ID | Delimitar associações; não prova identidade, vínculo jurídico ou poderes. |
| Indicadores de leitura incerta, limites e instrução suspeita | Exigir revisão em vez de inventar informação ou obedecer ao documento. |
| Campos configurados, rótulos e opções; assinatura do contexto | Restringir a saída e detectar mudança concorrente. |
| Instruções fixas e esquema estruturado de saída | Propostas com fonte/trecho/offset/campo/registro, dúvidas e cobertura de todas as unidades. |

O construtor documental não envia arquivos originais, imagens, binários, conversas completas, valores completos da ficha confirmada, redação integral do modelo, outros anexos não selecionados ou dados de outros cartórios. A assinatura de contexto depende também de IDs de revisões e mensagens, mas não revela seus textos no payload. O texto selecionado pode conter esses mesmos tipos de dados pessoais: essa exclusão não o torna anônimo.

O campo `store=False` está preparado. **Não equivale a garantia de retenção zero ou anonimato.** Termos, retenção, localização, tratamento contratual de dados e documentação oficial vigente precisam ser examinados antes de qualquer autorização. Nenhuma documentação externa foi consultada nesta etapa por restrição expressa do usuário; o SDK instalado foi inspecionado localmente. Compatibilidade de Responses/JSON Schema estrito permanece pendente de verificação oficial e teste real.

## Limites e recuperação

| Item | Política | Situação |
| --- | --- | --- |
| Seleção | Até 5 documentos por ação | Contrato local validado. |
| Texto | Até 200 unidades; 4.000 caracteres por unidade; 100.000 caracteres somados | Sem truncamento silencioso. Pedir seleção menor ao ultrapassar. |
| Entrada documental serializada, incluindo metadados e assinatura | 600.000 bytes UTF-8 | Validada localmente; instruções/esquema fixos acrescentam bytes ao envelope HTTP futuro. Não é limite total do HTTP. |
| Saída | 12.000 tokens solicitados; 500.000 bytes de texto estruturado; 200 propostas totais; até 10 propostas e 10 dúvidas por unidade | Tokens são parâmetro preparado, sem medição real; bytes/contrato/evidências são conferidos localmente. Transporte futuro deve limitar também o recebimento, sem apenas validar depois de alocar toda a resposta. |
| Tentativas | 1 por ação; `max_retries=0`; sem fallback | Uma chamada do fake por ação testada; parâmetros do SDK apenas preparados. Repetição manual explícita, sem laço automático. |
| Conexão / leitura / escrita / pool | 5 / 45 / 10 / 5 segundos | Opções preparadas; ainda sem transporte. |
| Prazo total absoluto | 60 segundos | **Planejado. Precisa implementação de deadline/cancelamento e testes do transporte.** Timeouts por fase não comprovam esse prazo total. |

Os padrões do SDK instalado não são usados como política de envio: o transporte futuro deve aplicar explicitamente essas opções. Não passar `prazo_total_s` ao construtor do SDK: ele é uma especificação separada a implementar, não um argumento suportado confirmado.

| Código público | Aviso e tratamento |
| --- | --- |
| `ia_bloqueada` | Fase atual, nenhum envio; continuar revisão manual. |
| `chave_ausente` | Pedir configuração à pessoa responsável, sem expor chave; nenhum dado aplicado. |
| `creditos_indisponiveis` | Código de quota do provedor; interromper e verificar conta antes de repetir. Não significa que saldo tenha sido consultado localmente. |
| `limite_temporario` | Limite de solicitações; não confundir com falta de crédito; sem repetição automática. |
| `tempo_esgotado` | Nenhuma proposta aplicada; revisar antes de tentar de novo. Timeout não elimina possível cobrança externa. |
| `credencial_recusada` / `provedor_indisponivel` | Revisão da configuração/indisponibilidade; sem troca para simulação. |
| `simulacao_fora_teste` | Recusa explícita, preservando histórico. |

Hoje o bloqueio de fase precede falhas reais de rede/conta. A classificação dessas falhas foi testada com exceções fabricadas no banco de testes; não é evidência de comportamento de um serviço externo. A chave ausente é detectada no diagnóstico; não houve tentativa de autenticação. Nenhuma configuração de cobrança foi alterada.

## Avaliação preparada

`casos_avaliacao_documental.py` define dez exercícios inteiramente fictícios e determinísticos: nome simples; nomes próximos com IDs distintos; cônjuge não deduzido; representação incerta; CPF divergente; página sem texto; preço ausente; pagamento futuro; leitura corrigida; instrução maliciosa.

Cada caso contém entrada e oráculo de verificação separado da requisição. O plano local inclui o oráculo para auditoria: **não enviar o arquivo inteiro ao modelo**. Apenas `requisicao_planejada`, quando preparada com modelo explícito, corresponde ao corpo proposto. O avaliador cobra fonte/versão/associação/valor corretos, contexto literal completo dos exercícios, informações obrigatórias e dúvidas. Esses critérios sintéticos não substituem avaliação semântica humana nem homologação jurídica. Campos omissos não significam inexistência do fato.

O comando de conferência de respostas lê envelopes locais; não autentica sua procedência, não executa IA e não aprova modelo. Exige todos os dez casos, sem duplicação, com hashes atuais dos casos, instruções e esquemas. Relatório sem erros significa somente que as respostas fornecidas passaram esses exercícios. Fixtures derivadas do oráculo nos testes verificam o próprio avaliador; não medem qualidade de IA.

## Comandos disponíveis agora, sem rede

Na raiz do projeto, em PowerShell, usar nomes de saída novos; os comandos recusam sobrescrever arquivos:

```powershell
Set-Location 'C:\Users\Erick Grotz\Documents\Codex\2026-10-23\bai\outputs\notarius'
.\.venv\Scripts\python.exe apps/notarius-api/manage.py check
.\.venv\Scripts\python.exe apps/notarius-api/manage.py test tests.test_preparacao_documental tests.test_analise_documental --noinput
.\.venv\Scripts\python.exe apps/notarius-api/manage.py diagnosticar_ia_documental --saida .local/diagnostico-antes-ativacao.json
.\.venv\Scripts\python.exe apps/notarius-api/manage.py avaliar_ia_documental --saida .local/plano-antes-ativacao.json
.\.venv\Scripts\python.exe apps/notarius-api/manage.py avaliar_ia_documental --help
```

Para testes Django, se a descoberta de `tests` depender do diretório, executar da pasta da API:

```powershell
Set-Location apps/notarius-api
..\..\.venv\Scripts\python.exe manage.py test tests.test_preparacao_documental tests.test_analise_documental --noinput
```

Depois de escolher explicitamente um modelo, pode-se gerar **somente um plano**, com `--modelo NOME_DO_MODELO_ESCOLHIDO`; isso não envia nada. O nome acima é um marcador, não recomendação de modelo. O comando `--executar-real` é recusado deliberadamente, sem relatório ou envio.

Para conferir posteriormente um JSON protegido de respostas fornecidas:

```powershell
..\..\.venv\Scripts\python.exe manage.py avaliar_ia_documental --respostas CAMINHO_DO_JSON --saida CAMINHO_NOVO_DO_RELATORIO
```

Formato: objeto com `versoes` exatamente iguais às do plano e `respostas` com uma entrada por caso: `{"caso":"nome_simples","resposta_api":{...envelope Responses...}}`. Não anexar chaves, cabeçalhos ou segredos. Relatórios e respostas devem ficar em local controlado; a saída não contém respostas brutas.

`avaliar_ia_compra_venda` é o avaliador histórico de mensagens/rótulos; não substitui esta bateria `documental_v1`.

## Ordem para uma ativação futura

1. Obter autorização expressa do usuário para piloto **somente com os dez casos fictícios**, indicar modelo, número de chamadas e teto de gasto aceito. Confirmar créditos/acesso na conta pelo responsável, sem alterar cobrança ou pedir chave no chat. Saldo não é inferido da presença da chave.
2. Conferir documentação oficial vigente, SDK instalado, suporte ao esquema e política de dados do provedor. Escolher e registrar modelo/versão. Definir `NOTARIUS_MODELO_DOCUMENTAL` explicitamente e configurar credencial pelo responsável em armazenamento protegido; não imprimir `.env`, chave, cabeçalhos ou variáveis completas.
3. Implementar e revisar transporte atualmente ausente, com destino fixo/sem override, pré-validação da chave, `store=False`, sem ferramentas, tentativas=1, SDK retries=0, limites de recebimento e deadline absoluto. Testar cancelamento, concorrência, ausência de chave, quota, 401/403, 429, timeout, recusa, resposta incompleta e falha de persistência usando transporte falso. **Não basta remover o bloqueio.**
4. Executar novamente testes locais, diagnóstico e plano atualizados. Revisar os hashes. Confirmar que a requisição de piloto contém somente dados fictícios, nunca anexos/atendimentos locais. A implementação futura deverá fornecer comando de execução real separado e protegido; **esse comando ainda não existe**.
5. Após autorização específica, começar por um caso; inspecionar resultado e consumo. Só então rodar os restantes dentro do teto autorizado, parando no primeiro erro, sem repetição automática. Registrar data, modelo efetivo, versão do SDK, hashes, ID de requisição, uso/custo disponível e falhas, sem segredos. Guardar evidências de procedência e respostas com acesso controlado.
6. Conferir envelopes pelo avaliador offline e revisão humana: campo, pessoa/papel/imóvel correto, fonte/página/leitura/trecho, interpretação, omissões, conflito e dúvida. Nenhum erro crítico de invenção, troca de pessoa, fonte inexistente ou quitação indevida é aceitável. Uma única campanha aprovada não comprova generalização para documentos reais.
7. A escrevente homologa redação integral, cenários, requisitos e condições, e executa o roteiro de uso. Revalidar privacidade, segurança, concorrência/isolamento e operação no ambiente de destino. Documentos reais exigem nova autorização e plano de validação adequados; não são liberados pelo resultado dos exercícios fictícios.

Consulte `MATRIZ_ACEITE_FINAL.md` para distinguir os três grupos de aceite. Não existe declaração de prontidão de produção ou jurídica nesta entrega.
