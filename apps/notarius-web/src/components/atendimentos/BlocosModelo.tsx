'use client'
import { useState } from 'react'
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material'
import type { TextoModelo } from '@/lib/atendimentos'

export function BlocosModelo({ value, disabled, onChange }: { value: TextoModelo; disabled: boolean; onChange: (v: TextoModelo) => void }) {
  const [kind, setKind] = useState('se'), [key, setKey] = useState(''), [position, setPosition] = useState('')
  const [field, setField] = useState(''), [allowed, setAllowed] = useState(''), [included, setIncluded] = useState('')
  const [positions, setPositions] = useState<string[]>([]), [text, setText] = useState('')
  const list = value.registros_minuta || []
  const selected = list.filter(p => positions.includes(p.chave))
  const lines = (s: string) => s.split('\n').map(v => v.trim()).filter(Boolean)
  const validCondition = !!position && /^[a-z][a-z0-9_]{0,39}$/.test(field) && lines(allowed).length > 0 && lines(included).length > 0 && lines(included).every(v => lines(allowed).includes(v))
  function add() {
    const header = kind === 'se' ? `se ${key} ${JSON.stringify({ campo: `${position}.${field}`, permitidos: lines(allowed), incluir: lines(included) })}` : `repetir ${key} ${positions.join(',')}`
    onChange({ ...value, corpo: `${value.corpo}\n{% ${header} %}${text}{% fim %}` })
    setKey(''); setText(''); setPositions([]); setAllowed(''); setIncluded('')
  }
  return <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer' }}>Blocos condicionais e repetições explícitas</Typography><Stack spacing={2} sx={{ pt: 2 }}>
    <Alert severity="info">Configure somente texto fornecido ou aprovado pela escrevente. Condição sem dado confirmado ou fora das alternativas previstas interrompe a minuta. Não há redação livre da IA, cláusula automática nem dedução de participantes.</Alert>
    <Typography variant="body2">Texto fora desses blocos pertence ao padrão fixo. Cada bloco tem identificador único. Nesta versão, todos os campos citados no modelo devem estar confirmados, inclusive nos blocos omitidos; não existem participantes opcionais ou blocos aninhados.</Typography>
    <TextField select label="Como incluir este trecho?" value={kind} disabled={disabled} onChange={e => setKind(e.target.value)}><MenuItem value="se">Condição confirmada de um campo</MenuItem><MenuItem value="repetir">Repetir para posições escolhidas</MenuItem></TextField>
    <TextField label="Identificador do bloco" value={key} disabled={disabled} onChange={e => setKey(e.target.value)} helperText="Exemplo: previsao. Letras minúsculas, números e sublinhado." />
    {kind === 'se' ? <>
      <TextField select label="Posição cujo dado controla a inclusão" value={position} disabled={disabled} onChange={e => setPosition(e.target.value)}>{list.map(p => <MenuItem key={p.chave} value={p.chave}>{p.rotulo} · {p.chave}</MenuItem>)}</TextField>
      <TextField label="Campo da condição" value={field} disabled={disabled} onChange={e => setField(e.target.value)} helperText="Use a chave configurada na ficha, por exemplo situacao_pagamento ou tipo_papel. O servidor confere a referência." />
      <TextField label="Valores previstos no cenário (um por linha)" multiline minRows={2} value={allowed} disabled={disabled} onChange={e => setAllowed(e.target.value)} />
      <TextField label="Incluir o texto para quais desses valores? (um por linha)" multiline minRows={2} value={included} disabled={disabled} onChange={e => setIncluded(e.target.value)} />
      <Typography variant="caption">Comparação literal e exata. Outro valor, falta de confirmação ou fonte desatualizada interrompe a preparação para decisão da escrevente. Incerteza não vale como alternativa aprovada.</Typography>
    </> : <>
      <TextField select label="Posições na ordem desejada" value="" disabled={disabled} onChange={e => setPositions(old => [...old, e.target.value])}>{list.filter(p => !positions.includes(p.chave) && (!selected.length || p.tipo === selected[0].tipo)).map(p => <MenuItem key={p.chave} value={p.chave}>{p.rotulo} · {p.chave}</MenuItem>)}</TextField>
      {positions.map((p,i) => <Stack direction="row" gap={1} key={p}><Typography>{i+1}. {list.find(v => v.chave === p)?.rotulo || p}</Typography><Button disabled={disabled} onClick={() => setPositions(old => old.filter(v => v !== p))}>Retirar desta repetição</Button></Stack>)}
      <Typography variant="caption">Use {'{{item.nome}}'} ou outro campo do tipo escolhido no texto. Cada item usa o próprio registro e fonte. Não há busca de pessoas por nome nem agrupamento automático por papel.</Typography>
    </>}
    <TextField label="Texto do bloco fornecido para revisão" multiline minRows={3} value={text} disabled={disabled} onChange={e => setText(e.target.value)} helperText="Não preencha com dados do exemplo nem acontecimentos presumidos. Use marcadores para os dados do caso." />
    <Button disabled={disabled || !/^[a-z][a-z0-9_]{0,39}$/.test(key) || !text.trim() || !list.length || (kind === 'se' ? !validCondition : !positions.length)} onClick={add}>Acrescentar bloco ao modelo em revisão</Button>
    <Typography variant="caption">A ação altera apenas o rascunho. Salvar cria versão do modelo, exige justificativa e nova aprovação expressa. O servidor valida os blocos e seus limites antes de aceitar.</Typography>
  </Stack></Box>
}
