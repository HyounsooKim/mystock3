"""E2E tests for complete authentication flow."""
import pytest
from playwright.async_api import Page, expect


@pytest.mark.e2e
class TestAuthenticationFlow:
    """End-to-end tests for complete authentication flow."""
    
    async def test_complete_signup_and_login_flow(self, page: Page):
        """Test complete user journey from signup to login."""
        # Navigate to app
        await page.goto("http://localhost:5173")
        
        # Click signup link
        await page.click('text="Sign Up"')
        await expect(page).to_have_url(/.*\/signup/)
        
        # Fill signup form
        email = f"e2e-{pytest.test_id}@example.com"
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', "TestPassword123")
        
        # Submit signup
        await page.click('button[type="submit"]')
        
        # Should redirect to dashboard
        await expect(page).to_have_url(/.*\/dashboard/)
        await expect(page.locator('text="Welcome"')).to_be_visible()
        
        # Logout
        await page.click('button:has-text("Logout")')
        await expect(page).to_have_url(/.*\/login/)
        
        # Login with same credentials
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', "TestPassword123")
        await page.click('button[type="submit"]')
        
        # Should be back in dashboard
        await expect(page).to_have_url(/.*\/dashboard/)
    
    async def test_signup_validation_errors(self, page: Page):
        """Test signup form validation."""
        await page.goto("http://localhost:5173/signup")
        
        # Try to submit empty form
        await page.click('button[type="submit"]')
        await expect(page.locator('text="Email is required"')).to_be_visible()
        
        # Invalid email
        await page.fill('input[type="email"]', "invalid-email")
        await page.click('button[type="submit"]')
        await expect(page.locator('text="Invalid email"')).to_be_visible()
        
        # Weak password
        await page.fill('input[type="email"]', "valid@example.com")
        await page.fill('input[type="password"]', "weak")
        await page.click('button[type="submit"]')
        await expect(page.locator('text=/password.*8 characters/i')).to_be_visible()
    
    async def test_login_with_wrong_credentials(self, page: Page):
        """Test login error handling."""
        await page.goto("http://localhost:5173/login")
        
        # Try non-existent user
        await page.fill('input[type="email"]', "nonexistent@example.com")
        await page.fill('input[type="password"]', "Password123")
        await page.click('button[type="submit"]')
        
        # Should show error message
        await expect(page.locator('text=/incorrect.*credentials/i')).to_be_visible()
        
        # Should stay on login page
        await expect(page).to_have_url(/.*\/login/)
    
    async def test_protected_route_redirects_to_login(self, page: Page):
        """Test that protected routes redirect unauthenticated users."""
        # Try to access dashboard without login
        await page.goto("http://localhost:5173/dashboard")
        
        # Should redirect to login
        await expect(page).to_have_url(/.*\/login/)
        await expect(page.locator('text="Please log in"')).to_be_visible()
    
    async def test_token_persistence_across_page_reload(self, page: Page):
        """Test that authentication persists after page reload."""
        # Login
        await page.goto("http://localhost:5173/login")
        email = f"persist-{pytest.test_id}@example.com"
        
        # First signup
        await page.click('text="Sign Up"')
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', "PersistPassword123")
        await page.click('button[type="submit"]')
        
        # Verify in dashboard
        await expect(page).to_have_url(/.*\/dashboard/)
        
        # Reload page
        await page.reload()
        
        # Should still be in dashboard (not redirected to login)
        await expect(page).to_have_url(/.*\/dashboard/)
        await expect(page.locator('text="Welcome"')).to_be_visible()
    
    async def test_logout_clears_authentication(self, page: Page):
        """Test that logout properly clears authentication."""
        # Login
        await page.goto("http://localhost:5173/login")
        email = f"logout-{pytest.test_id}@example.com"
        
        # Signup
        await page.click('text="Sign Up"')
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', "LogoutPassword123")
        await page.click('button[type="submit"]')
        
        # Logout
        await page.click('button:has-text("Logout")')
        await expect(page).to_have_url(/.*\/login/)
        
        # Try to access dashboard again
        await page.goto("http://localhost:5173/dashboard")
        
        # Should redirect to login
        await expect(page).to_have_url(/.*\/login/)
    
    async def test_duplicate_email_shows_error(self, page: Page):
        """Test duplicate email error in UI."""
        email = f"duplicate-{pytest.test_id}@example.com"
        
        # First signup
        await page.goto("http://localhost:5173/signup")
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', "Password123")
        await page.click('button[type="submit"]')
        await expect(page).to_have_url(/.*\/dashboard/)
        
        # Logout
        await page.click('button:has-text("Logout")')
        
        # Try to signup again with same email
        await page.click('text="Sign Up"')
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', "DifferentPassword123")
        await page.click('button[type="submit"]')
        
        # Should show error
        await expect(page.locator('text=/already.*registered/i')).to_be_visible()
        await expect(page).to_have_url(/.*\/signup/)
