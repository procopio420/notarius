import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Tenant {
  id: string
  nome: string
  uf: string
}

export interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  is_staff: boolean
  is_superuser: boolean
  tenants: Tenant[]
  default_tenant: Tenant | null
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface RegisterData {
  email: string
  first_name: string
  last_name: string
  password: string
  cartorio_id?: string | null
  cpf_hash?: string
  phone_hash?: string
}

interface AuthActions {
  setUser: (user: User) => void
  setToken: (token: string) => void
  login: (user: User, token: string) => void
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  setLoading: (loading: boolean) => void
  initializeAuth: () => void
}

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set) => ({
      // State
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      login: (user, token) => set({ 
        user, 
        token, 
        isAuthenticated: true,
        isLoading: false 
      }),
      register: async (data) => {
        set({ isLoading: true })
        try {
          // Generate username from email (first part before @)
          const username = data.email.split('@')[0]
          
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/register/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username,
              email: data.email,
              first_name: data.first_name,
              last_name: data.last_name,
              password: data.password,
              confirm_password: data.password, // Backend expects this
              cartorio_id: data.cartorio_id,
              cpf_hash: data.cpf_hash,
              phone_hash: data.phone_hash,
            }),
          })
          
          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || errorData.message || 'Erro ao criar conta')
          }
          
          const result = await response.json()
          
          // Handle response with status and redirect
          set({ 
            user: result.user, 
            token: result.token, 
            isAuthenticated: true,
            isLoading: false 
          })
          
          // Return result for redirect handling
          return result
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },
      logout: () => set({ 
        user: null, 
        token: null, 
        isAuthenticated: false,
        isLoading: false 
      }),
      setLoading: (isLoading) => set({ isLoading }),
      initializeAuth: () => {
        // This will be called on app startup to check if user is already authenticated
        set({ isLoading: false })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)

