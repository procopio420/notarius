# Matriz final de aceite — função principal do Notarius

25/10/2026 · Etapa 9 · **Preparação offline; envio real bloqueado; não liberado para documentos reais.**

O documento único de execução continua sendo `EXECUCAO_FLUXO_PRINCIPAL.md`. Esta matriz consolida os aceites, sem substituir seu histórico. Procedimento e comandos em `ATIVACAO_IA_DOCUMENTAL.md`; roteiro para a escrevente em `teste-integrado-etapa8/ROTEIRO_PARA_MAE.md`.

## 1. Implementação concluída e verificada localmente

| Aceite verificável | Evidência / limite da conclusão | Estado |
| --- | --- | --- |
| Pessoas com IDs próprios; papéis e relações separados; imóvel/negociação/pagamento separados | Testes de ficha, fontes e percursos integrados; migração de conteúdo amplo não reparte pessoas automaticamente. | Verificado localmente |
| Documentos classificados e vinculados explicitamente; original e versões preservados; referência de redação não alimenta novo caso | Testes de organização e análise documental; releitura/reclassificação invalida contexto antigo. OCR sintético não prova qualidade em documentos reais. | Verificado localmente |
| Extração só gera propostas/dúvidas com fonte; validação atômica e nenhuma confirmação da IA | Testes de análise documental, propostas e integração; respostas de provedor **simulado e identificado**, em banco isolado. | Verificado localmente |
| Divergências, vínculo incerto, página sem texto e omissões não viram fatos | Comparação/conversa/pendências e casos fictícios adversariais; resolução humana é simulada somente nos testes. | Verificado localmente |
| Conversa retoma pendências; minuta usa dados confirmados; edição/revisão/exportação; correção desatualiza | Etapa 8: 143 testes, incluindo nove percursos e rótulos; Word/PDF conferidos por conteúdo. Interface examinada no navegador; uso pela mãe ainda pendente. | Verificado localmente, nos casos definidos |
| Isolamento e alterações concorrentes | Testes por tenant/caso e versões/contexto; concorrência local SQLite. Não comprova ambiente PostgreSQL/produção. | Verificado localmente |
| Modo normal nunca substitui análise documental real por fake, inclusive repetição de análise simulada salva | Novo teste de replay, fábrica bloqueada, guardas de banco/configuração de teste e ausência de chamada ao SDK. Histórico continua identificado. | Verificado localmente |
| Falta de chave, quota, limite temporário, timeout e falha têm códigos/avisos seguros; trabalho preservado | Diagnóstico de chave ausente sem revelar valor. Exceções fabricadas testam mapeamento público, preservação de anexos/contagens e repetição explícita posterior. Não foram observados erros de um provedor real. | Verificado localmente, com falhas fabricadas |
| Limites de documentos/texto/bytes, validação de referência e envelope; nada truncado silenciosamente | Contratos e servidor; testes de excesso, Unicode inválido, JSON profundo/duplicado, fonte antiga/inexistente, pessoa trocada, omissão e dúvida vazia. | Verificado localmente |
| Tokens, SDK retries=0 e prazos por fase/total definidos | Construtor puro e política: 12.000 tokens; 1 tentativa; 5/45/10/5 segundos e total planejado 60s. **Não existe transporte nem deadline implementado.** | Preparado, sem validação de rede |
| Avaliação documental fictícia versionada e comandos sem rede | Dez casos embutidos; plano/oráculo separados; hashes, cobertura e procedência não atestada. Testes do avaliador usam fixtures e não medem IA. `--executar-real` recusa envio. | Verificado localmente |
| Diagnóstico/comandos não mostram chave, consultam créditos ou alteram cobrança | Relatório offline só registra presença da configuração e impedimentos. SDK/HTTP monitorados por mocks nos testes. Nenhum cliente real foi criado nesta etapa. | Verificado localmente |

Evidências da etapa 9: `.local/etapa9-regressao.log`, `.local/etapa9-diagnostico.json`, `.local/etapa9-plano-documental.json`. O diagnóstico não comprova validade da credencial. O plano não contém resultado de IA. Os totais da bateria estão registrados na seção 23 do documento único após sua conclusão.

## 2. Decisões e modelo que dependem da escrevente

| Entrega/decisão | Critério para aceite | Estado |
| --- | --- | --- |
| Redação profissional integral | Fornecer texto-base completo e versão; conferir transcrição/ordem das páginas do exemplo rasurado; distinguir texto fixo, dados e decisão. Imagens de exemplo não são dados do caso. | Pendente |
| Cenários permitidos | Homologar compra direta e representação, participantes múltiplos, cônjuges, poderes/limites e condições que interrompem o cenário. Não inferir exigência jurídica a partir do exemplo. | Pendente |
| Campos e documentos requeridos por cenário | Aprovar configuração e alternativas/exceções; definir como documentar justificativa e evidência. Nenhuma regra documental inventada como obrigatória. | Pendente |
| Cláusulas e condições | Aprovar blocos/repetições e condição exata de inclusão; situação de pagamento, quitação, consulta e assinatura só com informação expressa e confirmada. | Pendente |
| Revisão final e exportação | Aprovar redação e apresentação no Word/PDF utilizados; conferir edição manual e fontes da versão exata. Modelo fictício não é escritura homologada. | Pendente |
| Uso por pessoa iniciante | Mãe/escrevente executa roteiro sem confirmação fabricada pelo agente; registrar dúvidas, ajuda e retomada. | Pendente |

## 3. Testes reais dependentes de autorização e créditos

| Condição | Evidência necessária antes do aceite | Estado |
| --- | --- | --- |
| Autorização do piloto | Autorização expressa para casos fictícios, modelo, quantidade de chamadas e teto de gasto; responsável verifica créditos/acesso. | Pendente; nenhum envio autorizado |
| Provedor/modelo e dados enviados | Documentação oficial vigente, política de tratamento/retenção e compatibilidade de esquema aprovadas; destino fixo, credencial protegida. `store=False` não prova retenção zero. | Pendente |
| Transporte real | Implementar e revisar envio hoje ausente; deadline absoluto/cancelamento, limites de recebimento, uma tentativa, sem fallback, destino alternativo recusado e observabilidade sem segredos. Testar antes com transporte falso. | Pendente; não ativável por variável |
| Piloto e campanha fictícia real | Executar primeiro um caso autorizado e depois os demais, dentro do teto; origem comprovada, IDs de requisição/modelo/uso/hashes e revisão humana da interpretação. | Não realizado |
| Falhas reais do provedor | Verificar comportamento de quota, acesso, recusa, resposta incompleta, interrupções e timeout, sem repetições automáticas nem alterações parciais. Não provocar gasto/falhas sem plano autorizado. | Não realizado |
| Aceite de qualidade | Zero erro crítico de invenção, troca de pessoa/papel/imóvel, evidência falsa, decisão automática de conflito ou quitação indevida; registrar também omissões/dúvidas. Amostra fictícia tem alcance limitado. | Não realizado |
| Documentos reais / produção | Nova autorização, validação com amostras adequadas, homologação da escrevente e avaliação de privacidade, segurança, operação, concorrência e ambiente final. | Não autorizado e não comprovado |

**Conclusão de aceite:** o fluxo tem verificações locais e uma preparação offline auditável. Homologação profissional e avaliação real permanecem abertas. Nenhum desses grupos pode ser marcado como concluído por aprovação automática do sistema.
