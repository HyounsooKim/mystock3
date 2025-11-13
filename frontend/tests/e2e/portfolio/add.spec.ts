import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Add Stock to Portfolio', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')

    // Mock empty portfolio initially
    await mockApiResponse(page, '/api/v1/portfolio', [])
  })

  test('should successfully add a stock to portfolio with category', async ({ page }) => {
    // Mock search results
    await mockApiResponse(page, '/api/v1/stocks/search', [
      { symbol: 'AAPL', company_name: 'Apple Inc.', match_score: 0.95 }
    ])

    // Mock add to portfolio success
    await mockApiResponse(page, '/api/v1/portfolio', {
      entry_id: 'entry-1',
      user_id: testEmail,
      symbol: 'AAPL',
      company_name: 'Apple Inc.',
      category: '장기',
      purchase_price: 150.00,
      quantity: 10,
      current_price: 160.00,
      market_value: 1600.00,
      profit_loss: 100.00,
      profit_loss_percent: 6.67,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }, 201)

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click add stock button
    await page.click('button:has-text("종목 추가")')

    // Wait for modal
    await expect(page.locator('.modal')).toBeVisible()

    // Search for stock (using StockSearch component)
    const searchInput = page.locator('input[placeholder*="종목"]')
    await searchInput.fill('AAPL')

    // Wait for search results
    await page.waitForTimeout(500)  // Debounce delay

    // Select first result
    await page.click('.search-result:has-text("AAPL")')

    // Select category
    await page.selectOption('select[name="category"]', '장기')

    // Enter purchase price
    const priceInput = page.locator('input[name="purchase_price"]')
    await priceInput.fill('150.00')

    // Enter quantity
    const quantityInput = page.locator('input[name="quantity"]')
    await quantityInput.fill('10')

    // Verify total investment preview
    await expect(page.locator('.total-investment')).toContainText('1,500.00')

    // Submit
    await page.click('button:has-text("추가")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify portfolio table shows the entry
    await expect(page.locator('.portfolio-table')).toContainText('AAPL')
    await expect(page.locator('.portfolio-table')).toContainText('장기')
  })

  test('should show error when adding duplicate stock in same category (FR-017-1)', async ({ page }) => {
    // Mock duplicate error
    await page.route(/\/api\/v1\/portfolio$/, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '이미 해당 카테고리에 등록된 종목입니다'
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

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Open add modal
    await page.click('button:has-text("종목 추가")')

    // Fill form
    await page.locator('input[placeholder*="종목"]').fill('AAPL')
    await page.waitForTimeout(500)
    await page.click('.search-result:has-text("AAPL")')
    await page.selectOption('select[name="category"]', '장기')
    await page.locator('input[name="purchase_price"]').fill('150.00')
    await page.locator('input[name="quantity"]').fill('10')

    // Submit
    await page.click('button:has-text("추가")')

    // Verify error message
    await expect(page.locator('.alert-danger')).toContainText('이미 해당 카테고리에 등록된 종목입니다')

    // Modal should stay open
    await expect(page.locator('.modal')).toBeVisible()
  })

  test('should show error when portfolio limit reached (FR-020)', async ({ page }) => {
    // Mock portfolio limit error
    await page.route(/\/api\/v1\/portfolio$/, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '최대 10개 종목까지 등록 가능'
          })
        })
      } else {
        // Mock 10 existing entries
        const entries = Array.from({ length: 10 }, (_, i) => ({
          entry_id: `entry-${i}`,
          symbol: `STOCK${i}`,
          company_name: `Company ${i}`,
          category: '장기',
          purchase_price: 100.00,
          quantity: 5,
          current_price: 110.00,
          market_value: 550.00,
          profit_loss: 50.00,
          profit_loss_percent: 10.0
        }))
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(entries)
        })
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify 10 entries shown
    await expect(page.locator('.portfolio-item')).toHaveCount(10)

    // Open add modal
    await page.click('button:has-text("종목 추가")')

    // Fill form
    await page.locator('input[placeholder*="종목"]').fill('MSFT')
    await page.waitForTimeout(500)
    await page.selectOption('select[name="category"]', '단기')
    await page.locator('input[name="purchase_price"]').fill('300.00')
    await page.locator('input[name="quantity"]').fill('5')

    // Submit
    await page.click('button:has-text("추가")')

    // Verify error message
    await expect(page.locator('.alert-danger')).toContainText('최대 10개 종목까지 등록 가능')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()
  })

  test('should validate form inputs', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Open add modal
    await page.click('button:has-text("종목 추가")')

    // Try to submit without filling
    await page.click('button:has-text("추가")')

    // Verify validation messages
    await expect(page.locator('.modal')).toBeVisible()  // Modal stays open

    // Fill only symbol
    await page.locator('input[placeholder*="종목"]').fill('AAPL')
    await page.waitForTimeout(500)
    await page.click('.search-result:has-text("AAPL")')

    // Try to submit without price/quantity
    await page.click('button:has-text("추가")')
    await expect(page.locator('.modal')).toBeVisible()

    // Fill invalid price (negative)
    await page.locator('input[name="purchase_price"]').fill('-100')
    await expect(page.locator('button:has-text("추가")')).toBeDisabled()

    // Fill valid price
    await page.locator('input[name="purchase_price"]').fill('150.00')

    // Fill invalid quantity (0)
    await page.locator('input[name="quantity"]').fill('0')
    await expect(page.locator('button:has-text("추가")')).toBeDisabled()
  })

  test('should allow same stock in different categories', async ({ page }) => {
    // Mock successful adds to different categories
    let addCount = 0
    await page.route(/\/api\/v1\/portfolio$/, async (route) => {
      if (route.request().method() === 'POST') {
        addCount++
        const body = await route.request().postDataJSON()
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            entry_id: `entry-${addCount}`,
            user_id: testEmail,
            symbol: body.symbol,
            company_name: body.company_name,
            category: body.category,
            purchase_price: body.purchase_price,
            quantity: body.quantity,
            current_price: 160.00,
            market_value: body.quantity * 160,
            profit_loss: (160 - body.purchase_price) * body.quantity,
            profit_loss_percent: ((160 - body.purchase_price) / body.purchase_price) * 100
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

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Add AAPL to "장기"
    await page.click('button:has-text("종목 추가")')
    await page.locator('input[placeholder*="종목"]').fill('AAPL')
    await page.waitForTimeout(500)
    await page.click('.search-result:has-text("AAPL")')
    await page.selectOption('select[name="category"]', '장기')
    await page.locator('input[name="purchase_price"]').fill('150.00')
    await page.locator('input[name="quantity"]').fill('10')
    await page.click('button:has-text("추가")')
    await expect(page.locator('.modal')).not.toBeVisible()

    // Add AAPL to "단기" (should succeed)
    await page.click('button:has-text("종목 추가")')
    await page.locator('input[placeholder*="종목"]').fill('AAPL')
    await page.waitForTimeout(500)
    await page.click('.search-result:has-text("AAPL")')
    await page.selectOption('select[name="category"]', '단기')
    await page.locator('input[name="purchase_price"]').fill('155.00')
    await page.locator('input[name="quantity"]').fill('5')
    await page.click('button:has-text("추가")')

    // Should succeed - no error
    await expect(page.locator('.modal')).not.toBeVisible()
    await expect(page.locator('.alert-danger')).not.toBeVisible()
  })
})
