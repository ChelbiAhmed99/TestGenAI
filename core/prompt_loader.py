"""
Module de chargement des prompts de référence.

Charge les prompts depuis le catalogue JSON externe (/core/prompts/)
et fournit des méthodes utilitaires pour construire les messages LLM.

Auteur  : Mounira Ismail
Date    : Juin 2026
"""

import json
import os
from typing import Any

_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _load_catalog(filename: str = "gherkin_prompt.json") -> dict[str, Any]:
    """Charge un fichier de catalogue de prompts."""
    path = os.path.join(_PROMPT_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_catalog: dict[str, Any] | None = None


def get_catalog() -> dict[str, Any]:
    """Retourne le catalogue (chargé une seule fois, mis en cache)."""
    global _catalog
    if _catalog is None:
        _catalog = _load_catalog()
    return _catalog


def build_gherkin_messages(requirement_content: str) -> list[dict[str, str]]:
    """
    Construit la liste de messages (system + few-shot + user) prête
    à être envoyée au LLM pour la génération Gherkin.

    Args:
        requirement_content: Le texte brut de la spécification.

    Returns:
        Liste de dicts [{"role": "...", "content": "..."}]
    """
    cat = get_catalog()
    gherkin_cfg = cat["gherkin_generation"]

    messages = []

    # 1. System prompt
    messages.append({
        "role": "system",
        "content": gherkin_cfg["system_prompt"],
    })

    # 2. Few-shot examples
    for example in gherkin_cfg.get("few_shot_examples", []):
        messages.append({
            "role": example["role"],
            "content": example["content"],
        })

    # 3. User prompt with requirement injected
    user_prompt = gherkin_cfg["user_prompt_template"].replace(
        "{requirement_content}", requirement_content
    )
    messages.append({
        "role": "user",
        "content": user_prompt,
    })

    return messages


def build_test_script_messages(gherkin_content: str) -> list[dict[str, str]]:
    """
    Construit la liste de messages pour la génération de scripts Playwright.

    Args:
        gherkin_content: Les scénarios Gherkin à convertir.

    Returns:
        Liste de dicts [{"role": "...", "content": "..."}]
    """
    cat = get_catalog()
    script_cfg = cat["test_script_generation"]

    messages = [
        {"role": "system", "content": script_cfg["system_prompt"]},
        {
            "role": "user",
            "content": script_cfg["user_prompt_template"].replace(
                "{gherkin_content}", gherkin_content
            ),
        },
    ]

    return messages


def get_validation_rules() -> dict[str, Any]:
    """Retourne les règles de validation Gherkin du catalogue."""
    return get_catalog().get("validation", {})
