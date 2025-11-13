import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Delete Portfolio Entry', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  const mockPortfolioEntries = [
    {
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
    },
    {
      entry_id: 'entry-2',
      user_id: 'test@example.com',
      symbol: 'GOOGL',
      company_name: 'Alphabet Inc.',
      category: '단기',
      purchase_price: 2800.00,
      quantity: 2,
      current_price: 2850.00,
      market_value: 5700.00,
      profit_loss: 100.00,
      profit_loss_percent: 1.79,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  ]

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')

    // Mock portfolio with entries
    await mockApiResponse(page, '/api/v1/portfolio', mockPortfolioEntries)
  })

  test('should successfully delete a portfolio entry (FR-023)', async ({ page }) => {
    // Mock delete success
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
          contentType: 'application/json'
        })
      } else {
        await route.continue()
      }
    })

    // Mock updated portfolio after delete
    await page.route(/\/api\/v1\/portfolio$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([mockPortfolioEntries[1]])  // Only GOOGL remains
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify both entries visible
    await expect(page.locator('.portfolio-item')).toHaveCount(2)
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).toBeVisible()

    // Click delete button for AAPL
    await page.click('.portfolio-item:has-text("AAPL") button[title="삭제"]')

    // Confirmation modal should appear
    await expect(page.locator('.modal')).toBeVisible()
    await expect(page.locator('.modal')).toContainText('삭제')
    await expect(page.locator('.modal')).toContainText('AAPL')

    // Confirm delete
    await page.click('.modal button:has-text("삭제")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify AAPL removed, only GOOGL remains
    await expect(page.locator('.portfolio-item')).toHaveCount(1)
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).toBeVisible()
  })

  test('should cancel delete operation', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify both entries visible
    await expect(page.locator('.portfolio-item')).toHaveCount(2)

    // Click delete button for AAPL
    await page.click('.portfolio-item:has-text("AAPL") button[title="삭제"]')

    // Confirmation modal should appear
    await expect(page.locator('.modal')).toBeVisible()

    // Cancel delete
    await page.click('.modal button:has-text("취소")')

    // Modal should close
    await expect(page.locator('.modal')).not.toBeVisible()

    // Verify both entries still visible
    await expect(page.locator('.portfolio-item')).toHaveCount(2)
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).toBeVisible()
  })

  test('should show error when delete fails', async ({ page }) => {
    // Mock delete failure
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '포트폴리오 삭제에 실패했습니다'
          })
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click delete button
    await page.click('.portfolio-item:has-text("AAPL") button[title="삭제"]')

    // Confirm delete
    await page.click('.modal button:has-text("삭제")')

    // Verify error message
    await expect(page.locator('.alert-danger')).toContainText('포트폴리오 삭제에 실패했습니다')

    // Entry should still be visible
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).toBeVisible()
  })

  test('should show error when deleting non-existent entry', async ({ page }) => {
    // Mock 404 not found
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: '포트폴리오 항목을 찾을 수 없습니다'
          })
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click delete button
    await page.click('.portfolio-item:has-text("AAPL") button[title="삭제"]')

    // Confirm delete
    await page.click('.modal button:has-text("삭제")')

    // Verify error message
    await expect(page.locator('.alert-danger')).toContainText('포트폴리오 항목을 찾을 수 없습니다')
  })

  test('should delete all entries and show empty state', async ({ page }) => {
    // Mock delete success for both entries
    await page.route(/\/api\/v1\/portfolio\/entry-\d+$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
          contentType: 'application/json'
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Delete AAPL
    await page.click('.portfolio-item:has-text("AAPL") button[title="삭제"]')
    await page.click('.modal button:has-text("삭제")')
    await page.waitForTimeout(500)

    // Mock empty portfolio after first delete
    await mockApiResponse(page, '/api/v1/portfolio', [mockPortfolioEntries[1]])

    // Reload to see updated list
    await page.reload()

    // Delete GOOGL
    await page.click('.portfolio-item:has-text("GOOGL") button[title="삭제"]')
    await page.click('.modal button:has-text("삭제")')
    await page.waitForTimeout(500)

    // Mock empty portfolio
    await mockApiResponse(page, '/api/v1/portfolio', [])

    // Reload to see empty state
    await page.reload()

    // Verify empty state displayed
    await expect(page.locator('.empty-state')).toBeVisible()
    await expect(page.locator('.empty-state')).toContainText('포트폴리오가 비어 있습니다')
  })

  test('should recalculate totals after delete', async ({ page }) => {
    // Mock delete success
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
          contentType: 'application/json'
        })
      } else {
        await route.continue()
      }
    })

    // Mock updated portfolio
    await page.route(/\/api\/v1\/portfolio$/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([mockPortfolioEntries[1]])
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify initial totals (sum of both entries)
    await expect(page.locator('.summary-card:has-text("총 평가금액")')).toContainText('7,300.00')  // 1600 + 5700
    await expect(page.locator('.summary-card:has-text("총 손익")')).toContainText('200.00')  // 100 + 100

    // Delete AAPL entry
    await page.click('.portfolio-item:has-text("AAPL") button[title="삭제"]')
    await page.click('.modal button:has-text("삭제")')
    await page.waitForTimeout(500)

    // Reload to see updated totals
    await page.reload()

    // Verify updated totals (only GOOGL remains)
    await expect(page.locator('.summary-card:has-text("총 평가금액")')).toContainText('5,700.00')
    await expect(page.locator('.summary-card:has-text("총 손익")')).toContainText('100.00')
  })

  test('should disable delete button while operation in progress', async ({ page }) => {
    // Mock slow delete operation
    await page.route(/\/api\/v1\/portfolio\/entry-1$/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await page.waitForTimeout(1000)  // Simulate slow operation
        await route.fulfill({
          status: 204,
          contentType: 'application/json'
        })
      } else {
        await route.continue()
      }
    })

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click delete button
    await page.click('.portfolio-item:has-text("AAPL") button[title="삭제"]')

    // Confirm delete
    const deleteButton = page.locator('.modal button:has-text("삭제")')
    await deleteButton.click()

    // Button should be disabled during operation
    await expect(deleteButton).toBeDisabled()

    // Wait for operation to complete
    await page.waitForTimeout(1100)
  })
})
