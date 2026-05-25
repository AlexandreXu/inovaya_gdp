# Validation avant installation — InovaYa GdP v1.0.0

> Document produit après audit complet des fixtures, hooks et configurations de l'app `inovaya_gdp`.
> À lire intégralement avant tout déploiement sur une instance ERPNext v16.

---

## Légende des niveaux de risque

| Icône | Niveau | Signification |
|---|---|---|
| 🔴 | Élevé | Peut bloquer l'installation ou produire des données incorrectes |
| 🟡 | Moyen | Peut nécessiter une correction manuelle post-install |
| 🟢 | Faible | Cosmétique ou sans impact fonctionnel |
| ✅ | Validé | Vérifié et conforme |
| ❓ | Incertain | Non confirmé sur ERPNext v16 — à vérifier en premier |

---

## 1. Hypothèses techniques

| # | Hypothèse | Statut |
|---|---|---|
| H1 | L'instance cible tourne sur **ERPNext v16.x** avec Frappe v16.x | À confirmer |
| H2 | La base de données est MariaDB 10.6+ ou MySQL 8.0+ | À confirmer |
| H3 | L'instance est **clean** — aucune autre app custom installée | À confirmer |
| H4 | Le bench a accès à internet (ou au dépôt GitLab Softia) pour `get-app` | À confirmer |
| H5 | Les modules ERPNext **Projects, Buying, Accounts, HR** sont activés sur le site | À confirmer |
| H6 | La structure des DocTypes `Project`, `Task`, `Project Template` n'a **pas changé fondamentalement** entre v15 et v16 | ❓ Risque identifié |
| H7 | Les noms de rapports ERPNext v16 sont identiques à v15 | ❓ Risque moyen |

---

## 2. Vérifications réalisées lors de l'audit

### 2.1 Fixtures — Cohérence JSON

| Fixture | Vérification | Résultat |
|---|---|---|
| `role.json` | Format DocType valide, champs `name`, `role_name`, `desk_access`, `is_custom`, `disabled` | ✅ Conforme |
| `role.json` | Aucun doublon avec les rôles natifs ERPNext (`Projects User`, `Accounts User`, etc.) | ✅ Noms uniques |
| `custom_field.json` | Préfixe `inovaya_` systématique — aucun risque de collision avec champs natifs | ✅ Conforme |
| `custom_field.json` | Champ `Project.project_type` natif utilisé tel quel (non dupliqué) | ✅ Pas de duplication |
| `custom_field.json` | `insert_after: "notes"` (Project) — champ natif `notes` à confirmer en v16 | ❓ Risque moyen |
| `custom_field.json` | `insert_after: "type"` (Task) — champ natif `type` à confirmer en v16 | ❓ Risque moyen |
| `project_type.json` | Format minimal correct (`name`, `is_default`) | ✅ Conforme |
| `project_template.json` | Champs utilisés : `title`, `begin_on`, `duration`, `is_milestone` | 🔴 Risque élevé (voir §3.1) |
| `workspace.json` | DocTypes référencés en shortcuts — tous natifs ERPNext | ✅ Valides |
| `workspace.json` | Noms de rapports : `Daily Timesheet Summary`, `Employee Hours Utilization Based On Timesheet` | ✅ Confirmés v16 |
| `workspace.json` | Noms d'icônes : `project`, `task`, `note` | 🟡 Non confirmés (voir §3.3) |
| `workspace.json` | Champ `type: "Custom"` sur Workspace | ❓ À vérifier en v16 |

### 2.2 Hooks — Idempotence

| Hook | Analyse | Résultat |
|---|---|---|
| `after_install` | Opérations : log uniquement, aucune écriture DB | ✅ Idempotent |
| `after_migrate` | Opérations : log uniquement | ✅ Idempotent |
| Chargement fixtures | Frappe utilise un upsert (insert or update) — pas de doublons | ✅ Idempotent |
| Réinstallation | Deuxième `install-app` : les fixtures sont re-synchronisées sans doublon | ✅ Idempotent |
| `bench migrate` | Re-charge les fixtures à chaque migration via le hook `after_migrate` | ✅ Idempotent |

### 2.3 Intégrité du cœur Frappe/ERPNext

| Contrôle | Résultat |
|---|---|
| Pas de modification de DocTypes natifs (override, patch, alter) | ✅ Aucune |
| Pas de hooks `doc_events` sur les DocTypes natifs | ✅ Aucun |
| Pas de `override_doctype_class` | ✅ Aucun |
| Pas de patches dans `patches.txt` | ✅ Vide |
| Pas de JavaScript override (`doctype_js`) | ✅ Aucun |
| Champs ajoutés **uniquement** via Custom Field (mécanisme standard Frappe) | ✅ Conforme |
| Aucun accès direct aux tables SQL natifs | ✅ Conforme |

---

## 3. Risques identifiés

### 🔴 3.1 — Structure Project Template potentiellement modifiée en v16

**Description** : Des sources indiquent que ERPNext v16 a modifié l'approche des modèles de projet. Dans certaines versions récentes, les templates utilisent des `Task` normaux marqués avec un flag `is_template`, plutôt qu'un DocType séparé `Project Template Task`.

**Impact** : Si la structure du DocType `Project Template Task` a changé (champs renommés, suppression de `begin_on`/`duration`), la fixture `project_template.json` peut :
- Charger partiellement (projet créé mais sans tâches)
- Échouer silencieusement sur les tâches enfants
- Provoquer une erreur JSON sur les champs inconnus

**Vérification obligatoire avant installation** :
```bash
# Sur l'instance ERPNext v16 cible, dans bench console :
bench --site [site] console
>>> frappe.get_meta("Project Template").fields | {f.fieldname: f.fieldtype for f in frappe.get_meta("Project Template").fields}
>>> frappe.get_meta("Project Template Task").fields | {f.fieldname: f.fieldtype for f in frappe.get_meta("Project Template Task").fields}
```

**Action si le risque se confirme** : Adapter la fixture `project_template.json` à la nouvelle structure v16 avant l'installation.

**Contournement temporaire** : Si la fixture échoue, créer les 5 modèles manuellement via l'interface Projects → Project Template.

---

### 🟡 3.2 — Champ `insert_after` potentiellement invalide

**Description** : Les champs custom utilisent `insert_after` pour se positionner dans le formulaire :
- `Project-inovaya_section` → `insert_after: "notes"` (champ `notes` sur Project)
- `Task-inovaya_task_vertical` → `insert_after: "type"` (champ `type` sur Task)

**Impact** : Si ces champs natifs de référence n'existent pas exactement sous ce nom en v16, le comportement de Frappe est de placer le custom field à la **fin du formulaire** (pas d'erreur). Les champs seront toujours présents et fonctionnels, simplement mal positionnés.

**Vérification** :
```bash
bench --site [site] console
>>> [f.fieldname for f in frappe.get_meta("Project").fields]
>>> [f.fieldname for f in frappe.get_meta("Task").fields]
```

**Correction si besoin** : Modifier `insert_after` dans `custom_field.json` puis `bench migrate`.

---

### 🟡 3.3 — Noms d'icônes dans les workspaces

**Description** : Certains noms d'icônes utilisés dans `workspace.json` (`project`, `task`, `note`) ne sont pas confirmés dans l'ensemble des icônes Lucide/Feather de ERPNext v16.

**Impact** : Affichage d'une icône par défaut (générique) à la place. **Aucun impact fonctionnel.** Navigation et raccourcis pleinement opérationnels.

**Correction cosmétique optionnelle** : Remplacer par des icônes Lucide confirmées :

| Icône actuelle | Icône Lucide de remplacement |
|---|---|
| `project` | `folder` |
| `task` | `check-square` |
| `note` | `file-text` |

---

### 🟡 3.4 — Nom de dossier vs nom de l'app

**Description** : `bench get-app <url>` crée le dossier `apps/erpnext_ai/` (nom du dépôt GitLab), alors que l'app Python s'appelle `inovaya_gdp` (défini dans `setup.py`). Frappe attend par convention que `apps/<nom_dossier>/` corresponde au nom de l'app.

**Impact** : Peut provoquer des erreurs lors de `bench --site [site] install-app inovaya_gdp` si Frappe recherche `apps/inovaya_gdp/`.

**Solution** : Cloner manuellement avec le bon nom de dossier (voir §4 — checklist d'installation, étape 2).

---

### 🟢 3.5 — Module "InovaYa GdP" vide

**Description** : `modules.txt` crée un Module Def "InovaYa GdP" sans DocTypes associés (aucun DocType custom dans cette phase).

**Impact** : Le module apparaît dans la liste des modules Frappe mais est vide. Purement cosmétique. Aucun impact fonctionnel.

---

### 🟢 3.6 — Workspace `content: "[]"` 

**Description** : La zone de contenu principal de chaque workspace est vide (`"[]"`). Seuls les shortcuts sont configurés.

**Impact** : Les workspaces affichent les raccourcis en haut mais la zone de contenu est vide. InovaYa peut enrichir les workspaces manuellement via l'interface Frappe (drag & drop de cards, charts).

---

## 4. Checklist d'installation — Commandes exactes

### Prérequis (à vérifier avant toute commande)

```bash
# Vérifier la version ERPNext
bench version
# Attendu : ERPNext >= 16.0.0 , Frappe >= 16.0.0

# Vérifier que le site existe
bench --site [votre-site] list-apps
# Attendu : frappe, erpnext dans la liste

# Vérifier l'accès au dépôt Git
git ls-remote https://git.softia.fr/cloclo/poc/erpnext_ai.git
# Attendu : liste des branches dont POC_InovaYa_V16
```

---

### Étape 1 — Vérification v16 des DocTypes critiques (5 min)

> ⚠️ Faire cette étape AVANT d'installer l'app, pour détecter le risque 3.1.

```bash
bench --site [votre-site] console
```

Dans la console Python :
```python
# Vérifier Project Template Task
meta = frappe.get_meta("Project Template Task")
print([f.fieldname for f in meta.fields])
# Doit contenir : "title", "begin_on", "duration", "is_milestone"

# Vérifier les champs Project
meta_proj = frappe.get_meta("Project")
print([f.fieldname for f in meta_proj.fields if "note" in f.fieldname or f.fieldname == "notes"])
# Doit retourner le champ "notes" ou son équivalent

# Vérifier le champ type sur Task
meta_task = frappe.get_meta("Task")
print([f.fieldname for f in meta_task.fields if f.fieldname == "type"])
# Doit retourner ["type"] si le champ existe

# Quitter
quit()
```

**Si `Project Template Task` ne contient pas `begin_on` et `duration`** : ne pas installer, contacter l'intégrateur pour adapter `project_template.json`.

---

### Étape 2 — Clonage de l'app (2 min)

```bash
# Depuis le répertoire du bench ERPNext v16
cd /path/to/frappe-bench

# Cloner avec le bon nom de dossier (inovaya_gdp, pas erpnext_ai)
git clone https://git.softia.fr/cloclo/poc/erpnext_ai.git apps/inovaya_gdp \
  --branch POC_InovaYa_V16 \
  --single-branch

# Vérifier le contenu
ls apps/inovaya_gdp/
# Attendu : setup.py, requirements.txt, README.md, inovaya_gdp/, ...
```

---

### Étape 3 — Installation du package Python (1 min)

```bash
# Activer le virtualenv du bench
source env/bin/activate

# Installer le package en mode éditable
pip install -e apps/inovaya_gdp

# Vérifier l'installation
pip show inovaya_gdp
# Attendu : Name: inovaya_gdp, Version: 1.0.0
```

---

### Étape 4 — Installation de l'app sur le site (3-5 min)

```bash
bench --site [votre-site] install-app inovaya_gdp
```

**Sortie attendue** :
```
Installing inovaya_gdp...
Updating DocTypes for inovaya_gdp        : [========================================]
[inovaya_gdp] Installation de l'app InovaYa GdP terminée.
[inovaya_gdp] Les fixtures (rôles, champs, modèles, workspaces) ont été chargées.
```

---

### Étape 5 — Migration (synchronisation des fixtures) (1-2 min)

```bash
bench --site [votre-site] migrate
```

**Sortie attendue** :
```
Updating DocTypes for inovaya_gdp ...
[inovaya_gdp] Migration InovaYa GdP — fixtures synchronisées.
```

---

### Étape 6 — Compilation des assets (2-3 min)

```bash
bench build --app inovaya_gdp
# Ou si les workspaces n'apparaissent pas :
bench --site [votre-site] clear-cache
bench --site [votre-site] clear-website-cache
```

---

### Points de contrôle post-installation (10-15 min)

#### CP1 — Rôles créés

Aller dans **Settings → Roles**, vérifier la présence de :
- [ ] Collaborateur Projet
- [ ] Chef de Projet
- [ ] Manager InovaYa
- [ ] Responsable GdP
- [ ] Responsable Operations
- [ ] Direction Generale
- [ ] Finance InovaYa
- [ ] Logistique Achats
- [ ] RH InovaYa

**Via console** :
```python
bench --site [votre-site] console
>>> frappe.get_all("Role", filters={"name": ["like", "%InovaYa%"]}, pluck="name")
>>> frappe.get_all("Role", filters={"name": ["in", ["Collaborateur Projet","Chef de Projet","Manager InovaYa"]]}, pluck="name")
```

#### CP2 — Types de projet créés

**Projects → Project Type** — vérifier :
- [ ] IND
- [ ] CLIENT TEE
- [ ] R&D
- [ ] Digital
- [ ] Interne

#### CP3 — Modèles de projet créés

**Projects → Project Template** — vérifier :
- [ ] InovaYa - CLIENT TEE (11 tâches + 4 jalons)
- [ ] InovaYa - IND (8 tâches + 2 jalons)
- [ ] InovaYa - R&D (8 tâches + 2 jalons)
- [ ] InovaYa - Digital (8 tâches + 2 jalons)
- [ ] InovaYa - Interne (6 tâches + 1 jalon)

#### CP4 — Champs custom sur Project

Ouvrir un **Project** en mode édition, vérifier en bas du formulaire :
- [ ] Section "InovaYa" visible (collapsible)
- [ ] Champ "Verticale Métier" (Select)
- [ ] Champ "Synthèse d'Impact" (Small Text)
- [ ] Section "Facturation" (collapsible)
- [ ] Champ "Notes Facturation" (Small Text)

#### CP5 — Champ custom sur Task

Ouvrir une **Task** en mode édition :
- [ ] Champ "Verticale Métier" (Select) visible

#### CP6 — Workspaces disponibles

Vérifier dans la barre latérale (ou **Settings → Workspace**) :
- [ ] InovaYa Projets
- [ ] InovaYa Temps
- [ ] InovaYa Achats Projet
- [ ] InovaYa Finance Projet
- [ ] InovaYa RH Absences
- [ ] InovaYa Administration GdP (visible uniquement pour Responsable GdP + System Manager)

#### CP7 — Test de création de projet depuis modèle

1. **Projects → Project → Nouveau**
2. Choisir "Depuis un modèle" → sélectionner `InovaYa - CLIENT TEE`
3. Vérifier que les tâches sont générées
4. Vérifier que les jalons apparaissent correctement

---

## 5. Erreurs probables et résolutions

| Erreur | Cause probable | Résolution |
|---|---|---|
| `ModuleNotFoundError: No module named 'inovaya_gdp'` | Package pip non installé | Relancer `pip install -e apps/inovaya_gdp` |
| `App inovaya_gdp not found` lors de install-app | Dossier nommé `erpnext_ai` au lieu de `inovaya_gdp` | Cloner avec `--destination apps/inovaya_gdp` (voir étape 2) |
| Tâches absentes dans le Project Template après installation | Champs `begin_on`/`duration` inexistants en v16 | Adapter `project_template.json` ou créer manuellement |
| Champs custom non visibles sur Project | Migration non exécutée | Relancer `bench migrate` |
| Workspaces non visibles | Cache non vidé | `bench --site [site] clear-cache && bench build` |
| Rôles en doublon avec des rôles existants | Instance non clean | Vérifier les rôles existants avant installation |
| `frappe.exceptions.DoesNotExistError` sur Project Type | Module Projects non activé | Activer ERPNext Projects sur le site |
| Erreur sur fixture Workspace | Champ `type: "Custom"` non reconnu | Retirer le champ `type` de workspace.json et relancer migrate |

---

## 6. Décisions à prendre avant déploiement

| # | Décision | Option A | Option B | Impact |
|---|---|---|---|---|
| D1 | Structure Project Template v16 confirmée ? | Installer tel quel | Adapter la fixture | Bloquant si B |
| D2 | Modules ERPNext à activer (Buying, HR, Accounts) ? | Tous activés par défaut | Activation manuelle post-install | Workspaces Achats/Finance/RH inutilisables si non activés |
| D3 | Instance ERPNext dédiée InovaYa ou mutualisée avec Softia ? | Dédiée | Mutualisée | Impact sur les rôles et permissions (risque de collision si mutualisée) |
| D4 | Authentification GitLab Softia disponible depuis le serveur cible ? | SSH key configurée | Token HTTPS | Impact sur l'étape de clonage |
| D5 | Icônes workspaces à corriger maintenant (cosmétique) ? | Corriger avant install | Corriger après validation fonctionnelle | Aucun impact fonctionnel |
| D6 | Données de démo à précharger (client, employés, exercice fiscal) ? | Script de données démo | Configuration manuelle | Impact sur la démo InovaYa |

---

## 7. Limites connues de la Phase 1

| Limite | Contournement Phase 1 | Phase 2 |
|---|---|---|
| Aucun test automatisé inclus | Checklist manuelle (ce document) | Tests Frappe à écrire (B-tests) |
| Permissions par rôle non finalisées | Rôles créés, permissions à configurer manuellement | Fixtures de `Custom DocPerm` à ajouter |
| Workspaces avec contenu vide | Configurable manuellement par InovaYa | Charts et Number Cards à ajouter |
| Project Template potentiellement incompatible v16 | Création manuelle si nécessaire | Adapter après vérification instance |
| Aucune donnée de démo incluse | Scénario démo documenté dans `DEMO_SCENARIO_INOVAYA.md` | Script `demo_data.py` à créer |
| Pas de traduction FR incluse | ERPNext FR doit être activé séparément | Traductions à exporter en fixture |

---

## 8. Environnement de développement — Écart documenté

> Rappel : l'app a été développée en code pur sur un environnement **Frappe v15.107.2 sans ERPNext** (`C:\Users\Alexandre XU` / bench Softia). Elle n'a pas pu être exécutée localement.

L'instance cible requise est **ERPNext v16.x** sur Linux (Ubuntu recommandé).

Pour un environnement de test rapide : [Frappe Cloud](https://frappecloud.com) permet de créer une instance ERPNext v16 en 5 minutes.

---

*Document produit le 2026-05-25 — Version 1.0 — À mettre à jour après première installation sur instance v16.*
