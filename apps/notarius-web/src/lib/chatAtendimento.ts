import type { Anexo, OrigemDadoMinuta } from './atendimentos'

export function origemDaMinuta(origem?: OrigemDadoMinuta): Exclude<OrigemDadoMinuta, { tipo: 'legado' }> | undefined {
  return origem?.tipo === 'legado' ? origem.origem_anterior : origem
}

// Windows OCR supplies no confidence score: never invent which word is illegible.
export function pendenciasLeitura(files: Anexo[]) {
  return files.flatMap(file => {
    const pages = file.paginas.flatMap(page => {
      const texto = page.texto_ocr?.trim() || page.texto.trim()
      const ocr = !!page.texto_ocr?.trim() || /ocr/i.test(page.metodo || '')
      const limitada = !!page.limites_leitura?.length
      if (texto && !ocr && !limitada && page.situacao !== 'revisao') return []
      return [{ chave: `${file.id}:${file.leitura_versao}:${page.id}`, arquivo: file.nome,
        pagina: page.numero, texto, motivo: !texto ? 'Não consegui obter texto desta página. Envie uma foto mais nítida ou transcreva o conteúdo.'
          : limitada ? 'A leitura desta página foi interrompida por um limite. Confira o original e envie as partes que faltaram.'
          : ocr ? 'Esta transcrição veio da foto. Não tenho uma medida confiável de certeza por palavra. Confira com o original e informe qualquer correção.'
          : 'Esta página precisa de conferência. Compare a transcrição com o original.',
        aviso: page.aviso || '' }]
    })
    if (!file.paginas.length || file.cobertura?.limites?.length) pages.push({
      chave: `${file.id}:${file.leitura_versao}:cobertura`, arquivo: file.nome, pagina: 0, texto: '',
      motivo: !file.paginas.length ? 'Não consegui ler as páginas deste arquivo. Reenvie uma cópia legível.' : 'O arquivo não foi lido integralmente. Confira as páginas ausentes e envie-as separadamente.',
      aviso: file.cobertura?.aviso || file.aviso || '',
    })
    return pages
  })
}

// Describes local extraction only. It never compares identities or confirms facts.
export function resumoLeituraLocal(files: Anexo[]) {
  const incertos = files.filter(file => !file.paginas.length || file.situacao === 'revisao' || file.paginas.some(p => p.situacao === 'revisao' || !!p.limites_leitura?.length) || !!file.cobertura?.limites?.length)
  const semTexto = files.filter(file => !file.paginas.some(p => p.texto.trim() || p.texto_ocr?.trim()))
  return { total: files.length, incertos, semTexto }
}

export function textoDosDocumentos(files: Anexo[]) {
  return ['LEITURA LOCAL DOS DOCUMENTOS — NÃO É MINUTA',
    'Transcrição automática para conferência. Pode conter erros e omissões. Nenhum fato confirmado.',
    ...files.flatMap(file => [
      `\nARQUIVO: ${file.nome} · leitura ${file.leitura_versao}`,
      ...file.paginas.flatMap(page => [`\nPÁGINA ${page.numero} — ${page.situacao}`,
        page.texto || '[Sem texto extraível]',
        ...(page.texto_ocr && page.texto_ocr !== page.texto ? ['OCR LOCAL (CONFERIR):', page.texto_ocr] : []),
        ...(page.limites_leitura?.length ? [`Limites: ${page.limites_leitura.join(', ')}`] : [])])])].join('\n')
}
