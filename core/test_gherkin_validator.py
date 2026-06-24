"""
Tests unitaires — Validateur de syntaxe Gherkin.

Vérifie que le validateur détecte correctement les erreurs de syntaxe
dans les scénarios Gherkin (texte brut et format JSON structuré).

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import json
import os
import sys
import pytest

# Ensure core directory is in path
sys.path.insert(0, os.path.dirname(__file__))

from gherkin_validator import (
    validate_gherkin_text,
    validate_gherkin_json,
    json_to_gherkin,
    GherkinValidationError,
    ALLOWED_KEYWORDS,
    FORBIDDEN_KEYWORDS,
)


# ── Raw Gherkin Text Validation ─────────────────────────────────────────

class TestValidateGherkinTextValid:
    """Tests with valid Gherkin text."""

    VALID_GHERKIN = """Feature: User Authentication
  
  Scenario: Successful login
    Given the user is on the login page
    When the user enters valid credentials
    Then the user is redirected to the dashboard
"""

    def test_valid_gherkin_returns_no_errors(self):
        errors = validate_gherkin_text(self.VALID_GHERKIN)
        assert errors == []

    def test_valid_gherkin_with_and_but(self):
        gherkin = """Feature: Shopping Cart
  Scenario: Add item to cart
    Given the user is browsing products
    And the cart is empty
    When the user clicks "Add to Cart"
    But the item is out of stock
    Then an error message is shown
"""
        errors = validate_gherkin_text(gherkin)
        assert errors == []

    def test_valid_gherkin_with_background(self):
        gherkin = """Feature: Checkout
  Background:
    Given the user is logged in
    And the cart has items

  Scenario: Complete checkout
    Given the user is on the checkout page
    When the user clicks "Pay Now"
    Then the order is confirmed
"""
        errors = validate_gherkin_text(gherkin)
        assert errors == []

    def test_valid_scenario_outline(self):
        gherkin = """Feature: Login Validation
  Scenario Outline: Login with various credentials
    Given the user is on the login page
    When the user enters email "<email>"
    And the user enters password "<password>"
    Then the result is "<result>"

    Examples:
      | email           | password  | result  |
      | valid@test.com  | Valid123  | success |
      | invalid@test.com| wrong     | error   |
"""
        errors = validate_gherkin_text(gherkin)
        assert errors == []


class TestValidateGherkinTextInvalid:
    """Tests with invalid Gherkin text."""

    def test_empty_content(self):
        errors = validate_gherkin_text("")
        assert len(errors) > 0

    def test_missing_feature(self):
        gherkin = """Scenario: No feature keyword
    Given something
    When something happens
    Then something is expected
"""
        errors = validate_gherkin_text(gherkin)
        assert any("Feature" in e for e in errors)

    def test_missing_scenario(self):
        gherkin = """Feature: No scenarios at all
"""
        errors = validate_gherkin_text(gherkin)
        assert any("Scenario" in e for e in errors)

    def test_scenario_missing_given(self):
        gherkin = """Feature: Incomplete Scenario
  Scenario: Missing Given
    When something happens
    Then something is expected
"""
        errors = validate_gherkin_text(gherkin)
        assert any("Given" in e for e in errors)

    def test_scenario_missing_when(self):
        gherkin = """Feature: Incomplete Scenario
  Scenario: Missing When
    Given something exists
    Then something is expected
"""
        errors = validate_gherkin_text(gherkin)
        assert any("When" in e for e in errors)

    def test_scenario_missing_then(self):
        gherkin = """Feature: Incomplete Scenario
  Scenario: Missing Then
    Given something exists
    When something happens
"""
        errors = validate_gherkin_text(gherkin)
        assert any("Then" in e for e in errors)

    def test_forbidden_french_keywords(self):
        gherkin = """Feature: French Keywords
  Scenario: French steps
    Étant donné something
    When something
    Then something
"""
        errors = validate_gherkin_text(gherkin)
        assert any("Forbidden" in e or "forbidden" in e.lower() for e in errors)


# ── JSON Output Validation ──────────────────────────────────────────────

class TestValidateGherkinJsonValid:
    """Tests with valid JSON structures."""

    VALID_JSON = {
        "feature_title": "User Authentication",
        "scenarios": [
            {
                "type": "Scenario",
                "title": "Successful login",
                "steps": [
                    {"keyword": "Given", "text": "the user is on the login page"},
                    {"keyword": "When", "text": "the user enters valid credentials"},
                    {"keyword": "Then", "text": "the user is redirected to dashboard"},
                ],
            }
        ],
    }

    def test_valid_json_returns_no_errors(self):
        errors = validate_gherkin_json(self.VALID_JSON)
        assert errors == []

    def test_valid_json_as_string(self):
        json_str = json.dumps(self.VALID_JSON)
        errors = validate_gherkin_json(json_str)
        assert errors == []


class TestValidateGherkinJsonInvalid:
    """Tests with invalid JSON structures."""

    def test_invalid_json_string(self):
        errors = validate_gherkin_json("{not valid json")
        assert len(errors) > 0
        assert any("JSON" in e for e in errors)

    def test_missing_feature_title(self):
        data = {"scenarios": [{"type": "Scenario", "title": "Test", "steps": [
            {"keyword": "Given", "text": "a"},
            {"keyword": "When", "text": "b"},
            {"keyword": "Then", "text": "c"},
        ]}]}
        errors = validate_gherkin_json(data)
        assert any("feature_title" in e for e in errors)

    def test_empty_scenarios(self):
        data = {"feature_title": "Test", "scenarios": []}
        errors = validate_gherkin_json(data)
        assert any("scenario" in e.lower() for e in errors)

    def test_scenario_missing_title(self):
        data = {
            "feature_title": "Test",
            "scenarios": [{"type": "Scenario", "steps": [
                {"keyword": "Given", "text": "a"},
                {"keyword": "When", "text": "b"},
                {"keyword": "Then", "text": "c"},
            ]}],
        }
        errors = validate_gherkin_json(data)
        assert any("title" in e for e in errors)

    def test_invalid_scenario_type(self):
        data = {
            "feature_title": "Test",
            "scenarios": [{"type": "InvalidType", "title": "Test", "steps": [
                {"keyword": "Given", "text": "a"},
                {"keyword": "When", "text": "b"},
                {"keyword": "Then", "text": "c"},
            ]}],
        }
        errors = validate_gherkin_json(data)
        assert any("type" in e.lower() for e in errors)

    def test_empty_step_text(self):
        data = {
            "feature_title": "Test",
            "scenarios": [{"type": "Scenario", "title": "Test", "steps": [
                {"keyword": "Given", "text": ""},
                {"keyword": "When", "text": "b"},
                {"keyword": "Then", "text": "c"},
            ]}],
        }
        errors = validate_gherkin_json(data)
        assert any("Empty" in e or "empty" in e.lower() for e in errors)

    def test_scenario_outline_without_examples(self):
        data = {
            "feature_title": "Test",
            "scenarios": [{
                "type": "Scenario Outline",
                "title": "Test outline",
                "steps": [
                    {"keyword": "Given", "text": "a"},
                    {"keyword": "When", "text": "b"},
                    {"keyword": "Then", "text": "c"},
                ],
            }],
        }
        errors = validate_gherkin_json(data)
        assert any("examples" in e.lower() for e in errors)

    def test_missing_given_step(self):
        data = {
            "feature_title": "Test",
            "scenarios": [{"type": "Scenario", "title": "Test", "steps": [
                {"keyword": "When", "text": "something"},
                {"keyword": "Then", "text": "something"},
            ]}],
        }
        errors = validate_gherkin_json(data)
        assert any("Given" in e for e in errors)


# ── JSON to Gherkin Conversion ──────────────────────────────────────────

class TestJsonToGherkin:
    """Tests for JSON-to-Gherkin text conversion."""

    def test_converts_simple_scenario(self):
        data = {
            "feature_title": "User Login",
            "scenarios": [{
                "type": "Scenario",
                "title": "Successful login",
                "steps": [
                    {"keyword": "Given", "text": "the user is on the login page"},
                    {"keyword": "When", "text": "the user enters valid credentials"},
                    {"keyword": "Then", "text": "the user sees the dashboard"},
                ],
            }],
        }
        result = json_to_gherkin(data)
        assert "Feature: User Login" in result
        assert "Scenario: Successful login" in result
        assert "Given the user is on the login page" in result
        assert "When the user enters valid credentials" in result
        assert "Then the user sees the dashboard" in result

    def test_includes_tags(self):
        data = {
            "feature_title": "Test",
            "scenarios": [{
                "type": "Scenario",
                "title": "Tagged scenario",
                "tags": ["@smoke", "@regression"],
                "steps": [
                    {"keyword": "Given", "text": "a"},
                    {"keyword": "When", "text": "b"},
                    {"keyword": "Then", "text": "c"},
                ],
            }],
        }
        result = json_to_gherkin(data)
        assert "@smoke" in result
        assert "@regression" in result

    def test_includes_feature_description(self):
        data = {
            "feature_title": "My Feature",
            "feature_description": "This is a detailed description",
            "scenarios": [{
                "type": "Scenario",
                "title": "Test",
                "steps": [
                    {"keyword": "Given", "text": "a"},
                    {"keyword": "When", "text": "b"},
                    {"keyword": "Then", "text": "c"},
                ],
            }],
        }
        result = json_to_gherkin(data)
        assert "This is a detailed description" in result

    def test_roundtrip_validates(self):
        """JSON -> Gherkin text -> validate should pass."""
        data = {
            "feature_title": "Roundtrip Test",
            "scenarios": [{
                "type": "Scenario",
                "title": "Roundtrip",
                "steps": [
                    {"keyword": "Given", "text": "step one"},
                    {"keyword": "When", "text": "step two"},
                    {"keyword": "Then", "text": "step three"},
                ],
            }],
        }
        gherkin_text = json_to_gherkin(data)
        errors = validate_gherkin_text(gherkin_text)
        assert errors == []


# ── Constants Verification ──────────────────────────────────────────────

class TestConstants:
    """Verify keyword sets are properly defined."""

    def test_allowed_keywords_has_core_set(self):
        assert "Feature" in ALLOWED_KEYWORDS
        assert "Scenario" in ALLOWED_KEYWORDS
        assert "Given" in ALLOWED_KEYWORDS
        assert "When" in ALLOWED_KEYWORDS
        assert "Then" in ALLOWED_KEYWORDS
        assert "And" in ALLOWED_KEYWORDS
        assert "But" in ALLOWED_KEYWORDS

    def test_forbidden_keywords_has_french_set(self):
        assert "Étant donné" in FORBIDDEN_KEYWORDS
        assert "Lorsque" in FORBIDDEN_KEYWORDS
        assert "Alors" in FORBIDDEN_KEYWORDS
