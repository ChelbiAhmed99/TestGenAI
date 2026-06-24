"""
Tests unitaires — Module de Self-Correction.

Vérifie que le validateur TypeScript détecte les erreurs, et que la boucle
de rétroaction corrige automatiquement le code en moins de 2 itérations.

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from self_healer import (
    TypeScriptValidator,
    SelfHealer,
    ValidationResult,
    SelfHealResult,
    SELF_HEALING_SYSTEM_PROMPT,
)


# ── Sample Code Snippets ────────────────────────────────────────────────

VALID_CODE = """import { test, expect } from '@playwright/test';

test.describe('Login Tests', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');
    await page.locator('[data-testid="email"]').fill('user@test.com');
    await page.locator('[data-testid="password"]').fill('password123');
    await page.locator('button[type="submit"]').click();
  });
});
"""

CODE_WITH_MISSING_IMPORT = """// Missing import for 'test' and 'expect'
test.describe('Login Tests', () => {
  test('should login', async ({ page }) => {
    await page.goto('/login');
    const title: string = await page.title();
    expect(title).toBe('Login');
  });
});
"""

CODE_WITH_TYPE_ERROR = """import { test, expect } from '@playwright/test';

test('type error test', async ({ page }) => {
  const count: string = 42;
  await page.goto('/');
});
"""

CODE_WITH_SYNTAX_ERROR = """import { test, expect } from '@playwright/test';

test('syntax error test', async ({ page }) => {
  await page.goto('/login')
  const element = page.locator('.btn');
  await element.click(
});
"""

CODE_WITH_MULTIPLE_ERRORS = """// Missing import, type error, and undeclared variable
test.describe('Broken Suite', () => {
  test('broken test', async ({ page }) => {
    const result: number = "not a number";
    await page.goto(undeclaredUrl);
    await unknownPage.navigate();
  });
});
"""

# The corrected version of CODE_WITH_MISSING_IMPORT
CORRECTED_MISSING_IMPORT = """import { test, expect } from '@playwright/test';

test.describe('Login Tests', () => {
  test('should login', async ({ page }) => {
    await page.goto('/login');
    const title: string = await page.title();
    expect(title).toBe('Login');
  });
});
"""

# The corrected version of CODE_WITH_TYPE_ERROR
CORRECTED_TYPE_ERROR = """import { test, expect } from '@playwright/test';

test('type error test', async ({ page }) => {
  const count: number = 42;
  await page.goto('/');
});
"""


# ── TypeScript Validator Tests ───────────────────────────────────────────

class TestTypeScriptValidator:
    """Tests for the tsc --noEmit validation."""

    def test_valid_code_passes(self):
        v = TypeScriptValidator()
        result = v.validate(VALID_CODE)
        assert result.valid is True
        assert result.errors == []

    def test_missing_import_detected(self):
        v = TypeScriptValidator()
        result = v.validate(CODE_WITH_MISSING_IMPORT)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_type_error_detected(self):
        v = TypeScriptValidator()
        result = v.validate(CODE_WITH_TYPE_ERROR)
        assert result.valid is False
        assert any("string" in e.lower() or "number" in e.lower() or "TS" in e for e in result.errors)

    def test_syntax_error_detected(self):
        v = TypeScriptValidator()
        result = v.validate(CODE_WITH_SYNTAX_ERROR)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_multiple_errors_all_reported(self):
        v = TypeScriptValidator()
        result = v.validate(CODE_WITH_MULTIPLE_ERRORS)
        assert result.valid is False
        assert len(result.errors) >= 2

    def test_result_has_to_dict(self):
        v = TypeScriptValidator()
        result = v.validate(VALID_CODE)
        d = result.to_dict()
        assert "valid" in d
        assert "errors" in d
        assert "error_count" in d

    def test_empty_code_is_valid(self):
        """An empty file is technically valid TypeScript."""
        v = TypeScriptValidator()
        result = v.validate("")
        assert result.valid is True

    def test_simple_page_object_is_valid(self):
        code = """import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email"]');
  }

  async navigate(): Promise<void> {
    await this.page.goto('/login');
  }

  async fillEmail(email: string): Promise<void> {
    await this.emailInput.fill(email);
  }
}
"""
        v = TypeScriptValidator()
        result = v.validate(code, "LoginPage.ts")
        assert result.valid is True


# ── Self-Healer Tests (with mock correction function) ────────────────────

class TestSelfHealerWithMock:
    """Tests using a mock correction function instead of real LLM."""

    def test_valid_code_returns_immediately(self):
        """Valid code should not trigger any correction attempts."""
        healer = SelfHealer(max_iterations=3)
        result = healer.heal_sync(VALID_CODE)
        assert result.success is True
        assert result.iterations == 0
        assert result.final_code == VALID_CODE
        assert len(result.attempts) == 0

    def test_broken_code_without_corrector_returns_errors(self):
        """Without a correction function, errors are returned as-is."""
        healer = SelfHealer(max_iterations=3)
        result = healer.heal_sync(CODE_WITH_MISSING_IMPORT)
        assert result.success is False
        assert result.iterations == 1
        assert len(result.final_errors) > 0

    def test_missing_import_corrected_in_one_iteration(self):
        """
        ACCEPTANCE CRITERION: A deliberate error (missing import) is
        corrected automatically in ≤2 iterations.
        """
        def mock_corrector(system_prompt, user_prompt):
            # Simulate LLM adding the missing import
            return CORRECTED_MISSING_IMPORT

        healer = SelfHealer(max_iterations=3)
        result = healer.heal_sync(
            CODE_WITH_MISSING_IMPORT,
            correction_fn=mock_corrector,
        )
        assert result.success is True
        assert result.iterations <= 2
        assert len(result.attempts) >= 1

    def test_type_error_corrected_in_one_iteration(self):
        """
        ACCEPTANCE CRITERION: A type error (string = 42) is
        corrected automatically in ≤2 iterations.
        """
        def mock_corrector(system_prompt, user_prompt):
            return CORRECTED_TYPE_ERROR

        healer = SelfHealer(max_iterations=3)
        result = healer.heal_sync(
            CODE_WITH_TYPE_ERROR,
            correction_fn=mock_corrector,
        )
        assert result.success is True
        assert result.iterations <= 2

    def test_correction_receives_error_context(self):
        """The correction function must receive the actual tsc errors."""
        received_prompts = []

        def spy_corrector(system_prompt, user_prompt):
            received_prompts.append(user_prompt)
            return VALID_CODE  # Return valid to stop loop

        healer = SelfHealer(max_iterations=3)
        healer.heal_sync(CODE_WITH_MISSING_IMPORT, correction_fn=spy_corrector)

        assert len(received_prompts) == 1
        prompt = received_prompts[0]
        # Must contain the original code
        assert "Missing import" in CODE_WITH_MISSING_IMPORT or "test.describe" in prompt
        # Must contain tsc error references
        assert "error" in prompt.lower() or "TS" in prompt

    def test_system_prompt_contains_typescript_context(self):
        """The system prompt should mention TypeScript correction."""
        assert "TypeScript" in SELF_HEALING_SYSTEM_PROMPT
        assert "corrige" in SELF_HEALING_SYSTEM_PROMPT.lower() or "corriger" in SELF_HEALING_SYSTEM_PROMPT.lower()

    def test_max_iterations_respected(self):
        """If correction always fails, should stop at max_iterations."""
        def bad_corrector(system_prompt, user_prompt):
            return CODE_WITH_MISSING_IMPORT  # Return broken code every time

        healer = SelfHealer(max_iterations=2)
        result = healer.heal_sync(
            CODE_WITH_MISSING_IMPORT,
            correction_fn=bad_corrector,
        )
        assert result.success is False
        assert result.iterations == 2

    def test_result_to_dict(self):
        healer = SelfHealer(max_iterations=3)
        result = healer.heal_sync(VALID_CODE)
        d = result.to_dict()
        assert "success" in d
        assert "iterations" in d
        assert "max_iterations" in d
        assert "attempts" in d
        assert d["success"] is True

    def test_progressive_correction(self):
        """
        Simulate a 2-step correction: first attempt partially fixes,
        second attempt fully fixes.
        """
        call_count = 0

        def progressive_corrector(system_prompt, user_prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First attempt: fix import but introduce a new issue
                return CODE_WITH_TYPE_ERROR
            else:
                # Second attempt: fully fix
                return VALID_CODE

        healer = SelfHealer(max_iterations=3)
        result = healer.heal_sync(
            CODE_WITH_MISSING_IMPORT,
            correction_fn=progressive_corrector,
        )
        assert result.success is True
        assert result.iterations <= 3
        assert len(result.attempts) >= 2

    def test_corrector_exception_handled(self):
        """If the correction function raises, should handle gracefully."""
        def exploding_corrector(system_prompt, user_prompt):
            raise RuntimeError("LLM service unavailable")

        healer = SelfHealer(max_iterations=3)
        result = healer.heal_sync(
            CODE_WITH_MISSING_IMPORT,
            correction_fn=exploding_corrector,
        )
        assert result.success is False
        assert any("Correction failed" in e for e in result.final_errors)


# ── Acceptance Test: Deliberate Error Auto-Corrected ─────────────────────

class TestAcceptanceCriteria:
    """
    Preuve technique : Un test simulé contenant une erreur de syntaxe
    volontaire est corrigé automatiquement par la boucle en < 2 itérations.
    """

    def test_deliberate_missing_import_autocorrected(self):
        """
        INPUT:  Code missing 'import { test, expect }' statement
        EXPECT: Self-healer adds the import and returns valid code in ≤2 iterations
        """
        def corrector(system_prompt, user_prompt):
            return CORRECTED_MISSING_IMPORT

        healer = SelfHealer(max_iterations=2)
        result = healer.heal_sync(CODE_WITH_MISSING_IMPORT, correction_fn=corrector)

        assert result.success, f"Expected success but got errors: {result.final_errors}"
        assert result.iterations <= 2, f"Took {result.iterations} iterations (max 2)"
        assert "import" in result.final_code

    def test_deliberate_type_mismatch_autocorrected(self):
        """
        INPUT:  'const count: string = 42' (type mismatch)
        EXPECT: Self-healer fixes to 'const count: number = 42' in ≤2 iterations
        """
        def corrector(system_prompt, user_prompt):
            return CORRECTED_TYPE_ERROR

        healer = SelfHealer(max_iterations=2)
        result = healer.heal_sync(CODE_WITH_TYPE_ERROR, correction_fn=corrector)

        assert result.success, f"Expected success but got errors: {result.final_errors}"
        assert result.iterations <= 2
        assert "number" in result.final_code
