import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Channel {
  id: number
  telegram_id: string
  username: string
  title: string
  description: string | null
  language: string | null
  subscriber_count: number
  created_at: string
  last_fetched_at: string | null
}

export interface Message {
  id: number
  channel_id: number
  telegram_message_id: number
  original_text: string
  translated_text: string | null
  source_language: string | null
  media_type: string | null
  media_urls: string | null
  published_at: string
  fetched_at: string
  is_duplicate: boolean
  duplicate_group_id: string | null
}

export interface MessageListResponse {
  messages: Message[]
  total: number
  page: number
  page_size: number
}

export interface Summary {
  id: number
  summary_type: string
  content: string
  message_count: number
  generated_at: string
  period_start: string
  period_end: string
}

// API functions
export const channelsApi = {
  list: () => api.get<Channel[]>('/api/channels'),
  add: (username: string) => api.post<Channel>('/api/channels', { username }),
  delete: (id: number) => api.delete(`/api/channels/${id}`),
}

export const messagesApi = {
  list: (params?: {
    channel_id?: number
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
  }) => api.get<MessageListResponse>('/api/messages', { params }),
  get: (id: number) => api.get<Message>(`/api/messages/${id}`),
  fetchHistorical: (channelId: number, days: number = 7) =>
    api.post(`/api/messages/fetch-historical/${channelId}?days=${days}`),
  translate: (targetLanguage: string, channelId?: number) =>
    api.post('/api/messages/translate', null, {
      params: { target_language: targetLanguage, channel_id: channelId }
    }),
}

export const summariesApi = {
  getDaily: () => api.get<Summary>('/api/summaries/daily'),
  generate: () => api.post<Summary>('/api/summaries/generate', { summary_type: 'daily' }),
}

// Language options
export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'fr', name: 'Français' },
  { code: 'es', name: 'Español' },
  { code: 'de', name: 'Deutsch' },
  { code: 'ar', name: 'العربية' },
  { code: 'zh', name: '中文' },
  { code: 'ru', name: 'Русский' },
  { code: 'ja', name: '日本語' },
  { code: 'pt', name: 'Português' },
  { code: 'it', name: 'Italiano' },
]
