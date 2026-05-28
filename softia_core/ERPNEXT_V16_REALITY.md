# ERPNEXT_V16_REALITY.md — La réalité ERPNext v16
# Version : 1.0 — Mai 2026
# Source : découvertes en conditions réelles — projet InovaYa (Softia)
# Usage : lire AVANT tout développement sur ERPNext v16
#
# Ce fichier documente les écarts entre la documentation officielle
# Frappe/ERPNext et ce qui existe réellement en base sur une instance v16.
# Chaque point a été vérifié soit par inspection du source GitHub
# (branche version-16) soit par test sur instance réelle.

---

## MÉTHODE DE VÉRIFICATION

Ne jamais faire confiance à la documentation officielle ou à la mémoire.
Toujours vérifier directement dans le source ERPNext v16 :

```bash
git clone --depth=1 --branch version-16 \
  https://github.com/frappe/erpnext.git erpnext_v16

# Inspecter un DocType
cat erpnext_v16/erpnext/projects/doctype/DOCTYPE/DOCTYPE.json \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'Autoname: {d.get(\"autoname\")}')
for f in d['fields']:
    if f.get('fieldtype') not in ('Section Break','Column Break','Tab Break','HTML'):
        req = '✓ REQUIS' if f.get('reqd') else ''
        ro = '(read_only)' if f.get('read_only') else ''
        fetch = f'fetch_from={f[\"fetch_from\"]}' if f.get('fetch_from') else ''
        opts = f.get('options','') or ''
        print(f'  {f[\"fieldname\"]:35s} {f.get(\"fieldtype\",\"\"):20s} {opts:25s} {req} {ro} {fetch}')
"
```

---

## MODULE PROJECTS

### DocType : Task

**Autoname :** `TASK-.YYYY.-.#####`

| Champ | Type | Notes |
|---|---|---|
| `subject` | Data | ✅ Obligatoire |
| `project` | Link → Project | Optionnel |
| `type` | Link → **Task Type** | ⚠️ Link, pas Select libre |
| `status` | Select | Open / Working / Pending Review / Overdue / **Template** / Completed / Cancelled |
| `priority` | Select | Low / Medium / High / Urgent |
| `is_template` | Check | ✅ Natif |
| `is_milestone` | Check | ✅ Natif |
| `duration` | Int | ⚠️ Toujours 0 en base — calculé à la volée |
| `exp_start_date` | Datetime | ⚠️ Datetime, pas Date |
| `exp_end_date` | Datetime | ⚠️ Datetime, pas Date |
| `expected_time` | Float | Heures allouées |
| `_assign` | JSON string | ⚠️ Pas un champ standard — `["email@domain.com"]` |
| `template_task` | Data | Référence vers la Task template source |
| `start` | Int | Offset en jours depuis le début du projet |
| `is_group` | Check | Tâche parent (groupe) |
| `parent_task` | Link → Task | Hiérarchie |

**Points critiques :**

❌ `Task.assigned_to` N'EXISTE PAS en v16
→ ERPNext utilise `Task._assign` (JSON string Frappe)
→ Format : `["user@email.com"]` ou `["user1@email.com","user2@email.com"]`
→ Pour filtrer en SQL : `_assign LIKE '%"user@email.com"%'`
→ Pour lire en Python : `json.loads(doc._assign or "[]")`
→ En Python sur un doc non sauvegardé : `doc.get("_assign")` (pas `doc._assign`)

❌ `Task.duration` est fonctionnellement mort
→ ERPNext ne l'écrit jamais en base
→ Calculer à la volée : `frappe.utils.date_diff(exp_end_date, exp_start_date)`

⚠️ `Task.status = "Template"` est une valeur valide en v16
→ Confirmé dans le source task.json branche version-16
→ Utiliser pour les tâches modèles plutôt que "Open"

⚠️ `Task.type` est un Link vers `Task Type`, pas un Select libre
→ Ne pas utiliser sans créer le document Task Type correspondant

⚠️ `Task.exp_start_date` et `Task.exp_end_date` sont des Datetime
→ Utiliser `DATE(exp_start_date)` dans les requêtes SQL
→ Sur les Annexe Task (custom), préférer le type Date pour simplifier

---

### DocType : Project

**Autoname :** `field:project_name`

| Champ | Type | Notes |
|---|---|---|
| `project_name` | Data | ✅ Obligatoire |
| `status` | Select | Open / Completed / Cancelled |
| `project_type` | Link → Project Type | |
| `project_template` | Link → Project Template | |
| `customer` | Link → Customer | |
| `company` | Link → Company | ✅ Obligatoire |
| `expected_start_date` | Date | |
| `expected_end_date` | Date | |
| `percent_complete_method` | Select | Manual / Task Completion / Task Progress / Task Weight |

**Points critiques :**

❌ `Project.project_manager` N'EXISTE PAS en v16
→ Utiliser `Project.owner` (créateur du document)
→ Ou ajouter un Custom Field si nécessaire

✅ `copy_from_template()` est appelé dans `Project.after_insert()` natif
→ Notre hook `doc_events after_insert` se déclenche APRÈS le natif
→ Les tâches sont donc déjà créées quand notre hook s'exécute

❌ `copy_from_template()` ne propage PAS `is_milestone`
→ Corriger via hook `after_insert` qui relit `template_task` sur chaque Task
→ Voir pattern dans overrides/project.py InovaYa (commit B27)

---

### DocType : Project Template

**Autoname :** Prompt (nom saisi manuellement)

| Champ | Type | Notes |
|---|---|---|
| `project_type` | Link → Project Type | |
| `tasks` | Table → **Project Template Task** | ✅ Obligatoire |
| `disabled` | Check | |

---

### DocType : Project Template Task (child table)

⚠️ Ce DocType ne contient QUE deux champs utiles :

| Champ | Type | Notes |
|---|---|---|
| `task` | Link → Task | ✅ Obligatoire |
| `subject` | Read Only | fetch_from=task.subject — alimenté automatiquement |

❌ `duration`, `is_milestone`, `begin_on`, `title` N'EXISTENT PAS en v16
→ Ces champs existaient en v14/v15 — supprimés en v16
→ Ces données vivent sur la Task liée, pas sur le child table
→ Ne jamais les mettre dans project_template.json

**Implication pour les fixtures :**
```json
// Correct
{"task": "InovaYa-TEE-01"}

// Incorrect — champs inexistants
{"task": "InovaYa-TEE-01", "duration": 5, "is_milestone": 0}
```

---

### DocType : Project Type

**Autoname :** `field:project_type`

| Champ | Type | Notes |
|---|---|---|
| `project_type` | Data | ✅ Obligatoire |
| `description` | Text | |

---

### DocType : Task Type

**Autoname :** Prompt

| Champ | Type | Notes |
|---|---|---|
| `weight` | Float | |
| `description` | Small Text | |

⚠️ Aucun fixture par défaut — instance clean = aucun Task Type
→ Ne pas utiliser `Task.type` sans créer explicitement le Task Type

---

## MODULE BUYING / ACCOUNTS

### DocType : Purchase Order

| Champ | Type | Notes |
|---|---|---|
| `project` | Link → Project | ✅ Natif au header |
| `items[].project` | Link → Project | ✅ Natif par ligne aussi |

✅ Champ `project` présent au header ET par ligne
→ Jointure B16 possible directement sur `po.project`

### DocType : Material Request

⚠️ `Material Request` N'A PAS de champ `project` natif en v16
→ Contrairement à Purchase Order
→ Notre custom field `inovaya_linked_task` s'insère après `schedule_date`
→ Ne pas faire `insert_after: "project"` sur Material Request

### DocType : Purchase Invoice

| Champ | Type | Notes |
|---|---|---|
| `project` | Link → Project | ✅ Natif au header |
| `items[].project` | Link → Project | ✅ Natif par ligne |
| `items[].purchase_order` | Link → Purchase Order | Traçabilité |

✅ Champ `project` présent — pas besoin de remonter via PO→PI

---

## MODULE HR (app hrms séparée)

⚠️ `hrms` N'EST PAS dans ERPNext core en v16
→ C'est une app séparée : `bench get-app --branch version-16 hrms`
→ Vérifier la présence avant tout usage :
```python
frappe.db.exists("DocType", "Leave Application")
```

### Installation
```bash
bench get-app --branch version-16 hrms
bench --site [site] install-app hrms
bench --site [site] migrate
```

### DocType : Leave Application (après installation hrms)

| Champ | Type | Notes |
|---|---|---|
| `employee` | Link → Employee | ✅ Obligatoire |
| `leave_type` | Link → Leave Type | ✅ Obligatoire |
| `from_date` | Date | ✅ Obligatoire |
| `to_date` | Date | ✅ Obligatoire |
| `status` | Select | Open / Approved / Rejected |

**Prérequis pour créer une Leave Application :**
1. Employee existant avec `user_id` renseigné
2. Leave Type existant (aucun par défaut — à créer)
3. Leave Allocation pour l'employé (à soumettre)
4. Holiday List assignée à l'employé

---

## MODULE FRAPPE (framework)

### Workspace (Frappe v16)

⚠️ `type: "Custom"` N'EXISTE PAS en v16
→ Utiliser `is_standard: 0`

⚠️ `label` est obligatoire en v16 (en plus de `name`)

**Structure minimale d'un Workspace en fixture :**
```json
{
  "doctype": "Workspace",
  "name": "Mon Workspace",
  "label": "Mon Workspace",
  "is_standard": 0,
  "module": "NomModule",
  "content": "[]"
}
```

### Icônes Workspace

⚠️ Toutes les icônes ne sont pas disponibles en v16
→ Icônes sûres (Lucide) : `folder`, `check-square`, `file-text`,
  `clock`, `users`, `bar-chart-2`, `settings`, `briefcase`
→ Icônes à éviter : `project`, `task`, `note` (non disponibles en v16)

---

## FRAPPE FRAMEWORK — COMPORTEMENTS

### Fixtures — Convention de nommage des fichiers

⚠️ Frappe résout les fixtures par convention :
`DocType name` → `snake_case` → `.json`

```
"Task"             → task.json             ✅
"Custom Field"     → custom_field.json     ✅
"Project Template" → project_template.json ✅
"Workspace"        → workspace.json        ✅
```

❌ `template_task.json` ne sera jamais chargé pour le DocType "Task"
→ Le fichier doit impérativement s'appeler `task.json`

### Fixtures — Filtre sur Task

```python
# Correct — filtre multi-conditions
{
    "dt": "Task",
    "filters": [
        ["name", "like", "Prefix-%"],
        ["is_template", "=", 1],
    ],
}
```

### Modules — Règle du scrub

⚠️ Frappe convertit le nom du module en snake_case (`scrub()`)
pour construire le chemin d'import Python.

```python
scrub("InovaYa GdP") == "inovaya_gdp"  # collision avec le paquet !
scrub("InovaYa")     == "inovaya"       # OK
scrub("ProspectGdP") == "prospectgdp"  # OK si app != prospectgdp
```

→ Le module déclaré dans `modules.txt` NE DOIT JAMAIS avoir
  le même scrub que le nom du paquet Python (dossier de l'app)

### doc_events — Ordre d'exécution

```
before_validate
validate
before_save
    → Notre hook before_save (doc_events)
after_insert (natif ERPNext — ex: copy_from_template)
    → Notre hook after_insert (doc_events) ← s'exécute APRÈS le natif
on_update
    → Notre hook on_update (doc_events)
```

### set_value sans boucle infinie

```python
# Pour écrire un champ sans déclencher on_update à nouveau
frappe.db.set_value(
    "DocType", doc.name, "field", value,
    update_modified=False  # critique
)
doc.field = value  # cohérence en mémoire
```

### Timesheet — Localisation du champ project

⚠️ `project` est sur `tabTimesheet Detail` (ligne), PAS sur `tabTimesheet` (header)

```sql
-- Correct
SELECT tsd.project, SUM(tsd.hours)
FROM `tabTimesheet Detail` tsd
JOIN `tabTimesheet` ts ON ts.name = tsd.parent
WHERE ts.docstatus = 1
AND tsd.project = %(project)s
GROUP BY tsd.project

-- Incorrect — ts.project n'existe pas
WHERE ts.project = %(project)s
```

### _assign — Format JSON Frappe

```python
# Lire de façon sûre
import json
assignees = json.loads(doc.get("_assign") or "[]")
# → ["user1@email.com", "user2@email.com"]

# Filtrer en SQL — les guillemets font partie du JSON
frappe.db.sql("""
    SELECT name FROM `tabTask`
    WHERE _assign LIKE %(pattern)s
""", {"pattern": f'%"{user_email}"%'})

# NE PAS utiliser doc._assign directement
# sur un doc non sauvegardé → AttributeError possible
```

### bench reload-doc vs bench migrate

```bash
# bench reload-doc = recharge la DÉFINITION d'un DocType
# NE PAS utiliser pour les fixtures de données
bench --site site.local reload-doc app module doctype

# bench migrate = charge les fixtures ET les définitions
# C'est la bonne commande pour les fixtures
bench --site site.local migrate

# Charger manuellement des fixtures en console
from frappe.utils.fixtures import import_fixtures
import_fixtures("app_name", "DocType Name")
frappe.db.commit()
```

---

## COMPATIBILITÉ v15 → v16

Si un client a des données en v15 à migrer :

| Champ v15 | Champ v16 | Action |
|---|---|---|
| `Project Template Task.title` | `Project Template Task.task` (Link) | Réécrire les fixtures |
| `Project Template Task.begin_on` | Supprimé | Mettre sur Task.start |
| `Workspace.type = "Custom"` | `Workspace.is_standard = 0` | Corriger les fixtures |
| `Task.assigned_to` | `Task._assign` (JSON) | Adapter les requêtes SQL |

---

## VERSIONS DES DÉPENDANCES (mai 2026)

Pour un bench ERPNext v16 fonctionnel :

```bash
# Node.js : version 18 obligatoire (pas 20)
node --version  # doit afficher v18.x.x

# Python : 3.10+ recommandé
python3 --version

# MariaDB : 10.6+
mysql --version

# Configuration MariaDB obligatoire
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

---

## CHECKLIST AVANT INSTALLATION SUR INSTANCE CLEAN

Après `bench --site [site] install-app [app]` et `bench migrate` :

```python
# Vérifier en console Frappe
# 1. Tous les DocTypes custom sont créés
# 2. Toutes les fixtures sont chargées (counts corrects)
# 3. Les permissions sont en place
# 4. Les hooks sont enregistrés

# Vérifier les hooks
import frappe
app_hooks = frappe.get_hooks("doc_events", app_name="[app_name]")
print(app_hooks)
# Doit afficher les doc_events déclarés dans hooks.py

# Vérifier les scheduled jobs
jobs = frappe.db.get_all("Scheduled Job Type",
    filters={"method": ["like", "%[app_name]%"]},
    fields=["name", "method", "frequency", "stopped"])
for j in jobs:
    print(j)
```
