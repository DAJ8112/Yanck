import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, NavLink, Navigate, Outlet, Route, Routes } from 'react-router-dom'

import './App.css'
import { useAuth } from './context/AuthContext'
import ChatbotDetailPage from './routes/ChatbotDetailPage'
import ChatbotsPage from './routes/ChatbotsPage'

function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<ChatbotsPage />} />
        <Route path="chatbots/:chatbotId/*" element={<ChatbotDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function MainLayout() {
  const { token, setToken, clearToken } = useAuth()
  const [draftToken, setDraftToken] = useState(token ?? '')
  const [status, statusClass] = useMemo(() => {
    if (!token) {
      return ['No token configured', 'app__status app__status--inactive']
    }
    return ['Token stored', 'app__status app__status--active']
  }, [token])

  useEffect(() => {
    setDraftToken(token ?? '')
  }, [token])

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setToken(draftToken)
  }

  const handleClear = () => {
    setDraftToken('')
    clearToken()
  }

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <Link to="/" className="app__brand">
            <h1>RAG Builder</h1>
            <p>Configure and test retrieval-augmented chatbots.</p>
          </Link>
        </div>
        <form className="token-form" onSubmit={handleSubmit}>
          <label htmlFor="token-input" className="token-form__label">
            API token
          </label>
          <div className="token-form__controls">
            <input
              id="token-input"
              type="password"
              placeholder="Paste JWT access token"
              value={draftToken}
              onChange={(event) => setDraftToken(event.target.value)}
            />
            <button type="submit">Save</button>
            <button type="button" onClick={handleClear} className="token-form__clear">
              Clear
            </button>
          </div>
          <span className={statusClass}>{status}</span>
        </form>
      </header>
      <nav className="app__nav">
        <NavLink to="/" end>
          Chatbots
        </NavLink>
      </nav>
      <main className="app__main">
        <Outlet />
      </main>
    </div>
  )
}

export default App
