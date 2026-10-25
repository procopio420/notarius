'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { fichaDetalhadaApi, type TipoRegistro } from '@/lib/fichaDetalhada'
import type { TextoModelo } from '@/lib/atendimentos'

export function RegrasRevisaoModelo({ id, scope, value, disabled, onChange }: { id: string; scope: (string | undefined)[]; value: TextoModelo; disabled: boolean; onChange: (v: TextoModelo) => void }) {
  const schema = useQuery({ queryKey: ['schema-regras', id, ...scope], queryFn: () => fichaDetalhadaApi.get(id) })
  const [tipo, setTipo] = useState<TipoRegistro>('pessoa'), [campo, setCampo] = useState(''), [dep, setDep] = useState('')
  const currentFields = schema.data?.schema[tipo] || []
  const fields = [...currentFields, ...(tipo === 'pessoa' ? (value.campos_qualificacao || []).filter(f => !currentFields.some(c => c.chave === f.chave)) : [])]
  return <Box component="details"><Box component="summary" sx={{ cursor: 'pointer' }}>Requisitos e dependências para homologação profissional</Box><Stack spacing={2} sx={{ pt: 2 }}>
    <Alert severity="warning">Configuração do modelo a homologar pela escrevente. Não são exigências jurídicas definidas pelo sistema. Salvar estas alterações exige nova aprovação do modelo. Alterações em dados dependentes exigirão nova conferência.</Alert>
    <TextField select label="Tipo de registro" value={schema.data ? tipo : ''} disabled={disabled || !schema.data} onChange={e => { setTipo(e.target.value as TipoRegistro); setCampo(''); setDep('') }}>{Object.keys(schema.data?.schema || {}).map(t => <MenuItem key={t} value={t}>{t}</MenuItem>)}</TextField>
    <TextField select label="Campo que será conferido" value={campo} disabled={disabled} onChange={e => setCampo(e.target.value)}>{fields.filter(f => f.chave !== 'estado_registro').map(f => <MenuItem key={f.chave} value={f.chave}>{f.rotulo}</MenuItem>)}</TextField>
    <Button disabled={disabled || !campo || (value.campos_obrigatorios_ficha || []).some(r => r.tipo === tipo && r.chave === campo)} onClick={() => onChange({ ...value, campos_obrigatorios_ficha: [...value.campos_obrigatorios_ficha || [], { tipo, chave: campo }] })}>Exigir este campo neste modelo</Button>
    <TextField select label="Depende também de qual campo deste registro?" value={dep} disabled={disabled} onChange={e => setDep(e.target.value)}>{fields.filter(f => f.chave !== campo && f.chave !== 'estado_registro').map(f => <MenuItem key={f.chave} value={f.chave}>{f.rotulo}</MenuItem>)}</TextField>
    <Button disabled={disabled || !campo || !dep} onClick={() => { const rules = value.dependencias_campos_ficha || []; const previous = rules.find(r => r.tipo === tipo && r.chave === campo); onChange({ ...value, dependencias_campos_ficha: [...rules.filter(r => r !== previous), { tipo, chave: campo, depende_de: [...new Set([...(previous?.depende_de || []), dep])] }] }) }}>Registrar dependência para revisão</Button>
    {(value.campos_obrigatorios_ficha || []).map((r, i) => <Stack key={`${r.tipo}:${r.chave}`} direction="row"><Typography>Exigido pelo modelo: {r.tipo} · {r.chave}</Typography><Button disabled={disabled} onClick={() => onChange({ ...value, campos_obrigatorios_ficha: value.campos_obrigatorios_ficha!.filter((_, n) => n !== i) })}>Remover</Button></Stack>)}
    {(value.dependencias_campos_ficha || []).map((r, i) => <Stack key={`${r.tipo}:${r.chave}`} direction="row"><Typography>{r.tipo} · {r.chave} depende de: {r.depende_de.join(', ')}</Typography><Button disabled={disabled} onClick={() => onChange({ ...value, dependencias_campos_ficha: value.dependencias_campos_ficha!.filter((_, n) => n !== i) })}>Remover</Button></Stack>)}
    {schema.isError && <Alert severity="error">Não foi possível carregar os campos. Reabra o modelo.</Alert>}
  </Stack></Box>
}
