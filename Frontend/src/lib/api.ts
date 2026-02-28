import axios from 'axios'
import { supabase } from './supabaseClient'
import {
  AuthResponseSchema,
  FileListResponseSchema,
  UploadResponseSchema,
  DocumentListResponseSchema,
  DocumentUploadResponseSchema,
  type AuthResponse,
  type DocumentRecord,
} from './schemas'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000, // 5 minutes for long-running analysis
})

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors and validation
api.interceptors.response.use(
  (response) => {
    // Validate response data based on endpoint
    const url = response.config.url || ''
    
    try {
      if (url.includes('/auth/verify')) {
        response.data = AuthResponseSchema.parse(response.data)
      } else if (url.includes('/upload/files')) {
        response.data = FileListResponseSchema.parse(response.data)
      } else if (url.includes('/upload/file')) {
        response.data = UploadResponseSchema.parse(response.data)
      } else if (url.includes('/rag/documents') && response.config.method?.toLowerCase() === 'get') {
        response.data = DocumentListResponseSchema.parse(response.data)
      } else if (url.includes('/rag/documents') && response.config.method?.toLowerCase() === 'post') {
        response.data = DocumentUploadResponseSchema.parse(response.data)
      }
    } catch {
      // Validation failed; keep raw response data
    }
    
    return response
  },
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const { data: { session } } = await supabase.auth.refreshSession()
      if (session?.access_token) {
        // Retry the request with new token
        error.config.headers.Authorization = `Bearer ${session.access_token}`
        return api.request(error.config)
      } else {
        // Redirect to login
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// API functions with type safety
export const authAPI = {
  verifyToken: async (): Promise<AuthResponse> => {
    const response = await api.post('/auth/verify')
    return response.data
  },

  getUserInfo: async (): Promise<{ user: any }> => {
    const response = await api.get('/auth/user')
    return response.data
  },
}

export type { DocumentRecord }

export const documentsAPI = {
  list: async (params?: { skip?: number; limit?: number; document_type?: 'text' | 'video' }) => {
    const response = await api.get<{ documents: DocumentRecord[]; count: number; skip: number; limit: number }>(
      '/rag/documents',
      { params: { skip: params?.skip ?? 0, limit: params?.limit ?? 50, document_type: params?.document_type } }
    )
    return response.data
  },

  uploadText: async (text: string, metadata?: { title?: string; source?: string }) => {
    const response = await api.post<{ message: string; document_id: string | string[]; chunks_created?: number; status: string }>(
      '/rag/documents',
      { text, metadata: metadata ?? {}, document_type: 'text' }
    )
    return response.data
  },

  uploadVideo: async (file: File, title?: string, description?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (title) form.append('title', title)
    if (description) form.append('description', description)
    const response = await api.post<{ message: string; document_id: string; status: string }>(
      '/rag/documents/video',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },

  delete: async (documentId: string) => {
    const response = await api.delete<{ message: string; document_id: string }>(
      `/rag/documents/${documentId}`
    )
    return response.data
  },
}

export default api
