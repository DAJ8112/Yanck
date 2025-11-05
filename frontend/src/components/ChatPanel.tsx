import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'

import { chatWithBot, type ChatRequestPayload } from '../lib/chat'
import { getErrorMessage } from '../lib/api'
import type { ChatContextChunk, ConversationMessage, ChatResponsePayload } from '../types'

type ChatPanelProps = {
  chatbotId: string
  chatbotName: string
}

type ChatLogMessage = ConversationMessage & {
  pending?: boolean
}

function createLocalId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `local-${Math.random().toString(36).slice(2)}`
}

function mapResponseMessage(message: ConversationMessage): ChatLogMessage {
  return {
    ...message,
    pending: false,
  }
}

function ChatPanel({ chatbotId, chatbotName }: ChatPanelProps) {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatLogMessage[]>([])
  const [contextChunks, setContextChunks] = useState<ChatContextChunk[]>([])
  const [inputValue, setInputValue] = useState('')
  const [chatError, setChatError] = useState<string | null>(null)
  const [pendingMessageId, setPendingMessageId] = useState<string | null>(null)

  const chatMutation = useMutation({
    mutationFn: (payload: ChatRequestPayload) => chatWithBot(chatbotId, payload),
  })

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = inputValue.trim()
    if (!trimmed || chatMutation.isPending) {
      return
    }

    const localId = createLocalId()
    const userMessage: ChatLogMessage = {
      id: localId,
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
      pending: true,
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setChatError(null)
    setPendingMessageId(localId)

    chatMutation.mutate(
      {
        message: trimmed,
        conversation_id: conversationId ?? undefined,
      },
      {
        onSuccess: (response: ChatResponsePayload) => {
          setConversationId(response.conversation_id)
          setMessages((prev) => {
            const updated = prev.map((message) =>
              message.id === localId
                ? { ...message, pending: false }
                : message,
            )
            return [...updated, mapResponseMessage(response.reply)]
          })
          setContextChunks(response.context)
          setPendingMessageId(null)
        },
        onError: (error) => {
          setChatError(getErrorMessage(error))
          setMessages((prev) => prev.filter((message) => message.id !== localId))
          setPendingMessageId(null)
        },
      },
    )
  }

  const handleReset = () => {
    setConversationId(null)
    setMessages([])
    setContextChunks([])
    setChatError(null)
    setPendingMessageId(null)
  }

  const isSending = chatMutation.isPending && pendingMessageId !== null

  return (
    <section className="card chat">
      <header className="chat__header">
        <div>
          <h3>Chat</h3>
          <p>Ask questions to {chatbotName} using its ingested knowledge.</p>
        </div>
        <button type="button" className="secondary" onClick={handleReset} disabled={!messages.length}>
          Reset conversation
        </button>
      </header>

      <div className="chat__messages">
        {messages.length === 0 && <div className="chat__empty">Send a message to begin the conversation.</div>}
        {messages.map((message) => (
          <article key={message.id} className={`chat__message chat__message--${message.role}`}>
            <div className="chat__message-role">{message.role === 'assistant' ? chatbotName : 'You'}</div>
            <div className="chat__bubble">
              <p>{message.content}</p>
              {message.pending && <span className="chat__pending">Sending…</span>}
            </div>
          </article>
        ))}
        {isSending && <div className="chat__pending-indicator">Generating response…</div>}
      </div>

      {contextChunks.length > 0 && (
        <section className="chat__context">
          <h4>Retrieved context</h4>
          <ul>
            {contextChunks.map((chunk) => (
              <li key={chunk.id}>
                <header>
                  <span>{chunk.document_name ?? chunk.document_id}</span>
                  <span className="chat__score">Score {chunk.score.toFixed(3)}</span>
                </header>
                <p>{chunk.content}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <form className="chat__composer" onSubmit={handleSubmit}>
        <label htmlFor="chat-input" className="sr-only">
          Enter your message
        </label>
        <textarea
          id="chat-input"
          rows={3}
          placeholder="Ask a question about your documents…"
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          disabled={chatMutation.isPending}
        />
        {chatError && <div className="form__error form__error--global">{chatError}</div>}
        <div className="form__actions">
          <button type="submit" className="primary" disabled={chatMutation.isPending || !inputValue.trim()}>
            {chatMutation.isPending ? 'Sending…' : 'Send'}
          </button>
        </div>
      </form>
    </section>
  )
}

export default ChatPanel

