import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'

import { AuthProvider } from './context/AuthContext'
import { setStoredToken } from './lib/api'

type RenderOptions = {
  route?: string
  token?: string | null
  queryClient?: QueryClient
}

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

export function renderWithProviders(ui: ReactElement, options?: RenderOptions) {
  const { route = '/', token, queryClient = createTestQueryClient() } = options ?? {}

  if (token !== undefined) {
    setStoredToken(token)
  }

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </AuthProvider>
    </MemoryRouter>
  )

  return {
    queryClient,
    ...render(ui, { wrapper: Wrapper }),
  }
}

