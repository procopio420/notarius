'use client'

import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TextField, Typography } from '@mui/material'
import { ArrowRight, ChevronDown, FileCheck2, FilePenLine, Settings2 } from 'lucide-react'
import { atendimentosApi, type MinutaPreparada, type TextoModelo } from '@/lib/atendimentos'
import { EditorMinuta } from './EditorMinuta'
import { BibliotecaModelos } from './BibliotecaModelos'
import { PosicoesModelo } from './PosicoesModelo'
import { BlocosModelo } from './BlocosModelo'
import { VinculacaoMinuta } from './VinculacaoMinuta'
import { RegrasRevisaoModelo } from './RegrasRevisaoModelo'
import { CamposQualificacaoModelo } from './CamposQualificacaoModelo'
import { useRascunhoSessao } from '@/lib/rascunhoSessao'
import { RevisaoPadraoPiloto } from './RevisaoPadraoPiloto'

interface ModeloLocal { modelo: TextoModelo; motivo: string; versao: number; referencia: string | null }
const modeloLocalValido = (v: unknown): v is ModeloLocal | null => v === null || !!v && typeof (v as ModeloLocal).modelo?.corpo === 'string' && typeof (v as ModeloLocal).motivo === 'string' && typeof (v as ModeloLocal).versao === 'number'


export function PreparacaoMinuta({ id, scope }: { id: string; scope: (string | undefined)[] }) {
  const modelLocal = useRascunhoSessao<ModeloLocal | null>(scope, 'modelo-minuta', null, modeloLocalValido)
  const cache = useQueryClient()
  const models = useQuery({ queryKey: ['modelo-atendimento', ...scope], queryFn: () => atendimentosApi.modelos(id) })
  const state = useQuery({ queryKey: ['minuta-atendimento', ...scope], queryFn: () => atendimentosApi.redacao(id) })
  const [showModel, setShowModel] = useState(false)
  const [draft, setDraft] = useState<TextoModelo>({ corpo: '', representacao: '', observacoes: '' })
  const [approved, setApproved] = useState(false)
  const [reason, setReason] = useState('')
  const [expectedVersion, setExpectedVersion] = useState(0)
  const [referenceId, setReferenceId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState<MinutaPreparada | null>(null)
  const saveModelLocal = modelLocal.save, modelReady = modelLocal.ready
  useEffect(() => {
    if (showModel && modelReady) saveModelLocal({ modelo: draft, motivo: reason, versao: expectedVersion, referencia: referenceId })
  }, [showModel, modelReady, saveModelLocal, draft, reason, expectedVersion, referenceId])
  const current = models.data?.versoes[0]

  function openModel() {
    const saved = modelLocal.value
    if (saved) { setDraft(saved.modelo); setReferenceId(saved.referencia); setExpectedVersion(saved.versao); setApproved(false); setReason(saved.motivo); setError(''); setShowModel(true); return }
    const reference = models.data?.referencia
    const data = current || reference?.modelo || models.data?.base
    if (!data) return
    setDraft({ corpo: data.corpo, representacao: data.representacao, observacoes: data.observacoes, registros_minuta: data.registros_minuta || [], campos_qualificacao: data.campos_qualificacao || [], campos_obrigatorios_ficha: data.campos_obrigatorios_ficha || [], dependencias_campos_ficha: data.dependencias_campos_ficha || [] })
    setReferenceId(current?.referencia_id || null)
    setExpectedVersion(current?.versao || 0); setApproved(false)
    setReason(!current && reference ? `Base da escritura enviada · ${reference.versao}` : '')
    setError(''); setShowModel(true)
  }
  function failure(err: unknown) {
    const data = (err as { response?: { data?: unknown } }).response?.data
    setError(Array.isArray(data) ? data.join(' ') : typeof data === 'object' && data && 'detail' in data ? String(data.detail) : 'Não foi possível confirmar a operação. Atualize antes de tentar novamente.')
  }
  async function saveModel() {
    setBusy(true); setError('')
    try {
      await atendimentosApi.salvarModelo(id, { ...draft, aprovado: approved, justificativa: reason.trim(), versao_esperada: expectedVersion, referencia_id: referenceId })
      await Promise.all(['modelo-atendimento', 'minuta-atendimento', 'conferencia-atendimento', 'ficha-atendimento', 'ficha-detalhada'].map(key => cache.invalidateQueries({ queryKey: [key] })))
      setShowModel(false)
      modelLocal.clear()
    } catch (err) { failure(err) } finally { setBusy(false) }
  }
  async function prepare() {
    if (!state.data) return
    setBusy(true); setError('')
    try {
      const result = await atendimentosApi.prepararMinuta(id, state.data.assinatura)
      cache.setQueryData(['minuta-atendimento', ...scope], result)
      if (result.versoes[0]) setPreview(result.versoes[0])
    } catch (err) { failure(err); void state.refetch() } finally { setBusy(false) }
  }
  return <Stack spacing={2.5}>
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 1.5, pb: 1 }}>
      {[
        { number: '01', title: 'Conferir o modelo', text: state.data?.modelo_aprovado ? 'Modelo aprovado neste atendimento' : 'Revise o padrão e os participantes', done: !!state.data?.modelo_aprovado },
        { number: '02', title: 'Preparar a minuta', text: state.data?.versoes.length ? `${state.data.versoes.length} ${state.data.versoes.length > 1 ? 'versões salvas' : 'versão salva'}` : 'Preencher com os dados conferidos', done: !!state.data?.versoes.length },
        { number: '03', title: 'Revisar e baixar', text: 'Conferência final antes do Word e PDF', done: !!state.data?.versoes[0]?.revisao_final?.texto_corresponde && !state.data?.versoes[0]?.desatualizada },
      ].map(step => <Box key={step.number} sx={{ p: { xs: 1.25, sm: 2 }, borderRadius: 2.5, bgcolor: step.done ? '#eff5ec' : '#f7f8f4', border: '1px solid #e3e8e1' }}>
        <Stack direction="row" alignItems="center" gap={1} sx={{ mb: .6 }}><Typography sx={{ color: '#496349', fontSize: 12, fontWeight: 750, letterSpacing: '.06em' }}>{step.number}</Typography>{step.done && <FileCheck2 size={14} color="#496349" />}</Stack>
        <Typography fontWeight={650} sx={{ fontSize: { xs: 12, sm: 14 }, color: '#203c35' }}>{step.title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' }, mt: .5, fontSize: 13 }}>{step.text}</Typography>
      </Box>)}
    </Box>
    <Stack direction={{ xs: 'column', sm: 'row' }} gap={2} justifyContent="space-between" alignItems={{ sm: 'center' }}>
      <Box><Typography component="h3" fontWeight={650} sx={{ color: '#203c35' }}>{state.data?.versoes[0] ? 'Seu texto está aqui' : 'Tudo começa com os dados conferidos'}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: .5 }}>{state.data?.versoes[0] ? 'Abra a versão salva para editar, revisar e baixar.' : 'O modelo e os participantes precisam ser revisados antes da preparação.'}</Typography></Box>
      <Stack direction="row" gap={1} flexWrap="wrap" sx={{ flexShrink: 0 }}>
        <Button variant={state.data?.versoes[0] ? 'outlined' : 'contained'} startIcon={<FilePenLine size={17} />} onClick={prepare} disabled={busy || !state.data?.pronto || state.isError}>{busy ? 'Preparando…' : state.data?.versoes[0] ? 'Preparar nova versão' : 'Preparar minuta'}</Button>
        {state.data?.versoes[0] && <Button variant="contained" endIcon={<ArrowRight size={17} />} onClick={() => setPreview(state.data!.versoes[0])}>Abrir minuta v{state.data.versoes[0].versao}</Button>}
      </Stack>
    </Stack>
    <Box sx={{ pt: 2, borderTop: '1px solid #e3e8e1' }}>
      <Typography variant="body2" sx={{ fontWeight: 600, color: '#51635a', mb: 1 }}>Modelo e participantes</Typography>
      <Stack direction="row" gap={1} flexWrap="wrap"><Button variant="outlined" size="small" startIcon={<Settings2 size={16} />} onClick={openModel} disabled={!models.data || busy}>Revisar modelo</Button><VinculacaoMinuta key={scope.join(':')} id={id} scope={scope} /></Stack>
    </Box>
    {modelLocal.value && <Alert severity="info">Há rascunho local do modelo. “Revisar modelo” retoma o texto, mantendo a versão de origem e sem recuperar aprovação.</Alert>}
    {modelLocal.aviso && <Alert severity="warning">{modelLocal.aviso}</Alert>}
    {models.isError || state.isError ? <Alert severity="error" action={<Button onClick={() => { void models.refetch(); void state.refetch() }}>Atualizar</Button>}>Não foi possível conferir o modelo e a minuta.</Alert> : models.isLoading || state.isLoading ? <Typography role="status">Consultando o modelo, as versões salvas e a revisão atual…</Typography> : <Typography variant="caption" color="text.secondary">{!state.data?.modelo_aprovado ? 'A escrevente precisa revisar e aprovar o modelo antes de preparar a minuta.' : state.data?.pendencias ? 'Modelo aprovado; falta resolver as pendências do atendimento.' : 'Modelo aprovado e verificações iniciais respondidas. A minuta ainda exigirá revisão.'}</Typography>}
    {state.data?.versoes[0]?.desatualizada && <Alert severity="warning">Os dados ou o modelo mudaram após a preparação. Confira as pendências e prepare uma nova versão.</Alert>}
    {state.data?.modelo_aprovado && !state.data.pronto && !state.data.pendencias && state.data.motivo_bloqueio && <Alert severity="warning">{state.data.motivo_bloqueio}</Alert>}
    {error && !showModel && <Alert severity="error">{error}</Alert>}
    <Dialog open={showModel} onClose={() => !busy && setShowModel(false)} fullWidth maxWidth="md"><DialogTitle>Modelo de compra e venda</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        {models.data?.referencia && <Box>
          <Button disabled={busy} onClick={() => {
            const reference = models.data!.referencia
            setDraft({ ...reference.modelo }); setReferenceId(null); setApproved(false)
            setReason(`Base da escritura enviada · ${reference.versao}`); setError('')
          }}>Carregar modelo de compra e venda</Button>
          <Typography variant="body2">{models.data.referencia.aviso}</Typography>
          <Typography variant="caption">Ao salvar, os campos desta estrutura entram nas perguntas da conversa. As versões anteriores são preservadas.</Typography>
        </Box>}
        <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer' }}>Outras estruturas de compra e venda</Typography>
          {models.data?.padrao_piloto && <RevisaoPadraoPiloto padrao={models.data.padrao_piloto} disabled={busy} onLoad={() => {
            const candidate = models.data!.padrao_piloto
            setDraft(candidate.modelo); setReferenceId(null); setApproved(false)
            setExpectedVersion(current?.versao || 0); setReason(candidate.modelo.justificativa); setError('')
          }} />}
          <Alert severity="warning">Incluem posições para abertura, declarações, tributos, documentos, consultas e encerramento. Não são requisitos jurídicos ou modelos homologados. Carregar só altera este rascunho; não cria registros nem confirma dados.</Alert>
          {models.data?.referencias_complementares?.map(ref => <Button key={ref.variante} disabled={busy} onClick={() => { setDraft(ref.modelo); setApproved(false); setReferenceId(null); setReason(''); setError('') }}>Carregar {ref.nome}</Button>)}
        </Box>
        <Accordion disableGutters elevation={0} sx={{ border: '1px solid #e3e8e1', borderRadius: '12px !important', '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ChevronDown size={18} />}><Typography fontWeight={600}>Biblioteca e outros modelos</Typography></AccordionSummary>
          <AccordionDetails><Stack spacing={2}>
        <BibliotecaModelos id={id} scope={scope} current={current}
          canPublish={JSON.stringify(draft.registros_minuta || []) === JSON.stringify(current?.registros_minuta || []) && JSON.stringify(draft.campos_obrigatorios_ficha || []) === JSON.stringify(current?.campos_obrigatorios_ficha || []) && JSON.stringify(draft.dependencias_campos_ficha || []) === JSON.stringify(current?.dependencias_campos_ficha || []) && !busy && !!current && draft.corpo === current.corpo && draft.representacao === current.representacao && draft.observacoes === current.observacoes && JSON.stringify(draft.campos_qualificacao || []) === JSON.stringify(current.campos_qualificacao || [])}
          onLoad={model => { setDraft({ corpo: model.corpo, representacao: model.representacao, observacoes: model.observacoes, registros_minuta: model.registros_minuta || [], campos_qualificacao: model.campos_qualificacao || [], campos_obrigatorios_ficha: model.campos_obrigatorios_ficha || [], dependencias_campos_ficha: model.dependencias_campos_ficha || [] }); setReferenceId(model.id); setApproved(false); setReason(''); setError('') }} />
        {referenceId && <Typography variant="caption">Texto baseado em um padrão da biblioteca. A aprovação deve ser feita para este atendimento.</Typography>}
        <Button disabled={busy || !models.data?.modelo_ficticio_estruturado} onClick={() => { setDraft(models.data!.modelo_ficticio_estruturado); setReferenceId(null); setApproved(false); setReason('DEMONSTRAÇÃO FICTÍCIA SEM HOMOLOGAÇÃO PROFISSIONAL') }}>Carregar modelo fictício com condições e repetições</Button>
        <Alert severity="warning">A redação e as regras profissionais dependem de homologação pela escrevente. O exemplo fictício serve somente para testes e não contém redação profissional aprovada.</Alert>
          </Stack></AccordionDetails>
        </Accordion>
        <Typography variant="body2">{draft.registros_minuta?.length ? 'Blocos condicionais e repetições só entram conforme configuração explícita e dados confirmados. Use as posições configuradas e os campos da ficha, por exemplo {{vendedor1.nome}}. Cada marcador será substituído pelo valor confirmado daquele registro. Texto fora de blocos condicionais é fixo e precisa de revisão profissional.' : 'Modelo antigo por blocos: {{vendedores}}, {{compradores}}, {{imovel}}, {{preco}}, {{pagamento}}. Para usar a ficha separada, configure posições e substitua os marcadores pelo padrão posição.campo.'}</Typography>
        {!draft.registros_minuta?.length && <Box component="details"><Typography component="summary" sx={{ cursor: 'pointer' }}>Campos disponíveis para o modelo antigo</Typography>
          {models.data?.marcadores.map(field => <Typography variant="body2" key={field.chave}>{`{{${field.chave}}}`} — {field.rotulo}</Typography>)}
        </Box>}
        <TextField label="Texto fixo e campos do modelo" multiline minRows={10} value={draft.corpo} onChange={e => { setDraft({ ...draft, corpo: e.target.value }); setApproved(false) }} disabled={busy} slotProps={{ htmlInput: { maxLength: 60000 } }} />
        <TextField label={draft.registros_minuta?.length ? 'Bloco adicional de representação' : 'Bloco condicional de representação'} multiline minRows={3} value={draft.representacao} onChange={e => { setDraft({ ...draft, representacao: e.target.value }); setApproved(false) }} disabled={busy} helperText={draft.registros_minuta?.length ? "Blocos condicionais exigem configuração explícita. Use marcadores de posição.campo; não copie fatos do exemplo." : "Só entra quando representação tiver informação confirmada. Use {{representacao}}."} slotProps={{ htmlInput: { maxLength: 10000 } }} />
        <TextField label={draft.registros_minuta?.length ? 'Bloco adicional de observações' : 'Bloco condicional de observações'} multiline minRows={3} value={draft.observacoes} onChange={e => { setDraft({ ...draft, observacoes: e.target.value }); setApproved(false) }} disabled={busy} helperText={draft.registros_minuta?.length ? "Blocos condicionais exigem configuração explícita. Use marcadores de posição.campo." : "Só entra quando houver observações confirmadas. Use {{observacoes}}."} slotProps={{ htmlInput: { maxLength: 10000 } }} />
        <TextField label="Motivo ou descrição da revisão do modelo" multiline minRows={2} value={reason} onChange={e => setReason(e.target.value)} required disabled={busy} slotProps={{ htmlInput: { maxLength: 2000 } }} />
        <Accordion disableGutters elevation={0} sx={{ border: '1px solid #e3e8e1', borderRadius: '12px !important', '&:before': { display: 'none' } }}>
          <AccordionSummary expandIcon={<ChevronDown size={18} />}><Box><Typography fontWeight={600}>Campos, participantes e regras do modelo</Typography><Typography variant="body2" color="text.secondary">Confira esta configuração antes de aprovar o padrão.</Typography></Box></AccordionSummary>
          <AccordionDetails><Stack spacing={2}>
        <BlocosModelo value={draft} disabled={busy} onChange={v => { setDraft(v); setApproved(false) }} />
        <PosicoesModelo key={`posicoes:${scope.join(':')}`} id={id} scope={scope} value={draft} disabled={busy} onChange={v => { setDraft(v); setApproved(false) }} />
        <RegrasRevisaoModelo key={`regras:${scope.join(':')}`} id={id} scope={scope} value={draft} disabled={busy} onChange={v => { setDraft(v); setApproved(false) }} />
        <CamposQualificacaoModelo value={draft.campos_qualificacao || []} disabled={busy} onChange={fields => { setDraft({ ...draft, campos_qualificacao: fields }); setApproved(false) }} />
          </Stack></AccordionDetails>
        </Accordion>
        <FormControlLabel control={<Checkbox checked={approved} onChange={e => setApproved(e.target.checked)} disabled={busy} />} label={draft.registros_minuta?.length ? 'Revisei integralmente o padrão, suas posições e vínculos. Retirei os fatos do exemplo: pagamento, consultas e assinaturas exigem dados confirmados com fonte. Aprovo esta versão do modelo para este atendimento.' : 'Revisei o texto e aprovo esta versão do modelo para este atendimento.'} />
        <Typography variant="caption">Sem aprovação, o modelo fica salvo em rascunho e bloqueia a preparação. Cada alteração cria uma versão nova.</Typography>
        {models.data?.versoes.length ? <Box><Typography fontWeight={600}>Versões anteriores</Typography>{models.data.versoes.map(m => <Button key={m.id} disabled={busy} onClick={() => { setDraft({ corpo: m.corpo, representacao: m.representacao, observacoes: m.observacoes, registros_minuta: m.registros_minuta || [], campos_qualificacao: m.campos_qualificacao || [], campos_obrigatorios_ficha: m.campos_obrigatorios_ficha || [], dependencias_campos_ficha: m.dependencias_campos_ficha || [] }); setReferenceId(m.referencia_id || null); setApproved(false) }}>Carregar v{m.versao} · {m.aprovado ? 'aprovada' : 'rascunho'}</Button>)}</Box> : null}
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => { setShowModel(false); setApproved(false); modelLocal.clear() }}>Descartar só o rascunho local</Button><Button disabled={busy} onClick={() => setShowModel(false)}>Voltar e manter rascunho</Button><Button variant="contained" onClick={saveModel} disabled={busy || !reason.trim() || !draft.corpo.trim()}>{busy ? 'Salvando…' : approved ? 'Salvar modelo aprovado' : 'Salvar rascunho do modelo'}</Button></DialogActions>
    </Dialog>

    {preview && <EditorMinuta key={scope.join(":")} id={id} scope={scope} inicial={preview} onClose={() => setPreview(null)} />}
  </Stack>
}
