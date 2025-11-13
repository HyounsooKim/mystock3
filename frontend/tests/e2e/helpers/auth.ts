import { test as base, expect } from '@playwright/test'
import type { Page } from '@playwright/test'

/**
 * Authentication helper utilities for E2E tests
 */

export interface AuthHelpers {
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  isLoggedIn: () => Promise<boolean>
  getAuthToken: () => Promise<string | null>
}

/**
 * Create auth helpers for a page
 */
export function createAuthHelpers(page: Page): AuthHelpers {
  return {
    /**
     * Login with email and password
     */
    async login(email: string, password: string): Promise<void> {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')
      
      await page.fill('input[type="email"]', email)
      await page.fill('input[type="password"]', password)
      
      // Wait for navigation after clicking submit
      await Promise.all([
        page.waitForURL(/\/(dashboard|watchlist|portfolio)/, { timeout: 10000 }),
        page.click('button[type="submit"]')
      ])
      
      // Wait for page to stabilize
      await page.waitForLoadState('networkidle')
      
      // Verify token is stored
      const token = await page.evaluate(() => localStorage.getItem('auth_token'))
      expect(token).toBeTruthy()
    },

    /**
     * Signup with email and password
     */
    async signup(email: string, password: string): Promise<void> {
      await page.goto('/signup')
      await page.waitForLoadState('networkidle')
      
      await page.fill('input[id="email"]', email)
      await page.fill('input[id="password"]', password)
      await page.fill('input[id="confirmPassword"]', password)
      
      // Wait for navigation after clicking submit
      await Promise.all([
        page.waitForURL(/\/(dashboard|watchlist|portfolio)/, { timeout: 10000 }),
        page.click('button[type="submit"]')
      ])
      
      // Wait for page to stabilize
      await page.waitForLoadState('networkidle')
      
      // Verify token is stored
      const token = await page.evaluate(() => localStorage.getItem('auth_token'))
      expect(token).toBeTruthy()
    },

    /**
     * Logout current user
     */
    async logout(): Promise<void> {
      // Click logout button
      await page.click('.btn-logout, button:has-text("로그아웃")')
      
      // Confirm if dialog appears
      page.once('dialog', dialog => dialog.accept())
      
      // Wait for navigation to login
      await page.waitForURL('/login', { timeout: 5000 })
      
      // Verify token is cleared
      const token = await page.evaluate(() => localStorage.getItem('auth_token'))
      expect(token).toBeNull()
    },

    /**
     * Check if user is logged in
     */
    async isLoggedIn(): Promise<boolean> {
      const token = await page.evaluate(() => localStorage.getItem('auth_token'))
      return token !== null
    },

    /**
     * Get current auth token
     */
    async getAuthToken(): Promise<string | null> {
      return page.evaluate(() => localStorage.getItem('auth_token'))
    },
  }
}

/**
 * Extend Playwright test with auth helpers
 */
export const test = base.extend<{ authHelpers: AuthHelpers }>({
  authHelpers: async ({ page }, use) => {
    const helpers = createAuthHelpers(page)
    await use(helpers)
  },
})

export { expect }

/**
 * Test user credentials
 */
export const TEST_USER = {
  email: 'test@example.com',
  password: 'Test1234!'
}

/**
 * Login with test user
 */
export async function loginAsTestUser(page: Page): Promise<void> {
  const helpers = createAuthHelpers(page)
  await helpers.login(TEST_USER.email, TEST_USER.password)
}

/**
 * Generate random email for testing
 */
export function generateTestEmail(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `test-${timestamp}-${random}@example.com`
}

/**
 * Generate random password for testing
 */
export function generateTestPassword(): string {
  const length = 12
  const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let password = ''
  
  // Ensure at least one uppercase, lowercase, and digit
  password += 'A'
  password += 'a'
  password += '1'
  
  for (let i = 3; i < length; i++) {
    password += charset.charAt(Math.floor(Math.random() * charset.length))
  }
  
  // Shuffle the password
  return password.split('').sort(() => Math.random() - 0.5).join('')
}

/**
 * Wait for API response
 */
export async function waitForApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  timeout = 5000
): Promise<any> {
  const responsePromise = page.waitForResponse(
    response => {
      const url = response.url()
      return typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url)
    },
    { timeout }
  )
  
  const response = await responsePromise
  return response.json()
}

/**
 * Mock API response
 */
export async function mockApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  mockData: any,
  status = 200
): Promise<void> {
  await page.route(
    url => {
      const urlString = url.toString()
      return typeof urlPattern === 'string'
        ? urlString.includes(urlPattern)
        : urlPattern.test(urlString)
    },
    route => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(mockData),
      })
    }
  )
}

/**
 * Create authenticated page with token
 */
export async function createAuthenticatedPage(
  page: Page,
  token: string
): Promise<void> {
  await page.addInitScript((tokenValue) => {
    localStorage.setItem('auth_token', tokenValue)
  }, token)
}

/**
 * Clear all storage
 */
export async function clearStorage(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
}
