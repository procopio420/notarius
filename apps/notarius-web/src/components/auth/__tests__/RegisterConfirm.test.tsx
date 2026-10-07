/**
 * Basic tests for RegisterConfirm component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RegisterConfirm } from '../RegisterConfirm'
import { TenantSearchResult } from '@/types'

const mockAccountData = {
  email: 'test@example.com',
  first_name: 'John',
  last_name: 'Doe',
  password: 'password123',
}

const mockCartorio: TenantSearchResult = {
  id: '123',
  nome: 'Cartório Central',
  municipio: 'São Paulo',
  uf: 'SP',
  tipo: '1º Ofício',
}

describe('RegisterConfirm', () => {
  it('renders account summary', () => {
    const onSubmit = vi.fn()
    render(
      <RegisterConfirm
        accountData={mockAccountData}
        selectedCartorio={mockCartorio}
        cartorioRequested={false}
        onSubmit={onSubmit}
      />
    )

    expect(screen.getByText(/john doe/i)).toBeInTheDocument()
    expect(screen.getByText(/test@example.com/i)).toBeInTheDocument()
  })

  it('renders selected cartorio information', () => {
    const onSubmit = vi.fn()
    render(
      <RegisterConfirm
        accountData={mockAccountData}
        selectedCartorio={mockCartorio}
        cartorioRequested={false}
        onSubmit={onSubmit}
      />
    )

    expect(screen.getByText(/cartório central/i)).toBeInTheDocument()
    expect(screen.getByText(/são paulo/i)).toBeInTheDocument()
    expect(screen.getByText(/sp/i)).toBeInTheDocument()
  })

  it('shows request message when cartorio requested', () => {
    const onSubmit = vi.fn()
    render(
      <RegisterConfirm
        accountData={mockAccountData}
        selectedCartorio={null}
        cartorioRequested={true}
        onSubmit={onSubmit}
      />
    )

    expect(screen.getByText(/solicitação de inclusão/i)).toBeInTheDocument()
  })
})

