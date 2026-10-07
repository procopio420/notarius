'use client'

import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'

interface DocumentFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  statusFilter: string
  onStatusChange: (value: string) => void
  tipoFilter: string
  onTipoChange: (value: string) => void
  processoFilter: string
  onProcessoChange: (value: string) => void
}

export function DocumentFilters({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  tipoFilter,
  onTipoChange,
  processoFilter,
  onProcessoChange
}: DocumentFiltersProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Search */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Buscar documentos..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Status Filter */}
        <Select value={statusFilter} onValueChange={onStatusChange}>
          <SelectTrigger>
            <SelectValue placeholder="Status OCR" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos os status</SelectItem>
            <SelectItem value="pendente">Pendente</SelectItem>
            <SelectItem value="processando">Processando</SelectItem>
            <SelectItem value="concluido">Concluído</SelectItem>
            <SelectItem value="erro">Erro</SelectItem>
          </SelectContent>
        </Select>

        {/* Tipo Filter */}
        <Select value={tipoFilter} onValueChange={onTipoChange}>
          <SelectTrigger>
            <SelectValue placeholder="Tipo de Documento" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos os tipos</SelectItem>
            <SelectItem value="identidade">Identidade</SelectItem>
            <SelectItem value="cpf">CPF</SelectItem>
            <SelectItem value="comprovante_residencia">Comprovante de Residência</SelectItem>
            <SelectItem value="contrato">Contrato</SelectItem>
            <SelectItem value="escritura">Escritura</SelectItem>
            <SelectItem value="testamento">Testamento</SelectItem>
            <SelectItem value="outro">Outro</SelectItem>
          </SelectContent>
        </Select>

        {/* Processo Filter */}
        <Select value={processoFilter} onValueChange={onProcessoChange}>
          <SelectTrigger>
            <SelectValue placeholder="Processo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos os processos</SelectItem>
            <SelectItem value="sem_processo">Sem processo</SelectItem>
            {/* This would be populated from a separate query for available processes */}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
