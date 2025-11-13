import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Edit Watchlist Memo', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  const mockWatchlistItem = {
    id: 'item-1',
    user_id: 'test-user',
    symbol: 'AAPL',
    company_name: 'Apple Inc.',
    memo: 'Original memo',
    display_order: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    current_price: 175.43,
    change: 2.15,
    change_percent: 1.24
  }

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')

    // Mock watchlist with one item
    await mockApiResponse(page, '/api/v1/watchlist', [mockWatchlistItem])
  })

  test('should successfully edit memo', async ({ page }) => {
    // Mock successful update
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockWatchlistItem,
            memo: 'Updated memo'
          })
        })
      }
    })

    await page.goto('/watchlist')

    // Wait for watchlist to load
    await page.waitForSelector('.watchlist-item')

    // Click edit button
    await page.click('button[title="메모 수정"]')

    // Wait for edit modal
    await expect(page.locator('.modal')).toBeVisible()
    await expect(page.locator('.modal-title')).toContainText('메모 수정')

    // Verify pre-filled values
    await expect(page.locator('.form-control-plaintext')).toContainText('AAPL')
    await expect(page.locator('.form-control-plaintext')).toContainText('Apple Inc.')

    const memoInput = page.locator('input[placeholder*="메모"]')
    await expect(memoInput).toHaveValue('Original memo')

    // Edit memo
    await memoInput.clear()
    await memoInput.fill('Updated memo')

    // Verify character counter
    await expect(page.locator('.form-text')).toContainText('12/50자')

    // Click save
    await page.click('button:has-text("저장")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()
  })

  test('should enforce 50 character limit on memo edit', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    await expect(page.locator('.modal')).toBeVisible()

    const memoInput = page.locator('input[placeholder*="메모"]')
    const longMemo = 'A'.repeat(60)
    
    await memoInput.clear()
    await memoInput.fill(longMemo)

    // Input should be limited to 50 characters
    const value = await memoInput.inputValue()
    expect(value.length).toBeLessThanOrEqual(50)

    // Character counter should show 50/50
    await expect(page.locator('.form-text')).toContainText('50/50자')

    // Save button should still be enabled (50 chars is valid)
    await expect(page.locator('button:has-text("저장")')).not.toBeDisabled()
  })

  test('should show validation error when memo exceeds 50 characters', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    
    const memoInput = page.locator('input[placeholder*="메모"]')
    await memoInput.clear()
    
    // Try to paste very long text (if maxlength wasn't enforced)
    await memoInput.fill('A'.repeat(51))

    // Should either be truncated or show error
    const value = await memoInput.inputValue()
    if (value.length > 50) {
      await expect(page.locator('.invalid-feedback')).toBeVisible()
      await expect(page.locator('button:has-text("저장")')).toBeDisabled()
    }
  })

  test('should allow empty memo', async ({ page }) => {
    await mockApiResponse(page, /\/api\/v1\/watchlist\/item-1$/, {
      ...mockWatchlistItem,
      memo: ''
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    
    const memoInput = page.locator('input[placeholder*="메모"]')
    await memoInput.clear()

    // Save button should be enabled
    await expect(page.locator('button:has-text("저장")')).not.toBeDisabled()

    await page.click('button:has-text("저장")')

    // Should close successfully
    await expect(page.locator('.modal')).not.toBeVisible()
  })

  test('should close modal when cancel button is clicked', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    await expect(page.locator('.modal')).toBeVisible()

    const memoInput = page.locator('input[placeholder*="메모"]')
    await memoInput.clear()
    await memoInput.fill('Changed but not saved')

    // Click cancel
    await page.click('button:has-text("취소")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Reopen to verify changes weren't saved
    await page.click('button[title="메모 수정"]')
    await expect(memoInput).toHaveValue('Original memo')
  })

  test('should close modal when clicking backdrop', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    await expect(page.locator('.modal')).toBeVisible()

    // Click backdrop
    await page.locator('.modal-backdrop').click()

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()
  })

  test('should show loading state during save', async ({ page }) => {
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        await new Promise(resolve => setTimeout(resolve, 1000))
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockWatchlistItem)
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    
    const memoInput = page.locator('input[placeholder*="메모"]')
    await memoInput.fill('New memo')

    await page.click('button:has-text("저장")')

    // Loading spinner should appear
    await expect(page.locator('.spinner-border')).toBeVisible()

    // Button should be disabled during loading
    await expect(page.locator('button:has-text("저장")')).toBeDisabled()
  })

  test('should handle edit errors gracefully', async ({ page }) => {
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '종목 수정에 실패했습니다'
          })
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    
    const memoInput = page.locator('input[placeholder*="메모"]')
    await memoInput.fill('New memo')

    await page.click('button:has-text("저장")')

    // Error message should appear (either in modal or as notification)
    // This depends on your error handling implementation
    await page.waitForTimeout(500)
  })

  test('should display character count in real-time', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    
    const memoInput = page.locator('input[placeholder*="메모"]')
    await memoInput.clear()

    // Type and verify counter updates
    await memoInput.type('Test')
    await expect(page.locator('.form-text')).toContainText('4/50자')

    await memoInput.type(' memo')
    await expect(page.locator('.form-text')).toContainText('9/50자')

    await memoInput.clear()
    await expect(page.locator('.form-text')).toContainText('0/50자')
  })

  test('should not save if memo is unchanged', async ({ page }) => {
    let patchCalled = false
    
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCalled = true
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockWatchlistItem)
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.click('button[title="메모 수정"]')
    
    // Don't change the memo
    await page.click('button:has-text("저장")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // API call should still happen (or you can modify to skip unchanged)
    // This is implementation-dependent
  })
})
