import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { getStoredToken, setStoredToken } from '../lib/api'

type AuthContextValue = {
  token: string | null
  setToken: (token: string) => void
  clearToken: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

type AuthProviderProps = {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setTokenState] = useState<string | null>(() => getStoredToken())

  useEffect(() => {
    setTokenState(getStoredToken())
  }, [])

  const setToken = useCallback((value: string) => {
    const next = value.trim()
    if (!next) {
      setStoredToken(null)
      setTokenState(null)
      return
    }
    setStoredToken(next)
    setTokenState(next)
  }, [])

  const clearToken = useCallback(() => {
    setStoredToken(null)
    setTokenState(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ token, setToken, clearToken }),
    [token, setToken, clearToken],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

