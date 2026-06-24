"""
Validateur de syntaxe Gherkin.

Vérifie que les scénarios générés par l'IA respectent la syntaxe Gherkin
officielle et ne contiennent aucun mot-clé inventé.

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import json
import re
from typing import Any

try:
    from .prompt_loader import get_validation_rules
except ImportError:
    try:
        from prompt_loader import get_validation_rules
    except ImportError:
        def get_validation_rules():
            return {}


# Official Gherkin keywords
ALLOWED_KEYWORDS = {
    "Feature", "Background", "Scenario", "Scenario Outline",
    "Given", "When", "Then", "And", "But", "Examples", "*",
}

# Keywords that an AI might hallucinate (French translations, etc.)
FORBIDDEN_KEYWORDS = {
    "Étant donné", "Lorsque", "Alors", "Et que", "Soit",
    "Fonctionnalité", "Scénario", "Contexte",
}

STEP_KEYWORDS = {"Given", "When", "Then", "And", "But", "*"}


class GherkinValidationError(Exception):
    """Raised when Gherkin validation fails."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Gherkin validation failed: {'; '.join(errors)}")


def validate_gherkin_text(gherkin_text: str) -> list[str]:
    """
    Validate raw Gherkin text for syntax correctness.

    Args:
        gherkin_text: Raw Gherkin feature text.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    lines = gherkin_text.strip().split("\n")

    if not lines:
        return ["Empty Gherkin content"]

    # Check for Feature keyword
    has_feature = False
    has_scenario = False
    current_scenario_has_given = False
    current_scenario_has_when = False
    current_scenario_has_then = False
    scenario_title = ""

    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.strip()

        # Skip empty lines, comments, tags
        if not line or line.startswith("#") or line.startswith("@"):
            continue

        # Skip table rows and docstrings
        if line.startswith("|") or line.startswith('"""') or line.startswith("'''"):
            continue

        # Check for forbidden keywords
        for forbidden in FORBIDDEN_KEYWORDS:
            if line.startswith(forbidden):
                errors.append(
                    f"Line {line_num}: Forbidden keyword '{forbidden}' used. "
                    f"Use official English Gherkin keywords only."
                )

        # Parse known keywords
        if line.startswith("Feature:"):
            has_feature = True
        elif line.startswith("Background:"):
            pass
        elif line.startswith("Scenario Outline:") or line.startswith("Scenario:"):
            # Validate previous scenario completeness
            if has_scenario:
                _check_scenario_structure(
                    errors, scenario_title,
                    current_scenario_has_given,
                    current_scenario_has_when,
                    current_scenario_has_then,
                )
            has_scenario = True
            scenario_title = line.split(":", 1)[1].strip() if ":" in line else "Untitled"
            current_scenario_has_given = False
            current_scenario_has_when = False
            current_scenario_has_then = False
        elif line.startswith("Given ") or line.startswith("Given "):
            current_scenario_has_given = True
        elif line.startswith("When "):
            current_scenario_has_when = True
        elif line.startswith("Then "):
            current_scenario_has_then = True
        elif line.startswith("And ") or line.startswith("But "):
            pass  # Continuation of previous keyword
        elif line.startswith("Examples:"):
            pass

    # Validate last scenario
    if has_scenario:
        _check_scenario_structure(
            errors, scenario_title,
            current_scenario_has_given,
            current_scenario_has_when,
            current_scenario_has_then,
        )

    if not has_feature:
        errors.append("Missing 'Feature:' keyword at the beginning")

    if not has_scenario:
        errors.append("No 'Scenario:' found in the Gherkin content")

    return errors


def validate_gherkin_json(json_data: dict | str) -> list[str]:
    """
    Validate the structured JSON output from the AI.

    Args:
        json_data: Either a JSON string or parsed dict.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    if isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return [f"Invalid JSON: {e}"]

    if not isinstance(json_data, dict):
        return ["JSON output must be an object"]

    # Check required top-level fields
    if "feature_title" not in json_data:
        errors.append("Missing 'feature_title' in JSON output")

    scenarios = json_data.get("scenarios", [])
    if not scenarios:
        errors.append("No scenarios found in JSON output")
        return errors

    for i, scenario in enumerate(scenarios):
        prefix = f"Scenario[{i}]"

        if "title" not in scenario:
            errors.append(f"{prefix}: Missing 'title'")

        if "type" not in scenario:
            errors.append(f"{prefix}: Missing 'type'")
        elif scenario["type"] not in ("Scenario", "Scenario Outline"):
            errors.append(
                f"{prefix}: Invalid type '{scenario['type']}'. "
                f"Must be 'Scenario' or 'Scenario Outline'."
            )

        steps = scenario.get("steps", [])
        if not steps:
            errors.append(f"{prefix}: No steps defined")
            continue

        has_given = has_when = has_then = False
        for j, step in enumerate(steps):
            kw = step.get("keyword", "")
            if kw not in STEP_KEYWORDS:
                errors.append(
                    f"{prefix}.steps[{j}]: Invalid keyword '{kw}'. "
                    f"Allowed: {', '.join(sorted(STEP_KEYWORDS))}"
                )
            if kw == "Given":
                has_given = True
            elif kw == "When":
                has_when = True
            elif kw == "Then":
                has_then = True

            if "text" not in step or not step["text"].strip():
                errors.append(f"{prefix}.steps[{j}]: Empty step text")

        if not has_given:
            errors.append(f"{prefix} '{scenario.get('title', '')}': Missing 'Given' step")
        if not has_when:
            errors.append(f"{prefix} '{scenario.get('title', '')}': Missing 'When' step")
        if not has_then:
            errors.append(f"{prefix} '{scenario.get('title', '')}': Missing 'Then' step")

        # Validate Scenario Outline has Examples
        if scenario.get("type") == "Scenario Outline" and "examples" not in scenario:
            errors.append(f"{prefix}: 'Scenario Outline' must have 'examples'")

    return errors


def json_to_gherkin(json_data: dict) -> str:
    """
    Convert validated JSON structure back to raw Gherkin text.

    Args:
        json_data: Structured scenario JSON.

    Returns:
        Raw Gherkin feature file content.
    """
    lines = []
    lines.append(f"Feature: {json_data.get('feature_title', 'Untitled')}")
    if json_data.get("feature_description"):
        lines.append(f"  {json_data['feature_description']}")
    lines.append("")

    for scenario in json_data.get("scenarios", []):
        # Tags
        tags = scenario.get("tags", [])
        if tags:
            lines.append(f"  {' '.join(tags)}")

        # Scenario title
        stype = scenario.get("type", "Scenario")
        lines.append(f"  {stype}: {scenario.get('title', 'Untitled')}")

        # Steps
        for step in scenario.get("steps", []):
            lines.append(f"    {step['keyword']} {step['text']}")

        # Examples for Scenario Outline
        if stype == "Scenario Outline" and "examples" in scenario:
            examples = scenario["examples"]
            headers = examples.get("headers", [])
            rows = examples.get("rows", [])
            lines.append("")
            lines.append("    Examples:")
            if headers:
                lines.append(f"      | {' | '.join(headers)} |")
            for row in rows:
                lines.append(f"      | {' | '.join(str(c) for c in row)} |")

        lines.append("")

    return "\n".join(lines)


def _check_scenario_structure(
    errors: list[str], title: str,
    has_given: bool, has_when: bool, has_then: bool
):
    """Helper to check Given/When/Then completeness."""
    if not has_given:
        errors.append(f"Scenario '{title}': Missing 'Given' step")
    if not has_when:
        errors.append(f"Scenario '{title}': Missing 'When' step")
    if not has_then:
        errors.append(f"Scenario '{title}': Missing 'Then' step")
