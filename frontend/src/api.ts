import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

