import { apiClient } from './api'

import type { Chatbot, ChatbotDocument, CreateChatbotInput } from '../types'

const CHATBOTS_ENDPOINT = '/chatbots'

export async function fetchChatbots(): Promise<Chatbot[]> {
  const { data } = await apiClient.get<Chatbot[]>(CHATBOTS_ENDPOINT)
  return data
}

export async function createChatbot(payload: CreateChatbotInput): Promise<Chatbot> {
  const { data } = await apiClient.post<Chatbot>(CHATBOTS_ENDPOINT, payload)
  return data
}

export async function fetchChatbot(chatbotId: string): Promise<Chatbot> {
  const { data } = await apiClient.get<Chatbot>(`${CHATBOTS_ENDPOINT}/${chatbotId}`)
  return data
}

export async function fetchChatbotDocuments(chatbotId: string): Promise<ChatbotDocument[]> {
  const { data } = await apiClient.get<ChatbotDocument[]>(`${CHATBOTS_ENDPOINT}/${chatbotId}/documents`)
  return data
}

export async function uploadChatbotDocuments(
  chatbotId: string,
  files: File[],
): Promise<ChatbotDocument[]> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))

  const { data } = await apiClient.post<ChatbotDocument[]>(
    `${CHATBOTS_ENDPOINT}/${chatbotId}/documents`,
    formData,
  )
  return data
}

