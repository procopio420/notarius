# Etapa 6 — edição e exportação

## Uso

Abra a minuta atual e escolha **Editar minuta**. O editor conserva o texto sem reescrita automática. **Salvar nova versão** exige motivo e preserva o texto anterior. Fechar com alterações não salvas abre uma confirmação para continuar editando ou descartar. A página também sinaliza a tentativa de recarregar durante uma edição não salva.

**Baixar Word** e **Baixar PDF** exportam somente a versão salva mais recente. Downloads são bloqueados enquanto o editor está ativo e quando dados, documentos ou modelo tornarem a minuta desatualizada. Versões históricas permanecem disponíveis para consulta, sem exportação ou edição direta.

Uma alteração manual não atualiza a ficha nem é validada automaticamente como fato. Corrigir dados exige ajustar a ficha e preparar outra versão. As versões editadas têm identificação, autor, motivo e referência à versão anterior. Exportação é de minuta para revisão; não há assinatura, selo, certificação ou conclusão de ato.

## Implementação

- POST `editar-minuta/`: salva texto, motivo e identificador idempotente com verificação da versão e do estado dos dados.
- GET `minutas/{id}/exportar/?formato=docx|pdf`: autorização por cartório, verificação de versão, conferência e modelo aprovado antes da exportação.
- Word editável produzido por python-docx; PDF paginado por ReportLab com fonte incorporada, margens A4 e identificação de versão.
- Fonte de PDF: NOTARIUS_PDF_FONT, Times New Roman no Windows ou DejaVu Serif no Linux. Se faltar fonte ou houver caractere não suportado, a operação é recusada, sem substituição silenciosa.
- Downloads não usam URLs públicas e retornam Cache-Control no-store.

## Verificação

Testes cobrem edição com histórico, reenvio sem duplicação, concorrência, bloqueio após mudança dos dados, conteúdo inválido, acesso entre cartórios, Word reaberto com o texto salvo integral, PDF com acentos e caracteres literais, caracteres não suportados e paginação de texto longo.

Na interface, foi editada uma minuta exclusivamente fictícia; o aviso de alterações não salvas preservou o texto e o salvamento criou a versão 2. Ambos os botões de download foram acionados. Os arquivos retornados pela API foram lidos e o PDF foi renderizado e inspecionado visualmente.

Limitação de QA: o renderizador de DOCX foi executado e diagnosticou ausência de LibreOffice/soffice.exe. O Word passou por abertura e comparação estrutural do texto, mas sua paginação e aparência ainda não foram verificadas visualmente neste ambiente. O PDF teve inspeção visual. Não se deve confundir essa limitação com a revisão profissional do modelo real, que também continua necessária.
