export type ISODateTimeString = string

export type Chatbot = {
  id: string
  name: string
  slug: string
  system_prompt: string
  model_provider: string
  model_name: string
  temperature: number
  top_k: number
  deployment_slug: string | null
  is_published: boolean
  created_at: ISODateTimeString
  updated_at: ISODateTimeString
}

export type CreateChatbotInput = {
  name: string
  model_provider: string
  model_name: string
  system_prompt?: string
  temperature?: number
  top_k?: number
}

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed'

export type ChatbotDocument = {
  id: string
  file_name: string
  mime_type: string
  size_bytes: number
  status: DocumentStatus
  error: string | null
  created_at: ISODateTimeString
  updated_at: ISODateTimeString
}

export type ConversationMessageRole = 'user' | 'assistant' | 'system' | 'tool'

export type ConversationMessage = {
  id: string
  role: ConversationMessageRole
  content: string
  created_at: ISODateTimeString
}

export type ChatContextChunk = {
  id: string
  document_id: string
  document_name: string | null
  score: number
  content: string
}

export type ChatResponsePayload = {
  conversation_id: string
  reply: ConversationMessage
  context: ChatContextChunk[]
  created_new_conversation: boolean
}

