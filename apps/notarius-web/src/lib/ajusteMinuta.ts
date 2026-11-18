function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()
}

const campos = [
  ['vendedores', /\bvendedor(?:a|es|as)?\b/],
  ['compradores', /\bcomprador(?:a|es|as)?\b/],
  ['imovel', /\b(?:imovel|matricula|endereco do imovel)\b/],
  ['preco', /\bpreco\b/],
  ['pagamento', /\bpagamento\b/],
  ['quitacao', /\bquitacao\b/],
] as const

export function interpretarPedidoDeAjuste(texto: string) {
  const normalized = normalizar(texto.trim())
  if (!/^(?:ajuste|ajustar|corrija|corrigir|use|usar|adote|alter[ae]|atualize|troque)\b/.test(normalized)) return null
  const targets = campos.filter(([, pattern]) => pattern.test(normalized)).map(([key]) => key)
  const ambiguousPerson = /\b(?:rg|sobrenome|grafia|nome)\b/.test(normalized)
    && !targets.includes('vendedores') && !targets.includes('compradores')
  if (!targets.length && !ambiguousPerson && !/\b(?:minuta|endereco)\b/.test(normalized)) return null
  return { campos: targets, pessoaIndefinida: ambiguousPerson }
}

export function fonteMencionada(pedido: string, arquivo?: string) {
  if (!arquivo) return false
  const text = normalizar(pedido)
  const filename = normalizar(arquivo)
  const name = text.match(/\b(?:print|arquivo|anexo)\s+([a-z0-9_.-]+)/)?.[1].replace(/\.+$/, '')
  const tokens = filename.split(/[^a-z0-9]+/)
  return !!(name && (filename === name || tokens.includes(name)))
    || ['rg', 'matricula'].some(term => text.split(/[^a-z0-9]+/).includes(term) && tokens.includes(term))
}
