import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { InventoryPage } from '../pages/InventoryPage';

test.describe('SauceDemo User Authentication Tests', () => {
  let loginPage: LoginPage;
  let inventoryPage: InventoryPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    inventoryPage = new InventoryPage(page);
  });

  test('Scenario: Successful Login with Valid Credentials', async () => {
    await test.step('Given the user is on the SauceDemo login page', async () => {
      await loginPage.navigate();
    });

    await test.step('When the user enters the username "standard_user" and the password "secret_sauce"', async () => {
      // Inputs are filled inside the page object wrapper
      await loginPage.usernameInput.fill('standard_user');
      await loginPage.passwordInput.fill('secret_sauce');
    });

    await test.step('And clicks the login button', async () => {
      await loginPage.loginButton.click();
    });

    await test.step('Then the user should be redirected to the inventory page', async () => {
      await expect(loginPage.page).toHaveURL(/.*inventory.html/);
    });

    await test.step('And should see the products list header "Products"', async () => {
      const title = await inventoryPage.getTitleText();
      expect(title).toBe('Products');
      await expect(inventoryPage.shoppingCart).toBeVisible();
    });
  });

  test('Scenario: Failed Login with Invalid Credentials', async () => {
    await test.step('Given the user is on the SauceDemo login page', async () => {
      await loginPage.navigate();
    });

    await test.step('When the user enters the username "invalid_user" and the password "wrong_password"', async () => {
      await loginPage.usernameInput.fill('invalid_user');
      await loginPage.passwordInput.fill('wrong_password');
    });

    await test.step('And clicks the login button', async () => {
      await loginPage.loginButton.click();
    });

    await test.step('Then the user should see an error message containing "Epic sadface: Username and password do not match any user in this service"', async () => {
      const errorMsg = await loginPage.getErrorMessageText();
      expect(errorMsg).toContain('Epic sadface: Username and password do not match any user in this service');
      await expect(loginPage.errorMessage).toBeVisible();
    });
  });
});
