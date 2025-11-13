import { test, expect } from '../helpers/auth'
import { loginAsTestUser, mockApiResponse } from '../helpers/auth'

test.describe('Stock Quote Display', () => {
  const mockQuoteData = {
    symbol: 'AAPL',
    company_name: 'Apple Inc.',
    current_price: 175.43,
    change: 2.15,
    change_percent: 1.24,
    open: 173.28,
    high: 176.12,
    low: 172.95,
    volume: 52847293,
    last_updated: new Date().toISOString(),
    currency: 'USD'
  }

  test.beforeEach(async ({ page }) => {
    // Login with test user
    await loginAsTestUser(page)
  })

  test('should display stock quote with all details', async ({ page }) => {
    // Mock quote API
    await mockApiResponse(page, '/api/v1/stocks/AAPL/quote', mockQuoteData)

    // Navigate to watchlist (assumes watchlist displays quotes)
    await page.goto('/watchlist')
    
    // Add a stock to watchlist first (if needed)
    // For this test, we'll assume the quote component is rendered somewhere

    // Wait for quote to load
    await page.waitForSelector('.stock-quote', { timeout: 5000 })

    // Verify symbol and company name
    await expect(page.locator('.quote-title .symbol')).toContainText('AAPL')
    await expect(page.locator('.quote-title .company-name')).toContainText('Apple Inc.')

    // Verify current price
    const currentPrice = page.locator('.current-price')
    await expect(currentPrice).toBeVisible()
    await expect(currentPrice).toContainText('175.43')

    // Verify price change (positive)
    const priceChange = page.locator('.price-change')
    await expect(priceChange).toBeVisible()
    await expect(priceChange).toContainText('+2.15')
    await expect(priceChange).toContainText('+1.24%')
    await expect(priceChange).toHaveClass(/positive/)

    // Verify quote details
    await expect(page.locator('.detail-item').filter({ hasText: '시가' })).toContainText('173.28')
    await expect(page.locator('.detail-item').filter({ hasText: '고가' })).toContainText('176.12')
    await expect(page.locator('.detail-item').filter({ hasText: '저가' })).toContainText('172.95')
    await expect(page.locator('.detail-item').filter({ hasText: '거래량' })).toBeVisible()
  })

  test('should show negative price change in red', async ({ page }) => {
    const negativeQuote = {
      ...mockQuoteData,
      change: -3.25,
      change_percent: -1.82
    }

    await mockApiResponse(page, '/api/v1/stocks/AAPL/quote', negativeQuote)
    await page.goto('/watchlist')
    
    await page.waitForSelector('.stock-quote')

    const priceChange = page.locator('.price-change')
    await expect(priceChange).toContainText('-3.25')
    await expect(priceChange).toContainText('-1.82%')
    await expect(priceChange).toHaveClass(/negative/)
  })

  test('should show neutral price change for no change', async ({ page }) => {
    const neutralQuote = {
      ...mockQuoteData,
      change: 0,
      change_percent: 0
    }

    await mockApiResponse(page, '/api/v1/stocks/AAPL/quote', neutralQuote)
    await page.goto('/watchlist')
    
    await page.waitForSelector('.stock-quote')

    const priceChange = page.locator('.price-change')
    await expect(priceChange).toContainText('0.00')
    await expect(priceChange).toHaveClass(/neutral/)
  })

  test('should refresh quote when refresh button is clicked', async ({ page }) => {
    let callCount = 0
    const updatedQuote = { ...mockQuoteData, current_price: 176.50 }

    // Mock API with different responses
    await page.route(/\/api\/v1\/stocks\/AAPL\/quote/, async (route) => {
      callCount++
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(callCount === 1 ? mockQuoteData : updatedQuote)
      })
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.stock-quote')

    // Initial price
    await expect(page.locator('.current-price')).toContainText('175.43')

    // Click refresh button
    const refreshButton = page.locator('button[title="새로고침"]')
    await refreshButton.click()

    // Wait for updated price
    await page.waitForTimeout(500)
    await expect(page.locator('.current-price')).toContainText('176.50')
  })

  test('should display loading spinner while fetching quote', async ({ page }) => {
    // Delay the API response
    await page.route(/\/api\/v1\/stocks\/AAPL\/quote/, async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockQuoteData)
      })
    })

    await page.goto('/watchlist')

    // Loading spinner should be visible
    await expect(page.locator('.quote-loading .spinner-border')).toBeVisible()
    await expect(page.locator('.quote-loading')).toContainText('시세 정보를 불러오는 중')

    // Wait for quote to load
    await page.waitForSelector('.stock-quote .quote-content', { timeout: 3000 })
    
    // Loading should be gone
    await expect(page.locator('.quote-loading')).not.toBeVisible()
  })

  test('should display error message when quote fetch fails', async ({ page }) => {
    await mockApiResponse(
      page,
      '/api/v1/stocks/INVALID/quote',
      { detail: '종목을 찾을 수 없음' },
      404
    )

    await page.goto('/watchlist')
    
    // Wait for error to appear
    await page.waitForSelector('.alert-danger', { timeout: 3000 })

    // Verify error message
    await expect(page.locator('.alert-danger')).toBeVisible()
    await expect(page.locator('.alert-danger')).toContainText('종목을 찾을 수 없음')
  })

  test('should format volume numbers correctly', async ({ page }) => {
    const highVolumeQuote = {
      ...mockQuoteData,
      volume: 125430000 // 125.43M
    }

    await mockApiResponse(page, '/api/v1/stocks/AAPL/quote', highVolumeQuote)
    await page.goto('/watchlist')
    
    await page.waitForSelector('.stock-quote')

    // Volume should be formatted as millions
    const volumeDetail = page.locator('.detail-item').filter({ hasText: '거래량' })
    await expect(volumeDetail).toContainText('M')
  })

  test('should display last updated timestamp', async ({ page }) => {
    await mockApiResponse(page, '/api/v1/stocks/AAPL/quote', mockQuoteData)
    await page.goto('/watchlist')
    
    await page.waitForSelector('.stock-quote')

    // Last updated should be visible
    const footer = page.locator('.quote-footer')
    await expect(footer).toBeVisible()
    await expect(footer).toContainText('마지막 업데이트')
  })

  test('should handle rate limit error (429)', async ({ page }) => {
    await mockApiResponse(
      page,
      '/api/v1/stocks/AAPL/quote',
      { detail: 'API 호출 한도 초과. 잠시 후 다시 시도해주세요.' },
      429
    )

    await page.goto('/watchlist')
    
    // Wait for error
    await page.waitForSelector('.alert-danger', { timeout: 3000 })

    // Verify rate limit error message
    await expect(page.locator('.alert-danger')).toContainText('호출 한도 초과')
  })
})
