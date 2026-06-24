"""
Tests unitaires — Chargement du catalogue de prompts.

Vérifie que le prompt_loader charge correctement le catalogue JSON,
construit les messages LLM au bon format et retourne les règles de validation.

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import json
import os
import sys
import pytest

# Ensure core directory is in path
sys.path.insert(0, os.path.dirname(__file__))

from prompt_loader import (
    get_catalog,
    build_gherkin_messages,
    build_test_script_messages,
    get_validation_rules,
)


class TestCatalogLoading:
    """Tests pour le chargement du catalogue JSON."""

    def test_catalog_loads_successfully(self):
        cat = get_catalog()
        assert isinstance(cat, dict)

    def test_catalog_has_version(self):
        cat = get_catalog()
        assert "version" in cat
        assert cat["version"] == "2.0.0"

    def test_catalog_has_gherkin_generation(self):
        cat = get_catalog()
        assert "gherkin_generation" in cat

    def test_catalog_has_test_script_generation(self):
        cat = get_catalog()
        assert "test_script_generation" in cat

    def test_catalog_has_validation(self):
        cat = get_catalog()
        assert "validation" in cat


class TestBuildGherkinMessages:
    """Tests pour la construction des messages Gherkin."""

    def test_returns_list(self):
        msgs = build_gherkin_messages("Some requirement content")
        assert isinstance(msgs, list)

    def test_first_message_is_system(self):
        msgs = build_gherkin_messages("Test content")
        assert msgs[0]["role"] == "system"

    def test_last_message_is_user(self):
        msgs = build_gherkin_messages("Test content")
        assert msgs[-1]["role"] == "user"

    def test_user_prompt_contains_requirement(self):
        content = "As a user I want to login"
        msgs = build_gherkin_messages(content)
        assert content in msgs[-1]["content"]

    def test_has_few_shot_examples(self):
        msgs = build_gherkin_messages("Test")
        # Should have: system + few-shot pairs + user = at least 4 messages
        assert len(msgs) >= 4

    def test_system_prompt_mentions_gherkin(self):
        msgs = build_gherkin_messages("Test")
        system_content = msgs[0]["content"].lower()
        assert "gherkin" in system_content

    def test_system_prompt_mentions_json(self):
        msgs = build_gherkin_messages("Test")
        system_content = msgs[0]["content"].lower()
        assert "json" in system_content

    def test_all_messages_have_role_and_content(self):
        msgs = build_gherkin_messages("Test")
        for msg in msgs:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ("system", "user", "assistant")


class TestBuildTestScriptMessages:
    """Tests pour la construction des messages de script de test."""

    def test_returns_list(self):
        msgs = build_test_script_messages("Given the user is logged in")
        assert isinstance(msgs, list)

    def test_first_message_is_system(self):
        msgs = build_test_script_messages("Given something")
        assert msgs[0]["role"] == "system"

    def test_last_message_is_user(self):
        msgs = build_test_script_messages("Given something")
        assert msgs[-1]["role"] == "user"

    def test_user_prompt_contains_gherkin(self):
        gherkin = "Feature: Login\n  Scenario: Valid login"
        msgs = build_test_script_messages(gherkin)
        assert gherkin in msgs[-1]["content"]

    def test_system_prompt_mentions_playwright(self):
        msgs = build_test_script_messages("Test")
        system_content = msgs[0]["content"].lower()
        assert "playwright" in system_content

    def test_system_prompt_mentions_pom(self):
        msgs = build_test_script_messages("Test")
        system_content = msgs[0]["content"]
        assert "Page Object Model" in system_content or "POM" in system_content


class TestGetValidationRules:
    """Tests pour les règles de validation."""

    def test_returns_dict(self):
        rules = get_validation_rules()
        assert isinstance(rules, dict)

    def test_has_allowed_keywords(self):
        rules = get_validation_rules()
        assert "allowed_gherkin_keywords" in rules

    def test_allowed_keywords_contain_given_when_then(self):
        rules = get_validation_rules()
        keywords = rules["allowed_gherkin_keywords"]
        assert "Given" in keywords
        assert "When" in keywords
        assert "Then" in keywords

    def test_has_required_scenario_structure(self):
        rules = get_validation_rules()
        assert "required_scenario_structure" in rules

    def test_has_forbidden_keywords(self):
        rules = get_validation_rules()
        assert "forbidden_keywords" in rules
