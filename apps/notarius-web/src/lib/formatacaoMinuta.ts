import type { EstiloMinuta, FormatacaoMinuta } from './atendimentos'

type Intervalo = [number, number]
export const estilos = ['negrito', 'italico', 'sublinhado'] as const

function unir(intervalos: Intervalo[]): Intervalo[] {
  const result: Intervalo[] = []
  for (const [start, end] of intervalos.sort(([a], [b]) => a - b)) {
    const previous = result.at(-1)
    if (previous && start <= previous[1]) previous[1] = Math.max(previous[1], end)
    else result.push([start, end])
  }
  return result
}

export function alternarEstilo(formatacao: FormatacaoMinuta, estilo: EstiloMinuta, start: number, end: number) {
  const intervals = formatacao[estilo] || []
  const active = intervals.some(([a, b]) => a <= start && b >= end)
  const next = active ? intervals.flatMap(([a, b]): Intervalo[] => {
    if (b <= start || a >= end) return [[a, b]]
    const remaining: Intervalo[] = []
    if (a < start) remaining.push([a, start])
    if (b > end) remaining.push([end, b])
    return remaining
  }) : unir([...intervals, [start, end]])
  if (next.length > 500) return null
  const result = { ...formatacao }
  if (next.length) result[estilo] = next
  else delete result[estilo]
  return result
}

function cortaCaractere(text: string, offset: number) {
  const char = text.charCodeAt(offset)
  return char >= 0xdc00 && char <= 0xdfff
}

export function ajustarFormatacao(before: string, after: string, formatacao: FormatacaoMinuta) {
  if (before === after || !Object.keys(formatacao).length) return formatacao
  let start = 0
  while (start < before.length && start < after.length && before[start] === after[start]) start++
  if (cortaCaractere(before, start) || cortaCaractere(after, start)) start--
  let oldEnd = before.length, newEnd = after.length
  while (oldEnd > start && newEnd > start && before[oldEnd - 1] === after[newEnd - 1]) { oldEnd--; newEnd-- }
  if (cortaCaractere(before, oldEnd) || cortaCaractere(after, newEnd)) { oldEnd++; newEnd++ }
  const offset = newEnd - oldEnd
  const result: FormatacaoMinuta = {}
  for (const estilo of estilos) {
    const intervals = (formatacao[estilo] || []).flatMap(([a, b]): Intervalo[] => {
      if (b <= start) return [[a, b]]
      if (a >= oldEnd) return [[a + offset, b + offset]]
      if (a < start && b > oldEnd) return [[a, b + offset]]
      if (a < start) return [[a, start]]
      if (b > oldEnd) return [[newEnd, b + offset]]
      return []
    })
    if (intervals.length) result[estilo] = unir(intervals)
  }
  return result
}

export function trechosFormatados(partes: string[], formatacao: FormatacaoMinuta) {
  const limits = [...new Set(estilos.flatMap(estilo => (formatacao[estilo] || []).flat()))].sort((a, b) => a - b)
  const indices = { negrito: 0, italico: 0, sublinhado: 0 }
  let start = 0, boundary = 0
  return partes.map(part => {
    const from = start, end = from + part.length
    const spans: { texto: string; estilos: EstiloMinuta[] }[] = []
    while (start < end) {
      while (boundary < limits.length && limits[boundary] <= start) boundary++
      const next = Math.min(end, limits[boundary] ?? end)
      const active = estilos.filter(estilo => {
        const ranges = formatacao[estilo] || []
        while (indices[estilo] < ranges.length && ranges[indices[estilo]][1] <= start) indices[estilo]++
        const interval = ranges[indices[estilo]]
        return interval && interval[0] <= start
      })
      spans.push({ texto: part.slice(start - from, next - from), estilos: active })
      start = next
    }
    return spans
  })
}
