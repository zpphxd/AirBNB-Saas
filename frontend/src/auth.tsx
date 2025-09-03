import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api, getToken, saveToken, setToken, apiLogin, apiRegister, apiRefresh, UserRole } from './api'

type AuthState = {
  token: string | null
  role: UserRole | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, role: UserRole, name?: string) => Promise<void>
  logout: () => void
}

const AuthCtx = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTok] = useState<string | null>(getToken())
  const [role, setRole] = useState<UserRole | null>(null)

  useEffect(() => {
    if (token) {
      try {
        // decode JWT payload to read role (no validation) – for display/guards only
        const payload = JSON.parse(atob(token.split('.')[1]))
        setRole(payload.role as UserRole)
      } catch { setRole(null) }
    } else {
      setRole(null)
    }
  }, [token])

  const login = async (email: string, password: string) => {
    const { token } = await apiLogin(email, password)
    saveToken(token)
    setTok(token)
  }

  const register = async (email: string, password: string, role: UserRole, name?: string) => {
    const { token } = await apiRegister(email, password, role, name)
    saveToken(token)
    setTok(token)
  }

  const logout = () => { localStorage.removeItem('token'); setToken(null); setTok(null) }

  // simple refresh every 20 minutes
  useEffect(() => {
    const id = setInterval(async () => {
      const t = getToken(); if (!t) return
      try { const { token: nt } = await apiRefresh(t); saveToken(nt); setTok(nt) } catch {}
    }, 20 * 60 * 1000)
    return () => clearInterval(id)
  }, [])

  const value = useMemo(() => ({ token, role, login, register, logout }), [token, role])
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function Protected({ roles, children }: { roles?: UserRole[], children: React.ReactNode }) {
  const { token, role } = useAuth()
  if (!token) return <div>Please sign in to continue.</div>
  if (roles && role && !roles.includes(role)) return <div>Access denied for role {role}.</div>
  return <>{children}</>
}

