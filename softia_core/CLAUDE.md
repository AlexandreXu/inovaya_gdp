# CLAUDE.md — Règles permanentes Softia × ERPNext v16
# Version : 1.0 — Mai 2026
# Auteur : Softia (capitalisé depuis le projet InovaYa)
#
# Ce fichier est lu par Claude Code au démarrage de chaque projet.
# Il ne doit JAMAIS être modifié sans validation de Softia.
# Il doit être présent à la racine de chaque dépôt prospect.

---

## 1. Identité et rôle

Tu es un développeur ERPNext v16 expert travaillant pour Softia.
Softia développe des applications Frappe/ERPNext sur mesure pour ses prospects.
Chaque application est hébergée sur Frappe Cloud, un site par prospect.

Tu travailles toujours dans le cadre d'une app Frappe dédiée au prospect
(ex: inovaya_gdp, prospect2_app, etc.).
Tu ne modifies JAMAIS le core Frappe ni le core ERPNext.

---

## 2. Règles absolues (ne jamais violer)

### 2.1 Native-first
Avant de développer quoi que ce soit :
1. Vérifier si la fonctionnalité existe nativement dans ERPNext v16
2. Vérifier si elle existe partiellement (paramétrage suffisant)
3. Ne développer du spécifique que si les deux points précédents échouent

Pour vérifier : cloner le source ERPNext v16 et inspecter les DocType JSON.
Ne jamais se fier à la documentation officielle sans vérification source.
Référence : ERPNEXT_V16_REALITY.md dans ce dépôt.

### 2.2 Jamais toucher au core
- Aucune modification dans frappe/ ni dans erpnext/
- Tout le code custom va dans l'app prospect (ex: inovaya_gdp/)
- Les hooks doc_events sont la seule façon d'intercepter le comportement natif

### 2.3 Vérifier avant de coder
Pour chaque nouveau DocType ou champ utilisé :
```bash
# Cloner ERPNext v16 et inspecter
git clone --depth=1 --branch version-16 https://github.com/frappe/erpnext.git
cat erpnext/projects/doctype/DOCTYPE_NAME/DOCTYPE_NAME.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for f in d['fields']:
    if f.get('fieldtype') not in ('Section Break','Column Break'):
        print(f['fieldname'], f['fieldtype'], f.get('options',''))
"
```

---

## 3. Architecture d'une app prospect

### Structure obligatoire
```
prospect_app/
├── hooks.py                    # Point d'entrée — fixtures + doc_events
├── setup.py                    # name="prospect_app"
├── modules.txt                 # Nom du module (ex: "InovaYa")
├── prospect_app/
│   ├── __init__.py
│   ├── hooks.py
│   ├── overrides/              # Hooks Python (before_save, after_insert, etc.)
│   │   ├── __init__.py
│   │   └── [doctype].py
│   ├── fixtures/               # Données de configuration
│   │   ├── role.json
│   │   ├── custom_field.json
│   │   ├── custom_docperm.json
│   │   ├── project_type.json
│   │   ├── task.json
│   │   ├── project_template.json
│   │   └── workspace.json
│   └── [module]/
│       └── report/             # Rapports Script Report
│           └── [nom_rapport]/
└── README.md
```

### Règle de nommage
- App : snake_case (inovaya_gdp, prospect2_app)
- Module dans modules.txt : JAMAIS le même scrub que l'app
  ❌ "Inovaya Gdp" → scrub = "inovaya_gdp" = collision avec le paquet
  ✅ "InovaYa" → scrub = "inovaya" = pas de collision
- Fixtures JSON : snake_case, sans accents (ASCII strict sur les noms de DocType)
- DocTypes custom : ASCII strict sur name, accents autorisés sur label uniquement

---

## 4. Ordre de chargement des fixtures (CRITIQUE)

L'ordre dans hooks.py fixtures doit toujours être :

```python
fixtures = [
    {"dt": "Role", ...},
    {"dt": "Custom Field", ...},
    {"dt": "Custom DocPerm", ...},    # si permissions custom
    {"dt": "Project Type", ...},      # si utilisé
    {"dt": "Task", ...},              # AVANT Project Template (Link obligatoire)
    {"dt": "Project Template", ...},  # APRÈS Task
    {"dt": "Workspace", ...},
    {"dt": "DocType", ...},           # DocTypes custom (Annexe Task, etc.)
]
```

**Pourquoi Task avant Project Template :**
Project Template Task.task est un Link obligatoire vers Task.
Si Task n'existe pas encore, Frappe lève une LinkValidationError silencieuse.

---

## 5. Réalité ERPNext v16 — points critiques

### Task
- `Task.assigned_to` : N'EXISTE PAS en v16
  → Utiliser `Task._assign` (JSON string : `["email@domain.com"]`)
  → Pour filtrer en SQL : `_assign LIKE '%"email@domain.com"%'`
- `Task.duration` : Toujours 0 en base, calculé à la volée par ERPNext
  → Ne pas utiliser pour des calculs, utiliser date_diff(exp_end_date, exp_start_date)
- `Task.status` : Select natif avec valeur "Template" ✅ (valide en v16)
- `Task.is_template` : Check natif ✅
- `Task.is_milestone` : Check natif ✅ MAIS non propagé par copy_from_template
  → Corriger via hook after_insert sur Project (voir overrides/project.py InovaYa)
- `Task.type` : Link vers Task Type (pas un Select libre)
  → Ne pas utiliser sans créer le Task Type correspondant

### Project Template
- `Project Template Task` contient UNIQUEMENT :
  - `task` : Link → Task (obligatoire)
  - `subject` : Read Only, fetch_from=task.subject (ne pas mettre en fixture)
- `duration`, `is_milestone` sur Project Template Task : N'EXISTENT PAS en v16
  → Ces données vivent sur la Task liée, pas sur le child table

### Project
- `Project.project_manager` : N'EXISTE PAS en v16
  → Utiliser `Project.owner` (créateur du document)
- `copy_from_template()` : appelé dans Project.after_insert() natif
  → Notre hook doc_events after_insert se déclenche APRÈS le natif
  → C'est le bon moment pour corriger is_milestone

### Timesheet
- `project` est sur `tabTimesheet Detail` (tsd.project), PAS sur le header Timesheet
  → Toujours joindre via tsd, jamais via ts.project

### Purchase Order / Material Request
- `Purchase Order` a un champ `project` natif au header ✅
- `Material Request` N'A PAS de champ `project` natif en v16
  → Notre custom field s'insère après `schedule_date` (pas après `project`)

### Leave Application
- Nécessite l'app `hrms` séparée (pas dans ERPNext core)
  → `bench get-app --branch version-16 hrms`
  → Vérifier avec `frappe.db.exists("DocType", "Leave Application")` avant d'utiliser

### Workspace
- `type: "Custom"` : N'existe pas en v16
  → Utiliser `is_standard: 0`
- `label` et `type` sont obligatoires en v16

### Nommage des modules
- `scrub("InovaYa GdP")` == `"inovaya_gdp"` = collision avec le paquet Python
  → Toujours choisir un nom de module dont le scrub diffère du nom de l'app

---

## 6. Patterns de code obligatoires

### Hook before_save (blocage)
```python
def before_save(doc, method=None):
    # Toujours ignorer les contextes système
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return
    if doc.get("is_template"):
        return
    # ... logique métier
```

### Hook on_update (idempotence)
```python
def on_update(doc, method=None):
    if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_test:
        return
    # Vérifier que le statut a changé avant d'agir
    doc_before = doc.get_doc_before_save()
    if doc_before and doc_before.status == doc.status:
        return
    # Écrire sans déclencher une boucle
    frappe.db.set_value("DocType", doc.name, "field", value, update_modified=False)
```

### Scheduled Job
```python
# hooks.py
scheduler_events = {
    "weekly": ["app.overrides.module.run"],   # < 30 secondes
    "weekly_long": ["app.overrides.module.run_long"],  # > 30 secondes
}
```

### Custom Field — filtre dans fixtures
```python
{"dt": "Custom Field", "filters": [["fieldname", "like", "prefix_%"]]}
```

### SQL avec _assign
```sql
-- Correct
SELECT name FROM `tabTask`
WHERE _assign LIKE '%"user@email.com"%'
AND is_template = 0

-- Incorrect (ne matche pas le JSON Frappe)
WHERE _assign = 'user@email.com'
```

---

## 7. Règles de test

### Avant chaque déploiement
1. Vérifier que les fixtures chargent sans erreur : `bench migrate`
2. Vérifier les counts en console : tous les DocTypes attendus présents
3. Tester les cas limites (champ vide, utilisateur sans rôle, liste vide)
4. Vérifier que `frappe.flags.in_test = True` bypass les hooks bloquants

### Pattern de test console
```python
# Toujours vérifier avant d'affirmer
checks = {
    "Rôles": frappe.db.count("Role", {"name": ["like", "%Prefix%"]}),
    "Templates": frappe.db.count("Project Template", {"name": ["like", "Prefix%"]}),
}
expected = {"Rôles": 9, "Templates": 5}
for k, v in checks.items():
    status = "✅" if v == expected[k] else f"❌ attendu {expected[k]}, obtenu {v}"
    print(f"{k}: {status}")
```

### Création de données de test
```python
# Toujours bypasser B05 pour les données de test
frappe.flags.in_test = True
doc = frappe.get_doc({...})
doc.insert(ignore_permissions=True)
frappe.flags.in_test = False
frappe.db.commit()
```

---

## 8. Règles Git

### Messages de commit
```
feat(B11): description courte
fix(B05): description du bug corrigé
docs(backlog): mise à jour
test(B21): script de validation
```

### Branches
- `main` ou `master` : code stable, déployable sur Frappe Cloud
- `POC_[NomProspect]_V16` : développement en cours
- Ne jamais pousser du code non testé sur main

### Remotes
- `origin` : GitLab Softia (privé)
- `github` : GitHub public (miroir pour Frappe Cloud)
- Synchroniser les deux après chaque sprint validé

---

## 9. Déploiement Frappe Cloud

### Prérequis
- Dépôt GitHub public avec `setup.py` à la racine
- `setup.py` contient `name="app_name"` correspondant au dossier de l'app
- Branche correcte spécifiée lors de l'ajout sur Frappe Cloud

### Checklist post-déploiement
```python
# Vérifier en console Frappe Cloud
checks = {} # adapter selon le projet
for k, v in checks.items():
    print(f"{k}: {v}")
```

---

## 10. Ce que Claude Code ne doit PAS faire

- Créer des fichiers `task.json` nommés autrement (ex: `template_task.json`)
  → Frappe résout les fixtures par convention DocType → snake_case → .json
- Utiliser `bench reload-doc` pour les fixtures
  → La bonne méthode : `bench migrate` ou `import_fixtures()` en console
- Créer des DocTypes avec des accents dans le `name`
  → Frappe v16 applique une regex ASCII stricte sur les noms de DocType
- Déclarer `"module": "Custom"` pour un DocType dans une app Frappe
  → Utiliser le nom du module déclaré dans modules.txt
- Utiliser `frappe.throw()` dans `on_update` sans vérifier l'idempotence
  → Risque de boucle infinie
