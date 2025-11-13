import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Delete from Watchlist', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  const mockWatchlistItems = [
    {
      id: 'item-1',
      user_id: 'test-user',
      symbol: 'AAPL',
      company_name: 'Apple Inc.',
      memo: 'Tech giant',
      display_order: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      current_price: 175.43,
      change: 2.15,
      change_percent: 1.24
    },
    {
      id: 'item-2',
      user_id: 'test-user',
      symbol: 'GOOGL',
      company_name: 'Alphabet Inc.',
      memo: 'Search leader',
      display_order: 2,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      current_price: 142.50,
      change: -1.25,
      change_percent: -0.87
    },
    {
      id: 'item-3',
      user_id: 'test-user',
      symbol: 'MSFT',
      company_name: 'Microsoft Corp.',
      memo: 'Cloud services',
      display_order: 3,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      current_price: 378.91,
      change: 5.43,
      change_percent: 1.45
    }
  ]

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')

    // Mock watchlist with three items
    await mockApiResponse(page, '/api/v1/watchlist', mockWatchlistItems)
  })

  test('should successfully delete a watchlist item', async ({ page }) => {
    let deleteCallMade = false

    // Mock delete API
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCallMade = true
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        })
      }
    })

    // Mock refetch after delete
    await page.route(/\/api\/v1\/watchlist$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(deleteCallMade ? mockWatchlistItems.slice(1) : mockWatchlistItems)
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Verify initial count
    const items = page.locator('.watchlist-item')
    await expect(items).toHaveCount(3)

    // Click delete button for first item
    const deleteButton = page.locator('button[title="삭제"]').first()
    await deleteButton.click()

    // Confirm modal should appear
    await expect(page.locator('.modal')).toBeVisible()
    await expect(page.locator('.modal-body')).toContainText('정말 삭제하시겠습니까?')
    await expect(page.locator('.modal-body')).toContainText('AAPL')
    await expect(page.locator('.modal-body')).toContainText('Apple Inc.')

    // Click confirm
    await page.click('button:has-text("삭제")')

    // Wait for delete to complete
    await page.waitForTimeout(500)

    // Verify item was removed
    await expect(items).toHaveCount(2)
    await expect(page.locator('.watchlist-item')).not.toContainText('AAPL')

    // Verify delete API was called
    expect(deleteCallMade).toBe(true)
  })

  test('should cancel delete when cancel button is clicked', async ({ page }) => {
    let deleteCallMade = false

    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCallMade = true
        await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Click delete button
    await page.locator('button[title="삭제"]').first().click()

    // Modal should appear
    await expect(page.locator('.modal')).toBeVisible()

    // Click cancel
    await page.click('button:has-text("취소")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify all items still present
    await expect(page.locator('.watchlist-item')).toHaveCount(3)

    // Delete API should not have been called
    expect(deleteCallMade).toBe(false)
  })

  test('should cancel delete when clicking backdrop', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Click delete button
    await page.locator('button[title="삭제"]').first().click()

    // Modal should appear
    await expect(page.locator('.modal')).toBeVisible()

    // Click backdrop
    await page.locator('.modal-backdrop').click()

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // All items should still be present
    await expect(page.locator('.watchlist-item')).toHaveCount(3)
  })

  test('should show loading state during delete', async ({ page }) => {
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await new Promise(resolve => setTimeout(resolve, 1000))
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.locator('button[title="삭제"]').first().click()
    await expect(page.locator('.modal')).toBeVisible()

    await page.click('button:has-text("삭제")')

    // Loading spinner should appear
    await expect(page.locator('.spinner-border')).toBeVisible()

    // Delete button should be disabled
    await expect(page.locator('button:has-text("삭제")')).toBeDisabled()

    // Cancel button should be disabled during loading
    await expect(page.locator('button:has-text("취소")')).toBeDisabled()
  })

  test('should handle delete errors gracefully', async ({ page }) => {
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '종목 삭제에 실패했습니다'
          })
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.locator('button[title="삭제"]').first().click()
    await expect(page.locator('.modal')).toBeVisible()

    await page.click('button:has-text("삭제")')

    // Wait for error handling
    await page.waitForTimeout(500)

    // Error message should appear (either in modal or as notification)
    // This depends on your error handling implementation

    // Items should still be present (delete failed)
    await expect(page.locator('.watchlist-item')).toHaveCount(3)
  })

  test('should handle 404 error when item not found', async ({ page }) => {
    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '종목을 찾을 수 없습니다'
          })
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    await page.locator('button[title="삭제"]').first().click()
    await page.click('button:has-text("삭제")')

    await page.waitForTimeout(500)

    // Should show appropriate error message
    // Could either show error or remove item from UI since it doesn't exist
  })

  test('should delete correct item when multiple items exist', async ({ page }) => {
    let deletedItemId: string | null = null

    await page.route(/\/api\/v1\/watchlist\/[\w-]+$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        const url = route.request().url()
        deletedItemId = url.split('/').pop() || null
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Delete second item (GOOGL)
    const deleteButtons = page.locator('button[title="삭제"]')
    await deleteButtons.nth(1).click()

    await expect(page.locator('.modal-body')).toContainText('GOOGL')
    await page.click('button:has-text("삭제")')

    await page.waitForTimeout(500)

    // Verify correct item ID was deleted
    expect(deletedItemId).toBe('item-2')
  })

  test('should show empty state after deleting all items', async ({ page }) => {
    let itemsRemaining = [...mockWatchlistItems]

    await page.route(/\/api\/v1\/watchlist\/[\w-]+$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        const url = route.request().url()
        const itemId = url.split('/').pop()
        itemsRemaining = itemsRemaining.filter(item => item.id !== itemId)
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        })
      }
    })

    await page.route(/\/api\/v1\/watchlist$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(itemsRemaining)
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Delete all three items
    for (let i = 0; i < 3; i++) {
      await page.locator('button[title="삭제"]').first().click()
      await page.click('button:has-text("삭제")')
      await page.waitForTimeout(300)
    }

    // Empty state should be shown
    await expect(page.locator('.empty-state')).toBeVisible()
    await expect(page.locator('.empty-state')).toContainText('관심종목이 없습니다')
  })

  test('should update display order after delete', async ({ page }) => {
    let itemsAfterDelete = [mockWatchlistItems[1], mockWatchlistItems[2]]

    await page.route(/\/api\/v1\/watchlist\/item-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        })
      }
    })

    await page.route(/\/api\/v1\/watchlist$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(itemsAfterDelete)
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Delete first item
    await page.locator('button[title="삭제"]').first().click()
    await page.click('button:has-text("삭제")')
    await page.waitForTimeout(500)

    // Verify remaining items are in correct order
    const items = page.locator('.watchlist-item')
    await expect(items.nth(0)).toContainText('GOOGL')
    await expect(items.nth(1)).toContainText('MSFT')
  })
})
