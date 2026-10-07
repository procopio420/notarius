/**
 * Basic tests for RegisterCartorioSelect component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { RegisterCartorioSelect } from '../RegisterCartorioSelect'

// Mock fetch
global.fetch = vi.fn()

describe('RegisterCartorioSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders search input and UF filter', () => {
    const onSelect = vi.fn()
    const onRequestNew = vi.fn()
    render(<RegisterCartorioSelect onSelect={onSelect} onRequestNew={onRequestNew} />)

    expect(screen.getByLabelText(/buscar cartório/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/estado/i)).toBeInTheDocument()
  })

  it('shows empty state when no search term', () => {
    const onSelect = vi.fn()
    const onRequestNew = vi.fn()
    render(<RegisterCartorioSelect onSelect={onSelect} onRequestNew={onRequestNew} />)

    expect(screen.getByText(/digite o nome do cartório para buscar/i)).toBeInTheDocument()
  })
})

