/**
 * Basic tests for RegisterAccountForm component
 * These tests verify the component structure and basic functionality
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { RegisterAccountForm } from '../RegisterAccountForm'

describe('RegisterAccountForm', () => {
  it('renders form fields correctly', () => {
    const onSubmit = vi.fn()
    render(<RegisterAccountForm onSubmit={onSubmit} />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/nome/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/sobrenome/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
  })

  it('shows validation errors for required fields', async () => {
    const onSubmit = vi.fn()
    render(<RegisterAccountForm onSubmit={onSubmit} />)

    const submitButton = screen.getByRole('button', { name: /continuar/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).not.toHaveBeenCalled()
    })
  })

  it('calls onSubmit with form data when valid', async () => {
    const onSubmit = vi.fn()
    render(<RegisterAccountForm onSubmit={onSubmit} />)

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/nome/i), {
      target: { value: 'John' },
    })
    fireEvent.change(screen.getByLabelText(/sobrenome/i), {
      target: { value: 'Doe' },
    })
    fireEvent.change(screen.getByLabelText(/senha/i), {
      target: { value: 'password123' },
    })

    const submitButton = screen.getByRole('button', { name: /continuar/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        password: 'password123',
        cpf: undefined,
        phone: undefined,
      })
    })
  })

  it('toggles password visibility', () => {
    const onSubmit = vi.fn()
    render(<RegisterAccountForm onSubmit={onSubmit} />)

    const passwordInput = screen.getByLabelText(/senha/i)
    expect(passwordInput).toHaveAttribute('type', 'password')

    const toggleButton = screen.getByLabelText(/mostrar senha/i)
    fireEvent.click(toggleButton)

    expect(passwordInput).toHaveAttribute('type', 'text')
  })
})

