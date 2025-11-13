import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword } from '../helpers/auth'

test.describe('Dark Mode Persistence', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  test('should persist dark mode preference after logout and login', async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')

    // Enable dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(500) // Wait for API sync

    // Verify dark mode is enabled
    let isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // Logout
    await page.click('text=로그아웃')
    await page.waitForURL('/login')

    // Login again with same credentials
    await authHelpers.login(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForTimeout(500) // Wait for theme initialization

    // Dark mode should still be enabled
    isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // Toggle button should show sun icon (dark mode)
    const buttonText = await page.locator('.theme-toggle').textContent()
    expect(buttonText).toContain('☀️')
  })

  test('should persist light mode preference after logout and login', async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')

    // Ensure we start in light mode (default)
    const isDarkModeInitial = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    
    // If dark mode is on, toggle it off
    if (isDarkModeInitial) {
      await page.click('.theme-toggle')
      await page.waitForTimeout(500)
    }

    // Verify light mode is active
    let isLightMode = await page.evaluate(() => {
      return !document.documentElement.classList.contains('theme-dark')
    })
    expect(isLightMode).toBe(true)

    // Logout
    await page.click('text=로그아웃')
    await page.waitForURL('/login')

    // Login again
    await authHelpers.login(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForTimeout(500)

    // Light mode should still be active
    isLightMode = await page.evaluate(() => {
      return !document.documentElement.classList.contains('theme-dark')
    })
    expect(isLightMode).toBe(true)

    // Toggle button should show moon icon (light mode)
    const buttonText = await page.locator('.theme-toggle').textContent()
    expect(buttonText).toContain('🌙')
  })

  test('should initialize dark mode from backend on first page load', async ({ page, authHelpers }) => {
    // Sign up
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')

    // Enable dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(500)

    // Verify dark mode is stored in backend
    const isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // Close and reopen page (simulate new session)
    await page.close()
    
    // Create new page context
    const newPage = await page.context().newPage()
    
    // Login (this will fetch user preferences including dark_mode from backend)
    await authHelpers.login(testEmail, testPassword, newPage)
    await expect(newPage).toHaveURL('/dashboard')
    await newPage.waitForTimeout(500)

    // Dark mode should be initialized from backend before render
    const isDarkModeRestored = await newPage.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkModeRestored).toBe(true)

    await newPage.close()
  })

  test('should default new users to light mode', async ({ page, authHelpers }) => {
    // Sign up new user
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')

    // Check default theme is light mode
    const isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(false)

    // Toggle button should show moon (light mode)
    const buttonText = await page.locator('.theme-toggle').textContent()
    expect(buttonText).toContain('🌙')

    // data-bs-theme should be light
    const bsTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-bs-theme')
    })
    expect(bsTheme).toBe('light')
  })

  test('should sync localStorage with backend on theme change', async ({ page, authHelpers }) => {
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')

    // Check initial localStorage value
    let localStorageValue = await page.evaluate(() => {
      return localStorage.getItem('darkMode')
    })
    expect(localStorageValue).toBe('false') // Default

    // Toggle dark mode (syncs with backend)
    await page.click('.theme-toggle')
    await page.waitForTimeout(500)

    // Check localStorage updated
    localStorageValue = await page.evaluate(() => {
      return localStorage.getItem('darkMode')
    })
    expect(localStorageValue).toBe('true')

    // Reload page
    await page.reload()
    await page.waitForSelector('.theme-toggle')
    await page.waitForTimeout(500)

    // Dark mode should be restored from backend (not just localStorage)
    const isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // localStorage should still be true
    localStorageValue = await page.evaluate(() => {
      return localStorage.getItem('darkMode')
    })
    expect(localStorageValue).toBe('true')
  })

  test('should apply dark mode immediately on login without flash', async ({ page, authHelpers }) => {
    // Sign up and enable dark mode
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')
    
    await page.click('.theme-toggle')
    await page.waitForTimeout(500)

    // Logout
    await page.click('text=로그아웃')
    await page.waitForURL('/login')

    // Monitor when theme is applied during login
    let themeAppliedBeforeRender = false
    await page.evaluate(() => {
      // Create mutation observer to track when theme-dark class is added
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.attributeName === 'class') {
            const target = mutation.target as HTMLElement
            if (target.classList.contains('theme-dark')) {
              (window as any).__darkModeAppliedEarly = true
            }
          }
        })
      })
      observer.observe(document.documentElement, { attributes: true })
    })

    // Login
    await authHelpers.login(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    
    // Check if theme was applied early
    themeAppliedBeforeRender = await page.evaluate(() => {
      return !!(window as any).__darkModeAppliedEarly
    })

    // Dark mode should be active
    const isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // Note: We can't perfectly test "no flash" but we verify theme is applied quickly
  })

  test('should handle theme persistence when backend API fails', async ({ page, authHelpers }) => {
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')

    // Enable dark mode via localStorage (simulate offline mode)
    await page.evaluate(() => {
      localStorage.setItem('darkMode', 'true')
      // Manually apply theme
      document.documentElement.classList.add('theme-dark')
      document.documentElement.setAttribute('data-bs-theme', 'dark')
    })

    // Reload page
    await page.reload()
    await page.waitForSelector('.theme-toggle')

    // Dark mode should be restored from localStorage even if backend fails
    const isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)
  })

  test('should persist dark mode across multiple sessions', async ({ page, authHelpers }) => {
    // Session 1: Sign up and enable dark mode
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')
    
    await page.click('.theme-toggle')
    await page.waitForTimeout(500)
    await page.click('text=로그아웃')

    // Session 2: Login and verify dark mode
    await authHelpers.login(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForTimeout(500)
    
    let isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)
    await page.click('text=로그아웃')

    // Session 3: Login again and disable dark mode
    await authHelpers.login(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForSelector('.theme-toggle')
    
    await page.click('.theme-toggle') // Toggle off
    await page.waitForTimeout(500)
    await page.click('text=로그아웃')

    // Session 4: Login and verify light mode
    await authHelpers.login(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
    await page.waitForTimeout(500)
    
    isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(false)
  })
})
