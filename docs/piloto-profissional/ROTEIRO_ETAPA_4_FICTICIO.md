# Repetir o atendimento fictício com a escrevente

Exercício concluído em 25/10/2026, até minuta revisada e exportada. Todas as informações, confirmações, aprovação de cópia de modelo e revisão final deste exercício são simuladas. **Não representam aprovação do padrão profissional nem revisão de um caso real.**

## Reabrir o exercício já salvo

O acesso principal foi devolvido ao banco operacional anterior. Para examinar o exercício isolado, abra PowerShell na pasta do projeto:

```powershell
.\scripts\encerrar-piloto-local.ps1
.\scripts\iniciar-piloto-local.ps1 -Banco .local\etapa4-ficticio-20261025-134312-b469c4\exercicio.sqlite3
```

Abra **http://localhost:3002/atendimentos**. O acesso exclusivamente fictício fica em `.local/etapa4-ficticio-20261025-134312-b469c4/acesso-ficticio.json`, fora do Git. Não use senha real nesse exercício. Confira o cartório **EXERCÍCIO FICTÍCIO ETAPA 4 — APROVAÇÕES SIMULADAS** e o atendimento de mesmo exercício. O link direto é [abrir o exercício](http://localhost:3002/atendimentos/4d3eebe5-f14d-4566-a3d5-5fe0489fc07b), enquanto esse banco estiver selecionado.

## Sete tarefas para repetir o caminho

1. **Cadastro e modelo.** Confira cartório e atendimento. Em Minuta → Revisar modelo, examine o candidato e suas posições. Salvar como rascunho e reabrir deve preservar o texto e manter a geração bloqueada. A versão profissional oferecida continua sem aprovação. A aprovação existente na cópia deste exercício está identificada como simulada.
2. **Documentos.** Abra um arquivo `FICTICIO-...`, baixe o original e confira sua leitura. Veja finalidade, destinatário e página. Os 20 anexos deste exercício cobrem as posições do rascunho; não são uma lista de documentos obrigatórios para compra e venda.
3. **Ficha e fontes.** Em Conversa → Ficha detalhada, escolha explicitamente pessoa, papel, imóvel ou negócio e o campo. Selecione a página como fonte, transcreva trecho literal e revise o valor. Sem IA, esse é o caminho normal. Informação expressa da escrevente gera mensagem de origem; não é automaticamente uma constatação documental. Primeiro registre como informado e depois confirme somente o que efetivamente conferiu.
4. **Correção e pendências.** Examine o histórico de preço e condições do exercício. O preço foi corrigido manualmente; o documento antigo não foi apagado. Compare todas as fontes e justifique a escolha. Alterar preço exige revisar condições; a minuta anterior deve continuar desatualizada. Não resolva uma pendência apenas para liberar botão.
5. **Geração permitida.** Confira os vínculos por registro. Sem aprovação explícita da versão do modelo ou com pendência, preparar deve ser recusado. No exercício isolado, a cópia aprovada de forma simulada permitiu gerar v1 e, após a correção/conferência, v2. Essa simulação não se transfere para o padrão ou para outro atendimento.
6. **Edição e revisão.** Abra v3, compare com v2 e veja a nota acrescentada. Edição salva nova versão e não corrige a ficha automaticamente. A revisão final do exercício está registrada como simulada. Num novo percurso, sem revisão da versão atual, os downloads devem ficar bloqueados; alterar dados ou texto exige nova revisão.
7. **Exportação e retomada.** Baixe Word/PDF e confira pessoas, imóvel, preço, condições, acentos, zeros, encerramento e final do texto. Saia, encerre os serviços, inicie novamente e reabra o mesmo atendimento. O exercício foi retomado após reinício com v3 e revisão preservadas. Não interprete a situação “Em andamento” como ato lavrado: o percurso termina na minuta revisada exportada, sem assinatura ou conclusão do ato.

Os arquivos finais conferidos estão em `.local/etapa4-ficticio-20261025-134312-b469c4/minuta-ficticia-final.docx` e `.pdf`. Ambos têm duas páginas. A apresentação do DOCX foi renderizada e inspecionada com LibreOffice local; ainda cabe conferir no Microsoft Word ou programa efetivamente usado pela escrevente. As primeiras exportações e imagens de QA foram preservadas, mas os arquivos com sufixo `-final` são os resultados desta etapa.

## Voltar ao banco anterior

```powershell
.\scripts\encerrar-piloto-local.ps1
.\scripts\iniciar-piloto-local.ps1 -Banco apps/notarius-api/db.sqlite3
```

A troca não sobrescreve ou mescla bancos. Pode ser necessário entrar novamente depois da troca de ambiente; o token de um banco não autentica no outro. Para verificar os arquivos do exercício sem trocar o banco, use o relatório privado `resultado-final.json`. O script `scripts/conferir-exercicio-etapa4.py PASTA` confere o banco fictício e os arquivos renderizados; `--http` exige que esse exercício esteja em execução nas portas locais. Ele não aprova nem corrige dados.

Reprodução técnica adicional, somente fictícia: `.\.venv\Scripts\python.exe scripts/ensaio-piloto-etapa4.py` cria **outro banco novo** dentro de `.local`, usa API HTTP em porta loopback livre e simula decisões com identificação explícita. Não muda a seleção do banco operacional. Na execução desta rodada, houve um endereço incorreto no roteiro automático; ele foi corrigido e o atendimento preservado foi concluído pela interface. Não se declara execução automática única sem falhas.

## O que ainda impede o caso real

- A escrevente precisa aprovar a redação, o cenário, as posições e a aplicabilidade das cláusulas do padrão de origem. As aprovações deste banco fictício não servem para isso.
- O caso real precisa de documentos, fontes, associações, divergências e declarações efetivamente conferidos pela escrevente, sem reutilizar os dados deste exercício.
- A IA documental continua indisponível. Isso exige o caminho manual acompanhado; o ensaio com TXT não valida qualidade de OCR em documentos reais digitalizados ou ilegíveis.
- Apresentação e conteúdo final do caso devem ser conferidos no programa da escrevente. É necessário manter acesso local restrito e executar o backup com senha própria antes da sessão, conforme [operação local](../OPERACAO_PILOTO_LOCAL.md).

Anote a etapa em que houve dúvida, o comportamento observado e o que precisou de ajuda. Registre problemas sem dados pessoais na documentação versionada; preserve originais e material do caso em local privado.
