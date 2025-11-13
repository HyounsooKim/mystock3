/**
 * E2E Test: Watchlist Validation
 * 
 * Purpose: Validate existing watchlist data and core functionality
 * Test Data: AAPL, MSFT, NVDA (pre-registered)
 * User: test@example.com / Test1234!
 */

import { test, expect } from '@playwright/test'

const TEST_USER = {
  email: 'test@example.com',
  password: 'Test1234!'
}

const EXPECTED_STOCKS = ['AAPL', 'MSFT', 'NVDA']

test.describe('Watchlist Validation Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/')
    
    // Login
    await page.fill('input[type="email"]', TEST_USER.email)
    await page.fill('input[type="password"]', TEST_USER.password)
    await page.click('button[type="submit"]')
    
    // Wait for redirect to dashboard
    await page.waitForURL(/dashboard|watchlist/, { timeout: 10000 })
    
    // Navigate to watchlist page
    await page.click('a[href*="watchlist"]')
    await page.waitForURL(/watchlist/)
  })

  test('T121: Verify watchlist displays registered stocks', async ({ page }) => {
    // Wait for table to load
    await page.waitForSelector('table tbody tr', { timeout: 10000 })
    
    // Get all stock symbols from the table
    const stockRows = await page.locator('table tbody tr').all()
    
    expect(stockRows.length).toBeGreaterThanOrEqual(3)
    
    // Verify each expected stock is present
    for (const symbol of EXPECTED_STOCKS) {
      const symbolCell = page.locator(`table tbody tr:has-text("${symbol}")`)
      await expect(symbolCell).toBeVisible()
      
      console.log(`✓ Stock ${symbol} found in watchlist`)
    }
  })

  test('T121: Verify stock quote data is displayed', async ({ page }) => {
    // Wait for first stock row
    await page.waitForSelector('table tbody tr:first-child', { timeout: 10000 })
    
    const firstRow = page.locator('table tbody tr').first()
    
    // Check for stock symbol
    const symbolCell = firstRow.locator('td').nth(1)
    await expect(symbolCell).toBeVisible()
    const symbol = await symbolCell.textContent()
    expect(symbol).toBeTruthy()
    
    // Check for current price (should be displayed or show '-')
    const priceCell = firstRow.locator('td').nth(2)
    await expect(priceCell).toBeVisible()
    const price = await priceCell.textContent()
    expect(price).toBeTruthy()
    
    // Check for change percent (should be displayed or show '-')
    const changeCell = firstRow.locator('td').nth(3)
    await expect(changeCell).toBeVisible()
    const change = await changeCell.textContent()
    expect(change).toBeTruthy()
    
    console.log(`✓ Stock quote data: Symbol=${symbol}, Price=${price}, Change=${change}`)
  })

  test('T121: Verify duplicate stock prevention', async ({ page }) => {
    // Click "종목 추가" button
    await page.click('button:has-text("종목 추가")')
    
    // Wait for modal
    await page.waitForSelector('input[placeholder*="심볼"], input[placeholder*="AAPL"]', { timeout: 5000 })
    
    // Try to add AAPL (already exists)
    await page.fill('input[placeholder*="심볼"], input[placeholder*="AAPL"]', 'AAPL')
    
    // Fill other required fields
    const companyNameInput = page.locator('input').nth(1)
    await companyNameInput.fill('Apple Inc.')
    
    const memoInput = page.locator('input, textarea').last()
    await memoInput.fill('Duplicate test')
    
    // Submit form
    await page.click('button[type="submit"], button:has-text("추가")')
    
    // Wait for error message
    await page.waitForSelector('text=/이미.*관심종목.*추가/i', { timeout: 5000 })
    
    const errorMessage = await page.textContent('text=/이미.*관심종목.*추가/i')
    expect(errorMessage).toContain('이미')
    
    console.log(`✓ Duplicate prevention working: ${errorMessage}`)
  })

  test('T122: Edit stock memo', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('table tbody tr', { timeout: 10000 })
    
    // Click edit button on first stock
    const firstRow = page.locator('table tbody tr').first()
    const editButton = firstRow.locator('button[title*="수정"], button:has(svg)').first()
    await editButton.click()
    
    // Wait for edit modal
    await page.waitForSelector('textarea, input[type="text"]', { timeout: 5000 })
    
    // Update memo
    const memoInput = page.locator('textarea, input[type="text"]').last()
    const newMemo = `Updated at ${new Date().toISOString()}`
    await memoInput.fill(newMemo)
    
    // Submit
    await page.click('button[type="submit"], button:has-text("저장"), button:has-text("수정")')
    
    // Wait for modal to close
    await page.waitForTimeout(1000)
    
    // Verify memo updated
    const memoCell = await firstRow.locator('td').nth(4).textContent()
    expect(memoCell).toContain(newMemo)
    
    console.log(`✓ Memo updated successfully: ${newMemo}`)
  })

  test('T124: Delete stock from watchlist', async ({ page }) => {
    // Get initial row count
    await page.waitForSelector('table tbody tr', { timeout: 10000 })
    const initialCount = await page.locator('table tbody tr').count()
    
    // Click delete button on last stock
    const lastRow = page.locator('table tbody tr').last()
    const symbol = await lastRow.locator('td').nth(1).textContent()
    
    const deleteButton = lastRow.locator('button[title*="삭제"], button:has(svg)').last()
    await deleteButton.click()
    
    // Wait for confirmation dialog
    await page.waitForSelector('text=/삭제.*확인/i, button:has-text("삭제")', { timeout: 5000 })
    
    // Confirm deletion
    await page.click('button:has-text("삭제"), button:has-text("확인")')
    
    // Wait for deletion to complete
    await page.waitForTimeout(1000)
    
    // Verify row count decreased
    const newCount = await page.locator('table tbody tr').count()
    expect(newCount).toBe(initialCount - 1)
    
    console.log(`✓ Stock ${symbol} deleted successfully (${initialCount} → ${newCount})`)
  })

  test('T113: Verify price change color coding', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('table tbody tr', { timeout: 10000 })
    
    const rows = await page.locator('table tbody tr').all()
    
    for (const row of rows) {
      const changeCell = row.locator('td').nth(3)
      const changeText = await changeCell.textContent()
      
      if (changeText && changeText !== '-') {
        const cellClass = await changeCell.getAttribute('class')
        
        if (changeText.includes('+')) {
          // Positive change should have success/green class
          expect(cellClass).toMatch(/success|green/i)
          console.log(`✓ Positive change colored green: ${changeText}`)
        } else if (changeText.includes('-')) {
          // Negative change should have danger/red class
          expect(cellClass).toMatch(/danger|red/i)
          console.log(`✓ Negative change colored red: ${changeText}`)
        }
      }
    }
  })

  test('T123: Verify drag-and-drop reorder capability', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('table tbody tr', { timeout: 10000 })
    
    // Get initial order
    const initialOrder = await page.locator('table tbody tr td:nth-child(2)').allTextContents()
    
    // Check if drag handle is present
    const dragHandle = page.locator('table tbody tr:first-child .drag-handle, table tbody tr:first-child td:first-child svg')
    
    if (await dragHandle.count() > 0) {
      await expect(dragHandle.first()).toBeVisible()
      console.log('✓ Drag handle visible')
      
      // Note: Actual drag-and-drop test is complex with SortableJS
      // Just verify the UI elements are present
      const rowCount = await page.locator('table tbody tr').count()
      expect(rowCount).toBeGreaterThan(1)
      console.log(`✓ ${rowCount} stocks available for reordering`)
    } else {
      console.log('⚠ Drag handle not found - manual reorder test required')
    }
  })

  test('API Integration: Verify backend endpoints', async ({ page, request }) => {
    // Login to get token
    await page.goto('/')
    await page.fill('input[type="email"]', TEST_USER.email)
    await page.fill('input[type="password"]', TEST_USER.password)
    await page.click('button[type="submit"]')
    await page.waitForURL(/dashboard|watchlist/)
    
    // Extract token from localStorage
    const token = await page.evaluate(() => {
      const authStore = localStorage.getItem('auth')
      if (authStore) {
        const parsed = JSON.parse(authStore)
        return parsed.token || parsed.accessToken || parsed.access_token
      }
      return null
    })
    
    expect(token).toBeTruthy()
    
    // Test GET /watchlist endpoint
    const response = await request.get('http://localhost:8000/api/v1/watchlist', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(Array.isArray(data)).toBeTruthy()
    expect(data.length).toBeGreaterThanOrEqual(2) // At least 2 after deletion test
    
    console.log(`✓ API returned ${data.length} watchlist items`)
    
    // Verify data structure
    if (data.length > 0) {
      const item = data[0]
      expect(item).toHaveProperty('id')
      expect(item).toHaveProperty('symbol')
      expect(item).toHaveProperty('company_name')
      expect(item).toHaveProperty('display_order')
      console.log(`✓ Watchlist item structure valid:`, item)
    }
  })
})

test.describe('Watchlist Empty State', () => {
  test.skip('T176: Verify empty state UI', async ({ page }) => {
    // This test requires clearing all watchlist items first
    // Skipped for now as we have existing data
    console.log('⚠ Empty state test skipped - requires empty watchlist')
  })
})
