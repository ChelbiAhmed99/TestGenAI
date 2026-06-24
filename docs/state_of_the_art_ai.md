# 🧠 État de l'Art IA — Génération de Code par LLM

> **Projet** : TestGenAI — Génération automatisée de pipelines E2E  
> **Auteur** : Mounira Ismail 
> **Date** : Juin 2026  
> **Objectif** : Choisir le LLM optimal et définir la stratégie anti-hallucinations pour générer du code Gherkin + Playwright/TypeScript fiable.

---

## Table des matières

1. [Contexte & Enjeux](#1-contexte--enjeux)
2. [Benchmark des Modèles LLM](#2-benchmark-des-modèles-llm)
3. [Prompt Engineering — Techniques Clés](#3-prompt-engineering--techniques-clés)
4. [Stratégie Anti-Hallucinations](#4-stratégie-anti-hallucinations)
5. [Choix du Modèle pour le PoC/MVP](#5-choix-du-modèle-pour-le-pocmvp)
6. [Architecture d'Intégration](#6-architecture-dintégration)
7. [Références](#7-références)

---

## 1. Contexte & Enjeux

### 1.1 Ce que le LLM doit générer

TestGenAI demande au LLM de produire **trois artefacts distincts** à partir d'une User Story :

| Artefact | Format | Contrainte |
|---|---|---|
| Scénarios BDD | Gherkin (`.feature`) | Syntaxe stricte Given/When/Then |
| Page Objects | TypeScript (`.ts`) | Pattern POM, locators valides |
| Tests exécutables | TypeScript (`.spec.ts`) | Compatible Playwright Test Runner |

### 1.2 Risques identifiés

| Risque | Impact | Probabilité |
|---|---|---|
| **Hallucination de sélecteurs** | Le LLM invente des `data-testid` ou XPath inexistants | 🔴 Élevée |
| **Code non-compilable** | Imports manquants, types incorrects | 🟡 Moyenne |
| **Non-respect du POM** | Assertions dans les Page Objects, logique mélangée | 🟡 Moyenne |
| **Gherkin invalide** | Syntaxe cassée, steps ambigus | 🟢 Faible |

---

## 2. Benchmark des Modèles LLM

### 2.1 Comparaison Générale

| Critère | Google Gemini 2.5 | OpenAI GPT-4o | Anthropic Claude Sonnet | Mistral Large 2 | Llama 3 (70B) |
|---|---|---|---|---|---|
| **Génération TypeScript** | ✅ Excellent | ✅ Excellent | ✅ Leader | ✅ Bon | 🟡 Correct |
| **Sortie JSON structurée** | ✅ Natif (`response_schema`) | ✅ Natif (`response_format`) | ✅ Via tool-use | ✅ JSON mode | ⚠️ Manuel |
| **Respect des instructions** | ✅ Très bon | ✅ Gold standard | ✅ Très bon | 🟡 Bon | 🟡 Variable |
| **Fenêtre de contexte** | 1M+ tokens | 128K tokens | 200K tokens | 128K tokens | 128K tokens |
| **Vitesse de réponse** | ⚡ Très rapide (Flash) | ⚡ Rapide | 🟡 Modéré | ⚡ Rapide | Variable (hardware) |
| **Coût (input/1M tokens)** | ~$0.15 (Flash) / ~$1.25 (Pro) | ~$0.40 (4o-mini) / ~$2.50 (4o) | ~$3.00 (Sonnet) | ~$2.00 | Gratuit (self-hosted) |
| **Coût (output/1M tokens)** | ~$0.60 (Flash) / ~$10 (Pro) | ~$1.60 (mini) / ~$10 (4o) | ~$15 (Sonnet) | ~$6.00 | Infra uniquement |
| **Free Tier** | ✅ Généreux | ❌ Limité | ❌ Limité | ❌ Limité | N/A |
| **Hébergement** | Cloud (API) | Cloud (API) | Cloud (API) | Cloud + Self-hosted | Self-hosted (Ollama) |

### 2.2 Analyse par Modèle

#### Google Gemini 2.5 (Flash / Pro)

**Forces :**
- **Meilleur rapport qualité/prix** du marché — Flash est 10x moins cher que GPT-4o pour des performances comparables
- Free tier généreux pour le prototypage et le PoC
- Sortie structurée native via `response_schema` (JSON Schema complet)
- Fenêtre de contexte massive (1M+ tokens) : peut ingérer un projet entier
- Intégration LangChain mature (`@langchain/google-genai` + `.withStructuredOutput()`)
- Déjà mentionné dans la stack technique du projet (README)

**Faiblesses :**
- Légères variations de consistance entre versions de modèle
- Pour des schémas JSON très complexes/imbriqués, nécessite parfois des retries

#### OpenAI GPT-4o / GPT-4o-mini

**Forces :**
- Gold standard pour le function calling et les structured outputs
- Écosystème le plus mature (documentation, exemples, communauté)
- GPT-4o-mini offre un excellent rapport performance/prix pour les tâches simples

**Faiblesses :**
- Plus cher que Gemini Flash à performance comparable
- Free tier très limité — contrainte budgétaire pour un PFE
- Pas de modèle self-hosted

#### Anthropic Claude (Sonnet / Haiku)

**Forces :**
- Leader reconnu en génération de code complexe (SWE-bench)
- Excellent pour le refactoring et la compréhension architecturale
- Moins d'hallucinations sur le code TypeScript idiomatique

**Faiblesses :**
- **Le plus cher** des trois fournisseurs cloud
- Pas de free tier substantiel
- Structured output via tool-use (moins direct que Gemini/OpenAI)

#### Mistral Large 2

**Forces :**
- Modèle européen (conformité RGPD native)
- Disponible en self-hosted via Ollama
- JSON mode fiable

**Faiblesses :**
- Écosystème et documentation moins riches
- Performances en génération de code légèrement en retrait

#### Meta Llama 3 (70B / 8B)

**Forces :**
- 100% gratuit et open-source
- Exécutable localement via Ollama (aucun coût API)
- Aucune dépendance cloud

**Faiblesses :**
- Nécessite un GPU puissant (A100/H100 pour le 70B, minimum RTX 4090)
- Pas de structured output natif — nécessite du post-processing
- Qualité de génération de code inférieure aux modèles propriétaires
- Latence élevée sans infrastructure dédiée

---

## 3. Prompt Engineering — Techniques Clés

### 3.1 System Role Definition (Persona Contractuelle)

Le System Prompt ne doit pas être une simple description de persona. Il doit agir comme un **contrat** :

```python
SYSTEM_PROMPT = """
Tu es un ingénieur QA senior spécialisé en automatisation Playwright avec TypeScript.

## CONTRAT DE SORTIE
- Tu génères UNIQUEMENT du code valide, compilable et exécutable.
- Tu respectes STRICTEMENT le Design Pattern Page Object Model (POM).
- Tu ne places JAMAIS d'assertions dans les Page Objects.
- Tu utilises UNIQUEMENT des locators basés sur les attributs `data-test` fournis.
- Si un sélecteur n'est pas fourni dans le contexte, tu utilises `getByRole()` ou `getByText()`.
- Tu NE DEVINES JAMAIS un sélecteur CSS ou XPath.

## FORMAT DE SORTIE
Tu retournes EXCLUSIVEMENT un objet JSON conforme au schéma fourni.
Pas de texte avant. Pas de texte après. Pas de blocs markdown.

## CE QUE TU NE FAIS JAMAIS
- Inventer des attributs data-testid qui n'existent pas
- Ajouter des commentaires explicatifs hors du code
- Utiliser des sélecteurs CSS fragiles basés sur des classes de style
- Générer du code qui ne compile pas
"""
```

### 3.2 Few-Shot Prompting

Fournir 2-3 exemples complets d'entrée/sortie ancre le comportement du modèle plus efficacement que de longues instructions :

```python
FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """
User Story: En tant qu'utilisateur, je veux me connecter avec des identifiants valides.
Page cible: https://www.saucedemo.com
Sélecteurs disponibles: [data-test="username"], [data-test="password"], [data-test="login-button"]
"""
    },
    {
        "role": "assistant",
        "content": """{
  "feature": "Feature: User Authentication\\n\\n  Scenario: Successful login\\n    Given the user is on the login page\\n    When the user logs in with valid credentials\\n    Then the user should see the inventory page",
  "pageObjects": [
    {
      "fileName": "LoginPage.ts",
      "code": "import { Page, Locator } from '@playwright/test';\\n\\nexport class LoginPage {\\n  readonly page: Page;\\n  readonly usernameInput: Locator;\\n  readonly passwordInput: Locator;\\n  readonly loginButton: Locator;\\n\\n  constructor(page: Page) {\\n    this.page = page;\\n    this.usernameInput = page.locator('[data-test=\\"username\\"]');\\n    this.passwordInput = page.locator('[data-test=\\"password\\"]');\\n    this.loginButton = page.locator('[data-test=\\"login-button\\"]');\\n  }\\n\\n  async navigate() { await this.page.goto('/'); }\\n  async login(user: string, pass: string) {\\n    await this.usernameInput.fill(user);\\n    await this.passwordInput.fill(pass);\\n    await this.loginButton.click();\\n  }\\n}"
    }
  ],
  "specs": [
    {
      "fileName": "login.spec.ts",
      "code": "import { test, expect } from '@playwright/test';\\nimport { LoginPage } from '../pages/LoginPage';\\n\\ntest('Successful login', async ({ page }) => {\\n  const loginPage = new LoginPage(page);\\n  await loginPage.navigate();\\n  await loginPage.login('standard_user', 'secret_sauce');\\n  await expect(page).toHaveURL(/.*inventory/);\\n});"
    }
  ]
}"""
    }
]
```

### 3.3 Structured Output via API

Plutôt que d'espérer que le LLM respecte un format, on **force** la structure au niveau API :

```python
from pydantic import BaseModel, Field
from typing import List

class PageObjectFile(BaseModel):
    fileName: str = Field(description="Nom du fichier, ex: LoginPage.ts")
    code: str = Field(description="Code TypeScript complet du Page Object")

class SpecFile(BaseModel):
    fileName: str = Field(description="Nom du fichier, ex: login.spec.ts")
    code: str = Field(description="Code TypeScript complet du test")

class GeneratedTestSuite(BaseModel):
    feature: str = Field(description="Contenu complet du fichier .feature en Gherkin")
    pageObjects: List[PageObjectFile] = Field(description="Liste des Page Objects générés")
    specs: List[SpecFile] = Field(description="Liste des fichiers de test générés")
```

Avec LangChain + Gemini :

```python
from langchain_google_genai import ChatGoogleGenerativeAI

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1  # Basse température = moins de créativité = moins d'hallucinations
)

structured_model = model.with_structured_output(GeneratedTestSuite)
result = structured_model.invoke([system_msg, *few_shot_examples, user_msg])
# result est un objet GeneratedTestSuite typé et validé
```

### 3.4 Température et Paramètres

| Paramètre | Valeur recommandée | Justification |
|---|---|---|
| `temperature` | **0.1 — 0.2** | Minimise la "créativité" → réduit les hallucinations |
| `top_p` | **0.9** | Filtre les tokens les moins probables |
| `max_tokens` | **8192+** | Suffisant pour un fichier `.spec.ts` complet |
| `response_format` | **JSON Schema** | Force le format de sortie au niveau API |

---

## 4. Stratégie Anti-Hallucinations

### 4.1 Le Problème Central

Le risque n°1 pour TestGenAI est que le LLM **invente des sélecteurs CSS/XPath** qui n'existent pas dans l'application cible. Exemple d'hallucination typique :

```typescript
// ❌ HALLUCINATION — ce data-testid n'existe probablement pas
this.submitButton = page.locator('[data-testid="submit-form-btn"]');

// ✅ CORRECT — sélecteur fourni dans le contexte ou basé sur le rôle
this.submitButton = page.getByRole('button', { name: 'Submit' });
```

### 4.2 Architecture de Défense en 4 Couches

```
┌─────────────────────────────────────────────────────┐
│  COUCHE 1 — GROUNDING (Ancrage contextuel)          │
│  Fournir les sélecteurs réels au LLM via le prompt  │
├─────────────────────────────────────────────────────┤
│  COUCHE 2 — CONTRAINTE API                          │
│  Structured Output + System Prompt contractuel      │
├─────────────────────────────────────────────────────┤
│  COUCHE 3 — VALIDATION STATIQUE                     │
│  Vérification syntaxique du code généré             │
├─────────────────────────────────────────────────────┤
│  COUCHE 4 — VALIDATION DYNAMIQUE                    │
│  Exécution sandbox + feedback loop                  │
└─────────────────────────────────────────────────────┘
```

#### Couche 1 — Grounding (Ancrage Contextuel)

**Principe** : Ne jamais demander au LLM de deviner les sélecteurs. Lui fournir la liste exacte.

**Stratégies :**

| Méthode | Description | Quand l'utiliser |
|---|---|---|
| **Liste de sélecteurs manuelle** | L'utilisateur fournit les `data-testid` dans la User Story | PoC / MVP |
| **DOM Scraping** | Crawler automatique extrait les attributs `data-test`, `id`, `aria-label` | MVP avancé |
| **Annotated Markdown** | Convertir le HTML en Markdown simplifié avec les sélecteurs annotés | Production |

Exemple de prompt avec grounding :

```
## Sélecteurs disponibles sur la page de login :
- Champ username : [data-test="username"]
- Champ password : [data-test="password"]  
- Bouton login  : [data-test="login-button"]
- Message erreur : [data-test="error"]

⚠️ Tu dois utiliser EXCLUSIVEMENT ces sélecteurs. N'invente AUCUN sélecteur.
Si un élément n'a pas de sélecteur listé ci-dessus, utilise getByRole() ou getByText().
```

#### Couche 2 — Contrainte API

- **Structured Output** : Forcer le format JSON via `response_schema` (Gemini) ou `response_format` (OpenAI)
- **System Prompt contractuel** : Interdire explicitement l'invention de sélecteurs (cf. section 3.1)
- **Température basse** : `temperature=0.1` pour minimiser la créativité

#### Couche 3 — Validation Statique (Post-Génération)

```python
import re

def validate_generated_code(code: str, allowed_selectors: list[str]) -> dict:
    """Vérifie que le code généré n'utilise que des sélecteurs autorisés."""
    errors = []
    
    # Détecter les locators utilisés
    locator_pattern = r"page\.locator\(['\"](.+?)['\"]\)"
    used_locators = re.findall(locator_pattern, code)
    
    for locator in used_locators:
        if locator not in allowed_selectors:
            errors.append(f"⚠️ Sélecteur non autorisé détecté: {locator}")
    
    # Vérifier les imports
    if "from '@playwright/test'" not in code and "from \"@playwright/test\"" not in code:
        if ".spec.ts" in code or "test(" in code:
            errors.append("⚠️ Import @playwright/test manquant")
    
    # Vérifier la syntaxe TypeScript basique
    if code.count('{') != code.count('}'):
        errors.append("⚠️ Accolades non équilibrées")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "locators_used": used_locators
    }
```

#### Couche 4 — Validation Dynamique (Exécution Sandbox)

Pour le MVP avancé, exécuter le code généré dans un environnement isolé :

```python
import subprocess

def sandbox_validate(project_path: str) -> dict:
    """Tente de compiler et exécuter le code généré."""
    # Étape 1 : Vérification TypeScript
    tsc_result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=project_path, capture_output=True, timeout=30
    )
    
    if tsc_result.returncode != 0:
        return {"valid": False, "stage": "compilation", "error": tsc_result.stderr}
    
    # Étape 2 : Dry-run Playwright (optionnel)
    pw_result = subprocess.run(
        ["npx", "playwright", "test", "--reporter=json"],
        cwd=project_path, capture_output=True, timeout=60
    )
    
    return {
        "valid": pw_result.returncode == 0,
        "stage": "execution",
        "output": pw_result.stdout
    }
```

### 4.3 Self-Healing (Auto-Correction)

Si la validation échoue, renvoyer l'erreur au LLM pour correction :

```python
async def generate_with_retry(user_story, selectors, max_retries=3):
    for attempt in range(max_retries):
        result = await structured_model.invoke(build_prompt(user_story, selectors))
        validation = validate_generated_code(result.code, selectors)
        
        if validation["valid"]:
            return result
        
        # Feedback loop — le LLM corrige ses propres erreurs
        correction_prompt = f"""
        Le code que tu as généré contient les erreurs suivantes :
        {validation['errors']}
        
        Corrige le code en respectant strictement les sélecteurs autorisés.
        """
        # Relancer avec le contexte d'erreur
    
    raise GenerationError("Échec après 3 tentatives")
```

---

## 5. Choix du Modèle pour le PoC/MVP

### 5.1 Matrice de Décision

| Critère (pondération) | Gemini 2.5 Flash | GPT-4o-mini | Claude Haiku | Llama 3 70B |
|---|---|---|---|---|
| **Coût** (30%) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Qualité code TS** (25%) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Structured Output** (20%) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Intégration LangChain** (10%) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Free Tier / Budget PFE** (10%) | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Rapidité** (5%) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Score pondéré** | **4.60** | **4.05** | **3.55** | **3.50** |

### 5.2 Décision Finale

> ### ✅ Modèle retenu : **Google Gemini 2.5 Flash** (via API Google AI)

#### Justification

| Argument | Détail |
|---|---|
| **Coût optimal** | ~$0.15/M tokens input — le plus compétitif du marché, avec un free tier généreux idéal pour un PFE |
| **Structured Output natif** | `response_schema` force la sortie JSON au niveau API — pas de parsing manuel |
| **Intégration LangChain** | `@langchain/google-genai` + `.with_structured_output()` — pipeline prêt à l'emploi |
| **Cohérence avec le projet** | Gemini est déjà mentionné dans le README comme technologie cible |
| **Performance** | Vitesse de réponse la plus rapide — critique pour une UX fluide dans le dashboard |
| **Fenêtre de contexte** | 1M+ tokens — peut ingérer le golden_path template + la User Story + les sélecteurs sans problème |

#### Modèle de fallback

> **GPT-4o-mini** en seconde option si des problèmes de fiabilité sont rencontrés avec Gemini sur des schémas JSON complexes.

#### Pourquoi pas Llama 3 / Ollama ?

| Aspect | Verdict |
|---|---|
| Qualité de sortie structurée | Insuffisante sans structured output natif |
| Infrastructure requise | GPU dédié (coût supérieur à l'API Gemini Flash pour notre volume) |
| Temps de réponse | 5-15x plus lent qu'une API cloud |
| **Verdict** | Intéressant pour la confidentialité, mais non adapté au PoC/MVP |

### 5.3 Estimation des Coûts

Pour un usage typique TestGenAI (génération de test à partir d'une User Story) :

| Métrique | Estimation |
|---|---|
| Tokens input par requête | ~2 000 (system + few-shot + user story + sélecteurs) |
| Tokens output par requête | ~3 000 (feature + POM + spec) |
| Coût par génération (Flash) | ~$0.0003 + $0.0018 = **~$0.002** |
| Budget 1 000 générations | **~$2.00** |
| Free tier Google AI | ~1 500 requêtes/jour (RPD) pour Flash |

---

## 6. Architecture d'Intégration

### 6.1 Pipeline de Génération

```
┌──────────────┐    ┌───────────────┐    ┌──────────────────┐
│  User Story  │───▶│  Prompt       │───▶│  Gemini 2.5      │
│  + Sélecteurs│    │  Builder      │    │  Flash API       │
└──────────────┘    │  (System +    │    │  (Structured     │
                    │   Few-Shot +  │    │   Output)        │
                    │   Grounding)  │    └────────┬─────────┘
                    └───────────────┘             │
                                                  ▼
                                        ┌──────────────────┐
                                        │  Validation      │
                                        │  Statique        │
                                        │  (Sélecteurs +   │
                                        │   Syntaxe TS)    │
                                        └────────┬─────────┘
                                                  │
                                          ✅ OK   │  ❌ Erreur
                                          ┌───────┴──────┐
                                          ▼              ▼
                                   ┌────────────┐  ┌──────────┐
                                   │  Scaffolding│  │ Retry    │
                                   │  Projet    │  │ avec     │
                                   │  Playwright │  │ feedback │
                                   └────────────┘  └──────────┘
```

### 6.2 Stack Technique Retenue

| Composant | Technologie | Rôle |
|---|---|---|
| **LLM** | Google Gemini 2.5 Flash | Génération de code |
| **Orchestration** | LangChain (Python) | Chaîne de prompts, structured output |
| **Validation** | Pydantic + regex | Validation statique des sélecteurs |
| **Schéma** | Pydantic `BaseModel` | Définition du format de sortie |
| **Backend** | FastAPI | API REST exposant la génération |
| **Template** | Golden Path (`/templates/`) | Few-shot example + vérité terrain |

### 6.3 Variables d'Environnement Requises

```env
# .env
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
LLM_MAX_RETRIES=3
```

---

## 7. Références

| Source | Description |
|---|---|
| [Google AI — Structured Output](https://ai.google.dev/gemini-api/docs/structured-output) | Documentation officielle Gemini |
| [LangChain — Google GenAI](https://python.langchain.com/docs/integrations/chat/google_generative_ai/) | Intégration LangChain + Gemini |
| [OpenAI — Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) | Documentation structured output OpenAI |
| [Anthropic — Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use) | Structured output via Claude |
| [Semantic Triangulation (arXiv)](https://arxiv.org/abs/2402.09189) | Technique anti-hallucination 2025 |
| [Google AI Pricing](https://ai.google.dev/pricing) | Tarification officielle Gemini |

---

> **Ce document acte le choix de Google Gemini 2.5 Flash comme LLM principal pour TestGenAI.**  
> La stratégie anti-hallucinations repose sur un pipeline à 4 couches : Grounding → Contrainte API → Validation Statique → Validation Dynamique.
