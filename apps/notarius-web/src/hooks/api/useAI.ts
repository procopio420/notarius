import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/queryClient'
import { useAuthStore } from '@/store/slices/authSlice'

// Types
interface AnalyzeCommandRequest {
  command: string
}

interface AnalyzeCommandResponse {
  parsed_intent: {
    document_type: string
    parties: Array<{
      name: string
      role: string
      cpf?: string
      email?: string
    }>
    metadata: {
      validity_days?: number
      location?: string
      special_conditions?: string[]
    }
    confidence_score: number
  }
  suggested_clauses: Array<{
    id: string
    nome: string
    texto: string
    categoria: string
  }>
}

interface GenerateDocumentRequest {
  original_command: string
  parsed_intent: {
    document_type: string
    parties: Array<{
      name: string
      role: string
      cpf?: string
      email?: string
    }>
    metadata: {
      validity_days?: number
      location?: string
      special_conditions?: string[]
    }
    confidence_score: number
  }
  selected_clauses?: string[]
}

interface GenerateDocumentResponse {
  minuta: {
    id: string
    versao: number
    corpo_md: string
    variaveis_json: Record<string, unknown>
  }
  processo: {
    id: string
    tipo_ato: string
    status: string
  }
  ai_generation: {
    id: string
    confidence_score: number
    generation_time_ms: number
  }
}

// interface SuggestClausesRequest {
//   document_type: string
//   context?: string
// }

interface Clause {
  id: string
  nome: string
  texto: string
  categoria: string
  frequencia_uso: number
}

// Analyze command mutation
export const useAnalyzeCommand = () => {
  const { user, isAuthenticated } = useAuthStore()
  
  return useMutation({
    mutationKey: ['ai', 'analyzeCommand'],
    mutationFn: async (data: AnalyzeCommandRequest): Promise<AnalyzeCommandResponse> => {
      console.log('Sending command to backend:', JSON.stringify(data))
      try {
        if (!isAuthenticated || !user) {
          throw new Error('Please login to use AI features')
        }
        
        // For now, use a default tenant ID - in a real app this would come from user context
        const tenantId = localStorage.getItem('tenant_id') || '5c3c87a5-a3db-437d-ab0f-7e5670b1dbb9'
        
        // Use the Intent Engine microservice directly for command analysis
        const response = await api.post('http://localhost:8003/api/v1/parse-intent', {
          intent: data.command,
          processo_id: null, // Will be created later
          tenant_id: tenantId,
          user_id: String(user.id), // Convert to string as required by intent engine API
        })
        
        // Transform the response to match expected format
        const intentData = response.data.parsed_intent
        
        // Handle entities - can be object or legacy format
        let parties: Array<{ name: string; role: string; cpf?: string; email?: string }> = []
        
        // List of known non-party fields that should be excluded
        const nonPartyFields = new Set([
          'imovel', 'objeto', 'prazo', 'location', 'validity_days', 'validade',
          'validity', 'duration', 'tempo', 'periodo', 'data', 'date',
          'local', 'endereco', 'address', 'cidade', 'city', 'estado', 'state',
          'uf', 'valor', 'value', 'preco', 'price', 'tipo', 'type'
        ])
        
        // Valid party roles (roles that represent people/entities)
        const validPartyRoles = new Set([
          'outorgante', 'outorgado', 'grantor', 'grantee', 'parte', 'party',
          'autor', 'reclamante', 'requerente', 'requerido', 'reclamado',
          'testemunha', 'witness', 'interessado', 'interested', 'procurador',
          'procurado', 'mandante', 'mandatario'
        ])
        
        if (intentData.entities && typeof intentData.entities === 'object') {
          // New format: entities is an object with role keys and party objects as values
          // e.g., { outorgante: { nome: "João Silva", cpf: "123.456.789-00" }, outorgado: { nome: "Maria Souza", cpf: "987.654.321-00" } }
          Object.entries(intentData.entities).forEach(([role, entityData]) => {
            // Skip non-party fields (metadata fields)
            if (nonPartyFields.has(role.toLowerCase())) {
              return
            }
            
            // Only include if it's a valid party role, or if it's an object with a 'nome' field
            const isPartyRole = validPartyRoles.has(role.toLowerCase())
            
            // Handle both object format (new) and string format (legacy)
            if (typeof entityData === 'object' && entityData !== null) {
              // New format: entity is an object with nome, cpf, email, etc.
              const partyName = (entityData as any).nome || (entityData as any).name || ''
              
              // Only include if it has a name AND (it's a valid party role OR has cpf/email indicating it's a person)
              const hasPersonFields = !!(partyName && ((entityData as any).cpf || (entityData as any).email || isPartyRole))
              
              if (hasPersonFields) {
                parties.push({
                  name: String(partyName),
                  role: role,
                  cpf: (entityData as any).cpf || undefined,
                  email: (entityData as any).email || undefined
                })
              }
            } else if (typeof entityData === 'string' && entityData.trim() && isPartyRole) {
              // Legacy format: entity is a string (the name) - only if it's a valid party role
              parties.push({
                name: entityData,
                role: role,
                cpf: intentData.pii_fields?.includes('cpf') ? 'detected' : undefined
              })
            }
          })
        }
        
        // Fallback to empty array if no parties found
        if (parties.length === 0) {
          // Try legacy format as fallback
          if (intentData.entities?.outorgante) {
            const outorgante = typeof intentData.entities.outorgante === 'string' 
              ? intentData.entities.outorgante 
              : (intentData.entities.outorgante as any)?.nome || ''
            if (outorgante) {
              parties.push({
                name: String(outorgante),
                role: 'outorgante',
                cpf: (intentData.entities.outorgante as any)?.cpf || undefined
              })
            }
          }
          if (intentData.entities?.outorgado) {
            const outorgado = typeof intentData.entities.outorgado === 'string'
              ? intentData.entities.outorgado
              : (intentData.entities.outorgado as any)?.nome || ''
            if (outorgado) {
              parties.push({
                name: String(outorgado),
                role: 'outorgado',
                cpf: (intentData.entities.outorgado as any)?.cpf || undefined
              })
            }
          }
        }
        
        return {
          parsed_intent: {
            document_type: intentData.document_type || 'procuracao',
            parties: parties,
            metadata: {
              location: intentData.entities?.imovel || intentData.entities?.location || intentData.metadata?.location,
              validity_days: intentData.entities?.prazo || intentData.entities?.validity_days || intentData.metadata?.validity_days,
            },
            confidence_score: intentData.confidence || 0
          },
          suggested_clauses: intentData.suggestions?.map((suggestion: string, index: number) => ({
            id: `clause-${index}`,
            nome: suggestion,
            texto: suggestion,
            categoria: 'sugestão'
          })) || []
        }
      } catch (error: unknown) {
        console.error('Command analysis failed:', error)
        // Extract error message properly
        const errorMessage = (error as any)?.response?.data?.detail || (error as Error)?.message || 'Erro ao analisar o comando'
        throw new Error(errorMessage)
      }
    },
    onError: (error: unknown) => {
      console.error('Command analysis failed:', error)
    },
  })
}

// Generate document mutation
export const useGenerateDocument = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationKey: ['ai', 'generateDocument'],
    mutationFn: async (data: GenerateDocumentRequest): Promise<GenerateDocumentResponse> => {
      // 1. Create processo first
      const processoResponse = await api.post('/api/v1/processos/', {
        tipo_ato: data.parsed_intent.document_type,
      })
      
      // Store for later use
      const processoId = processoResponse.data.id
      
      // 2. Generate minuta
      const minutaResponse = await api.post('/api/v1/ai/generate-minuta/', {
        intent: data.original_command,
        processo_id: processoId,
      })
      
      return {
        minuta: minutaResponse.data,
        processo: processoResponse.data,
        ai_generation: {
          id: minutaResponse.data.id,
          confidence_score: minutaResponse.data.grounding_confidence || 0,
          generation_time_ms: 0,
        }
      }
    },
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.processos.list() })
      queryClient.invalidateQueries({ queryKey: queryKeys.minutas.list() })
    },
    onError: (error: unknown) => {
      console.error('Document generation failed:', error)
    },
  })
}

// Suggest clauses query
export const useSuggestClauses = (documentType: string, context?: string) => {
  return useQuery({
    queryKey: [...queryKeys.ai.suggestClauses(), documentType, context],
    queryFn: async (): Promise<Clause[]> => {
      // For now, return empty array since this endpoint doesn't exist yet
      // TODO: Implement clause suggestion endpoint (not critical for MVP)
      return []
    },
    enabled: !!documentType,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Get clause library
export const useClauseLibrary = () => {
  return useQuery({
    queryKey: ['clause-library'],
    queryFn: async (): Promise<Clause[]> => {
      // For now, return empty array since this endpoint doesn't exist yet
      // TODO: Implement clause library endpoint (not critical for MVP)
      return []
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}
