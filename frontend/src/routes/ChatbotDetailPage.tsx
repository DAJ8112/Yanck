import { useRef, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import {
  fetchChatbot,
  fetchChatbotDocuments,
  uploadChatbotDocuments,
} from '../lib/chatbots'
import { getErrorMessage } from '../lib/api'
import ChatPanel from '../components/ChatPanel'
import type { ChatbotDocument } from '../types'

const documentStatusLabels: Record<string, string> = {
  pending: 'Pending',
  processing: 'Processing',
  ready: 'Ready',
  failed: 'Failed',
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes)) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  let value = bytes
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

function formatDate(value: string): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function ChatbotDetailPage() {
  const { chatbotId } = useParams()
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const isAuthorized = Boolean(token)

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)

  const chatbotQuery = useQuery({
    queryKey: ['chatbots', chatbotId],
    queryFn: () => fetchChatbot(chatbotId!),
    enabled: Boolean(chatbotId) && isAuthorized,
  })

  const documentsQuery = useQuery({
    queryKey: ['chatbots', chatbotId, 'documents'],
    queryFn: () => fetchChatbotDocuments(chatbotId!),
    enabled: Boolean(chatbotId) && isAuthorized,
  })

  const uploadMutation = useMutation({
    mutationFn: (files: File[]) => uploadChatbotDocuments(chatbotId!, files),
    onSuccess: () => {
      setSelectedFiles([])
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      setUploadError(null)
      queryClient.invalidateQueries({ queryKey: ['chatbots', chatbotId, 'documents'] })
    },
    onError: (error) => {
      setUploadError(getErrorMessage(error))
    },
  })

  if (!chatbotId) {
    return (
      <section className="page">
        <header className="page__header">
          <h2>Chatbot not found</h2>
        </header>
        <div className="page__empty error">A chatbot identifier is required.</div>
      </section>
    )
  }

  const chatbot = chatbotQuery.data
  const documents = documentsQuery.data ?? []

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? [])
    setSelectedFiles(files)
    setUploadError(null)
  }

  const handleUpload = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selectedFiles.length || uploadMutation.isPending) return
    uploadMutation.mutate(selectedFiles)
  }

  const isLoading = chatbotQuery.isLoading || documentsQuery.isLoading
  const hasError = chatbotQuery.isError || documentsQuery.isError
  const errorMessage = chatbotQuery.isError
    ? getErrorMessage(chatbotQuery.error)
    : documentsQuery.isError
      ? getErrorMessage(documentsQuery.error)
      : null

  return (
    <section className="page">
      <header className="page__header">
        <h2>{chatbot?.name ?? 'Chatbot'}</h2>
        <p className="page__subtitle">
          Manage documents and ingestion pipeline for this assistant.
          {!isAuthorized && (
            <span className="warning">Provide an access token to load chatbot details.</span>
          )}
        </p>
      </header>

      {!isAuthorized && (
        <div className="page__empty error">Authentication token required to load chatbot details.</div>
      )}

      {isAuthorized && isLoading && <div className="page__empty">Loading chatbot data…</div>}

      {isAuthorized && hasError && <div className="page__empty error">{errorMessage}</div>}

      {isAuthorized && chatbot && (
        <section className="card detail">
          <div className="detail__row">
            <div>
              <h3>Configuration</h3>
              <dl>
                <div>
                  <dt>Model provider</dt>
                  <dd>{chatbot.model_provider}</dd>
                </div>
                <div>
                  <dt>Model name</dt>
                  <dd>{chatbot.model_name}</dd>
                </div>
                <div>
                  <dt>Temperature</dt>
                  <dd>{chatbot.temperature}</dd>
                </div>
                <div>
                  <dt>Top K</dt>
                  <dd>{chatbot.top_k}</dd>
                </div>
              </dl>
            </div>
            <div>
              <h3>Metadata</h3>
              <dl>
                <div>
                  <dt>ID</dt>
                  <dd><code>{chatbot.id}</code></dd>
                </div>
                <div>
                  <dt>Slug</dt>
                  <dd>{chatbot.slug}</dd>
                </div>
                <div>
                  <dt>Created</dt>
                  <dd>{formatDate(chatbot.created_at)}</dd>
                </div>
                <div>
                  <dt>Updated</dt>
                  <dd>{formatDate(chatbot.updated_at)}</dd>
                </div>
              </dl>
            </div>
          </div>
          {chatbot.system_prompt && (
            <div className="detail__prompt">
              <h4>System prompt</h4>
              <p>{chatbot.system_prompt}</p>
            </div>
          )}
        </section>
      )}

      {isAuthorized && (
        <section className="card upload">
          <form className="upload__form" onSubmit={handleUpload}>
            <div>
              <h3>Upload documents</h3>
              <p>Supports multiple files up to 50MB each.</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              disabled={uploadMutation.isPending}
              onChange={handleFileChange}
            />
            {selectedFiles.length > 0 && (
              <ul className="upload__files">
                {selectedFiles.map((file) => (
                  <li key={file.name}>{file.name}</li>
                ))}
              </ul>
            )}
            {uploadError && <div className="form__error form__error--global">{uploadError}</div>}
            <div className="form__actions">
              <button
                type="submit"
                className="primary"
                disabled={!selectedFiles.length || uploadMutation.isPending}
              >
                {uploadMutation.isPending ? 'Uploading…' : 'Upload'}
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() => {
                  setSelectedFiles([])
                  setUploadError(null)
                  if (fileInputRef.current) fileInputRef.current.value = ''
                }}
              >
                Clear
              </button>
            </div>
          </form>
        </section>
      )}

      {isAuthorized && !documentsQuery.isLoading && !documentsQuery.isError && (
        <section className="card documents">
          <header className="documents__header">
            <div>
              <h3>Documents</h3>
              <p>{documents.length} uploaded</p>
            </div>
            <button
              type="button"
              className="secondary"
              onClick={() => documentsQuery.refetch()}
              disabled={documentsQuery.isFetching}
            >
              {documentsQuery.isFetching ? 'Refreshing…' : 'Refresh'}
            </button>
          </header>
          {documents.length === 0 ? (
            <div className="page__empty">No documents uploaded yet.</div>
          ) : (
            <table className="documents__table">
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col">Size</th>
                  <th scope="col">Status</th>
                  <th scope="col">Updated</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document: ChatbotDocument) => (
                  <tr key={document.id}>
                    <td>
                      <div className="documents__file">
                        <span className="documents__name">{document.file_name}</span>
                        {document.error && (
                          <span className="documents__error">{document.error}</span>
                        )}
                      </div>
                    </td>
                    <td>{formatBytes(document.size_bytes)}</td>
                    <td>
                      <span className={`status status--${document.status}`}>
                        {documentStatusLabels[document.status] ?? document.status}
                      </span>
                    </td>
                    <td>{formatDate(document.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {isAuthorized && chatbot && (
        <ChatPanel chatbotId={chatbot.id} chatbotName={chatbot.name} />
      )}
    </section>
  )
}

export default ChatbotDetailPage

