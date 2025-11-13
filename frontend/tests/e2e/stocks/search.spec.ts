import { test, expect } from '../helpers/auth'
import { loginAsTestUser, mockApiResponse } from '../helpers/auth'

test.describe('Stock Search Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login with test user
    await loginAsTestUser(page)
  })

  test('should search for stocks and display results', async ({ page }) => {
    // Mock stock search API response
    await mockApiResponse(
      page,
      '/api/v1/stocks/search',
      [
        {
          symbol: 'AAPL',
          company_name: 'Apple Inc.',
          match_score: 0.95
        },
        {
          symbol: 'GOOGL',
          company_name: 'Alphabet Inc.',
          match_score: 0.85
        }
      ]
    )

    // Navigate to a page with stock search
    await page.goto('/watchlist')
    
    // Click add stock button to open modal
    await page.click('button:has-text("종목 추가")')
    
    // Wait for modal to appear
    await expect(page.locator('.modal')).toBeVisible()
    
    // Enter search query
    const searchInput = page.locator('input[placeholder*="종목명"]')
    await searchInput.fill('AAPL')
    
    // Wait for debounced search (500ms)
    await page.waitForTimeout(600)
    
    // Verify search results appear
    await expect(page.locator('.result-item')).toHaveCount(2)
    
    // Verify first result
    const firstResult = page.locator('.result-item').first()
    await expect(firstResult.locator('.result-symbol')).toHaveText('AAPL')
    await expect(firstResult.locator('.result-name')).toHaveText('Apple Inc.')
    
    // Verify second result
    const secondResult = page.locator('.result-item').nth(1)
    await expect(secondResult.locator('.result-symbol')).toHaveText('GOOGL')
    await expect(secondResult.locator('.result-name')).toHaveText('Alphabet Inc.')
  })

  test('should show no results message when search returns empty', async ({ page }) => {
    // Mock empty search response
    await mockApiResponse(page, '/api/v1/stocks/search', [])

    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')
    
    const searchInput = page.locator('input[placeholder*="종목명"]')
    await searchInput.fill('INVALIDSTOCK')
    await page.waitForTimeout(600)
    
    // Verify no results message
    await expect(page.locator('.no-results')).toBeVisible()
    await expect(page.locator('.no-results')).toContainText('검색 결과가 없습니다')
  })

  test('should clear search results when input is cleared', async ({ page }) => {
    // Mock search response
    await mockApiResponse(page, '/api/v1/stocks/search', [
      { symbol: 'AAPL', company_name: 'Apple Inc.', match_score: 0.95 }
    ])

    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')
    
    const searchInput = page.locator('input[placeholder*="종목명"]')
    await searchInput.fill('AAPL')
    await page.waitForTimeout(600)
    
    // Results should appear
    await expect(page.locator('.result-item')).toHaveCount(1)
    
    // Clear input
    await searchInput.clear()
    
    // Results should disappear
    await expect(page.locator('.result-item')).toHaveCount(0)
  })

  test('should handle search API errors gracefully', async ({ page }) => {
    // Mock API error
    await mockApiResponse(
      page,
      '/api/v1/stocks/search',
      { detail: '검색 중 오류가 발생했습니다' },
      500
    )

    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')
    
    const searchInput = page.locator('input[placeholder*="종목명"]')
    await searchInput.fill('AAPL')
    await page.waitForTimeout(600)
    
    // Verify error message is displayed
    await expect(page.locator('.invalid-feedback')).toBeVisible()
    await expect(page.locator('.invalid-feedback')).toContainText('오류')
  })

  test('should convert symbol input to uppercase', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')
    
    const symbolInput = page.locator('input[placeholder*="AAPL"]')
    await symbolInput.fill('aapl')
    
    // Verify it's converted to uppercase
    await expect(symbolInput).toHaveValue('AAPL')
  })

  test('should validate symbol length (1-5 characters)', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')
    
    const symbolInput = page.locator('input[placeholder*="AAPL"]')
    
    // Try to enter more than 5 characters
    await symbolInput.fill('TOOLONG')
    
    // Input should be limited to 5 characters
    const value = await symbolInput.inputValue()
    expect(value.length).toBeLessThanOrEqual(5)
  })
})
