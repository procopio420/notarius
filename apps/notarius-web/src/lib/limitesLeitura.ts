const descricoes: Record<string, string> = {
  quantidade_paginas: 'arquivo fora do limite de 1 a 40 páginas',
  ocr_10_paginas: 'limite de OCR em 10 páginas por arquivo',
  texto_50000: 'texto da página limitado a 50.000 caracteres',
  ocr_texto_50000: 'texto do OCR limitado a 50.000 caracteres',
  ocr_regioes_5000: 'OCR limitado a 5.000 regiões',
  arquivo_protegido: 'arquivo protegido por senha',
  tempo_ou_resposta: 'leitura não concluída no tempo disponível',
  falha_leitura: 'falha ao ler o arquivo',
}
export const descreverLimites = (limites: string[]) => limites.map(v => descricoes[v] || 'leitura incompleta; confira o original').join('; ')
