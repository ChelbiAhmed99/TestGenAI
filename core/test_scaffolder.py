"""
Tests unitaires — Moteur de Scaffolding.

Vérifie que le scaffolder génère correctement les arborescences de projets
Playwright/TypeScript avec Page Objects et fichiers .spec.ts conformes au POM.

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import json
import os
import shutil
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from scaffolder import (
    ProjectScaffolder,
    ScaffoldResult,
    _sanitize_filename,
    _to_pascal_case,
    _to_camel_case,
)


# ── Test output directory (cleaned after each test) ──────────────────────

TEST_OUTPUT = os.path.join(os.path.dirname(__file__), "_test_scaffold_output")


@pytest.fixture(autouse=True)
def cleanup():
    """Remove test output before and after each test."""
    if os.path.exists(TEST_OUTPUT):
        shutil.rmtree(TEST_OUTPUT)
    yield
    if os.path.exists(TEST_OUTPUT):
        shutil.rmtree(TEST_OUTPUT)


# ── Helpers ──────────────────────────────────────────────────────────────

SAMPLE_GHERKIN_JSON = {
    "feature_title": "User Authentication",
    "feature_description": "Login and registration flows",
    "scenarios": [
        {
            "tags": ["@smoke"],
            "type": "Scenario",
            "title": "Successful login with valid credentials",
            "steps": [
                {"keyword": "Given", "text": "the user is on the login page"},
                {"keyword": "When", "text": 'the user enters email "test@devoteam.com"'},
                {"keyword": "And", "text": 'the user enters password "Str0ng!"'},
                {"keyword": "And", "text": 'the user clicks the "Sign In" button'},
                {"keyword": "Then", "text": "the user is redirected to the dashboard"},
            ],
        },
        {
            "tags": ["@negative"],
            "type": "Scenario",
            "title": "Login fails with wrong password",
            "steps": [
                {"keyword": "Given", "text": "the user is on the login page"},
                {"keyword": "When", "text": 'the user enters email "test@devoteam.com"'},
                {"keyword": "And", "text": 'the user enters password "wrong"'},
                {"keyword": "And", "text": 'the user clicks the "Sign In" button'},
                {"keyword": "Then", "text": 'an error message "Invalid credentials" is displayed'},
            ],
        },
    ],
}

SAMPLE_PAGE_OBJECTS = [
    {
        "filename": "LoginPage.ts",
        "code": (
            "import { Page, Locator } from '@playwright/test';\n\n"
            "export class LoginPage {\n"
            "  readonly page: Page;\n"
            "  readonly emailInput: Locator;\n\n"
            "  constructor(page: Page) {\n"
            "    this.page = page;\n"
            "    this.emailInput = page.locator('[data-testid=\"email\"]');\n"
            "  }\n\n"
            "  async navigate() { await this.page.goto('/login'); }\n"
            "}\n"
        ),
    }
]

SAMPLE_SPEC_FILES = [
    {
        "filename": "login.spec.ts",
        "code": (
            "import { test, expect } from '@playwright/test';\n"
            "import { LoginPage } from '../pages/LoginPage';\n\n"
            "test('login test', async ({ page }) => {\n"
            "  const loginPage = new LoginPage(page);\n"
            "  await loginPage.navigate();\n"
            "});\n"
        ),
    }
]


# ── Utility Tests ────────────────────────────────────────────────────────

class TestUtilities:
    def test_sanitize_filename(self):
        assert _sanitize_filename("User Authentication") == "user-authentication"

    def test_sanitize_special_chars(self):
        assert _sanitize_filename("Login (v2.0)!") == "login-v20"

    def test_to_pascal_case(self):
        assert _to_pascal_case("login page") == "LoginPage"

    def test_to_pascal_case_kebab(self):
        assert _to_pascal_case("user-authentication") == "UserAuthentication"

    def test_to_camel_case(self):
        assert _to_camel_case("LoginPage") == "loginPage"

    def test_to_camel_case_spaces(self):
        assert _to_camel_case("shopping cart") == "shoppingCart"


# ── ScaffoldResult Tests ─────────────────────────────────────────────────

class TestScaffoldResult:
    def test_empty_result_is_success(self):
        r = ScaffoldResult("/tmp/test")
        assert r.success is True

    def test_result_with_errors_is_failure(self):
        r = ScaffoldResult("/tmp/test")
        r.errors.append("Something went wrong")
        assert r.success is False

    def test_to_dict(self):
        r = ScaffoldResult("/tmp/test")
        r.created_files.append("file.ts")
        d = r.to_dict()
        assert d["success"] is True
        assert d["file_count"] == 1


# ── Project Scaffold Tests ───────────────────────────────────────────────

class TestScaffoldProject:
    """Tests for scaffold_project with pre-generated code."""

    def test_creates_project_directory(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "My Test Project", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        assert result.success
        assert os.path.isdir(result.output_dir)

    def test_creates_required_subdirs(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "SubDir Test", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        for d in ["pages", "tests", "features"]:
            assert os.path.isdir(os.path.join(result.output_dir, d))

    def test_creates_package_json(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "PkgTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        pkg_path = os.path.join(result.output_dir, "package.json")
        assert os.path.isfile(pkg_path)
        with open(pkg_path) as f:
            data = json.load(f)
        assert "playwright" in json.dumps(data)

    def test_creates_tsconfig(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "TsTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        assert os.path.isfile(os.path.join(result.output_dir, "tsconfig.json"))

    def test_creates_playwright_config(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "PwTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES,
            base_url="https://example.com"
        )
        config_path = os.path.join(result.output_dir, "playwright.config.ts")
        assert os.path.isfile(config_path)
        with open(config_path) as f:
            content = f.read()
        assert "https://example.com" in content

    def test_creates_gitignore(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "GitTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        assert os.path.isfile(os.path.join(result.output_dir, ".gitignore"))

    def test_creates_gitlab_ci(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "CiTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        assert os.path.isfile(os.path.join(result.output_dir, ".gitlab-ci.yml"))

    def test_skips_gitlab_ci_when_disabled(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "NoCi", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES,
            include_ci=False
        )
        assert not os.path.isfile(os.path.join(result.output_dir, ".gitlab-ci.yml"))

    def test_creates_feature_file(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        gherkin = "Feature: Login\n  Scenario: Test\n    Given step"
        result = s.scaffold_project(
            "FeatureTest", gherkin, SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        feature_dir = os.path.join(result.output_dir, "features")
        files = os.listdir(feature_dir)
        assert len(files) == 1
        assert files[0].endswith(".feature")

    def test_creates_page_objects(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "PoTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        pages_dir = os.path.join(result.output_dir, "pages")
        assert os.path.isfile(os.path.join(pages_dir, "LoginPage.ts"))

    def test_creates_spec_files(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "SpecTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        tests_dir = os.path.join(result.output_dir, "tests")
        assert os.path.isfile(os.path.join(tests_dir, "login.spec.ts"))

    def test_page_object_has_correct_content(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "ContentTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        with open(os.path.join(result.output_dir, "pages", "LoginPage.ts")) as f:
            content = f.read()
        assert "export class LoginPage" in content
        assert "Page" in content

    def test_creates_readme(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "ReadmeTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        assert os.path.isfile(os.path.join(result.output_dir, "README.md"))

    def test_fails_on_existing_dir_without_overwrite(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        s.scaffold_project("DupTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES)
        result = s.scaffold_project(
            "DupTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES,
            overwrite=False
        )
        assert not result.success
        assert any("already exists" in e for e in result.errors)

    def test_overwrite_replaces_existing(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        s.scaffold_project("OverTest", "Feature: V1", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES)
        result = s.scaffold_project(
            "OverTest", "Feature: V2", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES,
            overwrite=True
        )
        assert result.success

    def test_file_count_matches(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_project(
            "CountTest", "Feature: Test", SAMPLE_PAGE_OBJECTS, SAMPLE_SPEC_FILES
        )
        # package.json, tsconfig, playwright.config, .gitignore, .gitlab-ci,
        # 1 feature, 1 page, 1 spec, README = 9
        assert result.to_dict()["file_count"] == 9


# ── Scaffold From Gherkin JSON Tests ─────────────────────────────────────

class TestScaffoldFromGherkinJson:
    """Tests for deterministic scaffolding from structured Gherkin JSON."""

    def test_generates_project_from_json(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json(
            "Auth Tests", SAMPLE_GHERKIN_JSON, overwrite=True
        )
        assert result.success

    def test_generates_page_objects_dir(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json("Auth PO", SAMPLE_GHERKIN_JSON, overwrite=True)
        pages_dir = os.path.join(result.output_dir, "pages")
        assert os.path.isdir(pages_dir)
        page_files = [f for f in os.listdir(pages_dir) if f.endswith(".ts")]
        assert len(page_files) >= 1

    def test_page_objects_have_valid_typescript(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json("Auth TS", SAMPLE_GHERKIN_JSON, overwrite=True)
        pages_dir = os.path.join(result.output_dir, "pages")
        for f in os.listdir(pages_dir):
            if f.endswith(".ts"):
                with open(os.path.join(pages_dir, f)) as fh:
                    content = fh.read()
                assert "import { Page, Locator } from '@playwright/test';" in content
                assert "export class" in content
                assert "readonly page: Page;" in content
                assert "constructor(page: Page)" in content

    def test_generates_spec_files(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json("Auth Spec", SAMPLE_GHERKIN_JSON, overwrite=True)
        tests_dir = os.path.join(result.output_dir, "tests")
        spec_files = [f for f in os.listdir(tests_dir) if f.endswith(".spec.ts")]
        assert len(spec_files) >= 1

    def test_spec_files_have_valid_structure(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json("Auth Struct", SAMPLE_GHERKIN_JSON, overwrite=True)
        tests_dir = os.path.join(result.output_dir, "tests")
        for f in os.listdir(tests_dir):
            if f.endswith(".spec.ts"):
                with open(os.path.join(tests_dir, f)) as fh:
                    content = fh.read()
                assert "import { test, expect } from '@playwright/test';" in content
                assert "test.describe(" in content
                assert "test.beforeEach(" in content
                assert "test.step(" in content

    def test_spec_contains_scenario_titles(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json("Auth Title", SAMPLE_GHERKIN_JSON, overwrite=True)
        tests_dir = os.path.join(result.output_dir, "tests")
        for f in os.listdir(tests_dir):
            if f.endswith(".spec.ts"):
                with open(os.path.join(tests_dir, f)) as fh:
                    content = fh.read()
                assert "Successful login with valid credentials" in content
                assert "Login fails with wrong password" in content

    def test_generates_feature_file(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json("Auth Feat", SAMPLE_GHERKIN_JSON, overwrite=True)
        features_dir = os.path.join(result.output_dir, "features")
        feature_files = [f for f in os.listdir(features_dir) if f.endswith(".feature")]
        assert len(feature_files) == 1
        with open(os.path.join(features_dir, feature_files[0])) as fh:
            content = fh.read()
        assert "Feature: User Authentication" in content

    def test_result_dict_has_all_fields(self):
        s = ProjectScaffolder(output_base=TEST_OUTPUT)
        result = s.scaffold_from_gherkin_json("Auth Dict", SAMPLE_GHERKIN_JSON, overwrite=True)
        d = result.to_dict()
        assert "success" in d
        assert "output_dir" in d
        assert "created_files" in d
        assert "file_count" in d
        assert d["file_count"] >= 8
