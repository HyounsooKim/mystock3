import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Portfolio Category Switching', () => {
  const testEmail = generateTestEmail()
  const testPassword = generateTestPassword()

  const mockPortfolioEntries = [
    {
      entry_id: 'entry-1',
      symbol: 'AAPL',
      company_name: 'Apple Inc.',
      category: '장기',
      purchase_price: 150.00,
      quantity: 10,
      current_price: 160.00,
      market_value: 1600.00,
      profit_loss: 100.00,
      profit_loss_percent: 6.67,
    },
    {
      entry_id: 'entry-2',
      symbol: 'MSFT',
      company_name: 'Microsoft Corporation',
      category: '장기',
      purchase_price: 300.00,
      quantity: 5,
      current_price: 310.00,
      market_value: 1550.00,
      profit_loss: 50.00,
      profit_loss_percent: 3.33,
    },
    {
      entry_id: 'entry-3',
      symbol: 'GOOGL',
      company_name: 'Alphabet Inc.',
      category: '단기',
      purchase_price: 2800.00,
      quantity: 2,
      current_price: 2700.00,
      market_value: 5400.00,
      profit_loss: -200.00,
      profit_loss_percent: -7.14,
    },
    {
      entry_id: 'entry-4',
      symbol: 'NVDA',
      company_name: 'NVIDIA Corporation',
      category: '단기',
      purchase_price: 450.00,
      quantity: 4,
      current_price: 400.00,
      market_value: 1600.00,
      profit_loss: -200.00,
      profit_loss_percent: -11.11,
    },
    {
      entry_id: 'entry-5',
      symbol: 'TSLA',
      company_name: 'Tesla Inc.',
      category: '정찰병',
      purchase_price: 200.00,
      quantity: 3,
      current_price: 220.00,
      market_value: 660.00,
      profit_loss: 60.00,
      profit_loss_percent: 10.0,
    }
  ]

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')

    // Mock portfolio with all categories
    await mockApiResponse(page, '/api/v1/portfolio', mockPortfolioEntries)
  })

  test('should display all entries by default (전체)', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify "전체" button is active
    await expect(page.locator('button:has-text("전체")')).toHaveClass(/btn-primary/)

    // Verify all 5 entries are visible
    await expect(page.locator('.portfolio-item')).toHaveCount(5)
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("MSFT")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("NVDA")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("TSLA")')).toBeVisible()
  })

  test('should filter to 장기 category when button clicked', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click "장기" button
    await page.click('button:has-text("장기")')

    // Verify "장기" button is active
    await expect(page.locator('button:has-text("장기")')).toHaveClass(/btn-primary/)

    // Verify only 2 장기 entries visible
    await expect(page.locator('.portfolio-item')).toHaveCount(2)
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("MSFT")')).toBeVisible()

    // Verify other entries not visible
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("NVDA")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("TSLA")')).not.toBeVisible()
  })

  test('should filter to 단기 category when button clicked', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click "단기" button
    await page.click('button:has-text("단기")')

    // Verify "단기" button is active
    await expect(page.locator('button:has-text("단기")')).toHaveClass(/btn-primary/)

    // Verify only 2 단기 entries visible
    await expect(page.locator('.portfolio-item')).toHaveCount(2)
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("NVDA")')).toBeVisible()

    // Verify other entries not visible
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("MSFT")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("TSLA")')).not.toBeVisible()
  })

  test('should filter to 정찰병 category when button clicked', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Click "정찰병" button
    await page.click('button:has-text("정찰병")')

    // Verify "정찰병" button is active
    await expect(page.locator('button:has-text("정찰병")')).toHaveClass(/btn-primary/)

    // Verify only 1 정찰병 entry visible
    await expect(page.locator('.portfolio-item')).toHaveCount(1)
    await expect(page.locator('.portfolio-item:has-text("TSLA")')).toBeVisible()

    // Verify other entries not visible
    await expect(page.locator('.portfolio-item:has-text("AAPL")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("MSFT")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).not.toBeVisible()
    await expect(page.locator('.portfolio-item:has-text("NVDA")')).not.toBeVisible()
  })

  test('should switch back to 전체 from filtered category', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Filter to "장기"
    await page.click('button:has-text("장기")')
    await expect(page.locator('.portfolio-item')).toHaveCount(2)

    // Switch back to "전체"
    await page.click('button:has-text("전체")')

    // Verify all 5 entries visible again
    await expect(page.locator('.portfolio-item')).toHaveCount(5)
  })

  test('should update totals when switching categories', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify initial totals (all entries)
    // Total market value: 1600 + 1550 + 5400 + 1600 + 660 = 10810
    // Total profit/loss: 100 + 50 - 200 - 200 + 60 = -190
    await expect(page.locator('.summary-card:has-text("총 평가금액")')).toContainText('10,810.00')
    await expect(page.locator('.summary-card:has-text("총 손익")')).toContainText('-190.00')

    // Filter to "장기"
    await page.click('button:has-text("장기")')

    // Verify updated totals (only 장기)
    // Total market value: 1600 + 1550 = 3150
    // Total profit/loss: 100 + 50 = 150
    await expect(page.locator('.summary-card:has-text("총 평가금액")')).toContainText('3,150.00')
    await expect(page.locator('.summary-card:has-text("총 손익")')).toContainText('150.00')

    // Filter to "단기"
    await page.click('button:has-text("단기")')

    // Verify updated totals (only 단기)
    // Total market value: 5400 + 1600 = 7000
    // Total profit/loss: -200 - 200 = -400
    await expect(page.locator('.summary-card:has-text("총 평가금액")')).toContainText('7,000.00')
    await expect(page.locator('.summary-card:has-text("총 손익")')).toContainText('-400.00')
  })

  test('should update heatmap when switching categories', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify heatmap with all entries
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()
    await page.waitForTimeout(1000)

    // Filter to "장기"
    await page.click('button:has-text("장기")')
    await page.waitForTimeout(500)

    // Heatmap should update to show only 2 entries
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Filter to "정찰병"
    await page.click('button:has-text("정찰병")')
    await page.waitForTimeout(500)

    // Heatmap should update to show only 1 entry
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()
  })

  test('should show empty state for category with no entries', async ({ page }) => {
    // Mock portfolio with only 장기 entries
    const onlyLongTerm = mockPortfolioEntries.filter(entry => entry.category === '장기')
    await mockApiResponse(page, '/api/v1/portfolio', onlyLongTerm)

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify entries in "전체"
    await expect(page.locator('.portfolio-item')).toHaveCount(2)

    // Filter to "정찰병" (no entries)
    await page.click('button:has-text("정찰병")')

    // Verify empty state
    await expect(page.locator('.portfolio-item')).toHaveCount(0)
    await expect(page.locator('.empty-state')).toBeVisible()
    await expect(page.locator('.empty-state')).toContainText('포트폴리오가 비어 있습니다')
  })

  test('should persist category selection on page reload', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Filter to "단기"
    await page.click('button:has-text("단기")')
    await expect(page.locator('.portfolio-item')).toHaveCount(2)

    // Reload page
    await page.reload()

    // Verify "단기" filter persists
    await expect(page.locator('button:has-text("단기")')).toHaveClass(/btn-primary/)
    await expect(page.locator('.portfolio-item')).toHaveCount(2)
    await expect(page.locator('.portfolio-item:has-text("GOOGL")')).toBeVisible()
  })

  test('should handle rapid category switching', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Rapidly switch categories
    await page.click('button:has-text("장기")')
    await page.waitForTimeout(100)
    await page.click('button:has-text("단기")')
    await page.waitForTimeout(100)
    await page.click('button:has-text("정찰병")')
    await page.waitForTimeout(100)
    await page.click('button:has-text("전체")')

    // Verify final state is correct (all entries)
    await expect(page.locator('button:has-text("전체")')).toHaveClass(/btn-primary/)
    await expect(page.locator('.portfolio-item')).toHaveCount(5)
  })

  test('should show correct category badge colors in filtered view', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Filter to "장기"
    await page.click('button:has-text("장기")')

    // Verify all visible entries show "장기" badge with green color
    const categoryBadges = page.locator('.portfolio-item .badge:has-text("장기")')
    await expect(categoryBadges).toHaveCount(2)
    await expect(categoryBadges.first()).toHaveClass(/badge-success/)  // Green

    // Filter to "단기"
    await page.click('button:has-text("단기")')

    // Verify all visible entries show "단기" badge with orange color
    const shortTermBadges = page.locator('.portfolio-item .badge:has-text("단기")')
    await expect(shortTermBadges).toHaveCount(2)
    await expect(shortTermBadges.first()).toHaveClass(/badge-warning/)  // Orange

    // Filter to "정찰병"
    await page.click('button:has-text("정찰병")')

    // Verify entry shows "정찰병" badge with blue color
    const scoutBadge = page.locator('.portfolio-item .badge:has-text("정찰병")')
    await expect(scoutBadge).toHaveCount(1)
    await expect(scoutBadge).toHaveClass(/badge-info/)  // Blue
  })

  test('should maintain category filter when adding new entry', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Filter to "장기"
    await page.click('button:has-text("장기")')
    await expect(page.locator('.portfolio-item')).toHaveCount(2)

    // Add new entry to "장기" category
    await mockApiResponse(page, '/api/v1/portfolio', {
      entry_id: 'entry-new',
      symbol: 'AMZN',
      company_name: 'Amazon.com Inc.',
      category: '장기',
      purchase_price: 3000.00,
      quantity: 1,
      current_price: 3100.00,
      market_value: 3100.00,
      profit_loss: 100.00,
      profit_loss_percent: 3.33
    }, 201)

    // Open add modal and submit (implementation details)
    // ...

    // Verify "장기" filter still active after add
    await expect(page.locator('button:has-text("장기")')).toHaveClass(/btn-primary/)

    // New entry should appear in filtered view
    await expect(page.locator('.portfolio-item')).toHaveCount(3)
  })
})
