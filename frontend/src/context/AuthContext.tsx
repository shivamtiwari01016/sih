import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, loginRequest } from '../lib/api'

export interface AuthUser {
  id: string
  full_name: string
  email: string
  role: string
  bureau_id: string | null
  bureau_name: string | null
  active: boolean
}

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<AuthUser>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  canWrite: boolean
  isAdmin: boolean
  isSuperAdmin: boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(Boolean(localStorage.getItem('token')))

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const response = await api.get<AuthUser>('/api/auth/me')
      setUser(response.data)
    } catch {
      localStorage.removeItem('token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshUser()
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const data = await loginRequest(email, password)
    localStorage.setItem('token', data.access_token)
    const response = await api.get<AuthUser>('/api/auth/me')
    setUser(response.data)
    return response.data
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.post('/api/auth/logout')
    } catch {
      // Ignore network errors on logout.
    }
    localStorage.removeItem('token')
    setUser(null)
    window.location.href = '/login'
  }, [])

  const value = useMemo<AuthContextValue>(() => {
    const role = user?.role || ''
    return {
      user,
      loading,
      login,
      logout,
      refreshUser,
      canWrite: ['Super Administrator', 'Bureau Administrator', 'Case Officer', 'Regional Officer'].includes(role),
      isAdmin: ['Super Administrator', 'Bureau Administrator'].includes(role),
      isSuperAdmin: role === 'Super Administrator',
    }
  }, [user, loading, login, logout, refreshUser])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
