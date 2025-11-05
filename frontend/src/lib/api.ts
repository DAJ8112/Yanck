import axios, { AxiosError, AxiosHeaders, type AxiosRequestHeaders } from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
export const TOKEN_STORAGE_KEY = 'ragbuilder.authToken'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (!token) {
    return config
  }

  if (config.headers) {
    const headers = config.headers as AxiosRequestHeaders & {
      set?: (name: string, value: string) => void
    }
    if (typeof headers.set === 'function') {
      headers.set('Authorization', `Bearer ${token}`)
    } else {
      headers.Authorization = `Bearer ${token}`
    }
  } else {
    config.headers = new AxiosHeaders({ Authorization: `Bearer ${token}` })
  }

  return config
})

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (!token) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    } else {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    }
  } catch (error) {
    console.warn('Unable to persist auth token', error)
  }
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>
    return (
      axiosError.response?.data?.detail ||
      axiosError.message ||
      'Request failed — please try again.'
    )
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Something went wrong.'
}

