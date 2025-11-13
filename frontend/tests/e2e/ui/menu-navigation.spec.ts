import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword } from '../helpers/auth'

test.describe('Menu Navigation Highlighting', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')
  })

  test('should highlight dashboard menu when on dashboard page', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForSelector('.nav-menu')

    // Dashboard link should have active class
    const dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    await expect(dashboardLink).toHaveClass(/active/)

    // Other links should not have active class
    const watchlistLink = page.locator('.nav-menu a[href="/watchlist"]')
    await expect(watchlistLink).not.toHaveClass(/active/)

    const portfolioLink = page.locator('.nav-menu a[href="/portfolio"]')
    await expect(portfolioLink).not.toHaveClass(/active/)
  })

  test('should highlight watchlist menu when on watchlist page', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.nav-menu')

    // Watchlist link should have active class
    const watchlistLink = page.locator('.nav-menu a[href="/watchlist"]')
    await expect(watchlistLink).toHaveClass(/active/)

    // Other links should not have active class
    const dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    await expect(dashboardLink).not.toHaveClass(/active/)

    const portfolioLink = page.locator('.nav-menu a[href="/portfolio"]')
    await expect(portfolioLink).not.toHaveClass(/active/)
  })

  test('should highlight portfolio menu when on portfolio page', async ({ page }) => {
    await page.goto('/portfolio')
    await page.waitForSelector('.nav-menu')

    // Portfolio link should have active class
    const portfolioLink = page.locator('.nav-menu a[href="/portfolio"]')
    await expect(portfolioLink).toHaveClass(/active/)

    // Other links should not have active class
    const dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    await expect(dashboardLink).not.toHaveClass(/active/)

    const watchlistLink = page.locator('.nav-menu a[href="/watchlist"]')
    await expect(watchlistLink).not.toHaveClass(/active/)
  })

  test('should update active menu when navigating between pages', async ({ page }) => {
    // Start on dashboard
    await page.goto('/dashboard')
    await page.waitForSelector('.nav-menu')

    let dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    await expect(dashboardLink).toHaveClass(/active/)

    // Click watchlist
    await page.click('.nav-menu a[href="/watchlist"]')
    await page.waitForURL('/watchlist')

    const watchlistLink = page.locator('.nav-menu a[href="/watchlist"]')
    await expect(watchlistLink).toHaveClass(/active/)
    await expect(dashboardLink).not.toHaveClass(/active/)

    // Click portfolio
    await page.click('.nav-menu a[href="/portfolio"]')
    await page.waitForURL('/portfolio')

    const portfolioLink = page.locator('.nav-menu a[href="/portfolio"]')
    await expect(portfolioLink).toHaveClass(/active/)
    await expect(watchlistLink).not.toHaveClass(/active/)

    // Click back to dashboard
    await page.click('.nav-menu a[href="/dashboard"]')
    await page.waitForURL('/dashboard')

    dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    await expect(dashboardLink).toHaveClass(/active/)
    await expect(portfolioLink).not.toHaveClass(/active/)
  })

  test('should maintain active menu after page reload', async ({ page }) => {
    // Navigate to watchlist
    await page.goto('/watchlist')
    await page.waitForSelector('.nav-menu')

    const watchlistLink = page.locator('.nav-menu a[href="/watchlist"]')
    await expect(watchlistLink).toHaveClass(/active/)

    // Reload page
    await page.reload()
    await page.waitForSelector('.nav-menu')

    // Watchlist should still be active
    await expect(watchlistLink).toHaveClass(/active/)

    const dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    await expect(dashboardLink).not.toHaveClass(/active/)
  })

  test('should show active menu with correct styling', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForSelector('.nav-menu')

    const dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    
    // Check that active link has visible styling (bold font or different background)
    const fontWeight = await dashboardLink.evaluate((el) => {
      return window.getComputedStyle(el).fontWeight
    })
    
    // Active link should have bolder font (typically 700 or 'bold')
    expect(parseInt(fontWeight)).toBeGreaterThanOrEqual(600)
  })

  test('should not show menu highlighting when not authenticated', async ({ page }) => {
    // Logout
    await page.click('button.btn-logout')
    await page.waitForURL('/login')

    // Try to access dashboard (should redirect to login)
    await page.goto('/dashboard')
    await page.waitForURL('/login')

    // Nav menu should not be visible
    const navMenu = page.locator('.nav-menu')
    await expect(navMenu).not.toBeVisible()
  })

  test('should handle navigation via browser back button', async ({ page }) => {
    // Navigate: dashboard -> watchlist -> portfolio
    await page.goto('/dashboard')
    await page.goto('/watchlist')
    await page.goto('/portfolio')
    
    await page.waitForSelector('.nav-menu')
    let portfolioLink = page.locator('.nav-menu a[href="/portfolio"]')
    await expect(portfolioLink).toHaveClass(/active/)

    // Browser back to watchlist
    await page.goBack()
    await page.waitForURL('/watchlist')
    
    const watchlistLink = page.locator('.nav-menu a[href="/watchlist"]')
    await expect(watchlistLink).toHaveClass(/active/)
    await expect(portfolioLink).not.toHaveClass(/active/)

    // Browser back to dashboard
    await page.goBack()
    await page.waitForURL('/dashboard')
    
    const dashboardLink = page.locator('.nav-menu a[href="/dashboard"]')
    await expect(dashboardLink).toHaveClass(/active/)
    await expect(watchlistLink).not.toHaveClass(/active/)
  })
})
