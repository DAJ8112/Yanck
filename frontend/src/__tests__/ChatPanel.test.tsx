import { expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'

import ChatPanel from '../components/ChatPanel'
import { renderWithProviders } from '../test-utils'
import * as chatApi from '../lib/chat'

vi.mock('../lib/chat')

const mockedChat = vi.mocked(chatApi.chatWithBot)

test('sends a chat message and renders assistant reply with context', async () => {
  const user = userEvent.setup()
  mockedChat.mockResolvedValue({
    conversation_id: 'conv-1',
    reply: {
      id: 'msg-assistant',
      role: 'assistant',
      content: 'Hello! How can I help?',
      created_at: new Date().toISOString(),
    },
    context: [
      {
        id: 'chunk-1',
        document_id: 'doc-1',
        document_name: 'faq.txt',
        score: 0.9123,
        content: 'Reset your password from the profile page.',
      },
    ],
    created_new_conversation: true,
  })

  renderWithProviders(<ChatPanel chatbotId="bot-1" chatbotName="Helper" />)

  const textarea = screen.getByPlaceholderText(/ask a question/i)
  await user.type(textarea, 'How do I reset my password?')
  await user.click(screen.getByRole('button', { name: /send/i }))

  await waitFor(() => expect(mockedChat).toHaveBeenCalledTimes(1))
  expect(mockedChat).toHaveBeenCalledWith('bot-1', {
    message: 'How do I reset my password?',
    conversation_id: undefined,
  })

  expect(screen.getByText(/Hello! How can I help/i)).toBeInTheDocument()
  expect(screen.getByText(/faq.txt/i)).toBeInTheDocument()
  expect(screen.getByText(/Score 0.912/i)).toBeInTheDocument()
})

