"""
Module de Self-Correction — Boucle de rétroaction pour corriger le code généré.

Intercepte les erreurs TypeScript (via tsc --noEmit), capture les messages
d'erreur, et renvoie le code erroné au LLM avec un prompt de correction
("Self-Healing") jusqu'à obtenir du code compilable.

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import os
import re
import sys
import json
import shutil
import tempfile
import subprocess
from typing import Any, Optional
from dataclasses import dataclass, field

# Add core to path for prompt_loader
CORE_DIR = os.path.dirname(__file__)
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)


# ── Data Structures ──────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    """Result of a TypeScript validation run."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    raw_output: str = ""
    return_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "error_count": len(self.errors),
            "raw_output": self.raw_output,
        }


@dataclass
class CorrectionAttempt:
    """Record of a single correction attempt."""
    iteration: int
    errors_before: list[str]
    code_after: str
    valid_after: bool


@dataclass
class SelfHealResult:
    """Final result of the self-healing pipeline."""
    original_code: str
    final_code: str
    success: bool
    iterations: int
    max_iterations: int
    attempts: list[CorrectionAttempt] = field(default_factory=list)
    final_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "iterations": self.iterations,
            "max_iterations": self.max_iterations,
            "code_changed": self.original_code != self.final_code,
            "final_errors": self.final_errors,
            "attempts": [
                {
                    "iteration": a.iteration,
                    "errors_before": a.errors_before,
                    "valid_after": a.valid_after,
                }
                for a in self.attempts
            ],
        }


# ── TypeScript Validator ─────────────────────────────────────────────────

# Minimal tsconfig for validation (no emit, strict mode)
VALIDATION_TSCONFIG = {
    "compilerOptions": {
        "target": "ES2022",
        "module": "ESNext",
        "moduleResolution": "bundler",
        "strict": True,
        "noEmit": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "forceConsistentCasingInFileNames": True,
        "types": [],
    },
    "include": ["*.ts"],
}

# Minimal type stubs so tsc knows about Playwright types
PLAYWRIGHT_TYPE_STUB = """
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
"""


class TypeScriptValidator:
    """
    Validates TypeScript code by running tsc --noEmit in a temporary directory.
    Uses minimal type stubs to avoid requiring node_modules installation.
    """

    def __init__(self, tsc_path: str = "npx"):
        """
        Args:
            tsc_path: Path to tsc binary or 'npx' to use npx tsc.
        """
        self.tsc_path = tsc_path

    def validate(self, code: str, filename: str = "test.ts") -> ValidationResult:
        """
        Validate TypeScript code by compiling with --noEmit.

        Args:
            code: TypeScript source code to validate.
            filename: Name for the temporary .ts file.

        Returns:
            ValidationResult with errors list.
        """
        # Create temp directory with the code and type stubs
        tmp_dir = tempfile.mkdtemp(prefix="testgenai_tsc_")

        try:
            # Write tsconfig
            tsconfig_path = os.path.join(tmp_dir, "tsconfig.json")
            with open(tsconfig_path, "w") as f:
                json.dump(VALIDATION_TSCONFIG, f)

            # Write Playwright type stubs
            stubs_path = os.path.join(tmp_dir, "playwright.d.ts")
            with open(stubs_path, "w") as f:
                f.write(PLAYWRIGHT_TYPE_STUB)

            # Write the code to validate
            code_path = os.path.join(tmp_dir, filename)
            with open(code_path, "w") as f:
                f.write(code)

            # Run tsc --noEmit
            cmd = self._build_tsc_command(tmp_dir)
            result = subprocess.run(
                cmd,
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=30,
                shell=isinstance(cmd, str),
            )

            # Parse errors
            errors = self._parse_tsc_output(result.stdout + result.stderr, filename)

            return ValidationResult(
                valid=result.returncode == 0 and len(errors) == 0,
                errors=errors,
                raw_output=(result.stdout + result.stderr).strip(),
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                valid=False,
                errors=["TypeScript compilation timed out (30s)"],
            )
        except FileNotFoundError:
            return ValidationResult(
                valid=False,
                errors=["tsc not found. Install TypeScript: npm i -g typescript"],
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _build_tsc_command(self, cwd: str) -> list[str]:
        """Build the tsc command to run."""
        if self.tsc_path == "npx":
            # Try to find local tsc for speed, otherwise fallback to npx
            core_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(core_dir)
            
            # Typical locations for local tsc in the project
            local_tsc_paths = [
                os.path.join(project_root, "frontend", "node_modules", "typescript", "bin", "tsc"),
                os.path.join(project_root, "templates", "golden_path", "node_modules", "typescript", "bin", "tsc"),
                os.path.join(project_root, "node_modules", "typescript", "bin", "tsc"),
            ]
            
            for tsc in local_tsc_paths:
                if os.path.isfile(tsc):
                    # Use Node to execute the local tsc script
                    return ["node", tsc, "--noEmit", "--pretty", "false"]

            # Fallback to npx (slower due to npm registry check)
            return ["npx", "-y", "-p", "typescript", "tsc", "--noEmit", "--pretty", "false"]
            
        return [self.tsc_path, "--noEmit", "--pretty", "false"]

    def _parse_tsc_output(self, output: str, filename: str) -> list[str]:
        """Parse tsc output into a list of error messages."""
        errors = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # tsc error format: file.ts(line,col): error TS1234: message
            if re.match(r".+\(\d+,\d+\):\s*error\s+TS\d+:", line):
                # Clean up the path prefix for readability
                cleaned = re.sub(r"^.*/", "", line)
                errors.append(cleaned)
            elif "error TS" in line:
                errors.append(line)
        return errors


# ── Self-Healing Prompt ──────────────────────────────────────────────────

SELF_HEALING_SYSTEM_PROMPT = """Tu es un expert TypeScript/Playwright qui corrige des erreurs de compilation.

## RÈGLES STRICTES
1. Tu reçois un code TypeScript contenant des erreurs de compilation.
2. Tu reçois les messages d'erreur exacts du compilateur TypeScript (tsc).
3. Tu DOIS corriger TOUTES les erreurs mentionnées.
4. Tu retournes UNIQUEMENT le code corrigé, sans aucune explication.
5. Ne change PAS la logique fonctionnelle — corrige seulement les erreurs de type/syntaxe.
6. Assure-toi que tous les imports sont présents et corrects.
7. N'ajoute PAS de blocs markdown (pas de ```typescript).

## CORRECTIONS COURANTES
- Import manquant → Ajouter le bon import
- Type incompatible → Corriger le type
- Propriété inexistante → Vérifier l'interface
- Variable non déclarée → Ajouter la déclaration
- Accolades/parenthèses non fermées → Fermer correctement
"""

SELF_HEALING_USER_TEMPLATE = """Le code TypeScript suivant produit des erreurs de compilation.

## CODE ERRONÉ
```
{code}
```

## ERREURS DU COMPILATEUR (tsc --noEmit)
{errors}

## INSTRUCTION
Corrige TOUTES les erreurs ci-dessus et renvoie UNIQUEMENT le code TypeScript corrigé.
Ne change pas la logique, corrige seulement les erreurs de type et de syntaxe."""


# ── Self-Healer Engine ───────────────────────────────────────────────────

class SelfHealer:
    """
    Boucle de rétroaction qui valide le code TypeScript généré par l'IA,
    et si des erreurs sont détectées, renvoie le code au LLM pour correction.

    Pipeline:
        Code → tsc --noEmit → Erreurs? → LLM correction → tsc → ... → Code final
    """

    def __init__(
        self,
        max_iterations: int = 3,
        validator: TypeScriptValidator = None,
    ):
        """
        Args:
            max_iterations: Maximum self-correction attempts.
            validator: Custom TypeScriptValidator instance.
        """
        self.max_iterations = max_iterations
        self.validator = validator or TypeScriptValidator()

    def validate_code(self, code: str, filename: str = "test.ts") -> ValidationResult:
        """
        Run TypeScript validation on the given code without correction.

        Args:
            code: TypeScript source code.
            filename: File name for the temporary file.

        Returns:
            ValidationResult.
        """
        return self.validator.validate(code, filename)

    async def heal(
        self,
        code: str,
        filename: str = "generated.spec.ts",
        llm_invoke=None,
    ) -> SelfHealResult:
        """
        Validate and self-correct TypeScript code.

        Args:
            code: Original TypeScript code to validate/fix.
            filename: Filename for tsc validation.
            llm_invoke: Async callable that takes (system_prompt, user_prompt)
                       and returns corrected code string. If None, uses the
                       AI service from the backend.

        Returns:
            SelfHealResult with the final code and correction history.
        """
        result = SelfHealResult(
            original_code=code,
            final_code=code,
            success=False,
            iterations=0,
            max_iterations=self.max_iterations,
        )

        current_code = code

        for i in range(self.max_iterations):
            # Step 1: Validate
            validation = self.validator.validate(current_code, filename)

            if validation.valid:
                result.final_code = current_code
                result.success = True
                result.iterations = i
                return result

            # Step 2: Attempt correction via LLM
            result.iterations = i + 1

            if llm_invoke is None:
                # No LLM available — return with errors
                result.final_code = current_code
                result.final_errors = validation.errors
                return result

            try:
                corrected_code = await llm_invoke(
                    SELF_HEALING_SYSTEM_PROMPT,
                    SELF_HEALING_USER_TEMPLATE.format(
                        code=current_code,
                        errors="\n".join(f"- {e}" for e in validation.errors),
                    ),
                )

                # Clean up potential markdown wrappers
                corrected_code = re.sub(r"```(typescript|ts)?\n", "", corrected_code)
                corrected_code = corrected_code.replace("```", "").strip()

                # Record the attempt
                attempt = CorrectionAttempt(
                    iteration=i + 1,
                    errors_before=validation.errors,
                    code_after=corrected_code,
                    valid_after=False,  # Will be checked next loop
                )
                result.attempts.append(attempt)

                current_code = corrected_code

            except Exception as e:
                result.final_code = current_code
                result.final_errors = validation.errors + [f"LLM correction failed: {e}"]
                return result

        # Final validation after all iterations
        final_validation = self.validator.validate(current_code, filename)
        result.final_code = current_code
        result.success = final_validation.valid
        result.final_errors = final_validation.errors

        # Update the last attempt's valid_after
        if result.attempts:
            result.attempts[-1].valid_after = final_validation.valid

        return result

    def heal_sync(
        self,
        code: str,
        filename: str = "generated.spec.ts",
        correction_fn=None,
    ) -> SelfHealResult:
        """
        Synchronous version of heal() for testing without async.

        Args:
            code: TypeScript code to validate/fix.
            filename: Filename for validation.
            correction_fn: Sync callable(system_prompt, user_prompt) -> str.

        Returns:
            SelfHealResult.
        """
        result = SelfHealResult(
            original_code=code,
            final_code=code,
            success=False,
            iterations=0,
            max_iterations=self.max_iterations,
        )

        current_code = code

        for i in range(self.max_iterations):
            validation = self.validator.validate(current_code, filename)

            if validation.valid:
                result.final_code = current_code
                result.success = True
                result.iterations = i
                return result

            result.iterations = i + 1

            if correction_fn is None:
                result.final_code = current_code
                result.final_errors = validation.errors
                return result

            try:
                corrected_code = correction_fn(
                    SELF_HEALING_SYSTEM_PROMPT,
                    SELF_HEALING_USER_TEMPLATE.format(
                        code=current_code,
                        errors="\n".join(f"- {e}" for e in validation.errors),
                    ),
                )

                corrected_code = re.sub(r"```(typescript|ts)?\n", "", corrected_code)
                corrected_code = corrected_code.replace("```", "").strip()

                attempt = CorrectionAttempt(
                    iteration=i + 1,
                    errors_before=validation.errors,
                    code_after=corrected_code,
                    valid_after=False,
                )
                result.attempts.append(attempt)
                current_code = corrected_code

            except Exception as e:
                result.final_code = current_code
                result.final_errors = validation.errors + [f"Correction failed: {e}"]
                return result

        final_validation = self.validator.validate(current_code, filename)
        result.final_code = current_code
        result.success = final_validation.valid
        result.final_errors = final_validation.errors

        if result.attempts:
            result.attempts[-1].valid_after = final_validation.valid

        return result
