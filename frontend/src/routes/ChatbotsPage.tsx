import { useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { createChatbot, fetchChatbots } from '../lib/chatbots'
import { getErrorMessage } from '../lib/api'
import type { Chatbot, CreateChatbotInput } from '../types'

const MODEL_PROVIDER_OPTIONS = [
  { value: 'gemini', label: 'Google Gemini' },
]

const MODEL_OPTIONS_BY_PROVIDER: Record<string, { value: string; label: string }[]> = {
  gemini: [
    { value: 'models/gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
  ],
}

const chatbotFormSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  model_provider: z.string().min(1, 'Provider is required'),
  model_name: z.string().min(1, 'Model is required'),
  system_prompt: z.string().max(5000, 'Prompt is too long').optional(),
  temperature: z.coerce.number().min(0).max(1),
  top_k: z.coerce.number().int().min(1).max(20),
})

type FormState = {
  name: string
  model_provider: string
  model_name: string
  system_prompt: string
  temperature: string
  top_k: string
}

const defaultFormState: FormState = {
  name: '',
  model_provider: MODEL_PROVIDER_OPTIONS[0]?.value ?? '',
  model_name: MODEL_OPTIONS_BY_PROVIDER[MODEL_PROVIDER_OPTIONS[0]?.value ?? '']?.[0]?.value ?? '',
  system_prompt: '',
  temperature: '0.2',
  top_k: '4',
}

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function ChatbotsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { token } = useAuth()

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['chatbots'],
    queryFn: fetchChatbots,
  })

  const [formState, setFormState] = useState<FormState>(defaultFormState)
  const [formErrors, setFormErrors] = useState<Record<keyof FormState, string | undefined>>({
    name: undefined,
    model_provider: undefined,
    model_name: undefined,
    system_prompt: undefined,
    temperature: undefined,
    top_k: undefined,
  })
  const [isCreating, setIsCreating] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const availableModels = MODEL_OPTIONS_BY_PROVIDER[formState.model_provider] ?? []

  const createMutation = useMutation({
    mutationFn: async (payload: CreateChatbotInput) => createChatbot(payload),
    onSuccess: (chatbot: Chatbot) => {
      setIsCreating(false)
      setFormState(defaultFormState)
      setFormErrors({
        name: undefined,
        model_provider: undefined,
        model_name: undefined,
        system_prompt: undefined,
        temperature: undefined,
        top_k: undefined,
      })
      setServerError(null)
      queryClient.invalidateQueries({ queryKey: ['chatbots'] })
      navigate(`/chatbots/${chatbot.id}`)
    },
    onError: (err) => {
      setServerError(getErrorMessage(err))
    },
  })

  const handleToggleForm = () => {
    setIsCreating((value) => !value)
    setFormErrors({
      name: undefined,
      model_provider: undefined,
      model_name: undefined,
      system_prompt: undefined,
      temperature: undefined,
      top_k: undefined,
    })
    setServerError(null)
  }

  const handleInputChange = (key: keyof FormState, value: string) => {
    setFormState((prev) => ({ ...prev, [key]: value }))
    setFormErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const parsed = chatbotFormSchema.safeParse({
      name: formState.name,
      model_provider: formState.model_provider,
      model_name: formState.model_name,
      system_prompt: formState.system_prompt ? formState.system_prompt : undefined,
      temperature: formState.temperature,
      top_k: formState.top_k,
    })

    if (!parsed.success) {
      const issues = parsed.error.flatten().fieldErrors
      setFormErrors((prev) => ({
        ...prev,
        name: issues.name?.[0],
        model_provider: issues.model_provider?.[0],
        model_name: issues.model_name?.[0],
        system_prompt: issues.system_prompt?.[0],
        temperature: issues.temperature?.[0],
        top_k: issues.top_k?.[0],
      }))
      setServerError(null)
      return
    }

    const payload: CreateChatbotInput = {
      ...parsed.data,
      system_prompt: parsed.data.system_prompt?.trim() || undefined,
    }
    setServerError(null)
    createMutation.mutate(payload)
  }

  const disableActions = !token

  return (
    <section className="page">
      <header className="page__header">
        <div>
          <h2>Chatbots</h2>
          <p className="page__subtitle">
            Create assistants and manage their RAG configuration.{' '}
            {!token && <span className="warning">Set an API token to load your chatbots.</span>}
          </p>
        </div>
        <button className="primary" onClick={handleToggleForm} disabled={disableActions}>
          {isCreating ? 'Close' : 'New Chatbot'}
        </button>
      </header>

      {isCreating && (
        <form className="card form" onSubmit={handleSubmit}>
          <h3>Create chatbot</h3>
          <div className="form__grid">
            <label>
              <span>Name</span>
              <input
                type="text"
                value={formState.name}
                onChange={(event) => handleInputChange('name', event.target.value)}
                required
              />
              {formErrors.name && <small className="form__error">{formErrors.name}</small>}
            </label>
            <label>
              <span>Model provider</span>
              <select
                value={formState.model_provider}
                onChange={(event) => {
                  const provider = event.target.value
                  const nextModels = MODEL_OPTIONS_BY_PROVIDER[provider] ?? []
                  const nextModelValue = nextModels[0]?.value ?? ''
                  setFormState((prev) => ({
                    ...prev,
                    model_provider: provider,
                    model_name: nextModelValue,
                  }))
                  setFormErrors((prev) => ({
                    ...prev,
                    model_provider: undefined,
                    model_name: undefined,
                  }))
                }}
                required
              >
                {MODEL_PROVIDER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {formErrors.model_provider && (
                <small className="form__error">{formErrors.model_provider}</small>
              )}
            </label>
            <label>
              <span>Model name</span>
              <select
                value={formState.model_name}
                onChange={(event) => handleInputChange('model_name', event.target.value)}
                required
              >
                {availableModels.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {formErrors.model_name && <small className="form__error">{formErrors.model_name}</small>}
            </label>
            <label>
              <span>Temperature</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={formState.temperature}
                onChange={(event) => handleInputChange('temperature', event.target.value)}
              />
              {formErrors.temperature && (
                <small className="form__error">{formErrors.temperature}</small>
              )}
            </label>
            <label>
              <span>Top K</span>
              <input
                type="number"
                min="1"
                max="20"
                value={formState.top_k}
                onChange={(event) => handleInputChange('top_k', event.target.value)}
              />
              {formErrors.top_k && <small className="form__error">{formErrors.top_k}</small>}
            </label>
          </div>
          <label className="form__stack">
            <span>System prompt</span>
            <textarea
              rows={4}
              value={formState.system_prompt}
              onChange={(event) => handleInputChange('system_prompt', event.target.value)}
              placeholder="Optional instructions for the assistant"
            />
            {formErrors.system_prompt && <small className="form__error">{formErrors.system_prompt}</small>}
          </label>
          {serverError && <div className="form__error form__error--global">{serverError}</div>}
          <div className="form__actions">
            <button type="submit" className="primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating…' : 'Create' }
            </button>
            <button type="button" onClick={handleToggleForm} className="secondary">
              Cancel
            </button>
          </div>
        </form>
      )}

      <section className="list">
        {isLoading && <div className="page__empty">Loading chatbots…</div>}
        {isError && <div className="page__empty error">{getErrorMessage(error)}</div>}
        {!isLoading && !isError && (data?.length ?? 0) === 0 && (
          <div className="page__empty">No chatbots yet — create one to get started.</div>
        )}
        <div className="list__grid">
          {(data ?? []).map((chatbot) => (
            <article
              key={chatbot.id}
              className="card list__item"
              onClick={() => navigate(`/chatbots/${chatbot.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(event: KeyboardEvent<HTMLElement>) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  navigate(`/chatbots/${chatbot.id}`)
                }
              }}
            >
              <header>
                <h3>{chatbot.name}</h3>
                <span className="badge">{chatbot.model_provider}</span>
              </header>
              <p className="list__meta">
                {chatbot.model_name} • Updated {dateFormatter.format(new Date(chatbot.updated_at))}
              </p>
              <p className="list__description">
                {chatbot.system_prompt ? chatbot.system_prompt.slice(0, 160) : 'No system prompt'}
                {chatbot.system_prompt && chatbot.system_prompt.length > 160 ? '…' : ''}
              </p>
            </article>
          ))}
        </div>
      </section>
    </section>
  )
}

export default ChatbotsPage

