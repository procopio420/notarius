'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { fichaDetalhadaApi, type TipoRegistro } from '@/lib/fichaDetalhada'
import type { TextoModelo } from '@/lib/atendimentos'

export function PosicoesModelo({ id, scope, value, disabled, onChange }: { id: string; scope: (string | undefined)[]; value: TextoModelo; disabled: boolean; onChange: (v: TextoModelo) => void }) {
  const schema = useQuery({ queryKey: ['schema-posicoes', ...scope], queryFn: () => fichaDetalhadaApi.get(id) })
  const [key, setKey] = useState(''), [label, setLabel] = useState(''), [type, setType] = useState<TipoRegistro>('pessoa')
  const [links, setLinks] = useState<Record<string, string>>({}), [field, setField] = useState(''), [position, setPosition] = useState('')
  const [scopeChoice, setScopeChoice] = useState('')
  const [category, setCategory] = useState('')
  const positions = value.registros_minuta || []
  const needed = type === 'papel' ? ['pessoa_a'] : type === 'relacao' ? ['pessoa_a', 'pessoa_b'] : type === 'negociacao' ? ['imovel'] : type === 'complemento' ? scopeChoice === 'pessoa' ? ['pessoa_a'] : scopeChoice === 'imovel' ? ['imovel'] : scopeChoice === 'pessoa_imovel' ? ['pessoa_a', 'imovel'] : [] : []
  const chosen = positions.find(p => p.chave === position)
  const fields = chosen ? [...schema.data?.schema[chosen.tipo] || [], ...(chosen.tipo === 'pessoa' ? value.campos_qualificacao || [] : [])].filter(f => f.chave !== 'estado_registro') : []
  return <Box component="details"><Box component="summary" sx={{ cursor: 'pointer' }}>Posições e marcadores da ficha detalhada</Box><Stack spacing={2} sx={{ pt: 2 }}>
    <Alert severity="info">Cada posição representa um registro escolhido pela escrevente para este atendimento. Para várias pessoas, configure posições separadas. Repetições usam uma lista explícita dessas posições. Blocos condicionais dependem de condições configuradas e dados confirmados; nenhuma condição é deduzida.</Alert>
    <TextField label="Identificador da posição (ex.: vendedor1)" value={key} disabled={disabled} onChange={e => setKey(e.target.value)} helperText="Use letras minúsculas, números e sublinhado; comece com letra." />
    <TextField label="Rótulo para a escrevente" value={label} disabled={disabled} onChange={e => setLabel(e.target.value)} />
    <TextField select label="Tipo de registro" value={type} disabled={disabled} onChange={e => { setType(e.target.value as TipoRegistro); setLinks({}); setScopeChoice('') }}>{['pessoa', 'papel', 'relacao', 'imovel', 'negociacao', 'ato', 'complemento'].map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}</TextField>
    {type === 'complemento' && <TextField select label="Âmbito deste complemento no modelo" value={scopeChoice} disabled={disabled} onChange={e => { setScopeChoice(e.target.value); setLinks({}) }}><MenuItem value="atendimento">Atendimento, sem pessoa ou imóvel específico</MenuItem><MenuItem value="pessoa">Pessoa específica</MenuItem><MenuItem value="imovel">Imóvel específico</MenuItem><MenuItem value="pessoa_imovel">Pessoa e imóvel específicos</MenuItem></TextField>}
    {type === 'complemento' && <TextField select label="Categoria esperada nesta posição" value={category} disabled={disabled} onChange={e => setCategory(e.target.value)}>{schema.data?.schema.complemento?.find(f => f.chave === 'categoria')?.opcoes?.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}</TextField>}
    {needed.map(link => <TextField key={link} select label={link === 'pessoa_a' ? 'Primeira pessoa deste papel ou relação' : link === 'pessoa_b' ? 'Segunda pessoa desta relação' : 'Imóvel desta negociação'} value={links[link] || ''} disabled={disabled} onChange={e => setLinks({ ...links, [link]: e.target.value })}>{positions.filter(p => p.tipo === (link === 'imovel' ? 'imovel' : 'pessoa')).map(p => <MenuItem key={p.chave} value={p.chave}>{p.rotulo} · {p.chave}</MenuItem>)}</TextField>)}
    <Button disabled={disabled || type === 'complemento' && (!scopeChoice || !category) || !/^[a-z][a-z0-9_]{0,39}$/.test(key) || !label.trim() || positions.some(p => p.chave === key) || needed.some(l => !links[l])} onClick={() => { onChange({ ...value, registros_minuta: [...positions, { chave: key, rotulo: label.trim(), tipo: type, vinculos: links, ...(type === 'complemento' ? { categoria: category } : {}) }] }); setKey(''); setLabel(''); setLinks({}); setCategory('') }}>Adicionar posição ao modelo</Button>
    {positions.map(p => <Stack key={p.chave} direction="row" gap={1}><Typography>{p.rotulo} · {p.chave} · {p.tipo}{p.categoria ? ` · ${p.categoria}` : ''}{Object.entries(p.vinculos).map(([k, v]) => ` · ${k}: ${v}`).join('')}</Typography><Button disabled={disabled} onClick={() => onChange({ ...value, registros_minuta: positions.filter(r => r.chave !== p.chave) })}>Remover posição</Button></Stack>)}
    {positions.length > 0 && <>
      <TextField select label="Posição do marcador" value={position} disabled={disabled} onChange={e => { setPosition(e.target.value); setField('') }}>{positions.map(p => <MenuItem key={p.chave} value={p.chave}>{p.rotulo}</MenuItem>)}</TextField>
      <TextField select label="Campo a preencher" value={field} disabled={disabled} onChange={e => setField(e.target.value)}>{[...new Map(fields.map(f => [f.chave, f])).values()].map(f => <MenuItem key={f.chave} value={f.chave}>{f.rotulo}</MenuItem>)}</TextField>
      {position && field && <><Typography>Marcador: {'{{'}{position}.{field}{'}}'}</Typography><Button disabled={disabled} onClick={() => onChange({ ...value, corpo: `${value.corpo}\n{{${position}.${field}}}` })}>Acrescentar marcador ao final do corpo</Button></>}
      <Typography variant="body2">Coloque os marcadores nos trechos adequados do padrão profissional. Substitua os marcadores de blocos antigos antes de salvar o modelo estruturado. A escrevente revisa e aprova o texto inteiro.</Typography>
    </>}
    {schema.isError && <Alert severity="error">Não foi possível carregar os campos. Reabra o modelo.</Alert>}
  </Stack></Box>
}
