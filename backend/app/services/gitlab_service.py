import os
import base64
import json
import re
from typing import Optional
import httpx

GITLAB_URL  = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
GITLAB_NAMESPACE = os.getenv("GITLAB_NAMESPACE", "")   # group or username


class GitLabService:
    """
    Enterprise GitLab integration service.
    Handles project creation, file scaffolding and CI/CD pipeline generation
    entirely on the GitLab side (no local disk writes needed).
    """

    # ------------------------------------------------------------------ #
    #   Helpers                                                            #
    # ------------------------------------------------------------------ #
    def _headers(self) -> dict:
        return {"PRIVATE-TOKEN": GITLAB_TOKEN, "Content-Type": "application/json"}

    def _encode(self, content: str) -> str:
        return base64.b64encode(content.encode()).decode()

    def _slug(self, name: str) -> str:
        return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")

    # ------------------------------------------------------------------ #
    #   CI/CD Pipeline Generator                                          #
    # ------------------------------------------------------------------ #
    def generate_ci_config(self, project_name: str = "testgenai") -> str:
        return f"""# TestGenAI — Auto-generated GitLab CI/CD Pipeline
# Project: {project_name}
# Powered by TestGenAI Enterprise Platform

stages:
  - install
  - test
  - report

variables:
  NODE_VERSION: "18"
  PLAYWRIGHT_VERSION: "1.42.0"

# ── Install dependencies ──────────────────────────────────
install_deps:
  stage: install
  image: mcr.microsoft.com/playwright:v{"{PLAYWRIGHT_VERSION}"}-jammy
  cache:
    key: "${{CI_COMMIT_REF_SLUG}}-deps"
    paths:
      - node_modules/
  script:
    - npm ci
  artifacts:
    paths:
      - node_modules/
    expire_in: 1h

# ── Run Playwright Tests ──────────────────────────────────
run_playwright:
  stage: test
  image: mcr.microsoft.com/playwright:v{"{PLAYWRIGHT_VERSION}"}-jammy
  dependencies:
    - install_deps
  script:
    - npx playwright test --reporter=line,json,allure-playwright
  artifacts:
    when: always
    paths:
      - allure-results/
      - test-results/
      - playwright-report/
    reports:
      junit: test-results/junit.xml
    expire_in: 7 days
  allow_failure: false

# ── Allure / Cucumber Report ───────────────────────────────
generate_report:
  stage: report
  image: frankescobar/allure-docker-service:latest
  dependencies:
    - run_playwright
  script:
    - allure generate allure-results -o allure-report --clean
  artifacts:
    paths:
      - allure-report/
    expire_in: 30 days
  pages:
    - allure-report/
"""

    # ------------------------------------------------------------------ #
    #   Playwright project scaffold                                        #
    # ------------------------------------------------------------------ #
    def _scaffold_files(self, project_name: str, gherkin: str, script: str) -> list[dict]:
        """
        Returns a list of GitLab API file-action dicts ready to be committed.
        Produces a full TypeScript Playwright project following Page Object Model.
        """
        pkg_json = json.dumps({
            "name": self._slug(project_name),
            "version": "1.0.0",
            "description": f"Auto-generated test project for {project_name}",
            "scripts": {
                "test": "npx playwright test",
                "test:headed": "npx playwright test --headed",
                "test:report": "npx playwright show-report"
            },
            "devDependencies": {
                "@playwright/test": "^1.42.0",
                "allure-playwright": "^2.13.0",
                "typescript": "^5.3.3"
            }
        }, indent=2)

        tsconfig = json.dumps({
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "lib": ["es2020"],
                "strict": True,
                "esModuleInterop": True,
                "outDir": "./dist",
                "rootDir": "./",
                "types": ["@playwright/test"]
            },
            "include": ["**/*.ts"],
            "exclude": ["node_modules", "dist"]
        }, indent=2)

        pw_config = """import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['line'],
    ['allure-playwright'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
});
"""

        readme = f"""# {project_name} — Auto-Generated Test Suite

> 🤖 Generated by **TestGenAI Enterprise Platform**

## Structure

```
.
├── pages/           # Page Object Model (POM) classes
├── tests/           # Playwright test specifications
├── features/        # Gherkin feature files
├── playwright.config.ts
├── tsconfig.json
└── package.json
```

## Quick Start

```bash
npm install
npx playwright install --with-deps
npm test
```

## CI/CD

This project ships with a `.gitlab-ci.yml` pipeline that:
1. Installs dependencies
2. Runs all Playwright tests
3. Generates an Allure report and publishes it as a GitLab Pages artifact
"""

        gitignore = """node_modules/
dist/
allure-results/
allure-report/
playwright-report/
test-results/
.env
"""

        feature_file = gherkin if gherkin else (
            f"Feature: {project_name}\n\n"
            "  Scenario: Placeholder\n"
            "    Given the application is running\n"
            "    When the user navigates to the home page\n"
            "    Then the home page should be visible\n"
        )

        test_script_file = script if script else (
            "import { test, expect, Page, Locator } from '@playwright/test';\n\n"
            "// TODO: Add generated Page Object Model and test steps here.\n"
        )

        ci_yaml = self.generate_ci_config(project_name)

        return [
            {"action": "create", "file_path": "package.json",           "content": pkg_json},
            {"action": "create", "file_path": "tsconfig.json",           "content": tsconfig},
            {"action": "create", "file_path": "playwright.config.ts",    "content": pw_config},
            {"action": "create", "file_path": "README.md",               "content": readme},
            {"action": "create", "file_path": ".gitignore",              "content": gitignore},
            {"action": "create", "file_path": ".gitlab-ci.yml",          "content": ci_yaml},
            {"action": "create", "file_path": f"features/{self._slug(project_name)}.feature", "content": feature_file},
            {"action": "create", "file_path": f"tests/{self._slug(project_name)}.spec.ts",    "content": test_script_file},
        ]

    # ------------------------------------------------------------------ #
    #   Main: Create GitLab project + push scaffold                       #
    # ------------------------------------------------------------------ #
    async def create_and_push_project(
        self,
        project_name: str,
        gherkin: str,
        script: str,
        namespace: Optional[str] = None,
    ) -> dict:
        """
        1. Creates a new private GitLab project.
        2. Scaffolds a full Playwright TypeScript project via a single commit.
        Returns project URL and status.
        """
        if not GITLAB_TOKEN:
            # Demo mode — return a simulated response
            slug = self._slug(project_name)
            return {
                "status": "demo",
                "message": "Configure GITLAB_TOKEN env var to push real projects.",
                "project_url": f"https://gitlab.com/demo-org/{slug}",
                "pipeline_url": f"https://gitlab.com/demo-org/{slug}/-/pipelines",
            }

        ns = namespace or GITLAB_NAMESPACE
        async with httpx.AsyncClient(timeout=30) as client:
            # 1 — Create project
            payload = {
                "name": project_name,
                "path": self._slug(project_name),
                "visibility": "private",
                "initialize_with_readme": False,
                "description": f"Auto-generated by TestGenAI for {project_name}",
            }
            if ns:
                payload["namespace_path"] = ns

            resp = await client.post(
                f"{GITLAB_URL}/api/v4/projects",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"GitLab project creation failed: {resp.text}")

            project = resp.json()
            project_id = project["id"]
            project_url = project["web_url"]

            # 2 — Push scaffold files in a single commit
            files = self._scaffold_files(project_name, gherkin, script)
            commit_payload = {
                "branch": "main",
                "commit_message": "🤖 chore: initial scaffold by TestGenAI Enterprise",
                "actions": files,
            }
            commit_resp = await client.post(
                f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/commits",
                headers=self._headers(),
                json=commit_payload,
            )
            if commit_resp.status_code not in (200, 201):
                raise RuntimeError(f"GitLab commit failed: {commit_resp.text}")

            return {
                "status": "success",
                "project_url": project_url,
                "pipeline_url": f"{project_url}/-/pipelines",
                "project_id": project_id,
            }


gitlab_service = GitLabService()
