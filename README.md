<div align="center">
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="Status Active">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  
  <h1>TestGenAI</h1>
  <h3>Plateforme Entreprise d'Ingénierie Qualité Augmentée par l'IA</h3>
  <p><em>Projet de Fin d'Études (PFE) - Génération automatisée de pipelines de tests de bout en bout</em></p>
</div>

---

## À propos du projet

**TestGenAI** est une solution innovante conçue pour combler le fossé entre les exigences métiers et l'automatisation des tests. En exploitant la puissance des LLM (Large Language Models), la plateforme est capable d'ingérer une simple *User Story* (texte, PDF ou ticket Jira) et de générer un pipeline de test complet (Gherkin + Playwright/TypeScript) exécutable et déployable instantanément sur GitLab CI.

Ce projet a été développé dans le cadre d'un **Projet de Fin d'Études (PFE)**, avec pour objectif de proposer une architecture robuste, scalable, et prête pour un environnement de production d'entreprise (SaaS).

---

## Fonctionnalités Clés (Les 5 Piliers)

1. **Ingestion Intelligente** : Importation dynamique de User Stories depuis Jira (API v3), fichiers PDF ou saisie manuelle.
2. **Génération par LLM (Gemini / OpenAI)** : Ingénierie de prompt spécialisée QA pour générer des scénarios BDD au format Gherkin (Given/When/Then).
3. **Code Scaffolding (Playwright + TypeScript)** : Génération de code de test automatisé respectant scrupuleusement le design pattern **Page Object Model (POM)**.
4. **Orchestration DevOps (GitLab)** : Création automatique de dépôts privés, push du code et déclenchement de pipelines CI/CD.
5. **Pilotage & Observabilité** : Tableaux de bord KPI, matrices de traçabilité, rapports PDF et historique d'exécution.

---

## Stack Technique

L'application repose sur une architecture **Monorepo** moderne et découplée :

| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Frontend** | ![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB) ![Vite](https://img.shields.io/badge/Vite-B73BFE?style=flat&logo=vite&logoColor=FFD62E) | Interface utilisateur réactive et dashboards interactifs. |
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=FastAPI&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | API RESTful performante, gestion des rôles et orchestration. |
| **Core AI** | ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white) | Moteur d'inférence LLM et traitement du langage naturel (NLP). |
| **Tests** | ![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat&logo=playwright&logoColor=white) | Framework d'automatisation UI E2E pour les tests générés. |
| **DevOps** | ![GitLab CI](https://img.shields.io/badge/GitLab_CI-181717?style=flat&logo=gitlab&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) | Conteneurisation et pipelines d'intégration continue. |

---

## Architecture du Monorepo

```text
TestGenAI/
├── core/                # Moteur d'Intelligence Artificielle (Python/Langchain)
├── backend/             # API Core de la plateforme (FastAPI)
├── frontend/            # Interface Web (React / Vite)
├── templates/           # Squelettes de code et modèles de génération
│   └── golden_path/     # Vérité Terrain : Template de test Playwright POM parfait
├── docs/                # Documentation, spécifications et livrables du PFE
├── run.sh               # Script d'orchestration pour lancer l'environnement
└── docker-compose.yml   # Configuration de l'infrastructure conteneurisée
```

---

## Démarrage Rapide

### Prérequis
- **Node.js** 18+ et **Python** 3.11+
- **Docker** (recommandé pour une exécution fluide)

### 1. Configuration de l'environnement
```bash
git clone <votre-repo-url>
cd TestGenAI

# Dupliquer et configurer le fichier d'environnement
cp .env.example .env
# Éditez le fichier .env avec vos clés API (Google Gemini, GitLab, Jira)
```

### 2. Lancement en une commande
Notre script `run.sh` s'occupe de créer les environnements virtuels, d'installer les dépendances et de démarrer les serveurs simultanément.

**En mode Local (Développement) :**
```bash
./run.sh --local
```

**En mode Conteneurisé (Production/Docker) :**
```bash
./run.sh --docker
```

L'application sera accessible sur :
- **Frontend UI** : `http://localhost:3000`
- **Backend API Docs** : `http://localhost:8000/docs`

---

## Gestion des Rôles (RBAC)

La plateforme intègre une gestion des rôles d'entreprise stricte :
- **Admin** : Accès complet à la plateforme, configuration des intégrations, exécution DevOps.
- **QA Engineer** : Création de spécifications, validation des scénarios IA, matrices de traçabilité.
- **Utilisateur Basique** : Consultation des rapports, vue globale (Dashboard).

---

## Workflow d'Exécution

1. **Ingestion** : Soumission d'une User Story via le Dashboard.
2. **Génération IA** : Le moteur `/core` analyse la demande et crée un fichier `.feature` (Gherkin).
3. **Validation & Scaffolding** : L'utilisateur valide le Gherkin. L'IA génère ensuite le code source complet (Playwright/TypeScript) basé sur le `/templates/golden_path`.
4. **Déploiement DevOps** : Le backend pousse l'ensemble du projet de test validé sur un nouveau dépôt GitLab et lance le pipeline d'intégration.
5. **Rapport** : L'utilisateur consulte la matrice de traçabilité et le rapport d'exécution final Allure/HTML.

---

<div align="center">
  <br/>
  <i>Développé avec passion pour automatiser l'avenir de la qualité logicielle.</i>
</div>
