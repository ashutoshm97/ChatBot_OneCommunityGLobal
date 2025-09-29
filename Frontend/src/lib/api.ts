import axios from 'axios'
import { supabase } from './supabaseClient'
import {
  AuthResponseSchema,
  type AuthResponse,

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
      if (url.includes('/analysis/analyze')) {
        // Temporarily disable validation to see if it's causing issues
        // const validatedData = AnalysisResultSchema.parse(response.data)
        // response.data = validatedData
      } else if (url.includes('/upload/files')) {
        const validatedData = FileListResponseSchema.parse(response.data)
        response.data = validatedData
      } else if (url.includes('/upload/file')) {
        const validatedData = UploadResponseSchema.parse(response.data)
        response.data = validatedData
      } else if (url.includes('/auth/verify')) {
        const validatedData = AuthResponseSchema.parse(response.data)
        response.data = validatedData
      }
    } catch (error) {
      // Response validation failed - continuing with raw data
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



export default api
