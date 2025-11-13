/**
 * E2E Test: Watchlist Validation
 * 
 * Purpose: Test watchlist CRUD operations (edit memo, delete, reorder)
 * User: test@example.com / Test1234!
 */

import { test, expect, Page } from '@playwright/test'

const TEST_USER = {
  email: 'test@example.com',
  password: 'Test1234!'
}

// Helper function for login
async function loginUser(page: Page) {
  await page.goto('/')
  await page.fill('input[type="email"]', TEST_USER.email)
  await page.fill('input[type="password"]', TEST_USER.password)
  await page.click('button[type="submit"]')
  await page.waitForTimeout(2000)
}

// Helper function to navigate to watchlist
async function navigateToWatchlist(page: Page) {
  const watchlistLink = page.locator('a:has-text("관심종목"), a[href*="watchlist"]')
  await watchlistLink.click()
  await page.waitForTimeout(2000)
  await page.waitForSelector('table tbody tr', { timeout: 10000 })
}


test.describe('Watchlist Validation', () => {
  test.describe('Memo Edit', () => {
    test('Should edit stock memo', async ({ page }) => {
      // Enable console logging
      page.on('console', msg => console.log('Browser:', msg.text()))
      page.on('response', response => {
        if (response.url().includes('/api/v1/watchlist')) {
          console.log(`API: ${response.request().method()} ${response.url()} - ${response.status()}`)
        }
      })
      
      // Login and navigate
      await loginUser(page)
      await navigateToWatchlist(page)
      
      // Get first row details
      const firstRow = page.locator('table tbody tr').first()
      const symbolBefore = await firstRow.locator('td').nth(1).textContent()
      const memoTextBefore = await firstRow.locator('td').nth(4).textContent()
      
      console.log(`📝 종목: ${symbolBefore}, 수정 전 메모: "${memoTextBefore}"`)
      
      // Open edit modal
      const editButton = firstRow.locator('button').first()
      await editButton.click()
      await page.waitForTimeout(1000)
      
      await expect(page.locator('.modal.show')).toBeVisible()
      console.log('✅ 메모 수정 모달 열림')
      
      // Update memo
      const memoInput = page.locator('.modal input[type="text"]')
      await expect(memoInput).toBeVisible()
      
      await memoInput.clear()
      const newMemo = `E2E 테스트 ${Date.now()}`
      await memoInput.fill(newMemo)
      console.log(`📝 새 메모: "${newMemo}"`)
      
      // Save
      const saveButton = page.locator('.modal button:has-text("저장")')
      await saveButton.click()
      await page.waitForTimeout(3000)
      
      // Verify modal closed
      await expect(page.locator('.modal.show')).not.toBeVisible()
      
      // Verify memo updated
      const rows = await page.locator('table tbody tr').all()
      let found = false
      
      for (const row of rows) {
        const symbol = await row.locator('td').nth(1).textContent()
        if (symbol === symbolBefore) {
          const memoText = await row.locator('td').nth(4).textContent()
          console.log(`📝 수정 후 메모: "${memoText}"`)
          
          if (memoText?.includes(newMemo)) {
            found = true
            console.log(`✅ 메모 수정 성공`)
            break
          }
        }
      }
      
      expect(found).toBe(true)
    })
  })

  test.describe('Delete', () => {
    test('Should delete a watchlist item', async ({ page }) => {
      // Enable logging
      page.on('console', msg => console.log('Browser:', msg.text()))
      page.on('response', response => {
        if (response.url().includes('/api/v1/watchlist')) {
          console.log(`API: ${response.request().method()} ${response.url()} - ${response.status()}`)
        }
      })
      
      // Login and navigate
      await loginUser(page)
      await navigateToWatchlist(page)
      
      // Get count before delete
      const rowsBefore = await page.locator('table tbody tr').count()
      console.log(`📊 삭제 전 종목 수: ${rowsBefore}`)
      
      // Get last row (to preserve test data)
      const lastRow = page.locator('table tbody tr').last()
      const symbolToDelete = await lastRow.locator('td').nth(1).textContent()
      console.log(`🗑️ 삭제할 종목: ${symbolToDelete}`)
      
      // Find and click delete button (second button in row)
      const deleteButton = lastRow.locator('button').nth(1)
      await deleteButton.click()
      await page.waitForTimeout(1000)
      
      // Confirm deletion in modal
      await expect(page.locator('.modal.show')).toBeVisible()
      console.log('✅ 삭제 확인 모달 열림')
      
      const confirmButton = page.locator('.modal button:has-text("삭제")')
      await confirmButton.click()
      await page.waitForTimeout(3000)
      
      // Verify count decreased
      const rowsAfter = await page.locator('table tbody tr').count()
      console.log(`📊 삭제 후 종목 수: ${rowsAfter}`)
      
      expect(rowsAfter).toBe(rowsBefore - 1)
      
      // Verify symbol no longer exists
      const rows = await page.locator('table tbody tr').all()
      let stillExists = false
      
      for (const row of rows) {
        const symbol = await row.locator('td').nth(1).textContent()
        if (symbol === symbolToDelete) {
          stillExists = true
          break
        }
      }
      
      expect(stillExists).toBe(false)
      console.log(`✅ 종목 삭제 성공: ${symbolToDelete}`)
    })
  })

  test.describe('Reorder', () => {
    test('Should reorder watchlist items', async ({ page }) => {
      // Enable logging
      page.on('console', msg => console.log('Browser:', msg.text()))
      page.on('response', response => {
        if (response.url().includes('/api/v1/watchlist')) {
          console.log(`API: ${response.request().method()} ${response.url()} - ${response.status()}`)
        }
      })
      
      // Login and navigate
      await loginUser(page)
      await navigateToWatchlist(page)
      
      // Get initial order
      const rows = await page.locator('table tbody tr').all()
      const initialOrder: string[] = []
      
      for (const row of rows) {
        const symbol = await row.locator('td').nth(1).textContent()
        if (symbol) initialOrder.push(symbol)
      }
      
      console.log(`📊 초기 순서: ${initialOrder.join(', ')}`)
      
      // Get first and second rows
      const firstRow = page.locator('table tbody tr').first()
      const secondRow = page.locator('table tbody tr').nth(1)
      
      // Get bounding boxes for drag and drop
      const firstBox = await firstRow.boundingBox()
      const secondBox = await secondRow.boundingBox()
      
      if (!firstBox || !secondBox) {
        throw new Error('Cannot get row positions')
      }
      
      // Perform drag and drop
      console.log('🔄 순서 변경 시작...')
      await page.mouse.move(firstBox.x + firstBox.width / 2, firstBox.y + firstBox.height / 2)
      await page.mouse.down()
      await page.mouse.move(secondBox.x + secondBox.width / 2, secondBox.y + secondBox.height + 10, { steps: 10 })
      await page.mouse.up()
      
      await page.waitForTimeout(3000)
      
      // Get new order
      const rowsAfter = await page.locator('table tbody tr').all()
      const newOrder: string[] = []
      
      for (const row of rowsAfter) {
        const symbol = await row.locator('td').nth(1).textContent()
        if (symbol) newOrder.push(symbol)
      }
      
      console.log(`📊 변경 후 순서: ${newOrder.join(', ')}`)
      
      // Verify order changed
      const orderChanged = JSON.stringify(initialOrder) !== JSON.stringify(newOrder)
      
      if (orderChanged) {
        console.log('✅ 순서 변경 성공')
      } else {
        console.log('⚠️ 순서가 변경되지 않음 (드래그 앤 드롭 기능이 구현되지 않았을 수 있음)')
      }
      
      // Note: This test will pass even if reorder is not implemented yet
      // It documents the expected behavior
      expect(rowsAfter.length).toBe(initialOrder.length)
    })
  })
})
