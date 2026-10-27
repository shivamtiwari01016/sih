import axios, { AxiosError } from 'axios'

const rawBase = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '')
// Prevent duplicate /api if the user sets VITE_API_BASE_URL ending with /api
export const API_BASE = rawBase.endsWith('/api') ? rawBase.slice(0, -4) : rawBase

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const url = error.config?.url || ''
    if (error.response?.status === 401 && !url.includes('/api/auth/login')) {
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item: any) => {
          const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : ''
          return `${field ? `${field}: ` : ''}${item.msg}`
        })
        .join(', ')
    }
    if (error.response?.data?.message) return String(error.response.data.message)
    if (error.code === 'ERR_NETWORK') {
      return 'Cannot reach the server. Please verify the backend is running and reachable.'
    }
    return error.message || 'Something went wrong'
  }
  return error instanceof Error ? error.message : 'Something went wrong'
}

export async function loginRequest(email: string, password: string) {
  const body = new URLSearchParams()
  body.append('username', email)
  body.append('password', password)
  const response = await api.post('/api/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data as { access_token: string; token_type: string }
}
