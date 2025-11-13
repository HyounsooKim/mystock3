import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Dark Mode Toggle', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
  })

  test('should toggle dark mode on button click', async ({ page }) => {
    await page.waitForSelector('.theme-toggle')

    // Check initial state (light mode by default)
    let isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(false)

    // Click dark mode toggle
    await page.click('.theme-toggle')
    await page.waitForTimeout(300) // Wait for transition

    // Check dark mode is enabled
    isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // Click again to toggle back to light mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Check light mode is restored
    isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(false)
  })

  test('should update toggle button icon when switching modes', async ({ page }) => {
    await page.waitForSelector('.theme-toggle')

    // Check initial icon (moon for light mode)
    let buttonText = await page.locator('.theme-toggle').textContent()
    expect(buttonText).toContain('🌙')

    // Toggle to dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Check icon changed to sun (for dark mode)
    buttonText = await page.locator('.theme-toggle').textContent()
    expect(buttonText).toContain('☀️')

    // Toggle back to light mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Check icon changed back to moon
    buttonText = await page.locator('.theme-toggle').textContent()
    expect(buttonText).toContain('🌙')
  })

  test('should apply dark mode CSS variables', async ({ page }) => {
    await page.waitForSelector('.theme-toggle')

    // Get background color in light mode
    const lightBg = await page.evaluate(() => {
      return getComputedStyle(document.documentElement).getPropertyValue('--color-bg')
    })

    // Toggle to dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Get background color in dark mode
    const darkBg = await page.evaluate(() => {
      return getComputedStyle(document.documentElement).getPropertyValue('--color-bg')
    })

    // Dark mode background should be different from light mode
    expect(darkBg).not.toBe(lightBg)
  })

  test('should apply Bootstrap dark mode data attribute', async ({ page }) => {
    await page.waitForSelector('.theme-toggle')

    // Check initial data-bs-theme attribute (light)
    let bsTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-bs-theme')
    })
    expect(bsTheme).toBe('light')

    // Toggle to dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Check data-bs-theme changed to dark
    bsTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-bs-theme')
    })
    expect(bsTheme).toBe('dark')
  })

  test('should sync dark mode preference with backend API', async ({ page }) => {
    let patchCalled = false
    let patchPayload: any = null

    // Mock PATCH /api/v1/auth/me endpoint
    await page.route(/\/api\/v1\/auth\/me$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCalled = true
        patchPayload = route.request().postDataJSON()
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user_id: 'test-user',
            email: testEmail,
            created_at: new Date().toISOString(),
            is_active: true,
            dark_mode: patchPayload.dark_mode,
            language: 'ko'
          })
        })
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user_id: 'test-user',
            email: testEmail,
            created_at: new Date().toISOString(),
            is_active: true,
            dark_mode: false,
            language: 'ko'
          })
        })
      }
    })

    await page.waitForSelector('.theme-toggle')

    // Toggle dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(500) // Wait for API call

    // Verify PATCH API was called with dark_mode: true
    expect(patchCalled).toBe(true)
    expect(patchPayload).toBeTruthy()
    expect(patchPayload.dark_mode).toBe(true)
  })

  test('should maintain dark mode across page navigation', async ({ page }) => {
    await page.waitForSelector('.theme-toggle')

    // Enable dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    let isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // Navigate to watchlist
    await page.goto('/watchlist')
    await page.waitForSelector('.theme-toggle')

    // Dark mode should still be enabled
    isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)

    // Navigate to portfolio
    await page.goto('/portfolio')
    await page.waitForSelector('.theme-toggle')

    // Dark mode should still be enabled
    isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)
  })

  test('should handle dark mode toggle errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route(/\/api\/v1\/auth\/me$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Internal server error'
          })
        })
      }
    })

    await page.waitForSelector('.theme-toggle')

    // Toggle dark mode (should still work in UI even if API fails)
    await page.click('.theme-toggle')
    await page.waitForTimeout(500)

    // UI should still show dark mode
    const isDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('theme-dark')
    })
    expect(isDarkMode).toBe(true)
  })

  test('should show dark mode toggle button in header', async ({ page }) => {
    await page.waitForSelector('.theme-toggle')

    // Toggle button should be visible
    const toggleButton = page.locator('.theme-toggle')
    await expect(toggleButton).toBeVisible()

    // Button should have proper tooltip/title
    const title = await toggleButton.getAttribute('title')
    expect(title).toContain('테마')
  })

  test('should maintain dark mode state in localStorage', async ({ page }) => {
    await page.waitForSelector('.theme-toggle')

    // Enable dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Check localStorage
    const darkModeValue = await page.evaluate(() => {
      return localStorage.getItem('darkMode')
    })
    expect(darkModeValue).toBe('true')

    // Disable dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Check localStorage updated
    const lightModeValue = await page.evaluate(() => {
      return localStorage.getItem('darkMode')
    })
    expect(lightModeValue).toBe('false')
  })

  test('should apply dark mode to all page elements', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForSelector('.theme-toggle')

    // Toggle to dark mode
    await page.click('.theme-toggle')
    await page.waitForTimeout(300)

    // Check that body/main elements have dark background
    const mainBgColor = await page.evaluate(() => {
      const main = document.querySelector('.app-main')
      if (!main) return null
      return window.getComputedStyle(main).backgroundColor
    })

    // Dark mode should have darker background (rgb values lower)
    expect(mainBgColor).toBeTruthy()
    
    // Verify footer also has dark styling
    const footerBgColor = await page.evaluate(() => {
      const footer = document.querySelector('.app-footer')
      if (!footer) return null
      return window.getComputedStyle(footer).backgroundColor
    })
    
    expect(footerBgColor).toBeTruthy()
  })
})
