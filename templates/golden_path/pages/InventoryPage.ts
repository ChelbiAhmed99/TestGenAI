import { Page, Locator } from '@playwright/test';

export class InventoryPage {
  readonly page: Page;
  readonly titleHeader: Locator;
  readonly shoppingCart: Locator;

  constructor(page: Page) {
    this.page = page;
    this.titleHeader = page.locator('[data-test="title"]'); // standard SauceDemo title header
    this.shoppingCart = page.locator('[data-test="shopping-cart-link"]');
  }

  async getTitleText(): Promise<string> {
    return await this.titleHeader.textContent() || '';
  }

  async isShoppingCartVisible(): Promise<boolean> {
    return await this.shoppingCart.isVisible();
  }
}
