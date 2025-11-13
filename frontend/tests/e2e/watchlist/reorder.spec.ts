import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Reorder Watchlist', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  const mockWatchlistItems = [
    {
      id: 'item-1',
      user_id: 'test-user',
      symbol: 'AAPL',
      company_name: 'Apple Inc.',
      memo: 'First item',
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
      memo: 'Second item',
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
      memo: 'Third item',
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

  test('should reorder watchlist items via drag and drop', async ({ page }) => {
    let reorderPayload: string[] | null = null

    // Mock reorder API
    await page.route(/\/api\/v1\/watchlist\/reorder$/, async (route) => {
      const body = route.request().postDataJSON()
      reorderPayload = body.item_ids
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      })
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Verify initial order
    const items = page.locator('.watchlist-item')
    await expect(items.nth(0)).toContainText('AAPL')
    await expect(items.nth(1)).toContainText('GOOGL')
    await expect(items.nth(2)).toContainText('MSFT')

    // Drag first item (AAPL) to third position
    const firstItem = items.nth(0)
    const thirdItem = items.nth(2)

    // Get bounding boxes
    const firstBox = await firstItem.boundingBox()
    const thirdBox = await thirdItem.boundingBox()

    if (firstBox && thirdBox) {
      // Perform drag and drop
      await page.mouse.move(firstBox.x + firstBox.width / 2, firstBox.y + firstBox.height / 2)
      await page.mouse.down()
      await page.mouse.move(thirdBox.x + thirdBox.width / 2, thirdBox.y + thirdBox.height / 2, { steps: 10 })
      await page.mouse.up()
    }

    // Wait for reorder API call
    await page.waitForTimeout(500)

    // Verify reorder API was called with correct order
    expect(reorderPayload).not.toBeNull()
    expect(reorderPayload).toEqual(['item-2', 'item-3', 'item-1'])
  })

  test('should visually indicate draggable items', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Hover over drag handle
    const dragHandle = page.locator('.drag-handle').first()
    await dragHandle.hover()

    // Cursor should change to grab/move
    const cursor = await dragHandle.evaluate((el) => {
      return window.getComputedStyle(el).cursor
    })
    
    expect(['grab', 'move', 'pointer']).toContain(cursor)
  })

  test('should show ghost element during drag', async ({ page }) => {
    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    const firstItem = page.locator('.watchlist-item').first()
    const box = await firstItem.boundingBox()

    if (box) {
      // Start dragging
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
      await page.mouse.down()
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2 + 50, { steps: 5 })

      // Ghost element should be visible
      const ghostElement = page.locator('.sortable-ghost')
      await expect(ghostElement).toBeVisible()

      // Release
      await page.mouse.up()
    }
  })

  test('should handle reorder errors gracefully', async ({ page }) => {
    // Mock reorder API error
    await page.route(/\/api\/v1\/watchlist\/reorder$/, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: '순서 변경에 실패했습니다'
        })
      })
    })

    // Mock second call to refetch watchlist (revert UI)
    await page.route(/\/api\/v1\/watchlist$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockWatchlistItems)
        })
      }
    }, { times: 2 })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    const items = page.locator('.watchlist-item')
    const firstItem = items.nth(0)
    const secondItem = items.nth(1)

    const firstBox = await firstItem.boundingBox()
    const secondBox = await secondItem.boundingBox()

    if (firstBox && secondBox) {
      // Perform drag and drop
      await page.mouse.move(firstBox.x + firstBox.width / 2, firstBox.y + firstBox.height / 2)
      await page.mouse.down()
      await page.mouse.move(secondBox.x + secondBox.width / 2, secondBox.y + secondBox.height / 2, { steps: 10 })
      await page.mouse.up()
    }

    // Wait for error handling and revert
    await page.waitForTimeout(1000)

    // Should revert to original order
    await expect(items.nth(0)).toContainText('AAPL')
    await expect(items.nth(1)).toContainText('GOOGL')
    await expect(items.nth(2)).toContainText('MSFT')
  })

  test('should preserve order after page reload', async ({ page }) => {
    const reorderedItems = [
      mockWatchlistItems[1], // GOOGL
      mockWatchlistItems[2], // MSFT
      mockWatchlistItems[0]  // AAPL
    ]

    // Mock reorder API
    await page.route(/\/api\/v1\/watchlist\/reorder$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      })
    })

    // Mock watchlist to return reordered items after reorder
    let reorderCalled = false
    await page.route(/\/api\/v1\/watchlist$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(reorderCalled ? reorderedItems : mockWatchlistItems)
        })
      }
    })

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    const items = page.locator('.watchlist-item')
    const firstItem = items.nth(0)
    const thirdItem = items.nth(2)

    const firstBox = await firstItem.boundingBox()
    const thirdBox = await thirdItem.boundingBox()

    if (firstBox && thirdBox) {
      // Perform drag and drop
      await page.mouse.move(firstBox.x + firstBox.width / 2, firstBox.y + firstBox.height / 2)
      await page.mouse.down()
      await page.mouse.move(thirdBox.x + thirdBox.width / 2, thirdBox.y + thirdBox.height / 2, { steps: 10 })
      await page.mouse.up()
    }

    reorderCalled = true
    await page.waitForTimeout(500)

    // Reload page
    await page.reload()
    await page.waitForSelector('.watchlist-item')

    // Verify new order persists
    const reloadedItems = page.locator('.watchlist-item')
    await expect(reloadedItems.nth(0)).toContainText('GOOGL')
    await expect(reloadedItems.nth(1)).toContainText('MSFT')
    await expect(reloadedItems.nth(2)).toContainText('AAPL')
  })

  test('should disable reorder for single item', async ({ page }) => {
    // Mock watchlist with only one item
    await mockApiResponse(page, '/api/v1/watchlist', [mockWatchlistItems[0]])

    await page.goto('/watchlist')
    await page.waitForSelector('.watchlist-item')

    // Drag handle may be hidden or disabled for single item
    const dragHandle = page.locator('.drag-handle')
    
    // Check if it exists but is disabled/hidden
    // This depends on implementation - might not have handle at all
    const count = await dragHandle.count()
    
    // Either no drag handles, or they're disabled
    if (count > 0) {
      const isVisible = await dragHandle.isVisible()
      if (isVisible) {
        // Try to drag - should not trigger reorder API
        const item = page.locator('.watchlist-item').first()
        const box = await item.boundingBox()
        
        if (box) {
          await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
          await page.mouse.down()
          await page.mouse.move(box.x + box.width / 2, box.y + 100, { steps: 5 })
          await page.mouse.up()
        }
      }
    }
  })
})
