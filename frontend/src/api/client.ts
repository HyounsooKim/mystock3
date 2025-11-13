/**
 * Axios HTTP client wrapper with JWT token interceptor.
 * Automatically attaches authentication token to requests.
 * Includes exponential backoff retry logic for network errors.
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const MAX_RETRIES = 3
const INITIAL_RETRY_DELAY = 1000 // 1 second
const RETRY_DELAY_MULTIPLIER = 2

// Retry-able error codes (network errors, server errors)
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]

// Track retry count for each request
interface RetryConfig extends InternalAxiosRequestConfig {
  _retryCount?: number
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and retry logic
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig
    
    // Handle 401 Unauthorized (token expired)
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('token_issued_at')
      window.location.href = '/login'
      return Promise.reject(error)
    }
    
    // Check if we should retry
    const shouldRetry = shouldRetryRequest(error, config)
    
    if (shouldRetry && config) {
      config._retryCount = config._retryCount || 0
      config._retryCount += 1
      
      // Calculate delay with exponential backoff
      const delay = INITIAL_RETRY_DELAY * Math.pow(RETRY_DELAY_MULTIPLIER, config._retryCount - 1)
      
      console.warn(
        `Request failed (attempt ${config._retryCount}/${MAX_RETRIES}). Retrying in ${delay}ms...`,
        {
          url: config.url,
          status: error.response?.status,
          message: error.message
        }
      )
      
      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, delay))
      
      // Retry the request
      return apiClient.request(config)
    }
    
    return Promise.reject(error)
  }
)

function shouldRetryRequest(error: AxiosError, config?: RetryConfig): boolean {
  if (!config) return false
  
  // Don't retry if max retries reached
  const retryCount = config._retryCount || 0
  if (retryCount >= MAX_RETRIES) return false
  
  // Don't retry POST/PUT/PATCH/DELETE by default (non-idempotent)
  const method = config.method?.toUpperCase()
  if (method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    // Only retry on network errors, not application errors
    return !error.response && error.code !== 'ECONNABORTED'
  }
  
  // Retry on network errors (no response)
  if (!error.response) {
    return error.code !== 'ECONNABORTED' // Don't retry timeouts
  }
  
  // Retry on specific status codes
  const status = error.response.status
  return RETRYABLE_STATUS_CODES.includes(status)
}

export default apiClient
