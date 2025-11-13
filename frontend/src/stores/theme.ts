import { ref } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '../api/client'
import { handleApiError } from '../utils/errorHandler'
import type { User } from '../types'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref<boolean>(
    localStorage.getItem('darkMode') === 'true' || false
  )

  function applyTheme(dark: boolean) {
    if (dark) {
      document.documentElement.classList.add('theme-dark')
      document.documentElement.setAttribute('data-bs-theme', 'dark')
    } else {
      document.documentElement.classList.remove('theme-dark')
      document.documentElement.setAttribute('data-bs-theme', 'light')
    }
  }

  async function toggleDarkMode(syncWithBackend: boolean = true) {
    const newValue = !isDark.value
    isDark.value = newValue
    localStorage.setItem('darkMode', String(newValue))
    applyTheme(newValue)
    
    // Sync with backend if authenticated
    if (syncWithBackend) {
      try {
        await apiClient.patch<User>('/auth/me', { dark_mode: newValue })
      } catch (error) {
        // Log error but don't fail the UI toggle
        console.error('Failed to sync dark mode with backend:', error)
      }
    }
  }

  function setDarkMode(value: boolean, syncWithBackend: boolean = false) {
    isDark.value = value
    localStorage.setItem('darkMode', String(value))
    applyTheme(value)
    
    // Optionally sync with backend
    if (syncWithBackend) {
      apiClient.patch<User>('/auth/me', { dark_mode: value }).catch((error) => {
        console.error('Failed to sync dark mode with backend:', error)
      })
    }
  }

  function initializeFromUser(user: User) {
    // Initialize theme from user preferences
    isDark.value = user.dark_mode || false
    localStorage.setItem('darkMode', String(isDark.value))
    applyTheme(isDark.value)
  }

  // Initialize theme on store creation
  applyTheme(isDark.value)

  return {
    isDark,
    toggleDarkMode,
    setDarkMode,
    initializeFromUser
  }
})
