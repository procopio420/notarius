'use client'
import { useState } from 'react'
import { Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material'
import type { CampoQualificacao } from '@/lib/atendimentos'

export function CamposQualificacaoModelo({ value, onChange, disabled }: { value: CampoQualificacao[]; onChange: (value: CampoQualificacao[]) => void; disabled: boolean }) {
  const [label, setLabel] = useState('')
  const [group, setGroup] = useState<CampoQualificacao['grupo']>('Qualificação')
  const key = `extra_${label.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '_')}`.slice(0, 40)
  return <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer', py: 1 }}>Campos adicionais de qualificação das pessoas</Typography>
    <Stack spacing={1}>
      <Typography variant="body2">Nome, CPF, documento, órgão emissor e campos básicos de qualificação já estão disponíveis na ficha. Acrescente aqui os campos particulares deste modelo. Esta lista não define exigências jurídicas.</Typography>
      {value.map(field => <Box key={field.chave}><Typography>{field.rotulo} · {field.grupo}</Typography><Button disabled={disabled} onClick={() => onChange(value.filter(f => f.chave !== field.chave))}>Retirar do modelo</Button></Box>)}
      <TextField label="Nome do campo adicional" value={label} disabled={disabled} onChange={e => setLabel(e.target.value)} slotProps={{ htmlInput: { maxLength: 100 } }} />
      <TextField select label="Grupo" value={group} disabled={disabled} onChange={e => setGroup(e.target.value as CampoQualificacao['grupo'])}>{['Identificação', 'Qualificação', 'Contato'].map(g => <MenuItem key={g} value={g}>{g}</MenuItem>)}</TextField>
      <Button disabled={disabled || !label.trim() || value.length >= 25 || value.some(f => f.chave === key)} onClick={() => { onChange([...value, { chave: key, rotulo: label.trim(), grupo: group }]); setLabel('') }}>Adicionar campo ao rascunho</Button>
      <Typography variant="caption">Salvar cria uma versão do modelo. Retirar um campo não apaga os dados e o histórico já registrados.</Typography>
    </Stack>
  </Box>
}
