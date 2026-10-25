'use client'
import { useCallback, useEffect, useRef, useState } from 'react'

export function useRascunhoSessao<T>(scope: (string | undefined)[], slot: string, initial: T, validar: (value: unknown) => value is T) {
  const key = scope.length > 0 && scope.every(v => !!v) ? `notarius:rascunho:v1:${JSON.stringify(scope)}:${slot}` : null
  const [state, setState] = useState<{ key: string | null; value: T; exists: boolean }>({ key: null, value: initial, exists: false })
  const [failure, setFailure] = useState<string | null>(null)
  const latest = useRef({ key, value: initial })
  const validator = useRef(validar); validator.current = validar
  const initialRef = useRef(initial)
  const value = state.key === key ? state.value : initialRef.current
  latest.current = { key, value }
  useEffect(() => {
    if (!key) return
    try {
      const raw = sessionStorage.getItem(key)
      if (raw && raw.length > 400000) throw new Error('limite')
      const parsed: unknown = raw ? JSON.parse(raw) : null
      if (raw && !validator.current(parsed)) throw new Error('formato')
      const restored = raw ? parsed as T : initialRef.current
      latest.current = { key, value: restored }
      setState({ key, value: restored, exists: !!raw }); setFailure(null)
    } catch { setFailure(key); setState({ key, value: initialRef.current, exists: false }) }
  }, [key])
  const save = useCallback((next: T | ((old: T) => T)) => {
    if (!key) return
    const current = latest.current.key === key ? latest.current.value : initialRef.current
    const updated = typeof next === 'function' ? (next as (old: T) => T)(current) : next
    latest.current = { key, value: updated }
    setState({ key, value: updated, exists: true })
    try {
      const serialized = JSON.stringify(updated)
      if (serialized.length > 400000 || !validator.current(updated)) throw new Error('limite')
      sessionStorage.setItem(key, serialized); setFailure(null)
    } catch { setFailure(key) }
  }, [key])
  const clear = useCallback(() => {
    if (!key) return
    latest.current = { key, value: initialRef.current }
    setState({ key, value: initialRef.current, exists: false })
    try { sessionStorage.removeItem(key); setFailure(null) } catch { setFailure(key) }
  }, [key])
  return { value, save, clear, exists: state.key === key && state.exists, ready: state.key === key && !!key,
    aviso: failure === key && key ? 'Não foi possível guardar ou recuperar o rascunho nesta aba. O texto atual fica apenas na memória; copie-o antes de recarregar.' : '' }
}

export interface RascunhoMensagem { texto: string; client_id: string; texto_tentado: string }
export function mensagemValida(value: unknown): value is RascunhoMensagem {
  const v = value as RascunhoMensagem | null
  return !!v && typeof v.texto === 'string' && v.texto.length <= 10000 && typeof v.client_id === 'string' && typeof v.texto_tentado === 'string'
}
