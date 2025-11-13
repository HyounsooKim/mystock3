/**
 * Global error handler for frontend application.
 */

import type { AxiosError } from 'axios'
import type { ApiError } from '../types'

export class AppError extends Error {
  code?: string
  statusCode?: number

  constructor(message: string, code?: string, statusCode?: number) {
    super(message)
    this.name = 'AppError'
    this.code = code
    this.statusCode = statusCode
  }
}

export function handleApiError(error: unknown): AppError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>
    
    if (axiosError.response) {
      // Server responded with error
      const apiError = axiosError.response.data
      return new AppError(
        apiError.detail || '서버 오류가 발생했습니다.',
        apiError.error_code,
        axiosError.response.status
      )
    } else if (axiosError.request) {
      // Request made but no response
      return new AppError(
        '서버에 연결할 수 없습니다. 네트워크를 확인해주세요.',
        'NETWORK_ERROR'
      )
    }
  }
  
  // Unknown error
  return new AppError(
    error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
    'UNKNOWN_ERROR'
  )
}

export function showErrorNotification(error: AppError): void {
  // TODO: Integrate with notification system (e.g., toast)
  console.error('Error:', error.message, error.code)
  alert(error.message)
}

// Import axios for type checking
import axios from 'axios'
