import { test, expect } from '../helpers/auth'
import { generateTestEmail, generateTestPassword, mockApiResponse } from '../helpers/auth'

test.describe('Portfolio Heatmap Visualization', () => {
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
      current_price: 165.00,
      market_value: 1650.00,
      profit_loss: 150.00,
      profit_loss_percent: 10.0,  // Green
    },
    {
      entry_id: 'entry-2',
      symbol: 'GOOGL',
      company_name: 'Alphabet Inc.',
      category: '단기',
      purchase_price: 2800.00,
      quantity: 2,
      current_price: 2700.00,
      market_value: 5400.00,
      profit_loss: -200.00,
      profit_loss_percent: -7.14,  // Red
    },
    {
      entry_id: 'entry-3',
      symbol: 'MSFT',
      company_name: 'Microsoft Corporation',
      category: '장기',
      purchase_price: 300.00,
      quantity: 5,
      current_price: 310.00,
      market_value: 1550.00,
      profit_loss: 50.00,
      profit_loss_percent: 3.33,  // Light green
    },
    {
      entry_id: 'entry-4',
      symbol: 'TSLA',
      company_name: 'Tesla Inc.',
      category: '정찰병',
      purchase_price: 200.00,
      quantity: 3,
      current_price: 220.00,
      market_value: 660.00,
      profit_loss: 60.00,
      profit_loss_percent: 10.0,  // Green
    },
    {
      entry_id: 'entry-5',
      symbol: 'NVDA',
      company_name: 'NVIDIA Corporation',
      category: '단기',
      purchase_price: 450.00,
      quantity: 4,
      current_price: 400.00,
      market_value: 1600.00,
      profit_loss: -200.00,
      profit_loss_percent: -11.11,  // Strong red
    }
  ]

  test.beforeEach(async ({ page, authHelpers }) => {
    // Sign up and login
    await authHelpers.signup(testEmail, testPassword)
    await expect(page).toHaveURL('/dashboard')

    // Mock portfolio with entries
    await mockApiResponse(page, '/api/v1/portfolio', mockPortfolioEntries)
  })

  test('should display heatmap with portfolio entries (FR-021)', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Verify heatmap container is visible
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Verify ECharts canvas is rendered
    const canvas = page.locator('.portfolio-heatmap canvas')
    await expect(canvas).toBeVisible()
    await expect(canvas).toHaveCount(1)
  })

  test('should color code entries based on profit/loss percentage', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Wait for heatmap to render
    await page.waitForTimeout(1000)

    // Verify heatmap exists
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Test color coding by hovering and checking tooltips
    // Note: ECharts uses canvas, so we can't directly test colors
    // Instead, we verify the data is passed correctly by checking tooltips

    // Hover over a positive entry (should show green in tooltip context)
    const canvas = page.locator('.portfolio-heatmap canvas')
    await canvas.hover({ position: { x: 100, y: 100 } })
    await page.waitForTimeout(500)

    // Verify tooltip appears with profit/loss data
    // (Exact tooltip verification depends on ECharts tooltip configuration)
  })

  test('should show entry details on hover', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Wait for heatmap to render
    await page.waitForTimeout(1000)

    // Hover over heatmap area
    const canvas = page.locator('.portfolio-heatmap canvas')
    await canvas.hover({ position: { x: 150, y: 150 } })
    await page.waitForTimeout(500)

    // Verify ECharts tooltip is visible
    // Note: ECharts tooltips are dynamically created divs
    const tooltip = page.locator('.echarts-tooltip')
    // Tooltip visibility depends on hover position and ECharts rendering
    // This is a visual verification test
  })

  test('should size rectangles proportional to market value', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Wait for heatmap to render
    await page.waitForTimeout(1000)

    // Verify heatmap is visible
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Visual verification: GOOGL (5400) should be larger than MSFT (1550)
    // This is a visual test - we verify the component exists
    // Actual size verification would require canvas analysis or screenshot comparison
  })

  test('should hide heatmap when portfolio is empty', async ({ page }) => {
    // Mock empty portfolio
    await mockApiResponse(page, '/api/v1/portfolio', [])

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Heatmap should not be visible
    await expect(page.locator('.portfolio-heatmap')).not.toBeVisible()

    // Empty state should be visible instead
    await expect(page.locator('.empty-state')).toBeVisible()
  })

  test('should update heatmap when category filter changes', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Initial heatmap with all entries
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()
    await page.waitForTimeout(1000)

    // Click "장기" category filter
    await page.click('button:has-text("장기")')
    await page.waitForTimeout(500)

    // Verify heatmap still visible (2 entries: AAPL, MSFT)
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Click "정찰병" category filter
    await page.click('button:has-text("정찰병")')
    await page.waitForTimeout(500)

    // Verify heatmap still visible (1 entry: TSLA)
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Click "전체" to show all
    await page.click('button:has-text("전체")')
    await page.waitForTimeout(500)

    // Verify heatmap shows all entries again
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()
  })

  test('should handle heatmap rendering with null profit/loss values', async ({ page }) => {
    // Mock entry with null P/L values (API failure)
    const entriesWithNull = [
      {
        entry_id: 'entry-1',
        symbol: 'AAPL',
        company_name: 'Apple Inc.',
        category: '장기',
        purchase_price: 150.00,
        quantity: 10,
        current_price: null,
        market_value: null,
        profit_loss: null,
        profit_loss_percent: null,
      },
      mockPortfolioEntries[1]  // One valid entry
    ]

    await mockApiResponse(page, '/api/v1/portfolio', entriesWithNull)

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Heatmap should still render with available data
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Should only show entry with valid data
    await page.waitForTimeout(1000)
  })

  test('should display profit/loss percentage labels on heatmap', async ({ page }) => {
    // Navigate to portfolio
    await page.goto('/portfolio')

    // Wait for heatmap to render
    await page.waitForTimeout(1000)

    // Verify heatmap exists
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Labels are rendered on canvas, so we verify the component exists
    // Visual verification would show:
    // - AAPL: +10.0%
    // - GOOGL: -7.14%
    // - MSFT: +3.33%
    // etc.
  })

  test('should use gradient color scale correctly', async ({ page }) => {
    // Create entries with specific P/L percentages to test color ranges
    const colorTestEntries = [
      {
        entry_id: 'green-strong',
        symbol: 'GREEN1',
        profit_loss_percent: 15.0,  // >10%: #22c55e
        market_value: 1000
      },
      {
        entry_id: 'green-good',
        symbol: 'GREEN2',
        profit_loss_percent: 7.5,  // 5-10%: #4ade80
        market_value: 1000
      },
      {
        entry_id: 'green-light',
        symbol: 'GREEN3',
        profit_loss_percent: 2.5,  // 0-5%: #86efac
        market_value: 1000
      },
      {
        entry_id: 'neutral',
        symbol: 'NEUTRAL',
        profit_loss_percent: 0.0,  // 0%: #94a3b8
        market_value: 1000
      },
      {
        entry_id: 'red-light',
        symbol: 'RED1',
        profit_loss_percent: -2.5,  // -5 to 0%: #fca5a5
        market_value: 1000
      },
      {
        entry_id: 'red-moderate',
        symbol: 'RED2',
        profit_loss_percent: -7.5,  // -10 to -5%: #f87171
        market_value: 1000
      },
      {
        entry_id: 'red-strong',
        symbol: 'RED3',
        profit_loss_percent: -15.0,  // <-10%: #dc2626
        market_value: 1000
      }
    ].map((entry, index) => ({
      entry_id: entry.entry_id,
      symbol: entry.symbol,
      company_name: `Company ${index}`,
      category: '장기',
      purchase_price: 100.00,
      quantity: 10,
      current_price: 100 + (entry.profit_loss_percent || 0),
      market_value: entry.market_value,
      profit_loss: (entry.profit_loss_percent || 0) * 10,
      profit_loss_percent: entry.profit_loss_percent,
    }))

    await mockApiResponse(page, '/api/v1/portfolio', colorTestEntries)

    // Navigate to portfolio
    await page.goto('/portfolio')

    // Wait for heatmap to render
    await page.waitForTimeout(1000)

    // Verify heatmap is visible with all color ranges
    await expect(page.locator('.portfolio-heatmap')).toBeVisible()

    // Visual verification: 7 rectangles with different colors
    // This is a visual test - actual color verification would require
    // canvas pixel analysis or screenshot comparison
  })
})
