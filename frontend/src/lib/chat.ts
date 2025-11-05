import { apiClient } from './api'

import type { ChatResponsePayload } from '../types'

export type ChatRequestPayload = {
  message: string
  conversation_id?: string
  top_k?: number
}

export async function chatWithBot(
  chatbotId: string,
  payload: ChatRequestPayload,
): Promise<ChatResponsePayload> {
  const { data } = await apiClient.post<ChatResponsePayload>(
    `/chatbots/${chatbotId}/chat`,
    payload,
  )
  return data
}

