import { test, expect } from '@playwright/test';

test.describe('Login Tests', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');
    await page.locator('[data-testid="email"]').fill('user@test.com');
    await page.locator('[data-testid="password"]').fill('password123');
    await page.locator('button[type="submit"]').click();
  });
});
