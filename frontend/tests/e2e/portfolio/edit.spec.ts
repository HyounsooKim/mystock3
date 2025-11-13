import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Edit Portfolio Entry', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  const mockPortfolioEntry = {
    entry_id: 'entry-1',
    user_id: 'test@example.com',
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
  }

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')

    // Mock portfolio with one entry
    await mockApiResponse(page, '/api/v1/portfolio', [mockPortfolioEntry])
  })

  test('should successfully edit purchase price and quantity (FR-022)', async ({ page }) => {
    // Mock update success
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        const body = await route.request().postDataJSON()
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockPortfolioEntry,
            purchase_price: body.purchase_price || mockPortfolioEntry.purchase_price,
            quantity: body.quantity || mockPortfolioEntry.quantity,
            market_value: (body.quantity || mockPortfolioEntry.quantity) * 160,
            profit_loss: ((160 - (body.purchase_price || mockPortfolioEntry.purchase_price)) * 
                         (body.quantity || mockPortfolioEntry.quantity)),
            profit_loss_percent: (((160 - (body.purchase_price || mockPortfolioEntry.purchase_price)) / 
                                  (body.purchase_price || mockPortfolioEntry.purchase_price)) * 100)
          })
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify entry is displayed
    await expect(page.locator('.portfolio-item')).toContainText('AAPL')
    await expect(page.locator('.portfolio-item')).toContainText('150.00')
    await expect(page.locator('.portfolio-item')).toContainText('10')

    // Click edit button
    await page.click('.portfolio-item button[title="수정"]')

    // Wait for edit modal
    await expect(page.locator('.modal')).toBeVisible()
    await expect(page.locator('.modal')).toContainText('포트폴리오 수정')

    // Verify existing values
    await expect(page.locator('input[name="purchase_price"]')).toHaveValue('150.00')
    await expect(page.locator('input[name="quantity"]')).toHaveValue('10')

    // Update purchase price
    await page.fill('input[name="purchase_price"]', '155.00')

    // Update quantity
    await page.fill('input[name="quantity"]', '12')

    // Verify total investment preview updated
    await expect(page.locator('.total-investment')).toContainText('1,860.00')

    // Submit
    await page.click('button:has-text("저장")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify updated values in table
    await expect(page.locator('.portfolio-item')).toContainText('155.00')
    await expect(page.locator('.portfolio-item')).toContainText('12')
  })

  test('should edit only purchase price', async ({ page }) => {
    // Mock update success
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        const body = await route.request().postDataJSON()
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockPortfolioEntry,
            purchase_price: body.purchase_price,
            profit_loss: ((160 - body.purchase_price) * 10),
            profit_loss_percent: (((160 - body.purchase_price) / body.purchase_price) * 100)
          })
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click edit button
    await page.click('.portfolio-item button[title="수정"]')

    // Update only purchase price
    await page.fill('input[name="purchase_price"]', '148.00')

    // Submit
    await page.click('button:has-text("저장")')

    // Verify modal closed
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify quantity unchanged
    await expect(page.locator('.portfolio-item')).toContainText('10')
  })

  test('should edit only quantity', async ({ page }) => {
    // Mock update success
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        const body = await route.request().postDataJSON()
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockPortfolioEntry,
            quantity: body.quantity,
            market_value: body.quantity * 160,
            profit_loss: ((160 - 150) * body.quantity)
          })
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click edit button
    await page.click('.portfolio-item button[title="수정"]')

    // Update only quantity
    await page.fill('input[name="quantity"]', '15')

    // Submit
    await page.click('button:has-text("저장")')

    // Verify modal closed
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify purchase price unchanged
    await expect(page.locator('.portfolio-item')).toContainText('150.00')
  })

  test('should validate edit form inputs', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click edit button
    await page.click('.portfolio-item button[title="수정"]')

    // Try negative purchase price
    await page.fill('input[name="purchase_price"]', '-100')
    await expect(page.locator('button:has-text("저장")')).toBeDisabled()

    // Fix purchase price
    await page.fill('input[name="purchase_price"]', '150.00')

    // Try zero quantity
    await page.fill('input[name="quantity"]', '0')
    await expect(page.locator('button:has-text("저장")')).toBeDisabled()

    // Try negative quantity
    await page.fill('input[name="quantity"]', '-5')
    await expect(page.locator('button:has-text("저장")')).toBeDisabled()

    // Fix quantity
    await page.fill('input[name="quantity"]', '10')
    await expect(page.locator('button:has-text("저장")')).toBeEnabled()
  })

  test('should cancel edit without saving', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify original values
    await expect(page.locator('.portfolio-item')).toContainText('150.00')

    // Click edit button
    await page.click('.portfolio-item button[title="수정"]')

    // Change values
    await page.fill('input[name="purchase_price"]', '200.00')
    await page.fill('input[name="quantity"]', '20')

    // Cancel
    await page.click('button:has-text("취소")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify original values unchanged
    await expect(page.locator('.portfolio-item')).toContainText('150.00')
    await expect(page.locator('.portfolio-item')).toContainText('10')
    await expect(page.locator('.portfolio-item')).not.toContainText('200.00')
    await expect(page.locator('.portfolio-item')).not.toContainText('20')
  })

  test('should show error when update fails', async ({ page }) => {
    // Mock update failure
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '포트폴리오 수정에 실패했습니다'
          })
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click edit button
    await page.click('.portfolio-item button[title="수정"]')

    // Update values
    await page.fill('input[name="purchase_price"]', '155.00')

    // Submit
    await page.click('button:has-text("저장")')

    // Verify error message
    await expect(page.locator('.alert-danger')).toContainText('포트폴리오 수정에 실패했습니다')

    // Modal may stay open or close depending on implementation
  })

  test('should display read-only stock info in edit modal', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click edit button
    await page.click('.portfolio-item button[title="수정"]')

    // Verify stock info displayed (read-only)
    await expect(page.locator('.modal')).toContainText('AAPL')
    await expect(page.locator('.modal')).toContainText('Apple Inc.')
    await expect(page.locator('.modal')).toContainText('장기')

    // Verify symbol/company/category are not editable
    await expect(page.locator('.modal input[value="AAPL"]')).toBeDisabled()
    await expect(page.locator('.modal input[value="Apple Inc."]')).toBeDisabled()
  })
})
