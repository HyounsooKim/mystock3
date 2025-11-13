import { test, expect } from '../helpers/auth'
import { loginAsTestUser, mockApiResponse } from '../helpers/auth'

test.describe('Add Stock to Watchlist', () => {
  test.beforeEach(async ({ page }) => {
    // Login with test user
    await loginAsTestUser(page)

    // Mock empty watchlist initially
    await mockApiResponse(page, '/api/v1/watchlist', [])
  })

  test('should successfully add a stock to watchlist', async ({ page }) => {
    // Mock search results
    await mockApiResponse(page, '/api/v1/stocks/search', [
      { symbol: 'AAPL', company_name: 'Apple Inc.', match_score: 0.95 }
    ])

    // Mock add to watchlist success
    await mockApiResponse(page, '/api/v1/watchlist', {
      id: 'test-id-1',
      user_id: 'test-user',
      symbol: 'AAPL',
      company_name: 'Apple Inc.',
      memo: 'Great tech stock',
      display_order: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }, 201)

    // Navigate to watchlist
    await page.goto('/watchlist')

    // Click add stock button
    await page.click('button:has-text("종목 추가")')

    // Wait for modal
    await expect(page.locator('.modal')).toBeVisible()

    // Enter symbol
    const symbolInput = page.locator('input[placeholder*="AAPL"]')
    await symbolInput.fill('AAPL')

    // Enter company name
    const companyInput = page.locator('input[placeholder*="Apple"]')
    await companyInput.fill('Apple Inc.')

    // Enter memo
    const memoInput = page.locator('input[placeholder*="메모"]')
    await memoInput.fill('Great tech stock')

    // Verify character counter
    await expect(page.locator('.form-text')).toContainText('16/50자')

    // Submit
    await page.click('button:has-text("추가")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Success notification or table update would be visible
    // (depends on implementation)
  })

  test('should show error when adding duplicate stock', async ({ page }) => {
    // Mock duplicate error
    await page.route(/\/api\/v1\/watchlist$/, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '이미 관심종목에 추가된 종목입니다'
          })
        })
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        })
      }
    })

    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    await page.locator('input[placeholder*="AAPL"]').fill('AAPL')
    await page.locator('input[placeholder*="Apple"]').fill('Apple Inc.')
    await page.click('button:has-text("추가")')

    // Wait for error message
    await expect(page.locator('.alert-danger')).toBeVisible()
    await expect(page.locator('.alert-danger')).toContainText('이미 관심종목에 추가된 종목입니다')
  })

  test('should enforce 50 character limit on memo', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    const memoInput = page.locator('input[placeholder*="메모"]')
    const longMemo = 'A'.repeat(60)
    
    await memoInput.fill(longMemo)

    // Input should be limited to 50 characters
    const value = await memoInput.inputValue()
    expect(value.length).toBeLessThanOrEqual(50)

    // Character counter should show 50/50
    await expect(page.locator('.form-text')).toContainText('50/50자')
  })

  test('should validate required fields', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    // Try to submit without filling required fields
    const addButton = page.locator('button:has-text("추가")')
    
    // Button should be disabled initially
    await expect(addButton).toBeDisabled()

    // Fill symbol only
    await page.locator('input[placeholder*="AAPL"]').fill('AAPL')
    await expect(addButton).toBeDisabled()

    // Fill company name
    await page.locator('input[placeholder*="Apple"]').fill('Apple Inc.')
    
    // Now button should be enabled
    await expect(addButton).not.toBeDisabled()
  })

  test('should convert symbol to uppercase automatically', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    const symbolInput = page.locator('input[placeholder*="AAPL"]')
    await symbolInput.fill('aapl')

    // Should be converted to uppercase
    await expect(symbolInput).toHaveValue('AAPL')
  })

  test('should validate symbol format (1-5 uppercase letters)', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    const symbolInput = page.locator('input[placeholder*="AAPL"]')
    
    // Try invalid symbols
    await symbolInput.fill('123')
    await symbolInput.blur()
    
    // Should show validation error
    await expect(page.locator('.invalid-feedback')).toBeVisible()

    // Try valid symbol
    await symbolInput.fill('AAPL')
    await symbolInput.blur()
    
    // Error should disappear
    await expect(page.locator('.invalid-feedback')).not.toBeVisible()
  })

  test('should close modal when cancel button is clicked', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    await expect(page.locator('.modal')).toBeVisible()

    // Click cancel
    await page.click('button:has-text("취소")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()
  })

  test('should close modal when clicking backdrop', async ({ page }) => {
    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    await expect(page.locator('.modal')).toBeVisible()

    // Click backdrop
    await page.locator('.modal-backdrop').click()

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()
  })

  test('should show loading state during submission', async ({ page }) => {
    // Delay API response
    await page.route(/\/api\/v1\/watchlist$/, async (route) => {
      if (route.request().method() === 'POST') {
        await new Promise(resolve => setTimeout(resolve, 1000))
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'test-id',
            symbol: 'AAPL',
            company_name: 'Apple Inc.',
            memo: '',
            display_order: 1
          })
        })
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        })
      }
    })

    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    await page.locator('input[placeholder*="AAPL"]').fill('AAPL')
    await page.locator('input[placeholder*="Apple"]').fill('Apple Inc.')
    
    // Click submit
    await page.click('button:has-text("추가")')

    // Loading spinner should appear
    await expect(page.locator('.spinner-border')).toBeVisible()

    // Button should be disabled during loading
    await expect(page.locator('button:has-text("추가")')).toBeDisabled()
  })

  test('should clear form after successful submission', async ({ page }) => {
    await mockApiResponse(page, '/api/v1/watchlist', {
      id: 'test-id',
      symbol: 'AAPL',
      company_name: 'Apple Inc.',
      memo: 'Test',
      display_order: 1
    }, 201)

    await page.goto('/watchlist')
    await page.click('button:has-text("종목 추가")')

    await page.locator('input[placeholder*="AAPL"]').fill('AAPL')
    await page.locator('input[placeholder*="Apple"]').fill('Apple Inc.')
    await page.locator('input[placeholder*="메모"]').fill('Test')

    await page.click('button:has-text("추가")')

    // Wait for modal to close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Open modal again
    await page.click('button:has-text("종목 추가")')

    // Form should be reset
    await expect(page.locator('input[placeholder*="AAPL"]')).toHaveValue('')
    await expect(page.locator('input[placeholder*="Apple"]')).toHaveValue('')
    await expect(page.locator('input[placeholder*="메모"]')).toHaveValue('')
  })
})
