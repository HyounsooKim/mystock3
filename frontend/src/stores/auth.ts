import { ref } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '../api/client'
import { handleApiError } from '../utils/errorHandler'
import type { AuthResponse, LoginRequest, SignupRequest, User } from '../types'
import { useThemeStore } from './theme'

const TOKEN_EXPIRY_CHECK_INTERVAL = 60000 // 1 minute
const TOKEN_LIFETIME = 7 * 24 * 60 * 60 * 1000 // 7 days

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const isAuthenticated = ref<boolean>(!!token.value)
  const tokenIssuedAt = ref<number | null>(
    localStorage.getItem('token_issued_at') 
      ? parseInt(localStorage.getItem('token_issued_at')!, 10) 
      : null
  )
  
  let expiryCheckInterval: number | null = null

  function setAuth(newToken: string, newUser: User) {
    token.value = newToken
    user.value = newUser
    isAuthenticated.value = true
    const now = Date.now()
    tokenIssuedAt.value = now
    localStorage.setItem('auth_token', newToken)
    localStorage.setItem('token_issued_at', now.toString())
    
    // Initialize theme from user preferences
    const themeStore = useThemeStore()
    themeStore.initializeFromUser(newUser)
    
    // Start expiry check
    startExpiryCheck()
  }

  function clearAuth() {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    tokenIssuedAt.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('token_issued_at')
    
    // Stop expiry check
    stopExpiryCheck()
  }
  
  function isTokenExpired(): boolean {
    if (!tokenIssuedAt.value) return true
    const now = Date.now()
    return now - tokenIssuedAt.value > TOKEN_LIFETIME
  }
  
  function startExpiryCheck() {
    stopExpiryCheck() // Clear any existing interval
    
    expiryCheckInterval = window.setInterval(() => {
      if (isTokenExpired()) {
        handleSessionExpiry()
      }
    }, TOKEN_EXPIRY_CHECK_INTERVAL)
  }
  
  function stopExpiryCheck() {
    if (expiryCheckInterval !== null) {
      clearInterval(expiryCheckInterval)
      expiryCheckInterval = null
    }
  }
  
  async function handleSessionExpiry() {
    clearAuth()
    
    // Show notification
    alert('세션이 만료되었습니다. 다시 로그인해 주세요.')
    
    // Redirect to login using window.location (router may not be available in store)
    window.location.href = '/login'
  }

  async function login(email: string, password: string) {
    try {
      const loginData: LoginRequest = { email, password }
      const response = await apiClient.post<AuthResponse>('/auth/login', loginData)
      setAuth(response.data.access_token, response.data.user)
      return response.data.user
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  async function signup(email: string, password: string) {
    try {
      const signupData: SignupRequest = { email, password }
      const response = await apiClient.post<AuthResponse>('/auth/signup', signupData)
      setAuth(response.data.access_token, response.data.user)
      return response.data.user
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  async function logout() {
    try {
      await apiClient.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
    }
  }

  async function fetchCurrentUser() {
    try {
      const response = await apiClient.get<User>('/auth/me')
      user.value = response.data
      
      // Update theme when fetching user
      const themeStore = useThemeStore()
      themeStore.initializeFromUser(response.data)
    } catch (error) {
      clearAuth()
      throw error
    }
  }

  async function updatePreferences(updates: { dark_mode?: boolean; language?: string }) {
    try {
      const response = await apiClient.patch<User>('/auth/me', updates)
      user.value = response.data
      return response.data
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    setAuth,
    clearAuth,
    login,
    signup,
    logout,
    fetchCurrentUser,
    updatePreferences,
    isTokenExpired,
    startExpiryCheck,
    stopExpiryCheck,
    handleSessionExpiry
  }
})
