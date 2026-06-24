"""
Tests unitaires pour le module d'ingestion NLP.

Couvre le parsing de User Stories (Markdown/Confluence, FR/EN)
et de fichiers Swagger 2.0 / OpenAPI 3.x.

Usage :
    cd "/home/choubi/Desktop/Mounira Project/core"
    python -m pytest test_ingestion.py -v
"""

import json
import os
import pytest
from ingestion import UserStoryParser, SwaggerParser, IngestionPipeline


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")


@pytest.fixture
def us_parser():
    return UserStoryParser()


@pytest.fixture
def swagger_parser():
    return SwaggerParser()


@pytest.fixture
def pipeline():
    return IngestionPipeline()


@pytest.fixture
def sample_user_story():
    with open(os.path.join(SAMPLE_DIR, "sample_user_story.md"), "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def sample_swagger():
    with open(os.path.join(SAMPLE_DIR, "sample_swagger.json"), "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def sample_openapi():
    with open(os.path.join(SAMPLE_DIR, "sample_openapi.json"), "r", encoding="utf-8") as f:
        return f.read()


# ===========================================================================
#  UserStoryParser Tests
# ===========================================================================

class TestUserStoryParserMarkdown:
    """Tests de parsing d'une User Story standard en Markdown."""

    def test_parse_returns_correct_source_type(self, us_parser, sample_user_story):
        result = us_parser.parse(sample_user_story)
        assert result["source_type"] == "USER_STORY"

    def test_parse_extracts_title(self, us_parser, sample_user_story):
        result = us_parser.parse(sample_user_story)
        assert result["title"] is not None
        assert len(result["title"]) > 0
        assert "Authentification" in result["title"] or "US-042" in result["title"]

    def test_parse_extracts_user_story_block(self, us_parser, sample_user_story):
        result = us_parser.parse(sample_user_story)
        us = result["user_story"]
        assert us["role"] is not None
        assert "enregistré" in us["role"] or "utilisateur" in us["role"]
        assert us["action"] is not None
        assert "connecter" in us["action"]
        assert us["benefit"] is not None
        assert "tableau de bord" in us["benefit"] or "dashboard" in us["benefit"].lower()

    def test_parse_extracts_all_acceptance_criteria(self, us_parser, sample_user_story):
        result = us_parser.parse(sample_user_story)
        criteria = result["acceptance_criteria"]
        # The sample file has 7 acceptance criteria
        assert len(criteria) >= 7, (
            f"Expected at least 7 criteria, got {len(criteria)}: {criteria}"
        )

    def test_parse_criteria_content_is_accurate(self, us_parser, sample_user_story):
        result = us_parser.parse(sample_user_story)
        criteria_text = " ".join(result["acceptance_criteria"])
        # Verify key business rules are captured
        assert "identifiants valides" in criteria_text.lower() or "valides" in criteria_text.lower()
        assert "erreur" in criteria_text.lower()
        assert "verrouillé" in criteria_text.lower() or "5 tentatives" in criteria_text.lower()

    def test_parse_extracts_metadata(self, us_parser, sample_user_story):
        result = us_parser.parse(sample_user_story)
        meta = result["metadata"]
        assert "priority" in meta
        assert "Haute" in meta["priority"] or "High" in meta["priority"]

    def test_parse_preserves_raw_content(self, us_parser, sample_user_story):
        result = us_parser.parse(sample_user_story)
        assert result["raw_content"] == sample_user_story


class TestUserStoryParserEnglish:
    """Tests de parsing d'une User Story en anglais."""

    ENGLISH_US = """
# US-101: User Login

## User Story

As a registered user,
I want to log in with my email and password,
So that I can access my personalized dashboard.

## Acceptance Criteria

- Valid credentials redirect the user to the dashboard
- Invalid credentials display an error message "Invalid email or password"
- Empty fields show inline validation errors
- After 3 failed attempts, the account is locked for 10 minutes
- A "Forgot password" link is available on the login page

## Metadata

- Priority: High
- Labels: auth, security
"""

    def test_parse_english_user_story(self, us_parser):
        result = us_parser.parse(self.ENGLISH_US)
        assert result["source_type"] == "USER_STORY"
        assert result["user_story"]["role"] is not None
        assert "registered user" in result["user_story"]["role"]
        assert result["user_story"]["action"] is not None
        assert "log in" in result["user_story"]["action"]
        assert result["user_story"]["benefit"] is not None

    def test_parse_english_acceptance_criteria(self, us_parser):
        result = us_parser.parse(self.ENGLISH_US)
        criteria = result["acceptance_criteria"]
        assert len(criteria) >= 5
        criteria_text = " ".join(criteria)
        assert "dashboard" in criteria_text.lower()
        assert "locked" in criteria_text.lower() or "3 failed" in criteria_text.lower()


class TestUserStoryParserConfluence:
    """Tests de parsing d'une User Story avec macros Confluence."""

    CONFLUENCE_US = """
{panel:title=US-200 : Création de compte}

h2. User Story

{info}
*En tant qu'* visiteur du site,
*Je veux* créer un compte avec mon email,
*Afin de* pouvoir utiliser les fonctionnalités premium.
{info}

h2. Critères d'acceptation

{panel}
- L'email doit être unique dans le système
- Le mot de passe doit contenir au moins 8 caractères
- Un email de confirmation est envoyé après l'inscription
- Le compte est inactif tant que l'email n'est pas confirmé
{panel}

- Priorité : Moyenne
- Labels : registration, onboarding
"""

    def test_parse_confluence_cleans_macros(self, us_parser):
        result = us_parser.parse(self.CONFLUENCE_US)
        # Macros should be stripped
        assert "{panel" not in json.dumps(result["acceptance_criteria"])
        assert "{info" not in json.dumps(result["acceptance_criteria"])

    def test_parse_confluence_extracts_criteria(self, us_parser):
        result = us_parser.parse(self.CONFLUENCE_US)
        assert len(result["acceptance_criteria"]) >= 4

    def test_parse_confluence_extracts_user_story(self, us_parser):
        result = us_parser.parse(self.CONFLUENCE_US)
        us = result["user_story"]
        assert us["role"] is not None
        assert "visiteur" in us["role"]


class TestUserStoryParserCheckboxes:
    """Tests de parsing avec des checkboxes Markdown."""

    CHECKBOX_US = """
# US-300 : Panier d'achat

En tant qu' acheteur,
Je veux ajouter des produits à mon panier,
Afin de pouvoir les commander.

## Critères d'acceptation

- [ ] Le bouton "Ajouter au panier" est visible sur la page produit
- [x] Le nombre d'articles dans le panier est mis à jour en temps réel
- [ ] Le panier affiche le prix total
- [ ] Un produit déjà dans le panier peut être supprimé
"""

    def test_parse_checkboxes(self, us_parser):
        result = us_parser.parse(self.CHECKBOX_US)
        criteria = result["acceptance_criteria"]
        assert len(criteria) >= 4
        # Check that checkbox markers are stripped
        for criterion in criteria:
            assert "[ ]" not in criterion
            assert "[x]" not in criterion


class TestUserStoryParserNumberedList:
    """Tests de parsing avec des listes numérotées."""

    NUMBERED_US = """
# US-400 : Recherche produits

En tant qu' utilisateur,
Je veux rechercher des produits par nom,
Afin de trouver rapidement ce que je cherche.

## Critères d'acceptation

1. La barre de recherche est accessible depuis toutes les pages
2. Les résultats apparaissent en temps réel (autocomplétion)
3. La recherche supporte les fautes de frappe (fuzzy search)
4) Si aucun résultat n'est trouvé, un message explicite est affiché
5. Les résultats sont triés par pertinence
"""

    def test_parse_numbered_list(self, us_parser):
        result = us_parser.parse(self.NUMBERED_US)
        criteria = result["acceptance_criteria"]
        assert len(criteria) >= 5
        criteria_text = " ".join(criteria)
        assert "autocomplétion" in criteria_text or "temps réel" in criteria_text


class TestUserStoryParserEdgeCases:
    """Tests des cas limites du parser User Story."""

    def test_empty_input_raises_error(self, us_parser):
        with pytest.raises(ValueError, match="vide"):
            us_parser.parse("")

    def test_none_input_raises_error(self, us_parser):
        with pytest.raises(ValueError, match="vide"):
            us_parser.parse(None)

    def test_whitespace_only_raises_error(self, us_parser):
        with pytest.raises(ValueError, match="vide"):
            us_parser.parse("   \n\n   ")

    def test_minimal_text_returns_valid_structure(self, us_parser):
        result = us_parser.parse("Simple requirement text without structure")
        assert result["source_type"] == "USER_STORY"
        assert result["title"] is not None
        assert isinstance(result["acceptance_criteria"], list)
        assert isinstance(result["metadata"], dict)
        assert result["raw_content"] == "Simple requirement text without structure"


# ===========================================================================
#  SwaggerParser Tests
# ===========================================================================

class TestSwaggerParserV2:
    """Tests de parsing d'un fichier Swagger 2.0."""

    def test_parse_returns_correct_source_type(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        assert result["source_type"] == "SWAGGER"

    def test_parse_extracts_api_info(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        info = result["api_info"]
        assert info["title"] == "Petstore API"
        assert info["version"] == "1.0.0"
        assert "/v1" in info["base_url"]

    def test_parse_extracts_all_endpoints(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        endpoints = result["endpoints"]
        # The sample has: GET /pets, POST /pets, GET /pets/{petId},
        # PUT /pets/{petId}, DELETE /pets/{petId}
        assert len(endpoints) == 5, (
            f"Expected 5 endpoints, got {len(endpoints)}: "
            f"{[(e['method'], e['path']) for e in endpoints]}"
        )

    def test_parse_extracts_methods_correctly(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        methods = {(e["path"], e["method"]) for e in result["endpoints"]}
        assert ("/pets", "GET") in methods
        assert ("/pets", "POST") in methods
        assert ("/pets/{petId}", "GET") in methods
        assert ("/pets/{petId}", "PUT") in methods
        assert ("/pets/{petId}", "DELETE") in methods

    def test_parse_extracts_query_parameters(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        get_pets = next(
            e for e in result["endpoints"]
            if e["path"] == "/pets" and e["method"] == "GET"
        )
        param_names = [p["name"] for p in get_pets["parameters"]]
        assert "limit" in param_names
        assert "offset" in param_names

    def test_parse_extracts_path_parameters(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        get_pet = next(
            e for e in result["endpoints"]
            if e["path"] == "/pets/{petId}" and e["method"] == "GET"
        )
        path_params = [p for p in get_pet["parameters"] if p["in"] == "path"]
        assert len(path_params) == 1
        assert path_params[0]["name"] == "petId"
        assert path_params[0]["required"] is True

    def test_parse_extracts_request_body(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        post_pet = next(
            e for e in result["endpoints"]
            if e["path"] == "/pets" and e["method"] == "POST"
        )
        assert post_pet["request_body"] is not None
        assert post_pet["request_body"]["content_type"] == "application/json"

    def test_parse_extracts_responses(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        get_pets = next(
            e for e in result["endpoints"]
            if e["path"] == "/pets" and e["method"] == "GET"
        )
        assert "200" in get_pets["responses"]
        assert get_pets["responses"]["200"]["description"] == "A paged array of pets"

    def test_parse_extracts_schemas(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        schemas = result["schemas"]
        assert "Pet" in schemas
        assert "NewPet" in schemas
        assert "Error" in schemas
        assert "properties" in schemas["Pet"]

    def test_parse_preserves_raw_content(self, swagger_parser, sample_swagger):
        result = swagger_parser.parse(sample_swagger)
        assert result["raw_content"] == sample_swagger


class TestSwaggerParserOpenAPIV3:
    """Tests de parsing d'un fichier OpenAPI 3.x."""

    def test_parse_returns_correct_source_type(self, swagger_parser, sample_openapi):
        result = swagger_parser.parse(sample_openapi)
        assert result["source_type"] == "SWAGGER"

    def test_parse_extracts_api_info(self, swagger_parser, sample_openapi):
        result = swagger_parser.parse(sample_openapi)
        info = result["api_info"]
        assert info["title"] == "User Management API"
        assert info["version"] == "2.1.0"
        assert "api.example.com" in info["base_url"]

    def test_parse_extracts_all_endpoints(self, swagger_parser, sample_openapi):
        result = swagger_parser.parse(sample_openapi)
        endpoints = result["endpoints"]
        # GET /users, POST /users, GET /users/{userId},
        # PATCH /users/{userId}, DELETE /users/{userId}, POST /auth/login
        assert len(endpoints) == 6, (
            f"Expected 6 endpoints, got {len(endpoints)}: "
            f"{[(e['method'], e['path']) for e in endpoints]}"
        )

    def test_parse_extracts_header_parameters(self, swagger_parser, sample_openapi):
        result = swagger_parser.parse(sample_openapi)
        get_users = next(
            e for e in result["endpoints"]
            if e["path"] == "/users" and e["method"] == "GET"
        )
        header_params = [p for p in get_users["parameters"] if p["in"] == "header"]
        assert len(header_params) >= 1
        assert header_params[0]["name"] == "Authorization"

    def test_parse_extracts_openapi3_request_body(self, swagger_parser, sample_openapi):
        result = swagger_parser.parse(sample_openapi)
        post_users = next(
            e for e in result["endpoints"]
            if e["path"] == "/users" and e["method"] == "POST"
        )
        assert post_users["request_body"] is not None
        assert post_users["request_body"]["content_type"] == "application/json"
        assert post_users["request_body"]["required"] is True

    def test_parse_resolves_refs_to_schemas(self, swagger_parser, sample_openapi):
        result = swagger_parser.parse(sample_openapi)
        schemas = result["schemas"]
        assert "User" in schemas
        assert "CreateUserRequest" in schemas
        assert "LoginRequest" in schemas
        assert "AuthToken" in schemas
        # User schema should have properties
        assert "properties" in schemas["User"]
        user_props = schemas["User"]["properties"]
        assert "username" in user_props
        assert "email" in user_props

    def test_parse_extracts_multiple_responses(self, swagger_parser, sample_openapi):
        result = swagger_parser.parse(sample_openapi)
        post_users = next(
            e for e in result["endpoints"]
            if e["path"] == "/users" and e["method"] == "POST"
        )
        assert "201" in post_users["responses"]
        assert "400" in post_users["responses"]
        assert "409" in post_users["responses"]


class TestSwaggerParserEdgeCases:
    """Tests des cas limites du parser Swagger."""

    def test_empty_input_raises_error(self, swagger_parser):
        with pytest.raises(ValueError, match="vide"):
            swagger_parser.parse("")

    def test_invalid_json_raises_error(self, swagger_parser):
        with pytest.raises(ValueError, match="JSON invalide"):
            swagger_parser.parse("not json at all {{{")

    def test_non_swagger_json_raises_error(self, swagger_parser):
        with pytest.raises(ValueError, match="non reconnu"):
            swagger_parser.parse('{"name": "not a swagger file"}')

    def test_json_array_raises_error(self, swagger_parser):
        with pytest.raises(ValueError, match="objet JSON"):
            swagger_parser.parse('[1, 2, 3]')


# ===========================================================================
#  IngestionPipeline Tests
# ===========================================================================

class TestIngestionPipeline:
    """Tests de la façade IngestionPipeline."""

    def test_auto_detect_user_story(self, pipeline, sample_user_story):
        result = pipeline.ingest(sample_user_story, source_type="auto")
        assert result["source_type"] == "USER_STORY"

    def test_auto_detect_swagger(self, pipeline, sample_swagger):
        result = pipeline.ingest(sample_swagger, source_type="auto")
        assert result["source_type"] == "SWAGGER"

    def test_auto_detect_openapi(self, pipeline, sample_openapi):
        result = pipeline.ingest(sample_openapi, source_type="auto")
        assert result["source_type"] == "SWAGGER"

    def test_explicit_user_story_type(self, pipeline, sample_user_story):
        result = pipeline.ingest(sample_user_story, source_type="USER_STORY")
        assert result["source_type"] == "USER_STORY"

    def test_explicit_swagger_type(self, pipeline, sample_swagger):
        result = pipeline.ingest(sample_swagger, source_type="SWAGGER")
        assert result["source_type"] == "SWAGGER"

    def test_invalid_type_raises_error(self, pipeline, sample_user_story):
        with pytest.raises(ValueError, match="non reconnu"):
            pipeline.ingest(sample_user_story, source_type="INVALID")

    def test_empty_input_raises_error(self, pipeline):
        with pytest.raises(ValueError, match="vide"):
            pipeline.ingest("")

    def test_case_insensitive_source_type(self, pipeline, sample_user_story):
        result = pipeline.ingest(sample_user_story, source_type="user_story")
        assert result["source_type"] == "USER_STORY"

    def test_output_is_json_serializable(self, pipeline, sample_user_story, sample_swagger):
        """Vérifie que la sortie est bien sérialisable en JSON."""
        us_result = pipeline.ingest(sample_user_story)
        swagger_result = pipeline.ingest(sample_swagger)

        # These should not raise
        us_json = json.dumps(us_result, ensure_ascii=False, indent=2)
        swagger_json = json.dumps(swagger_result, ensure_ascii=False, indent=2)

        assert len(us_json) > 0
        assert len(swagger_json) > 0

    def test_raw_content_preserved_user_story(self, pipeline, sample_user_story):
        """Vérifie que raw_content préserve 100% du contenu original."""
        result = pipeline.ingest(sample_user_story)
        assert result["raw_content"] == sample_user_story

    def test_raw_content_preserved_swagger(self, pipeline, sample_swagger):
        """Vérifie que raw_content préserve 100% du contenu original."""
        result = pipeline.ingest(sample_swagger)
        assert result["raw_content"] == sample_swagger


# ===========================================================================
#  Integration Tests — Full Pipeline
# ===========================================================================

class TestIntegrationUserStory:
    """Test d'intégration complet : fichier sample → parsing → payload structuré."""

    def test_full_pipeline_user_story(self, pipeline, sample_user_story):
        result = pipeline.ingest(sample_user_story)

        # Structure complète
        assert "source_type" in result
        assert "title" in result
        assert "user_story" in result
        assert "acceptance_criteria" in result
        assert "metadata" in result
        assert "raw_content" in result

        # Données substantielles
        assert len(result["acceptance_criteria"]) >= 7
        assert result["user_story"]["role"] is not None
        assert result["user_story"]["action"] is not None

        # Le payload est prêt pour le Prompt Builder
        payload_json = json.dumps(result, ensure_ascii=False)
        assert len(payload_json) > 100


class TestIntegrationSwagger:
    """Test d'intégration complet : fichier Swagger → parsing → payload structuré."""

    def test_full_pipeline_swagger(self, pipeline, sample_swagger):
        result = pipeline.ingest(sample_swagger)

        # Structure complète
        assert "source_type" in result
        assert "api_info" in result
        assert "endpoints" in result
        assert "schemas" in result
        assert "raw_content" in result

        # Données substantielles
        assert len(result["endpoints"]) == 5
        assert len(result["schemas"]) >= 3

        # Chaque endpoint a les champs requis
        for endpoint in result["endpoints"]:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "parameters" in endpoint
            assert "responses" in endpoint

        # Le payload est prêt pour le Prompt Builder
        payload_json = json.dumps(result, ensure_ascii=False)
        assert len(payload_json) > 100


class TestIntegrationOpenAPI:
    """Test d'intégration complet : fichier OpenAPI 3.x → parsing → payload structuré."""

    def test_full_pipeline_openapi(self, pipeline, sample_openapi):
        result = pipeline.ingest(sample_openapi)

        assert result["source_type"] == "SWAGGER"
        assert len(result["endpoints"]) == 6
        assert len(result["schemas"]) >= 5

        # Verify a complex endpoint with requestBody
        post_users = next(
            e for e in result["endpoints"]
            if e["path"] == "/users" and e["method"] == "POST"
        )
        assert post_users["request_body"] is not None
        assert post_users["request_body"]["schema"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
