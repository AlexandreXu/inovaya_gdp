# CONTEXT — InovaYa GdP

Projet de configuration ERPNext v16 native-first pour InovaYa SAS (traitement des eaux industrielles).
App Frappe : `inovaya_gdp` — Phase 1 livrée, Phase 2 installation en cours.

## Vocabulaire du domaine

| Terme | Définition |
|-------|-----------|
| GdP | Gestion de Projets |
| Fixture | Fichier JSON chargé par Frappe à l'installation (`bench migrate`) |
| Template Task | Enregistrement `Task` avec `is_template=1` (format ERPNext v16) |
| Project Template | Modèle de projet Frappe référençant des Template Tasks |
| Workspace | Espace de navigation ERPNext configurable par rôle |
| Custom Field | Champ ajouté à un DocType natif sans modifier le core |
| Bench | Outil CLI Frappe pour gérer les apps et les sites |
| Native-first | Approche : zéro dev custom avant d'épuiser les capacités ERPNext natives |
| TEE | Traitement des Eaux et Environnement (type de projet InovaYa) |
| IND | Industriel (type de projet InovaYa) |

## Règles d'usage des Skills

### Skills actifs maintenant
- `/diagnose` — erreurs d'installation, comportements ERPNext inattendus, fixtures mal chargées
- `/handoff` — en fin de session longue, avant de changer de contexte
- `/zoom-out` — quand on touche un DocType ou module Frappe/ERPNext inconnu
- `/triage` — priorisation du Backlog B01–B26 une fois l'installation validée

### Skills réservés à plus tard (après validation du socle ERPNext v16)
- `/tdd` — quand on écrira des tests Python sur les développements Phase 2
- `/to-prd` — pour spécifier les items du backlog en Product Requirements
- `/to-issues` — pour déverser le backlog en issues GitLab tracées
- `/improve-codebase-architecture` — après que l'app aura du code custom à analyser

### Contrainte générale
Ne pas déclencher de skills de génération autonome, d'automatisation externe ou de
développement complet sans demande explicite d'Alexandre XU.

## État du projet

- **Dépôt** : https://git.softia.fr/cloclo/poc/erpnext_ai.git — branche `POC_InovaYa_V16`
- **Répertoire local** : `F:\Inovaya\`
- **Dernier commit** : `2654c20` — fixtures v16 adaptées + PLAN_INSTALLATION.md
- **Cible** : ERPNext v16.19.1 (Frappe v16)
- **Environnement local** : Frappe v15 uniquement — ne pas toucher au bench Softia existant

## Décisions architecturales clés (ADR)

### ADR-01 — Native-first, zéro DocType custom en Phase 1
Toute configuration passe par des fixtures JSON (Role, Custom Field, Project Type,
Project Template, Workspace). Pas de DocType custom, pas de Python métier en Phase 1.

### ADR-02 — Template Tasks comme enregistrements Task séparés (ERPNext v16)
En v16, les données de planning des modèles de projet vivent sur des Task avec
`is_template=1` et non plus dans la child table `Project Template Task`.
Champs : `subject` (pas `title`), `start` (pas `begin_on`).

### ADR-03 — Clone manuel obligatoire (nom repo ≠ nom package)
Le dépôt s'appelle `erpnext_ai` mais le package Python est `inovaya_gdp`.
Installation : `git clone ... apps/inovaya_gdp` (jamais `bench get-app`).

### ADR-04 — Ordre de chargement des fixtures
Task (is_template=1) doit être chargé AVANT Project Template.
Ordre dans hooks.py : Role → Custom Field → Project Type → Task → Project Template → Workspace.

## Fichiers clés

| Fichier | Rôle |
|---------|------|
| `inovaya_gdp/hooks.py` | Point d'entrée, fixtures, hooks install |
| `inovaya_gdp/fixtures/template_task.json` | 41 Task is_template=1 (v16) |
| `inovaya_gdp/fixtures/project_template.json` | 5 modèles (format v16) |
| `inovaya_gdp/fixtures/workspace.json` | 6 workspaces InovaYa |
| `PLAN_INSTALLATION.md` | 2 scénarios d'installation (self-hosted + Frappe Cloud) |
| `VALIDATION_AVANT_INSTALLATION.md` | Audit risques + checklist |
| `BACKLOG_DEVELOPPEMENTS_SPECIFIQUES.md` | 26 items Phase 2 (B01–B26) |
| `HISTORIQUE_PROJET_INOVAYA_GDP.docx` | Historique complet de la session |
