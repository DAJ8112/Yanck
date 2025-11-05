import { beforeEach, expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'

import { renderWithProviders } from '../test-utils'
import ChatbotsPage from '../routes/ChatbotsPage'
import * as chatbotsApi from '../lib/chatbots'
import type { Chatbot } from '../types'

vi.mock('../lib/chatbots')

const mockedFetch = vi.mocked(chatbotsApi.fetchChatbots)
const mockedCreate = vi.mocked(chatbotsApi.createChatbot)

beforeEach(() => {
  mockedFetch.mockResolvedValue([])
  mockedCreate.mockReset()
})

test('shows empty state when no chatbots exist', async () => {
  renderWithProviders(<ChatbotsPage />, { token: 'test-token' })

  await waitFor(() => expect(mockedFetch).toHaveBeenCalled())
  expect(await screen.findByText(/No chatbots yet/i)).toBeInTheDocument()
})

test('creates a chatbot and calls the API with form values', async () => {
  const user = userEvent.setup()
  const newChatbot: Chatbot = {
    id: 'bot-123',
    name: 'Support Bot',
    slug: 'support-bot',
    system_prompt: 'Be helpful.',
    model_provider: 'ollama',
    model_name: 'llama3',
    temperature: 0.2,
    top_k: 4,
    deployment_slug: null,
    is_published: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }

  mockedCreate.mockResolvedValue(newChatbot)

  renderWithProviders(<ChatbotsPage />, { token: 'test-token' })

  await waitFor(() => expect(mockedFetch).toHaveBeenCalled())

  await user.click(screen.getByRole('button', { name: /new chatbot/i }))

  await user.type(screen.getByLabelText(/^Name$/i), 'Support Bot')
  await user.selectOptions(screen.getByLabelText(/Model provider/i), 'gemini')
  await user.selectOptions(screen.getByLabelText(/Model name/i), 'models/gemini-2.5-flash')
  await user.clear(screen.getByLabelText(/Temperature/i))
  await user.type(screen.getByLabelText(/Temperature/i), '0.3')
  await user.clear(screen.getByLabelText(/Top K/i))
  await user.type(screen.getByLabelText(/Top K/i), '5')
  await user.type(screen.getByLabelText(/System prompt/i), 'Answer with context')

  await user.click(screen.getByRole('button', { name: /create/i }))

  await waitFor(() => expect(mockedCreate).toHaveBeenCalledTimes(1))
  expect(mockedCreate).toHaveBeenCalledWith(
    expect.objectContaining({
      name: 'Support Bot',
      model_provider: 'gemini',
      model_name: 'models/gemini-2.5-flash',
      temperature: 0.3,
      top_k: 5,
      system_prompt: 'Answer with context',
    }),
  )
})

