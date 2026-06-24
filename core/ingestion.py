"""
Module d'Ingestion NLP — Parsing des User Stories et fichiers Swagger/OpenAPI.

Ce module nettoie, structure et formate le texte brut fourni par l'utilisateur
(User Story Markdown/Confluence ou fichier Swagger/OpenAPI) pour produire un
payload JSON standardisé destiné au module de Prompt Engineering.

Classes publiques :
    - UserStoryParser  : Extrait titre, rôle/action/bénéfice et critères d'acceptation.
    - SwaggerParser    : Extrait routes, méthodes, paramètres et schémas.
    - IngestionPipeline: Façade unifiée avec auto-détection du type d'entrée.

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import re
import json
import copy
from typing import Any


# ---------------------------------------------------------------------------
#  Utilitaires de nettoyage
# ---------------------------------------------------------------------------

def _clean_confluence_macros(text: str) -> str:
    """Supprime les macros Confluence ({panel}, {code}, {noformat}, etc.)."""
    # Remove block macros like {panel:title=...}...{panel}
    text = re.sub(r'\{panel(?::[^}]*)?\}', '', text)
    text = re.sub(r'\{code(?::[^}]*)?\}', '', text)
    text = re.sub(r'\{noformat\}', '', text)
    text = re.sub(r'\{quote\}', '', text)
    text = re.sub(r'\{info(?::[^}]*)?\}', '', text)
    text = re.sub(r'\{warning(?::[^}]*)?\}', '', text)
    text = re.sub(r'\{note(?::[^}]*)?\}', '', text)
    text = re.sub(r'\{expand(?::[^}]*)?\}', '', text)
    text = re.sub(r'\{color(?::[^}]*)?\}', '', text)
    text = re.sub(r'\{toc(?::[^}]*)?\}', '', text)
    return text


def _clean_html_tags(text: str) -> str:
    """Supprime les balises HTML inline résiduelles."""
    return re.sub(r'<[^>]+>', '', text)


def _clean_markdown_formatting(text: str) -> str:
    """Supprime le formatage Markdown (gras, italique) tout en préservant le texte."""
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # Italic: *text* or _text_ (but not inside words)
    text = re.sub(r'(?<!\w)\*(.+?)\*(?!\w)', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
    return text


def _normalize_whitespace(text: str) -> str:
    """Normalise les espaces et lignes vides excessifs."""
    # Collapse multiple blank lines into two
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip trailing whitespace per line
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    return text.strip()


# ---------------------------------------------------------------------------
#  UserStoryParser
# ---------------------------------------------------------------------------

class UserStoryParser:
    """
    Parse une User Story en texte brut (Markdown / Confluence) et extrait :
    - Le titre
    - Le bloc As a / I want / So that (FR et EN)
    - Les critères d'acceptation
    - Les métadonnées optionnelles (priorité, labels, etc.)
    """

    # Patterns pour le bloc User Story (français)
    _FR_ROLE_PATTERN = re.compile(
        r"(?:\*\*)?en\s+tant\s+qu[e']?\s*(?:\*\*)?\s*(.+?)(?:\s*,|\s*$)",
        re.IGNORECASE
    )
    _FR_ACTION_PATTERN = re.compile(
        r"(?:\*\*)?je\s+veux\s*(?:\*\*)?\s*(.+?)(?:\s*,|\s*$)",
        re.IGNORECASE
    )
    _FR_BENEFIT_PATTERN = re.compile(
        r"(?:\*\*)?afin\s+de\s*(?:\*\*)?\s*(.+?)(?:\s*\.|\s*$)",
        re.IGNORECASE
    )

    # Patterns pour le bloc User Story (anglais)
    _EN_ROLE_PATTERN = re.compile(
        r"(?:\*\*)?as\s+an?\s*(?:\*\*)?\s*(.+?)(?:\s*,|\s*$)",
        re.IGNORECASE
    )
    _EN_ACTION_PATTERN = re.compile(
        r"(?:\*\*)?i\s+want\s+(?:to\s+)?(?:\*\*)?\s*(.+?)(?:\s*,|\s*$)",
        re.IGNORECASE
    )
    _EN_BENEFIT_PATTERN = re.compile(
        r"(?:\*\*)?so\s+that\s*(?:\*\*)?\s*(.+?)(?:\s*\.|\s*$)",
        re.IGNORECASE
    )

    # Pattern pour les sections de critères d'acceptation
    _AC_SECTION_PATTERN = re.compile(
        r"(?:#+\s*)?(?:crit[eè]res?\s+d['\u2019]acceptation|acceptance\s+criteria|"
        r"definition\s+of\s+done|DoD|AC)\s*:?\s*(?:\n|$)",
        re.IGNORECASE
    )

    # Patterns pour les items de liste
    _LIST_ITEM_PATTERNS = [
        re.compile(r'^\s*[-*•]\s+\[[ x]\]\s*(.+)$', re.MULTILINE),  # Checkboxes
        re.compile(r'^\s*[-*•]\s+(.+)$', re.MULTILINE),              # Bullet points
        re.compile(r'^\s*\d+[.)]\s+(.+)$', re.MULTILINE),            # Numbered lists
    ]

    def parse(self, raw_text: str) -> dict[str, Any]:
        """
        Parse une User Story brute et retourne un dictionnaire structuré.

        Args:
            raw_text: Texte brut de la User Story (Markdown ou Confluence).

        Returns:
            Dictionnaire JSON structuré avec les champs :
            source_type, title, user_story, acceptance_criteria, metadata, raw_content.

        Raises:
            ValueError: Si le texte est vide ou None.
        """
        if not raw_text or not raw_text.strip():
            raise ValueError("Le texte de la User Story ne peut pas être vide.")

        # Préserver le contenu brut original
        raw_content = raw_text

        # Nettoyage
        cleaned = _clean_confluence_macros(raw_text)
        cleaned = _clean_html_tags(cleaned)
        cleaned = _normalize_whitespace(cleaned)

        # Extraction
        title = self._extract_title(cleaned)
        user_story = self._extract_user_story_block(cleaned)
        acceptance_criteria = self._extract_acceptance_criteria(cleaned)
        metadata = self._extract_metadata(cleaned)

        return {
            "source_type": "USER_STORY",
            "title": title,
            "user_story": user_story,
            "acceptance_criteria": acceptance_criteria,
            "metadata": metadata,
            "raw_content": raw_content,
        }

    def _extract_title(self, text: str) -> str:
        """Extrait le titre depuis un heading Markdown (#) ou la première ligne significative."""
        # Try Markdown headings (# Title or ## Title)
        match = re.search(r'^#+\s+(.+?)$', text, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            # Remove Markdown formatting from title
            title = _clean_markdown_formatting(title)
            return title

        # Fallback: first non-empty line
        for line in text.split('\n'):
            line = line.strip()
            if line:
                return _clean_markdown_formatting(line)

        return "Sans titre"

    def _extract_user_story_block(self, text: str) -> dict[str, str | None]:
        """Extrait le bloc As a / I want / So that en FR ou EN."""
        result = {"role": None, "action": None, "benefit": None}

        # Clean formatting for pattern matching
        cleaned = _clean_markdown_formatting(text)

        # Try French patterns first
        role_match = self._FR_ROLE_PATTERN.search(cleaned)
        action_match = self._FR_ACTION_PATTERN.search(cleaned)
        benefit_match = self._FR_BENEFIT_PATTERN.search(cleaned)

        if role_match or action_match:
            if role_match:
                result["role"] = role_match.group(1).strip().rstrip(',')
            if action_match:
                result["action"] = action_match.group(1).strip().rstrip(',')
            if benefit_match:
                result["benefit"] = benefit_match.group(1).strip().rstrip('.')
            return result

        # Try English patterns
        role_match = self._EN_ROLE_PATTERN.search(cleaned)
        action_match = self._EN_ACTION_PATTERN.search(cleaned)
        benefit_match = self._EN_BENEFIT_PATTERN.search(cleaned)

        if role_match:
            result["role"] = role_match.group(1).strip().rstrip(',')
        if action_match:
            result["action"] = action_match.group(1).strip().rstrip(',')
        if benefit_match:
            result["benefit"] = benefit_match.group(1).strip().rstrip('.')

        return result

    def _extract_acceptance_criteria(self, text: str) -> list[str]:
        """Extrait les critères d'acceptation d'une User Story."""
        criteria = []

        # Find the AC section
        ac_match = self._AC_SECTION_PATTERN.search(text)
        if ac_match:
            # Get content after the AC header until the next section header or end
            ac_start = ac_match.end()
            # Find the next section (## header or end of text)
            next_section = re.search(r'^#+\s+', text[ac_start:], re.MULTILINE)
            if next_section:
                ac_text = text[ac_start:ac_start + next_section.start()]
            else:
                ac_text = text[ac_start:]
        else:
            # No explicit AC section — scan the entire text for list items
            ac_text = text

        # Clean formatting before extracting items
        ac_text_clean = _clean_markdown_formatting(ac_text)

        # Extract list items using all patterns.
        # Track matched positions to prevent the bullet pattern from
        # re-capturing lines already matched by the checkbox pattern.
        seen_texts = set()
        seen_positions = set()
        for pattern in self._LIST_ITEM_PATTERNS:
            for match in pattern.finditer(ac_text_clean):
                # Skip if this line was already matched by a prior pattern
                if match.start() in seen_positions:
                    continue
                item = match.group(1).strip()
                if item and item not in seen_texts:
                    # Skip metadata-looking items
                    if not re.match(
                        r'^(priorit[ée]|sprint|labels?|estimation|points?)\s*:',
                        item,
                        re.IGNORECASE
                    ):
                        criteria.append(item)
                        seen_texts.add(item)
                seen_positions.add(match.start())

        return criteria

    def _extract_metadata(self, text: str) -> dict[str, Any]:
        """Extrait les métadonnées optionnelles (priorité, labels, sprint, etc.)."""
        metadata = {}

        # Clean formatting
        cleaned = _clean_markdown_formatting(text)

        # Priority
        priority_match = re.search(
            r'(?:priorit[ée]|priority)\s*:\s*(.+?)$',
            cleaned, re.IGNORECASE | re.MULTILINE
        )
        if priority_match:
            metadata["priority"] = priority_match.group(1).strip()

        # Sprint
        sprint_match = re.search(
            r'sprint\s*:\s*(.+?)$',
            cleaned, re.IGNORECASE | re.MULTILINE
        )
        if sprint_match:
            metadata["sprint"] = sprint_match.group(1).strip()

        # Labels
        labels_match = re.search(
            r'labels?\s*:\s*(.+?)$',
            cleaned, re.IGNORECASE | re.MULTILINE
        )
        if labels_match:
            raw_labels = labels_match.group(1).strip()
            metadata["labels"] = [
                label.strip()
                for label in re.split(r'[,;]', raw_labels)
                if label.strip()
            ]

        # Estimation / Story Points
        estimation_match = re.search(
            r'(?:estimation|story\s*points?|points?)\s*:\s*(.+?)$',
            cleaned, re.IGNORECASE | re.MULTILINE
        )
        if estimation_match:
            metadata["estimation"] = estimation_match.group(1).strip()

        return metadata


# ---------------------------------------------------------------------------
#  SwaggerParser
# ---------------------------------------------------------------------------

class SwaggerParser:
    """
    Parse un fichier Swagger 2.0 ou OpenAPI 3.x (JSON) et extrait :
    - Les informations générales de l'API
    - Tous les endpoints avec méthodes, paramètres, request bodies et responses
    - Les schémas/définitions avec résolution des $ref
    """

    # HTTP methods recognized
    _HTTP_METHODS = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}

    def parse(self, raw_input: str) -> dict[str, Any]:
        """
        Parse un fichier Swagger/OpenAPI brut (JSON string) et retourne
        un dictionnaire structuré.

        Args:
            raw_input: Chaîne JSON brute d'un fichier Swagger 2.0 ou OpenAPI 3.x.

        Returns:
            Dictionnaire JSON structuré avec les champs :
            source_type, api_info, endpoints, schemas, raw_content.

        Raises:
            ValueError: Si l'entrée n'est pas du JSON valide ou n'est pas un
                        fichier Swagger/OpenAPI reconnu.
        """
        if not raw_input or not raw_input.strip():
            raise ValueError("Le contenu Swagger/OpenAPI ne peut pas être vide.")

        raw_content = raw_input

        try:
            spec = json.loads(raw_input)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON invalide : {e}")

        if not isinstance(spec, dict):
            raise ValueError("Le fichier Swagger/OpenAPI doit être un objet JSON.")

        # Detect format
        is_swagger2 = 'swagger' in spec
        is_openapi3 = 'openapi' in spec

        if not is_swagger2 and not is_openapi3:
            raise ValueError(
                "Format non reconnu. Le fichier doit contenir une clé "
                "'swagger' (2.0) ou 'openapi' (3.x)."
            )

        # Extract
        api_info = self._extract_api_info(spec, is_swagger2)
        schemas = self._extract_schemas(spec, is_swagger2)
        endpoints = self._extract_endpoints(spec, schemas, is_swagger2)

        return {
            "source_type": "SWAGGER",
            "api_info": api_info,
            "endpoints": endpoints,
            "schemas": schemas,
            "raw_content": raw_content,
        }

    def _extract_api_info(self, spec: dict, is_swagger2: bool) -> dict[str, str]:
        """Extrait les informations générales de l'API."""
        info = spec.get('info', {})
        result = {
            "title": info.get('title', 'Untitled API'),
            "version": info.get('version', '0.0.0'),
            "description": info.get('description', ''),
        }

        if is_swagger2:
            host = spec.get('host', '')
            base_path = spec.get('basePath', '')
            schemes = spec.get('schemes', ['https'])
            result["base_url"] = f"{schemes[0]}://{host}{base_path}" if host else base_path
        else:
            servers = spec.get('servers', [])
            result["base_url"] = servers[0].get('url', '') if servers else ''

        return result

    def _extract_schemas(self, spec: dict, is_swagger2: bool) -> dict[str, Any]:
        """Extrait et aplatit les schémas/définitions."""
        if is_swagger2:
            raw_definitions = spec.get('definitions', {})
        else:
            raw_definitions = spec.get('components', {}).get('schemas', {})

        schemas = {}
        for name, schema_def in raw_definitions.items():
            schemas[name] = self._simplify_schema(schema_def)

        return schemas

    def _simplify_schema(self, schema: dict) -> dict[str, Any]:
        """Simplifie un schéma en extrayant type, properties, required, enum."""
        if not isinstance(schema, dict):
            return {"type": str(schema)}

        result = {}

        if 'type' in schema:
            result['type'] = schema['type']

        if 'required' in schema:
            result['required'] = schema['required']

        if 'enum' in schema:
            result['enum'] = schema['enum']

        if 'properties' in schema:
            props = {}
            for prop_name, prop_def in schema['properties'].items():
                if isinstance(prop_def, dict):
                    prop_info = {}
                    if 'type' in prop_def:
                        prop_info['type'] = prop_def['type']
                    if 'format' in prop_def:
                        prop_info['format'] = prop_def['format']
                    if 'enum' in prop_def:
                        prop_info['enum'] = prop_def['enum']
                    if 'minLength' in prop_def:
                        prop_info['minLength'] = prop_def['minLength']
                    if 'maxLength' in prop_def:
                        prop_info['maxLength'] = prop_def['maxLength']
                    if 'default' in prop_def:
                        prop_info['default'] = prop_def['default']
                    if 'description' in prop_def:
                        prop_info['description'] = prop_def['description']
                    # Handle $ref inside properties
                    if '$ref' in prop_def:
                        prop_info['$ref'] = self._resolve_ref_name(prop_def['$ref'])
                    props[prop_name] = prop_info
                else:
                    props[prop_name] = {"type": str(prop_def)}
            result['properties'] = props

        if 'items' in schema:
            items = schema['items']
            if isinstance(items, dict) and '$ref' in items:
                result['items'] = self._resolve_ref_name(items['$ref'])
            elif isinstance(items, dict):
                result['items'] = self._simplify_schema(items)

        return result

    def _resolve_ref_name(self, ref: str) -> str:
        """Extrait le nom du schéma depuis un chemin $ref."""
        # "#/definitions/Pet" -> "Pet"
        # "#/components/schemas/User" -> "User"
        return ref.rsplit('/', 1)[-1] if '/' in ref else ref

    def _resolve_ref(self, ref_obj: dict, schemas: dict) -> dict[str, Any] | str:
        """Résout un $ref vers sa définition simplifiée."""
        if '$ref' in ref_obj:
            name = self._resolve_ref_name(ref_obj['$ref'])
            return name  # Return schema name for reference
        return ref_obj

    def _extract_endpoints(
        self, spec: dict, schemas: dict, is_swagger2: bool
    ) -> list[dict[str, Any]]:
        """Extrait tous les endpoints avec leurs détails."""
        endpoints = []
        paths = spec.get('paths', {})

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.lower() not in self._HTTP_METHODS:
                    continue
                if not isinstance(operation, dict):
                    continue

                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get('summary', ''),
                    "operation_id": operation.get('operationId', ''),
                    "tags": operation.get('tags', []),
                    "parameters": [],
                    "request_body": None,
                    "responses": {},
                }

                # Extract parameters
                params = operation.get('parameters', [])
                # Also include path-level parameters
                path_params = path_item.get('parameters', [])
                all_params = path_params + params

                for param in all_params:
                    if not isinstance(param, dict):
                        continue

                    if is_swagger2 and param.get('in') == 'body':
                        # Swagger 2.0: body parameter = request body
                        body_schema = param.get('schema', {})
                        if '$ref' in body_schema:
                            schema_name = self._resolve_ref_name(body_schema['$ref'])
                            resolved = schemas.get(schema_name, {})
                        else:
                            resolved = self._simplify_schema(body_schema)
                        endpoint["request_body"] = {
                            "content_type": "application/json",
                            "required": param.get('required', False),
                            "schema": resolved,
                            "schema_ref": (
                                self._resolve_ref_name(body_schema['$ref'])
                                if '$ref' in body_schema
                                else None
                            ),
                        }
                    else:
                        param_info = {
                            "name": param.get('name', ''),
                            "in": param.get('in', ''),
                            "required": param.get('required', False),
                            "description": param.get('description', ''),
                        }

                        # Type info — Swagger 2.0 vs OpenAPI 3.x
                        if is_swagger2:
                            param_info["type"] = param.get('type', 'string')
                            if 'format' in param:
                                param_info["format"] = param['format']
                        else:
                            param_schema = param.get('schema', {})
                            param_info["type"] = param_schema.get('type', 'string')
                            if 'format' in param_schema:
                                param_info["format"] = param_schema['format']
                            if 'default' in param_schema:
                                param_info["default"] = param_schema['default']

                        endpoint["parameters"].append(param_info)

                # OpenAPI 3.x: requestBody
                if not is_swagger2 and 'requestBody' in operation:
                    req_body = operation['requestBody']
                    content = req_body.get('content', {})
                    for content_type, media_type in content.items():
                        body_schema = media_type.get('schema', {})
                        if '$ref' in body_schema:
                            schema_name = self._resolve_ref_name(body_schema['$ref'])
                            resolved = schemas.get(schema_name, {})
                        else:
                            resolved = self._simplify_schema(body_schema)
                        endpoint["request_body"] = {
                            "content_type": content_type,
                            "required": req_body.get('required', False),
                            "schema": resolved,
                            "schema_ref": (
                                self._resolve_ref_name(body_schema['$ref'])
                                if '$ref' in body_schema
                                else None
                            ),
                        }
                        break  # Take the first content type

                # Extract responses
                for status_code, response_def in operation.get('responses', {}).items():
                    if not isinstance(response_def, dict):
                        continue

                    resp_info = {
                        "description": response_def.get('description', ''),
                    }

                    # Response schema
                    if is_swagger2:
                        resp_schema = response_def.get('schema', {})
                        if resp_schema:
                            if '$ref' in resp_schema:
                                resp_info["schema_ref"] = self._resolve_ref_name(
                                    resp_schema['$ref']
                                )
                            elif resp_schema.get('type') == 'array':
                                items = resp_schema.get('items', {})
                                if '$ref' in items:
                                    resp_info["schema"] = {
                                        "type": "array",
                                        "items": self._resolve_ref_name(items['$ref']),
                                    }
                                else:
                                    resp_info["schema"] = self._simplify_schema(resp_schema)
                            else:
                                resp_info["schema"] = self._simplify_schema(resp_schema)
                    else:
                        content = response_def.get('content', {})
                        for _, media_type in content.items():
                            resp_schema = media_type.get('schema', {})
                            if '$ref' in resp_schema:
                                resp_info["schema_ref"] = self._resolve_ref_name(
                                    resp_schema['$ref']
                                )
                            elif resp_schema.get('type') == 'array':
                                items = resp_schema.get('items', {})
                                if '$ref' in items:
                                    resp_info["schema"] = {
                                        "type": "array",
                                        "items": self._resolve_ref_name(items['$ref']),
                                    }
                                else:
                                    resp_info["schema"] = self._simplify_schema(resp_schema)
                            else:
                                resp_info["schema"] = self._simplify_schema(resp_schema)
                            break  # Take first content type

                    endpoint["responses"][str(status_code)] = resp_info

                endpoints.append(endpoint)

        return endpoints


# ---------------------------------------------------------------------------
#  IngestionPipeline — Façade unifiée
# ---------------------------------------------------------------------------

class IngestionPipeline:
    """
    Point d'entrée principal du module d'ingestion.

    Détecte automatiquement le type d'entrée (User Story vs Swagger/OpenAPI)
    et route vers le parser approprié.
    """

    def __init__(self):
        self._us_parser = UserStoryParser()
        self._swagger_parser = SwaggerParser()

    def ingest(self, raw_input: str, source_type: str = "auto") -> dict[str, Any]:
        """
        Parse l'entrée brute et retourne un payload JSON structuré.

        Args:
            raw_input: Texte brut ou JSON à parser.
            source_type: Type de source — "USER_STORY", "SWAGGER", ou "auto"
                         pour la détection automatique.

        Returns:
            Dictionnaire JSON structuré prêt pour le Prompt Builder.

        Raises:
            ValueError: Si le type n'est pas reconnu ou l'entrée est invalide.
        """
        if not raw_input or not raw_input.strip():
            raise ValueError("L'entrée ne peut pas être vide.")

        source_type = source_type.upper()

        if source_type == "AUTO":
            source_type = self._detect_type(raw_input)

        if source_type == "USER_STORY":
            return self._us_parser.parse(raw_input)
        elif source_type == "SWAGGER":
            return self._swagger_parser.parse(raw_input)
        else:
            raise ValueError(
                f"Type de source non reconnu : '{source_type}'. "
                "Utilisez 'USER_STORY', 'SWAGGER' ou 'auto'."
            )

    def _detect_type(self, raw_input: str) -> str:
        """Détecte automatiquement le type d'entrée."""
        stripped = raw_input.strip()

        # If it starts with '{', try to parse as JSON and check for swagger/openapi keys
        if stripped.startswith('{'):
            try:
                data = json.loads(stripped)
                if isinstance(data, dict):
                    if 'swagger' in data or 'openapi' in data:
                        return "SWAGGER"
                    if 'paths' in data:
                        return "SWAGGER"
            except json.JSONDecodeError:
                pass

        # Default to User Story for any text-based input
        return "USER_STORY"
