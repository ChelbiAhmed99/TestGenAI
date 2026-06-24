declare module '@playwright/test' {
  export interface Page {
    goto(url: string, options?: any): Promise<any>;
    locator(selector: string): Locator;
    getByRole(role: string, options?: any): Locator;
    getByText(text: string | RegExp, options?: any): Locator;
    getByTestId(testId: string): Locator;
    waitForURL(url: string | RegExp, options?: any): Promise<void>;
    url(): string;
    title(): Promise<string>;
  }
  export interface Locator {
    click(options?: any): Promise<void>;
    fill(value: string, options?: any): Promise<void>;
    textContent(options?: any): Promise<string | null>;
    isVisible(options?: any): Promise<boolean>;
    isEnabled(options?: any): Promise<boolean>;
    count(): Promise<number>;
    nth(index: number): Locator;
  }
  export interface TestInfo { }
  export interface TestType {
    (title: string, body: (args: { page: Page }) => Promise<void>): void;
    describe(title: string, body: () => void): void;
    beforeEach(body: (args: { page: Page }) => Promise<void>): void;
    afterEach(body: (args: { page: Page }) => Promise<void>): void;
    step(title: string, body: () => Promise<void>): Promise<void>;
  }
  export const test: TestType;
  export const expect: any;
  export function defineConfig(config: any): any;
  export const devices: Record<string, any>;
}
