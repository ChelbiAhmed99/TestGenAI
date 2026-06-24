# Golden Path Template — Gherkin & Page Object Model (POM)

This directory serves as the **Ground Truth** (Vérité Terrain) template for the AI code generation engine. It demonstrates the ideal files, structure, and design patterns to be produced.

## Contents
- `login.feature`: The Gherkin specification file defining scenarios for successful and failed authentication.
- `pages/LoginPage.ts`: Page Object class representing elements and actions on the SauceDemo login page.
- `pages/InventoryPage.ts`: Page Object class representing elements and actions on the post-login inventory page.
- `tests/login.spec.ts`: The Playwright test script executing Gherkin steps via Page Objects.
- `playwright.config.ts`: Configuration settings for Playwright runs.

## Setup & Execution
To run these reference tests locally:
```bash
cd templates/golden_path
npm install
npx playwright install
npm run test
```
