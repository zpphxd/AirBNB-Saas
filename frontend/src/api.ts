import axios from 'axios'

const API_URL = (import.meta as any).env?.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000')

export const api = axios.create({ baseURL: API_URL })

export function setToken(token: string | null) {
  if (token) api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  else delete api.defaults.headers.common['Authorization']
}

export function getToken(): string | null {
  return localStorage.getItem('token')
}

export function saveToken(t: string) {
  localStorage.setItem('token', t)
  setToken(t)
}

setToken(getToken())

export function setDemoRole(role: 'host'|'cleaner'|'admin') {
  localStorage.setItem('demoRole', role)
  api.defaults.headers.common['X-Demo-Role'] = role
}

// Initialize demo role header if present
const demoRole = (localStorage.getItem('demoRole') as any) || 'host'
api.defaults.headers.common['X-Demo-Role'] = demoRole

export type UserRole = 'host' | 'cleaner' | 'admin'

export async function apiRegister(email: string, password: string, role: UserRole, name?: string) {
  const r = await api.post('/auth/register', { email, password, role, name })
  return r.data as { token: string }
}

export async function apiLogin(email: string, password: string) {
  const r = await api.post(`/auth/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`)
  return r.data as { token: string }
}

export async function apiRefresh(token?: string) {
  const r = await api.post('/auth/refresh', token ? { token } : undefined)
  return r.data as { token: string }
}
