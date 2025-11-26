import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../api/client'

interface User {
  id: string
  email: string
  fullName: string
  role: string
  tier: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: any) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        const response = await api.post('/auth/login', { email, password })
        const { access_token } = response.data

        // Store token
        localStorage.setItem('token', access_token)

        // Fetch user data
        const userResponse = await api.get('/auth/me', {
          headers: { Authorization: `Bearer ${access_token}` },
        })

        set({
          token: access_token,
          user: userResponse.data,
          isAuthenticated: true,
        })
      },

      register: async (data: any) => {
        await api.post('/auth/register', {
          email: data.email,
          password: data.password,
          full_name: data.fullName,
          organization_name: data.organizationName,
        })

        // Auto-login after registration
        await useAuthStore.getState().login(data.email, data.password)
      },

      logout: () => {
        localStorage.removeItem('token')
        set({ user: null, token: null, isAuthenticated: false })
      },

      setUser: (user: User) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
