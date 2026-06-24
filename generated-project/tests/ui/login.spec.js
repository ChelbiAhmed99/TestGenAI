import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/LoginPage';

test.describe('Feature: User Authentication', () => {
  test('Scenario: Positive login scenario', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await test.step('Given the user is on the login page', async () => {
      await loginPage.goto();
    });
    await test.step('When the user enters a valid email and password', async () => {
      await loginPage.login('user@example.com', 'ValidPass123!');
    });
    await test.step('Then the system should redirect to the dashboard', async () => {
      await expect(page).toHaveURL(/.*dashboard/);
    });
  });

  test('Scenario: Invalid password scenario', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await test.step('Given the user is on the login page', async () => {
      await loginPage.goto();
    });
    await test.step('When the user enters a valid email but an invalid password', async () => {
      await loginPage.login('user@example.com', 'WrongPass!');
    });
    await test.step('Then the system should display an "Invalid credentials" error message', async () => {
      await expect(loginPage.errorMessage).toHaveText(/Invalid credentials/i);
    });
  });
});
